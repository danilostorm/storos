# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-004A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002, WEB-VM-001 e VM-003A permanecem fechados.
- **VM-003B está fechado funcional e documentalmente.**
- Head funcional VM-003B: `a8e0e9895efd24e4814c87297feefb34e5d123bb`.
- Head documental VM-003B: `874db3cb783bc4c18e9ca0c42f46963d06480f86`.
- **VM-004A está em implementação/validação remota neste lote**; não é executor.
- `features.vm_write_enabled=false` permanece obrigatório.
- Nenhum backend libvirt mutável, endpoint web de escrita ou autorização de aplicação foi introduzido.
- Fase 0 continua aberta para laboratório físico/GPU; nenhum modelo está homologado para compartilhamento simultâneo.

## VM-003B — fechamento documental confirmado

O head documental `874db3cb783bc4c18e9ca0c42f46963d06480f86` repetiu os quatro gates:

- Project continuity `34717404728`: verde;
- Host agent `34717404729`: **63/63 testes**;
- Development image `34717404730`: verde;
- Bootable media `34717404733`, job `103617073406`: verde.

Development image:

- `image-evidence` ID `10305900646`;
- digest `sha256:4f609548ae0aa0b98941ad59dd9420136b1c46e2ff18ec92210adb659636198e`.

Bootable media:

- libvirt 12.0.0 e QEMU 10.2.2;
- mesmo QCOW2 inicializado duas vezes;
- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`;
- QCOW2 SHA-256 `5af00fe1802072a080f3ce2cfa94d2d62312d037ecebbe67132f4fecdd8a8998`;
- `storos-boot-evidence` ID `10305392144`, digest `sha256:eaa1e78cda0ba7103e87f1e1d6d31bbd7dbf74d330358f9e74df6f2cba70fba2`;
- `storos-qcow2` ID `10305182438`, digest `sha256:0a9c20020afca1054788eff4de88f8301cc65928a6c132e3c1b437c172b29996`.

Isso encerra o VM-003B sem promover QCOW2 a mídia de instalação e sem autorizar escrita no hipervisor.

## VM-004A — preflight fail-closed

Objetivo: materializar a fronteira de segurança imediatamente anterior a um futuro executor, ainda sem qualquer capacidade de executar.

A decisão/contrato está em [docs/VM_PREFLIGHT.md](docs/VM_PREFLIGHT.md).

### Fingerprints estáveis

Foi identificado que o `snapshot_sha256` histórico do plano inclui campos derivados por `read_snapshot()`, como `age_seconds` e `stale`. Esse hash é preservado para auditoria e compatibilidade, mas não é usado sozinho como precondição futura.

O novo `storos_fingerprints.py` define:

- `snapshot_fingerprint_version=1`;
- fingerprint semântico de snapshot que exclui apenas timestamps/frescor derivados e normaliza ordem de VMs/erros;
- `plan_fingerprint_version=1`;
- fingerprint semântico do plano que ignora o hash/idade legados do snapshot e mantém intenção, ações, warnings, status e fingerprint estável do snapshot.

### Ledger schema 3

Novas tarefas `vm_reconcile` passam a schema 3 com:

- geração/hash da intenção;
- `snapshot_sha256` legado;
- versão/hash semântico do snapshot;
- versão/hash semântico do plano.

Tarefas schema 2 continuam legíveis para histórico/API, mas o preflight as bloqueia como `legacy_task_preconditions`.

A validação do ledger também endurece coerência de status, ações, sequência, `blocked`, `reason` e warnings sem permitir ação executável.

### Preflight

Novo `storos_preflight.py`:

- recebe somente tarefa persistida validada;
- deriva locks de VM/recurso;
- adquire locks em ordem determinística;
- relê tarefa, intenção, snapshot fresco e configuração **sob lock**;
- recalcula plano e fingerprints;
- detecta drift de geração/hash, snapshot e plano;
- rejeita snapshot stale;
- rejeita ação bloqueada/desconhecida;
- persiste auditoria em `/var/lib/storos/preflight`;
- nunca chama `virsh` ou adaptador mutável.

Locks são representados por chaves como `vm:<uuid>`, firmware, target de disco e MAC de interface; o nome físico do lock é SHA-256 da chave e o arquivo usa modo `0600`.

### Bloqueios deliberados

Mesmo com tarefa e estado perfeitamente consistentes, VM-004A exige e registra:

- `feature_gate_enabled=false`;
- `authorization_granted=false`;
- `mutating_backend_available=false`.

Consequentemente todo resultado possui:

- `status=blocked`;
- `can_execute=false`;
- `executed=false`.

A configuração ainda rejeita `features.vm_write_enabled=true`, portanto o lote não cria caminho oculto para aplicação.

### CLI e imagem

Novos comandos locais:

- `storosctl vm-preflight --task-id <uuid>`;
- `storosctl preflight-list`;
- `storosctl preflight-show --preflight-id <uuid>`.

O smoke da imagem passa a exigir os módulos de fingerprints/preflight e executa um preflight real sobre a tarefa dry-run criada no próprio smoke, exigindo exatamente os três bloqueios deliberados acima.

## Cobertura adicionada

O lote adiciona testes para:

- fingerprint estável apesar de timestamps/idade e ordem de VMs;
- fingerprint mudando quando o estado observado muda;
- ledger schema 3;
- leitura backward-compatible de tarefa schema 2;
- detecção de fingerprint de plano adulterado;
- preflight consistente ainda bloqueado pelos três requisitos de segurança;
- drift de intenção;
- drift semântico de snapshot;
- snapshot stale;
- ação desconhecida;
- tentativa de tornar ação executável;
- schema 2 inelegível para preflight;
- fluxo CLI de criação da tarefa e preflight;
- painel continuando apenas a expor tarefas não executáveis.

## Segurança preservada

- `features.vm_write_enabled=false`.
- Sem executor/worker mutável.
- Sem `virsh define/start/shutdown/setvcpus/setmem` no preflight.
- Sem endpoint web de preflight ou aplicação.
- Sem autorização de escrita.
- Sem detach automático.
- Sem Secure Boot/NVRAM gerenciado.
- Sem passthrough, SR-IOV, mediated devices ou GPU.
- Sem boot físico USB.
- QCOW2 continua laboratório interno.

## Validação pendente deste lote

Este texto descreve a implementação publicada, **não afirma sucesso remoto antecipado**. O VM-004A só poderá ser fechado após:

1. Project continuity verde;
2. Host agent/suíte integral verde;
3. Development image verde com o novo smoke;
4. Bootable media verde com o mesmo QCOW2 em dois boots;
5. comparação do changelog confirmando histórico somente aditivo.

Qualquer falha deve ser corrigida na causa; não reduzir os critérios.

## Próxima tarefa após VM-004A

Somente depois do fechamento remoto do preflight, desenhar uma etapa separada de autorização/capacidade/adaptador para futura aplicação. Não habilitar escrita real automaticamente e não mesclar o PR #2 sem instrução explícita.

## Continuidade

- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` + `PROJECT_STATE.md` no mesmo commit/lote.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- **Não mesclar o PR #2 sem instrução explícita.**
