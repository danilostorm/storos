# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **VM-001A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Head funcional validado do VM-001: `45bd655269d8ef45f1c6f5ace9ff82ce3f8454fc`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para validação física de GPU/hardware.
- CFG-001 está concluído: agente somente leitura, persistência de boot, configuração transacional e painel autenticado somente leitura têm prova remota entre dois boots do mesmo QCOW2.
- **VM-001 está concluído:** contrato de intenção de VM, planner/reconciler dry-run e ledger persistente de tarefas foram implementados e validados remotamente sem executor mutável.

## Evidência remota do VM-001

- Host agent `34699051160` (#69): verde.
- Project continuity `34699051144` (#81): verde.
- Development image `34699051205` (#75): verde.
- Bootable media `34699051187` (#49), job `103567451447`: verde.
- O Development image e o estágio `Build and stage bootc image` do Bootable executaram o smoke do planner/ledger dentro da imagem final, exigindo `can_apply=false` e `executable=false`.
- O mesmo QCOW2 foi iniciado duas vezes. Primeiro boot: `boot_count=1`, painel autenticado pronto com `config_generation=1` e agente pronto. Segundo boot: `boot_count=2` com novo `boot_id`, agente e painel autenticado prontos novamente.
- Fingerprint de configuração nos dois boots: `bd40b1655bfebfa9aaafdbf1f9520aef87655e52132f0c38ab95961970cb649c`.
- Fingerprint do token nos dois boots: `d2690aaebd5da0a39c1233932d82516da6073eb00f4e6eb57765614c4f04171a`. A credencial bruta não aparece nos marcadores usados como evidência.
- O gate emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.
- Artefato `storos-boot-evidence`: ID `10299687818`, digest `sha256:63780ac5e92c2450ad4159adaf6484515cf2ab1521bb42dc19534898ec0f62c5`.
- QCOW2 validado: SHA-256 `ba9d51ebb91bc91e08d9e84d41be1f13a07c0efcf89a94527543027e6778538b`. Artefato `storos-qcow2`: ID `10300291526`.

## VM-001 — estado funcional

- `src/storos_vm.py` valida intenção de VM schema v1 com UUID, nome, `desired_state`, vCPU e RAM fixa em MiB.
- O planner compara intenção com o snapshot do agente e descreve diferenças como `create_vm`, `rename_vm`, `set_vcpus`, `set_memory`, `start_vm` e `shutdown_vm`.
- Todo plano usa `mode=dry_run`, `can_apply=false`; todas as ações usam `executable=false`. Não existe executor nem adaptador libvirt mutável.
- O plano inclui hashes SHA-256 da intenção normalizada e do snapshot usado, relacionando a proposta às entradas que a produziram.
- A CLI passa o snapshot por `read_snapshot(..., max_age=30)`. Snapshot antigo gera `blocked/refresh_snapshot`.
- Inventário `partial` sem a VM não pode gerar `create_vm`; produz `blocked/inspect_inventory` porque ausência não está comprovada.
- vCPU ou `max_memory_reported_kib` ausentes bloqueiam o plano e exigem inspeção em vez de assumir recurso configurável.
- `src/storos_tasks.py` grava tarefas em `/var/lib/storos/tasks/<uuid>.json` com escrita atômica, fsync, diretório `0750`, arquivo `0640` e rejeição de plano aplicável/ação executável.
- CLI possui `vm-plan`, `vm-reconcile-dry-run`, `task-list` e `task-show`.
- O Containerfile inclui os módulos e `check-image.sh` exercita planner + ledger contra `test:///default`.
- Contrato e limites estão em [docs/VM_PLANNER.md](docs/VM_PLANNER.md); arquitetura em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Verificação do incremento

- 15 testes focados passaram localmente para planner, ledger e integração CLI.
- Casos cobertos: schema estrito, criação/start descritivos, convergência, rename/CPU/RAM/start, shutdown, dados de recurso ausentes, inventário parcial, snapshot stale, inventário indisponível, UUID duplicado, persistência/permissões do ledger, rejeição de ação executável e comandos CLI dry-run.
- `image/check-image.sh` passou em `bash -n` antes da publicação e depois passou dentro das imagens remotas construídas pelo CI.
- O Bootable media confirmou que a adição do planner/ledger não regrediu a persistência e prontidão já comprovadas pelo CFG-001.

## Limitações atuais

- `features.vm_write_enabled=false` continua obrigatório.
- Nenhuma mutação libvirt está habilitada; nenhum `virsh define/start/shutdown/setvcpus/setmem` é executado pelo planner ou ledger.
- Não existe worker/executor de tarefas.
- A intenção desejada ainda não possui store persistente/revisões próprios; isso fica para VM-002.
- O painel web continua somente leitura e ainda não expõe tarefas/planos.
- O contrato inicial não cobre discos, rede, firmware, dispositivos, passthrough, mínimos/máximos dinâmicos de RAM ou GPU.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB ainda.
- QEMU no CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada; RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta — VM-002

1. Criar store persistente e versionado para intenção desejada de VMs, separado do estado observado do agente.
2. Adicionar geração/revisão e concorrência otimista para impedir aplicação baseada em intenção obsoleta.
3. Formalizar precondições e locks por VM/tarefa e relacionar cada plano às gerações de intenção/configuração e ao snapshot observado.
4. Manter reconciliação em plan/dry-run e `features.vm_write_enabled=false`; nenhum executor real nesta etapa.
5. Preparar exposição somente leitura de intenção/plano/tarefas para o painel depois do contrato persistente estar estável.
6. STOR-009/010/011, boot físico e validação física de GPU permanecem pendentes; CI virtual não encerra Fase 0.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Obedecer `AGENTS.md` em toda publicação. Não mesclar o PR #2 sem instrução explícita.
