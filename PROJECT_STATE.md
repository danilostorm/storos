# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-004B em publicação/validação**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, PR #2 aberto e **não autorizado para merge**.
- VM-002, WEB-VM-001, VM-003A e VM-003B permanecem fechados.
- **VM-004A está fechado funcional e documentalmente.**
- Head documental fechado VM-004A: `c247ff6ea636e0c8394cf37b7390fcd6f4d30ca0`.
- VM-004B formaliza o contrato futuro `JOBS → COMPUTE` em modo **deny-only/contract-only**.
- `features.vm_write_enabled=false` permanece obrigatório.
- Não existe executor, worker mutável, endpoint web de aplicação, autorização de escrita ou backend libvirt mutável.
- Fase 0 continua aberta para laboratório físico/GPU.

## VM-004A — fechamento formal confirmado

O head documental `c247ff6ea636e0c8394cf37b7390fcd6f4d30ca0` repetiu os gates após registrar o fechamento:

- Project continuity `34727613164`: verde;
- Host agent `34727613165`, job `103644447734`: **74/74 testes**;
- Development image `34727613151`, job `103644447808`: verde;
- Bootable media `34727613159`, job `103644447779`: verde.

Evidências dessa rodada documental:

- `image-evidence` ID `10307924863`, digest `sha256:9037319da169b2af9e057acb565e186cb7c95fac3d14aaa851a0ec50f775af52`;
- QCOW2 SHA-256 `5c3f04c7cba8263bac06dbfe861f43d310aad2123d634c36021e163375740543`;
- `storos-boot-evidence` ID `10308806410`, digest `sha256:cc57a0072cf4b9bb241b614216fb0fa7bb3ed9d831d8cec9bbf3fed3c5835694`;
- `storos-qcow2` ID `10308127235`, digest `sha256:e889474434bff18d4ab386f9cb11a04da8dda1890c60e2525860d6a13af4be4c`.

O mesmo QCOW2 foi inicializado duas vezes e o gate emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`. Nenhum outro commit de “fechamento do fechamento” é necessário.

## VM-004B — contrato de execução deny-only

A nova decisão arquitetural está em `docs/VM_EXECUTION_CONTRACT.md`.

### Objetivo

Definir a forma futura do adaptador de escrita e da autorização antes de criar qualquer executor real. Esta etapa não concede autoridade nova; ela torna explícito o que uma etapa posterior precisará implementar e verificar.

### Contrato implementado

Novo `src/storos_execution_contract.py`:

- catálogo fechado das 11 ações não bloqueantes já descritas pelo planner/preflight;
- metadados por ação: escopo do recurso, classe de operação, verificação esperada e classificação de compensação;
- validação tipada dos payloads atuais de criação, rename, vCPU, RAM, lifecycle, firmware, discos e interfaces;
- rejeição de ação desconhecida, ação marcada bloqueada ou ação que tente chegar ao contrato com `executable=true`;
- capacidades do backend fixadas em `backend_id=disabled`, `backend_kind=none`, `mutating_available=false` e `supported=false` para todas as ações;
- decisão de autorização com identidade explícita, UUID e ação, mas sempre `granted=false`, `reason_code=authorization_unavailable` e `scopes=[]`;
- resultado desta etapa restrito a `status=not_attempted`, `executed=false`, `applied=false` e `observed_after_apply=null`; resultado forjado como aplicado deve ser rejeitado.

O catálogo do contrato é comparado em teste com `SUPPORTED_ACTION_TYPES` do preflight para impedir divergência silenciosa entre as duas fronteiras.

### Integração na imagem

O `Containerfile` passa a copiar o módulo e executa uma prova deny-only durante o build:

- contrato não executável e sem worker;
- feature gate não pode habilitar escrita pela camada de contrato;
- backend mutável indisponível e todas as ações sem suporte real;
- autorização de exemplo negada.

O `image/check-image.sh` existente continua provando que intenção/planner/tarefas/preflight permanecem dry-run/bloqueados; não foi criado comando `apply`, `execute` ou endpoint mutável.

## Verificação antes da publicação

Teste isolado do novo módulo executado localmente: **7/7 testes verdes**, cobrindo catálogo, payloads tipados, ação desconhecida, ação bloqueada/malformada, backend deny-only, autorização deny-all e impossibilidade de forjar resultado aplicado.

A publicação deste lote ainda precisa repetir no head final:

1. Project continuity;
2. suíte integral do Host agent;
3. Development image com a prova deny-only do Containerfile;
4. Bootable media com dois boots do mesmo QCOW2.

Nenhum resultado remoto é antecipado neste registro.

## Segurança preservada

- `features.vm_write_enabled=false` continua obrigatório e o validador de configuração ainda rejeita `true`.
- Preflight VM-004A continua com `feature_gate_enabled=false`, `authorization_granted=false` e `mutating_backend_available=false`.
- Sem executor/worker.
- Sem shell arbitrário.
- Sem `virsh define/start/shutdown/setvcpus/setmem` ou equivalente mutável.
- Sem endpoint web mutável.
- Token administrativo do painel não é promovido a autorização de escrita.
- Sem remoção automática de hardware não gerenciado.
- Sem gerenciamento de Secure Boot/NVRAM.
- Sem passthrough, SR-IOV, mediated devices ou GPU.
- Sem boot físico USB.
- QCOW2 continua artefato de laboratório, não release de instalação.

## Limitações atuais

- O control plane StorOS ainda não cria/inicia/para/importa VMs de verdade.
- Não existe política dinâmica aplicada de CPU/RAM.
- Sem RBAC/scopes reais para escrita.
- Sem TLS integrado.
- Nenhum boot físico em pendrive foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark.
- Nenhuma GPU foi homologada para compartilhamento simultâneo.

## Próxima tarefa concreta

Primeiro, obter os quatro gates verdes do VM-004B sem enfraquecer os testes. Só depois desenhar a etapa seguinte que conectará **preflight + decisão de autorização + declaração de capacidades** a um adaptador ainda simulado, mantendo mutação real desabilitada até autorização e validação próprias.

Qualquer backend libvirt real, worker ou habilitação de `features.vm_write_enabled` permanece uma etapa separada e não está autorizada por este lote.

## Continuidade

- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` e `PROJECT_STATE.md` no mesmo lote.
- Mudança arquitetural VM-004B está documentada em `docs/VM_EXECUTION_CONTRACT.md`.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- **Não mesclar o PR #2 sem instrução explícita.**
