"""VM-004D: OS-authenticated execution authority, still deny-only."""
from __future__ import annotations

from datetime import datetime, timezone
import json, os, re, tempfile
from pathlib import Path
from uuid import UUID, uuid4

from storos_execution_contract import (
    ACTION_CONTRACTS, ExecutionContractError, action_contract, backend_capabilities,
    non_execution_result, validate_execution_result, validate_planned_action,
)
from storos_preflight import PREFLIGHT_ROOT, run_vm_preflight
from storos_tasks import TASK_ROOT, read_task
from storos_vm_store import VM_INTENT_ROOT
from storos_agent import SNAPSHOT
from storos_config import CONFIG_ROOT

AUTHORITY_ROOT = Path('/var/lib/storos/execution-authority')
POLICY_FILE = AUTHORITY_ROOT / 'policy.json'
DECISION_ROOT = AUTHORITY_ROOT / 'decisions'
POLICY_SCHEMA_VERSION = 1
AUTHORITY_SCHEMA_VERSION = 1

class AuthorityError(ValueError):
    pass

def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def _uuid(value, field):
    try: return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc: raise AuthorityError(f'{field} inválido') from exc

def _text(value, field, maximum=160):
    if not isinstance(value, str): raise AuthorityError(f'{field} inválido')
    value=value.strip()
    if not value or len(value)>maximum or any(ord(c)<32 for c in value): raise AuthorityError(f'{field} inválido')
    return value

def _identity_id(value):
    value=_text(value,'identity_id',128)
    if not re.fullmatch(r'[A-Za-z0-9._:@-]+',value): raise AuthorityError('identity_id inválido')
    return value

def _principal_id(value, field):
    if not isinstance(value,int) or isinstance(value,bool) or value<0: raise AuthorityError(f'{field} inválido')
    return value

def _scope(value):
    value=_text(value,'scope',96); prefix='vm:action:'
    if not value.startswith(prefix): raise AuthorityError('scope fora do contrato VM-004D')
    action=value[len(prefix):]
    if action!='*' and action not in ACTION_CONTRACTS: raise AuthorityError('scope referencia ação desconhecida')
    return value

def _selector(value):
    return '*' if value=='*' else _uuid(value,'vm_uuid selector')

def _fsync_dir(path):
    fd=os.open(Path(path),os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def _write_json(path,data,mode=0o640):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            os.fchmod(f.fileno(),mode); json.dump(data,f,ensure_ascii=True,allow_nan=False,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path); _fsync_dir(path.parent)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def identity_record(identity_id, uid, gid, scopes, vm_uuids, enabled=True):
    if not isinstance(enabled,bool) or not isinstance(scopes,list) or not scopes or not isinstance(vm_uuids,list) or not vm_uuids:
        raise AuthorityError('registro de identidade inválido')
    return {'identity_id':_identity_id(identity_id),'enabled':enabled,'uid':_principal_id(uid,'uid'),'gid':_principal_id(gid,'gid'),
            'scopes':sorted({_scope(x) for x in scopes}),'vm_uuids':sorted({_selector(x) for x in vm_uuids})}

def validate_identity_policy(policy):
    if not isinstance(policy,dict) or set(policy)!={'schema_version','generation','identities'} or policy.get('schema_version')!=1:
        raise AuthorityError('Política de identidade incompatível')
    generation=policy.get('generation')
    if not isinstance(generation,int) or isinstance(generation,bool) or generation<1: raise AuthorityError('generation inválida')
    identities=policy.get('identities')
    if not isinstance(identities,list) or not identities: raise AuthorityError('Política sem identidades')
    out=[]; ids=set(); principals=set()
    for item in identities:
        if not isinstance(item,dict) or set(item)!={'identity_id','enabled','uid','gid','scopes','vm_uuids'}: raise AuthorityError('Identidade incompatível')
        iid=_identity_id(item['identity_id']); enabled=item['enabled']; uid=_principal_id(item['uid'],'uid'); gid=_principal_id(item['gid'],'gid')
        if iid in ids or (uid,gid) in principals: raise AuthorityError('identidade/principal duplicado')
        if not isinstance(enabled,bool): raise AuthorityError('enabled inválido')
        scopes=item['scopes']; selectors=item['vm_uuids']
        if not isinstance(scopes,list) or not scopes or not isinstance(selectors,list) or not selectors: raise AuthorityError('Escopo/VMs inválidos')
        ids.add(iid); principals.add((uid,gid))
        out.append({'identity_id':iid,'enabled':enabled,'uid':uid,'gid':gid,'scopes':sorted({_scope(x) for x in scopes}),'vm_uuids':sorted({_selector(x) for x in selectors})})
    return {'schema_version':1,'generation':generation,'identities':sorted(out,key=lambda x:x['identity_id'])}

def write_identity_policy(policy,path=POLICY_FILE):
    policy=validate_identity_policy(policy); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); os.chmod(path.parent,0o750); _write_json(path,policy,0o640); return policy

def read_identity_policy(path=POLICY_FILE):
    return validate_identity_policy(json.loads(Path(path).read_text()))

def authenticate_local_identity(uid,gid,policy):
    policy=validate_identity_policy(policy); uid=_principal_id(uid,'uid'); gid=_principal_id(gid,'gid'); matched=None
    for item in policy['identities']:
        if item['enabled'] and item['uid']==uid and item['gid']==gid: matched=item
    if matched is None: return {'authenticated':False,'identity_id':None,'policy_generation':policy['generation'],'uid':uid,'gid':gid,'scopes':[],'vm_uuids':[]}
    return {'authenticated':True,'identity_id':matched['identity_id'],'policy_generation':policy['generation'],'uid':uid,'gid':gid,'scopes':list(matched['scopes']),'vm_uuids':list(matched['vm_uuids'])}

def authenticate_current_process(policy):
    return authenticate_local_identity(os.geteuid(),os.getegid(),policy)

def authorize_execution_action(identity,action_type,vm_uuid):
    try: action_type=action_contract(action_type)['type']
    except ExecutionContractError as exc: raise AuthorityError(str(exc)) from exc
    vm_uuid=_uuid(vm_uuid,'vm_uuid')
    if not isinstance(identity,dict): raise AuthorityError('Contexto de identidade inválido')
    base={'identity_id':identity.get('identity_id'),'action_type':action_type,'vm_uuid':vm_uuid,'matched_scope':None}
    if identity.get('authenticated') is not True: return {**base,'granted':False,'reason_code':'identity_not_authenticated'}
    scopes=identity.get('scopes'); selectors=identity.get('vm_uuids')
    if not isinstance(scopes,list) or not isinstance(selectors,list): raise AuthorityError('Contexto de identidade incompatível')
    exact=f'vm:action:{action_type}'; matched=exact if exact in scopes else ('vm:action:*' if 'vm:action:*' in scopes else None)
    if matched is None: return {**base,'granted':False,'reason_code':'scope_missing'}
    base['matched_scope']=matched
    if '*' not in selectors and vm_uuid not in selectors: return {**base,'granted':False,'reason_code':'vm_not_allowed'}
    return {**base,'granted':True,'reason_code':'authorized'}

class DenyOnlyCapabilityProvider:
    provider_id='disabled-contract-provider'; provider_kind='contract-negotiation'
    def __init__(self):
        self._backend=backend_capabilities()
        if self._backend.get('mutating_available') is not False: raise AuthorityError('backend mutável incompatível')
    def describe(self):
        return {'provider_id':self.provider_id,'provider_kind':self.provider_kind,'backend_id':self._backend['backend_id'],
                'mutating_available':False,'apply_method_available':False,'contract_actions':sorted(ACTION_CONTRACTS)}
    def negotiate(self,action_type):
        try: action_type=action_contract(action_type)['type']
        except ExecutionContractError as exc: raise AuthorityError(str(exc)) from exc
        item=self._backend.get('actions',{}).get(action_type)
        if not isinstance(item,dict) or item.get('supported') is not False: raise AuthorityError('capacidade mutável inesperada')
        return {'action_type':action_type,'contract_supported':True,'mutating_supported':False,'eligible':False,
                'reason_code':self._backend.get('reason_code','mutating_backend_unavailable')}

def negotiate_execution_capabilities(action_types,provider=None):
    if not isinstance(action_types,list) or not action_types: raise AuthorityError('Lista de ações inválida')
    provider=provider or DenyOnlyCapabilityProvider()
    if hasattr(provider,'apply'): raise AuthorityError('provider não pode expor apply')
    desc=provider.describe()
    if desc.get('mutating_available') is not False or desc.get('apply_method_available') is not False: raise AuthorityError('provider mutável incompatível')
    return {'provider':desc,'actions':[provider.negotiate(x) for x in action_types],'all_eligible':False}

def _validate_inputs(task,preflight):
    if not isinstance(task,dict) or not isinstance(preflight,dict): raise AuthorityError('Tarefa/preflight inválidos')
    task_id=_uuid(task.get('task_id'),'task_id'); vm_uuid=_uuid(task.get('vm_uuid'),'vm_uuid'); preflight_id=_uuid(preflight.get('preflight_id'),'preflight_id')
    if _uuid(preflight.get('task_id'),'preflight.task_id')!=task_id or _uuid(preflight.get('vm_uuid'),'preflight.vm_uuid')!=vm_uuid: raise AuthorityError('Preflight não pertence à tarefa/VM')
    if preflight.get('status')!='blocked' or preflight.get('can_execute') is not False or preflight.get('executed') is not False: raise AuthorityError('preflight não está fail-closed')
    if task.get('schema_version')!=3 or task.get('status')!='planned' or task.get('mode')!='dry_run' or task.get('executable') is not False: raise AuthorityError('tarefa incompatível')
    plan=task.get('plan')
    if not isinstance(plan,dict) or plan.get('status')!='changes_planned' or plan.get('mode')!='dry_run' or plan.get('can_apply') is not False: raise AuthorityError('plano incompatível')
    pre=task.get('preconditions'); obs=preflight.get('observed')
    if not isinstance(pre,dict) or not isinstance(obs,dict): raise AuthorityError('fingerprint ausente')
    fps=(pre.get('plan_fingerprint_sha256'),plan.get('plan_fingerprint_sha256'),obs.get('plan_fingerprint_sha256'))
    if not all(isinstance(x,str) and re.fullmatch(r'[0-9a-f]{64}',x) for x in fps) or len(set(fps))!=1: raise AuthorityError('drift/fingerprint inválido')
    actions=plan.get('actions')
    if not isinstance(actions,list) or not actions: raise AuthorityError('plano sem ações')
    blockers=preflight.get('blockers')
    if not isinstance(blockers,list): raise AuthorityError('preflight sem blockers válidos')
    blocker_codes=[]
    for item in blockers:
        if not isinstance(item,dict) or not isinstance(item.get('code'),str) or not item['code']:
            raise AuthorityError('blocker de preflight inválido')
        if item['code'] not in blocker_codes: blocker_codes.append(item['code'])
    if not {'feature_gate_disabled','mutating_backend_unavailable'}.issubset(blocker_codes):
        raise AuthorityError('preflight não preserva blockers obrigatórios')
    return task_id,preflight_id,vm_uuid,fps[0],actions,blocker_codes

def evaluate_execution_authority(task,preflight,uid,gid,policy,provider=None):
    task_id,pid,vm_uuid,fp,actions,blockers=_validate_inputs(task,preflight)
    identity=authenticate_local_identity(uid,gid,policy); provider=provider or DenyOnlyCapabilityProvider()
    normalized_actions=[]
    for action in actions:
        try: normalized_actions.append(validate_planned_action(action,vm_uuid))
        except ExecutionContractError as exc: raise AuthorityError(f'Ação fora do contrato: {exc}') from exc
    caps=negotiate_execution_capabilities([a['action_type'] for a in normalized_actions],provider)
    decisions=[]; grants=[]
    for normalized,cap in zip(normalized_actions,caps['actions']):
        auth=authorize_execution_action(identity,normalized['action_type'],vm_uuid); grants.append(auth['granted'])
        reason=cap['reason_code'] if auth['granted'] else auth['reason_code']
        result=validate_execution_result(non_execution_result(normalized['action_type'],vm_uuid,reason))
        decisions.append({'sequence':normalized['sequence'],'action_type':normalized['action_type'],'authorization':auth,'capability':cap,'eligible':False,'result':result})
    all_auth=bool(grants) and all(grants)
    if not identity['authenticated']: blockers.append('identity_authentication_failed')
    if not all_auth: blockers.append('authorization_denied')
    for code in ('capability_negotiation_denied','mutating_backend_unavailable'):
        if code not in blockers: blockers.append(code)
    record={'schema_version':1,'authority_check_id':str(uuid4()),'task_id':task_id,'preflight_id':pid,'vm_uuid':vm_uuid,'plan_fingerprint_sha256':fp,
            'checked_at':_now(),'status':'denied','can_execute':False,'executed':False,
            'identity':{'authenticated':identity['authenticated'],'identity_id':identity['identity_id'],'policy_generation':identity['policy_generation'],'uid':identity['uid'],'gid':identity['gid']},
            'requirements':{'preflight_passed':False,'identity_authenticated':identity['authenticated'],'all_actions_authorized':all_auth,
                            'capabilities_satisfied':False,'mutating_backend_available':False,'feature_gate_enabled':False},
            'capability_provider':caps['provider'],'blocker_codes':blockers,'actions':decisions}
    return _validate_authority_record(record)

def _validate_authority_record(record):
    expected={'schema_version','authority_check_id','task_id','preflight_id','vm_uuid','plan_fingerprint_sha256','checked_at','status','can_execute','executed','identity','requirements','capability_provider','blocker_codes','actions'}
    if not isinstance(record,dict) or set(record)!=expected or record.get('schema_version')!=1: raise AuthorityError('Registro incompatível')
    for f in ('authority_check_id','task_id','preflight_id','vm_uuid'): _uuid(record.get(f),f)
    if not isinstance(record.get('plan_fingerprint_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',record['plan_fingerprint_sha256']): raise AuthorityError('fingerprint inválido')
    if record.get('status')!='denied' or record.get('can_execute') is not False or record.get('executed') is not False: raise AuthorityError('VM-004D não pode executar')

    ident=record.get('identity')
    if not isinstance(ident,dict) or set(ident)!={'authenticated','identity_id','policy_generation','uid','gid'} or not isinstance(ident['authenticated'],bool): raise AuthorityError('identidade auditada inválida')
    if not isinstance(ident['policy_generation'],int) or isinstance(ident['policy_generation'],bool) or ident['policy_generation']<1: raise AuthorityError('policy_generation inválida')
    _principal_id(ident['uid'],'uid'); _principal_id(ident['gid'],'gid')
    if ident['authenticated']: _identity_id(ident['identity_id'])
    elif ident['identity_id'] is not None: raise AuthorityError('identity_id inesperado')

    req=record.get('requirements'); keys={'preflight_passed','identity_authenticated','all_actions_authorized','capabilities_satisfied','mutating_backend_available','feature_gate_enabled'}
    if not isinstance(req,dict) or set(req)!=keys or not all(isinstance(req[k],bool) for k in keys): raise AuthorityError('requisitos inválidos')
    if req['preflight_passed'] is not False or req['capabilities_satisfied'] is not False or req['mutating_backend_available'] is not False or req['feature_gate_enabled'] is not False: raise AuthorityError('requisito mutável satisfeito indevidamente')
    if req['identity_authenticated'] is not ident['authenticated']: raise AuthorityError('autenticação divergente')

    provider=record.get('capability_provider')
    provider_keys={'provider_id','provider_kind','backend_id','mutating_available','apply_method_available','contract_actions'}
    if not isinstance(provider,dict) or set(provider)!=provider_keys: raise AuthorityError('provider inválido')
    if provider.get('mutating_available') is not False or provider.get('apply_method_available') is not False: raise AuthorityError('provider mutável incompatível')
    if provider.get('contract_actions')!=sorted(ACTION_CONTRACTS): raise AuthorityError('catálogo de capacidades divergente')

    blockers=record.get('blocker_codes')
    if not isinstance(blockers,list) or not blockers or len(blockers)!=len(set(blockers)) or not all(isinstance(x,str) and x for x in blockers): raise AuthorityError('blockers inválidos')
    mandatory={'feature_gate_disabled','mutating_backend_unavailable','capability_negotiation_denied'}
    if not mandatory.issubset(blockers): raise AuthorityError('blockers obrigatórios ausentes')

    actions=record.get('actions')
    if not isinstance(actions,list) or not actions: raise AuthorityError('sem decisões')
    grants=[]
    for d in actions:
        if not isinstance(d,dict) or set(d)!={'sequence','action_type','authorization','capability','eligible','result'}: raise AuthorityError('decisão inválida')
        if not isinstance(d['sequence'],int) or isinstance(d['sequence'],bool) or d['sequence']<1: raise AuthorityError('sequence inválida')
        try: action_type=action_contract(d['action_type'])['type']
        except ExecutionContractError as exc: raise AuthorityError('ação auditada inválida') from exc
        auth=d['authorization']; auth_keys={'identity_id','action_type','vm_uuid','matched_scope','granted','reason_code'}
        if not isinstance(auth,dict) or set(auth)!=auth_keys or not isinstance(auth['granted'],bool): raise AuthorityError('autorização auditada inválida')
        if auth['action_type']!=action_type or _uuid(auth['vm_uuid'],'authorization.vm_uuid')!=record['vm_uuid']: raise AuthorityError('autorização diverge da ação/VM')
        if auth['identity_id']!=ident['identity_id']: raise AuthorityError('autorização diverge da identidade')
        _text(auth['reason_code'],'authorization.reason_code',96)
        if auth['granted']:
            _scope(auth['matched_scope'])
            if not ident['authenticated'] or auth['reason_code']!='authorized': raise AuthorityError('concessão de autorização inconsistente')
        elif auth['matched_scope'] is not None:
            _scope(auth['matched_scope'])
        grants.append(auth['granted'])

        cap=d['capability']; cap_keys={'action_type','contract_supported','mutating_supported','eligible','reason_code'}
        if not isinstance(cap,dict) or set(cap)!=cap_keys: raise AuthorityError('capacidade auditada inválida')
        if cap['action_type']!=action_type or cap['contract_supported'] is not True or cap['mutating_supported'] is not False or cap['eligible'] is not False: raise AuthorityError('capacidade incompatível')
        _text(cap['reason_code'],'capability.reason_code',96)
        if d['eligible'] is not False: raise AuthorityError('ação elegível indevidamente')
        r=validate_execution_result(d['result'])
        if r['action_type']!=action_type or r['vm_uuid']!=record['vm_uuid'] or r['executed'] is not False or r['applied'] is not False: raise AuthorityError('resultado mutável/divergente')

    all_auth=bool(grants) and all(grants)
    if req['all_actions_authorized'] is not all_auth: raise AuthorityError('resumo de autorização divergente')
    if not ident['authenticated'] and 'identity_authentication_failed' not in blockers: raise AuthorityError('blocker de autenticação ausente')
    if not all_auth and 'authorization_denied' not in blockers: raise AuthorityError('blocker de autorização ausente')
    if all_auth and 'authorization_denied' in blockers: raise AuthorityError('blocker de autorização indevido')
    return record

def run_execution_authority_check(task_id,task_root=TASK_ROOT,intent_root=VM_INTENT_ROOT,snapshot_path=SNAPSHOT,config_root=CONFIG_ROOT,preflight_root=PREFLIGHT_ROOT,policy_path=POLICY_FILE,decision_root=DECISION_ROOT):
    task=read_task(task_id,task_root)
    preflight=run_vm_preflight(task_id,task_root=task_root,intent_root=intent_root,snapshot_path=snapshot_path,config_root=config_root,preflight_root=preflight_root)
    task=read_task(task_id,task_root); policy=read_identity_policy(policy_path); identity=authenticate_current_process(policy)
    record=evaluate_execution_authority(task,preflight,identity['uid'],identity['gid'],policy)
    root=Path(decision_root); root.mkdir(parents=True,exist_ok=True); os.chmod(root,0o750); _write_json(root/f"{record['authority_check_id']}.json",record,0o640); return record

def read_authority_check(authority_check_id,root=DECISION_ROOT):
    authority_check_id=_uuid(authority_check_id,'authority_check_id'); record=_validate_authority_record(json.loads((Path(root)/f'{authority_check_id}.json').read_text()))
    if record['authority_check_id']!=authority_check_id: raise AuthorityError('ID diverge do arquivo')
    return record

def list_authority_checks(root=DECISION_ROOT):
    root=Path(root)
    if not root.exists(): return []
    out=[]
    for path in sorted(root.glob('*.json')):
        try: out.append(read_authority_check(path.stem,root))
        except (OSError,ValueError,TypeError,json.JSONDecodeError): pass
    return sorted(out,key=lambda x:(x.get('checked_at',''),x.get('authority_check_id','')))
