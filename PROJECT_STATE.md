# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **BOOT-002**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base desta atualização: `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. Fase 1 já tem agente, boot QCOW2 validado e agora avança para persistência.

## Evidência já concluída

- O workflow `Bootable media` gera QCOW2 bootável a partir da imagem bootc StorOS, usando OVMF/QEMU TCG para prova funcional.
- O bloqueio de schema do `disk.yaml` foi resolvido e `qemu-img` valida o disco gerado.
- O primeiro boot aplica corretamente o preset vendor `10-storos.preset`, mantendo `storos-agent.service` habilitado.
- **Run `34665004511`**, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: build, lint, QCOW2, boot UEFI/QEMU, marcador `STOROS_AGENT_READY snapshot=written`, artefatos e upload do QCOW2 passaram. Este é o primeiro boot StorOS + agente comprovado em VM descartável.
- Host agent, Development image e Project continuity também passaram nesse commit.

## BOOT-002 em implementação

- `storosctl` passa a registrar `/proc/sys/kernel/random/boot_id` em `/var/lib/storos/boot-state.json`.
- O estado usa JSON schema 1, modo 0640, gravação atômica, `fsync` do arquivo e diretório e só incrementa `boot_count` para um `boot_id` novo.
- `storos-agent.service` usa `StateDirectory=storos`, registra o boot em `ExecStartPre`, inicia o daemon e emite `STOROS_AGENT_READY snapshot=written boot_count=N` em `ExecStartPost` somente depois de o snapshot existir.
- Testes unitários cobrem repetição do mesmo boot ID, segundo boot distinto, permissões do arquivo e ID inválido.
- O CI BOOT-002 inicializa **o mesmo QCOW2 duas vezes**. O primeiro boot deve emitir `boot_count=1`; o segundo, `boot_count=2`. QEMU é encerrado depois do marcador para reduzir tempo sem trocar o disco entre boots.
- O resultado remoto de BOOT-002 ainda precisa ficar verde antes de declarar a persistência validada.

## Limitações

- Nenhum boot físico por USB ainda.
- Persistência básica de estado está sendo validada; configuração transacional completa ainda não existe.
- Sem painel web autenticado, criação/alteração de VMs ou política automática de CPU/RAM.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release.

## Próxima tarefa concreta

1. Fechar o workflow BOOT-002 com dois boots verdes no mesmo QCOW2 e `boot_count` 1 → 2.
2. Registrar a evidência do run no changelog/estado sem apagar resultados históricos.
3. Implementar a camada de configuração persistente transacional da Fase 1.
4. Em seguida iniciar a fundação do painel web autenticado consumindo o contrato do agente.
5. STOR-009/010/011 permanecem pendentes; CI virtual não encerra a Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer AGENTS.md e atualizar CHANGELOG.md + PROJECT_STATE.md juntos.
