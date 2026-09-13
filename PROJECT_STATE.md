# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-004C em publicação/validação**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, PR #2 aberto e **não autorizado para merge**.
- VM-002, WEB-VM-001, VM-003A, VM-003B e VM-004A permanecem fechados.
- **VM-004B está validado remotamente** no head `27d233d1f6f115928219e5974cbfe0ac898ea13a`.
- VM-004C adiciona somente admission simulada/deny-only; não adiciona execução real.
- `features.vm_write_enabled=false` permanece obrigatório.
- Não existe executor, worker mutável, endpoint web de aplicação, autorização real de escrita ou backend libvirt mutável.
- Fase 0 continua aberta para laboratório físico/GPU.

## VM-004B — fechamento remoto

Head validado: `27d233d1f6f115928219e5974cbfe0ac898ea13a`.

Quatro gates de push ficaram verdes:

- Project continuity `34730616504`, job `103652600134`;
- Host agent `34730616508`, job `103652600220`: **81/81 testes**;
- Development image `34730616538`, job `103652600407`;
- Bootable media `34730616503`, job `103652600394`.

Evidências:

- `image-evidence` ID `10308434031`, digest `sha256:f0714c001145d3c44034da0d9596f365a12b37fd7d6f9d8ae316781372656952`;
- QCOW2 SHA-256 `d834399388ec5da20d67150efe64832db1e992a85c3868edefb72cf6f1e50372`;
- `storos-boot-evidence` ID `10308459678`, digest `sha256:5e4ca31e806c350a1e7fc857bc80a393fb68dac12f632c147c802781483eb377`;
- `storos-qcow2` ID `10309940637`, digest `sha256:6555a48c2cb2fe5fa3d2e6bffd3e53c2c58088c27a4ca24c4f4be1a303b7697e`.

O mesmo QCOW2 inicializou duas vezes, avançou `boot_count=1 → 2`, preservou `config_generation=1` e os fingerprints da configuração/token, e emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.

## VM-004C — admission simulada deny-only

A decisão arquitetural está em `docs/VM_EXECUTION_ADMISSION.md`.

### Objetivo

Conectar uma tarefa persistida a um preflight fresco, ao contrato tipado VM-004B, a uma identidade apenas alegada e às capacidades deny-only do backend, produzindo uma decisão auditável que continua incapaz de executar qualquer ação.

### Implementação preparada

Novo `src/storos_execution_admission.py`:

- lê a tarefa e executa um novo preflight;
- relê a tarefa depois do preflight;
- exige tarefa schema 3 `planned`, `dry_run`, `executable=false`;
- exige plano `changes_planned`, `dry_run`, `can_apply=false`;
- vincula tarefa/preflight por `task_id`, `vm_uuid` e `plan_fingerprint_sha256`;
- exige os três blockers deliberados do estágio atual;
- valida cada ação pelo contrato VM-004B;
- consulta autorização deny-all e backend `disabled/none`;
- usa `DenyOnlySimulationAdapter`, sem método `apply`;
- gera por ação somente `not_attempted`, `executed=false`, `applied=false`;
- grava admission `status=denied`, `can_execute=false`, `executed=false` em `/var/lib/storos/execution-admissions` com modos `0750/0640` e escrita atômica/fsync;
- marca `claimed_identity` explicitamente como `identity_authenticated=false`.

### Verificação local

A suíte isolada do VM-004C passou **8/8 testes**, cobrindo:

- admission válida somente como denial/non-execution;
- inexistência do método `apply`;
- mismatch tarefa/preflight;
- drift do fingerprint do plano;
- ação desconhecida;
- tentativa de forjar identidade autenticada;
- persistência privada do registro;
- descarte de registro corrompido na listagem.

O lote ainda precisa repetir os quatro gates remotos no head publicado antes de VM-004C ser considerado fechado.

## Segurança preservada

- `features.vm_write_enabled=false` continua obrigatório e `true` continua rejeitado.
- Preflight continua fail-closed.
- VM-004C não autentica identidades e não concede scopes.
- Token administrativo do painel não vira autorização de escrita.
- Adaptador simulado não possui `apply`.
- Sem executor/worker.
- Sem shell arbitrário.
- Sem chamada mutável a `virsh`/libvirt.
- Sem endpoint web mutável.
- Sem remoção automática de hardware não gerenciado.
- Sem gerenciamento de Secure Boot/NVRAM.
- Sem passthrough, SR-IOV, mediated devices ou GPU.
- Sem boot físico USB.
- QCOW2 continua artefato de laboratório, não release de instalação.

## Limitações atuais

- O control plane ainda não cria/inicia/para/importa VMs de verdade.
- Não existe identidade/autorização real para aplicação.
- Não existe backend mutável nem política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado/RBAC de escrita.
- Nenhum boot físico em pendrive foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark.
- Nenhuma GPU foi homologada para compartilhamento simultâneo.

## Próxima tarefa concreta

Primeiro, obter Project continuity, Host agent, Development image e Bootable media verdes no head VM-004C.

Depois disso, desenhar uma etapa separada para **identidade/autorização real e negociação de capacidades ainda sem mutação**, preservando preflight/locks/fingerprints e exigindo nova validação antes de qualquer executor. Um estágio de aplicação real deverá readquirir locks e relevar estado fresco; nenhum registro VM-004C poderá ser reutilizado como autorização de execução.

Backend libvirt mutável, worker e habilitação de `features.vm_write_enabled` continuam fora do VM-004C e exigirão etapa própria e autorização explícita antes de uso real.

## Continuidade

- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` e `PROJECT_STATE.md` no mesmo lote.
- Mudança arquitetural VM-004C está documentada em `docs/VM_EXECUTION_ADMISSION.md`.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- **Não mesclar o PR #2 sem instrução explícita.**
