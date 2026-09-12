# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **VM-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste incremento: `4742ee4b9e3da2420c93f6fcd26424a331b16016`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para validação física de GPU/hardware.
- CFG-001 está concluído: agente somente leitura, persistência de boot, configuração transacional e painel autenticado somente leitura já têm prova remota entre dois boots do mesmo QCOW2.
- **VM-001 está em implementação/publicação:** contrato de intenção de VM, planner/reconciler dry-run e ledger persistente de tarefas foram implementados sem executor mutável.

## Evidência concluída antes do VM-001

- Head validado do CFG-001: `496e3bfbba637519c1fabe32414ea0a64ac018da`.
- Host agent `34693451988`, Development image `34693452020`, Project continuity `34693451976` e Bootable media `34693452040`: verdes.
- O mesmo QCOW2 registrou `boot_count=1 → 2`, agente e painel autenticado prontos nos dois boots, `config_generation=1` e fingerprints idênticos de configuração/token.
- O gate emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.
- A tentativa 1 do Bootable media #47 congelou antes dos services StorOS sob QEMU/TCG; o rerun do mesmo commit passou integralmente e a ocorrência permanece registrada como instabilidade de runner/TCG.

## VM-001 — implementação atual

- Novo `src/storos_vm.py`: valida intenção de VM schema v1 com UUID, nome, `desired_state`, vCPU e RAM fixa em MiB.
- O planner compara intenção com o snapshot do agente e descreve diferenças como `create_vm`, `rename_vm`, `set_vcpus`, `set_memory`, `start_vm` e `shutdown_vm`.
- Todo plano usa `mode=dry_run`, `can_apply=false`; todas as ações usam `executable=false`. Não existe executor nem adaptador libvirt mutável.
- O plano inclui hashes SHA-256 da intenção normalizada e do snapshot usado, permitindo relacionar a proposta às entradas que a produziram.
- A CLI passa o snapshot por `read_snapshot(..., max_age=30)`. Snapshot antigo gera `blocked/refresh_snapshot`.
- Se o inventário for `partial` e a VM não estiver presente, o planner não propõe criação; produz `blocked/inspect_inventory` porque ausência não está comprovada.
- Se vCPU ou `max_memory_reported_kib` estiverem ausentes, o plano fica bloqueado e exige inspeção em vez de assumir recurso configurável.
- Novo `src/storos_tasks.py`: tarefas em `/var/lib/storos/tasks/<uuid>.json`, escrita atômica, `fsync` do arquivo/diretório, diretório `0750`, arquivo `0640` e rejeição de planos/aplicações executáveis.
- CLI adiciona `vm-plan`, `vm-reconcile-dry-run`, `task-list` e `task-show`.
- O Containerfile inclui os dois novos módulos. `check-image.sh` executa um plano e uma tarefa contra o driver `test:///default` e exige que nada seja aplicável/executável.
- Contrato e limites estão em [docs/VM_PLANNER.md](docs/VM_PLANNER.md); a arquitetura foi atualizada em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Verificação local deste incremento

- 15 testes focados passaram para planner, ledger e integração CLI.
- Casos cobertos: schema estrito, criação/start descritivos, convergência, rename/CPU/RAM/start, shutdown, dados de recurso ausentes, inventário parcial, snapshot stale, inventário indisponível, UUID duplicado, persistência/permissões do ledger, rejeição de ação executável e comandos CLI dry-run.
- `image/check-image.sh` passou em `bash -n` antes da publicação.
- O CI remoto deste lote ainda precisa ficar verde antes de VM-001 ser marcado como concluído.

## Limitações atuais

- `features.vm_write_enabled=false` continua obrigatório.
- Nenhuma mutação libvirt está habilitada; nenhum `virsh define/start/shutdown/setvcpus/setmem` é executado pelo planner ou ledger.
- O painel web continua somente leitura e não ganhou endpoint de tarefas neste incremento.
- O contrato inicial ainda não cobre discos, rede, firmware, dispositivos, passthrough, mínimos/máximos dinâmicos de RAM ou GPU.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB ainda.
- QEMU no CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada; RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Publicar VM-001 e obter Host agent, Development image e Project continuity verdes; Bootable media deve continuar comprovando que o novo código não quebra o boot existente.
2. Se o CI falhar, corrigir sem habilitar escrita libvirt e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` no mesmo lote.
3. Com o CI verde, registrar a evidência remota e marcar VM-001 concluído.
4. Próximo incremento: VM-002 deve persistir intenção de VM e desenhar precondições/locks para futura aplicação, ainda em plan/dry-run antes de qualquer executor real.
5. STOR-009/010/011 e a validação física de GPU permanecem pendentes; CI virtual não encerra Fase 0.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Obedecer `AGENTS.md` em toda publicação. Não mesclar o PR #2 sem instrução explícita.
