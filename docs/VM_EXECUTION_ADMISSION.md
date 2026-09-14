# VM-004C — admission simulada deny-only

## Objetivo

VM-004C conecta o preflight fail-closed do VM-004A ao contrato tipado deny-only do VM-004B sem criar uma etapa de aplicação. O resultado é uma decisão auditável de **admission negada**: a tarefa, o preflight fresco, o fingerprint do plano, uma identidade apenas alegada e as capacidades declaradas do backend são avaliados juntos, mas nenhuma ação pode ser executada.

Esta etapa não é um executor, não é autorização real e não é um backend libvirt.

## Fluxo

`storos_execution_admission.py` implementa o fluxo:

1. lê a tarefa persistida do ledger;
2. executa um novo `run_vm_preflight()` para obter observação e blockers atuais;
3. relê a tarefa depois do preflight;
4. exige tarefa schema 3, `planned`, `dry_run` e `executable=false`;
5. exige plano `changes_planned`, `dry_run` e `can_apply=false`;
6. vincula tarefa e preflight pelo mesmo `task_id`, `vm_uuid` e `plan_fingerprint_sha256`;
7. valida cada ação pelo contrato tipado VM-004B;
8. consulta a autorização deny-all e as capacidades do backend `disabled/none`;
9. passa cada ação pelo adaptador `DenyOnlySimulationAdapter`, que possui apenas `simulate_non_execution()` e não possui método `apply`;
10. persiste um registro auditável em `/var/lib/storos/execution-admissions/<admission_id>.json`.

O registro usa diretório `0750`, arquivo `0640`, escrita atômica e `fsync`.

## Identidade

`claimed_identity` é apenas metadado de auditoria informado pelo chamador. VM-004C grava explicitamente `identity_authenticated=false` e rejeita um registro que tente afirmar o contrário.

O token administrativo atual do painel não é convertido em identidade de execução e não concede scopes. A decisão de autorização do VM-004B continua retornando `granted=false`, `reason_code=authorization_unavailable` e `scopes=[]`.

## Vínculo com o preflight

A admission só aceita o preflight atual em estado fail-closed:

- `status=blocked`;
- `can_execute=false`;
- `executed=false`;
- blockers obrigatórios `feature_gate_disabled`, `authorization_unavailable` e `mutating_backend_unavailable` presentes.

O fingerprint do plano precisa ser um SHA-256 válido e idêntico em:

- `task.preconditions.plan_fingerprint_sha256`;
- `task.plan.plan_fingerprint_sha256`;
- `preflight.observed.plan_fingerprint_sha256`.

Divergência falha fechada e não produz admission válida.

## Adaptador de simulação

`DenyOnlySimulationAdapter` declara:

- `adapter_id=simulation-deny-only`;
- `adapter_kind=simulation`;
- `mutating_available=false`;
- `apply_method_available=false`.

Ele não contém método `apply`. Para cada ação validada, produz somente o `non_execution_result()` do VM-004B: `status=not_attempted`, `executed=false`, `applied=false` e `observed_after_apply=null`.

## Locks e replay

Os locks do VM-004A protegem a avaliação de preflight e são liberados quando o preflight termina. Isso é aceitável no VM-004C porque a admission **não muta nada**.

Um futuro estágio real de aplicação não poderá reutilizar um registro VM-004C como autoridade. Antes de qualquer mutação, deverá adquirir novamente os locks dos recursos, reler tarefa/intenção/configuração, obter observação fresca, revalidar fingerprints, autenticar a identidade, autorizar scopes, confirmar capacidade do backend e persistir auditoria própria. Drift entre admission e aplicação deve bloquear e exigir novo ciclo.

## Invariantes

VM-004C preserva:

- `features.vm_write_enabled=false`;
- nenhum worker/executor;
- nenhum método `apply` no adaptador;
- nenhum shell arbitrário;
- nenhuma chamada mutável a `virsh`/libvirt;
- nenhum endpoint web mutável;
- painel administrativo continua read-only;
- nenhum gerenciamento de Secure Boot/NVRAM, passthrough, SR-IOV, mediated devices ou GPU.

## Critério de validação

Antes de ser considerado fechado, o head final do VM-004C deve passar:

1. Project continuity;
2. suíte integral do Host agent, incluindo testes de admission;
3. Development image importando o módulo e provando que o adaptador não possui `apply`;
4. Bootable media gerando e inicializando o mesmo QCOW2 duas vezes sem regressão de persistência.

Esses gates não autorizam mutação real. Backend libvirt de escrita, identidade/autorização reais, worker e eventual habilitação de `features.vm_write_enabled` pertencem a etapas posteriores separadas.
