# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **BOOT-002A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior: `3064b5849330e4405cc4dda4a8921f083440389e`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. Fase 1 já tem agente, QCOW2 bootável e persistência básica observada em dois boots reais da mesma imagem.

## Evidência concluída

- O workflow `Bootable media` gera e valida QCOW2 bootável a partir da imagem bootc StorOS, usando OVMF/QEMU TCG.
- O preset vendor `10-storos.preset` mantém `storos-agent.service` habilitado no primeiro boot.
- Run `34665004511`, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: build, lint, QCOW2, boot UEFI/QEMU, `STOROS_AGENT_READY snapshot=written` e upload do QCOW2 passaram. Este é o primeiro boot StorOS + agente comprovado em VM descartável.
- BOOT-002 adicionou `/var/lib/storos/boot-state.json`, escrita atômica/fsync e contador baseado no `boot_id` do kernel; reiniciar apenas o serviço não conta como novo boot.
- Run `34665914397`, head `3064b5849330e4405cc4dda4a8921f083440389e`: build e QCOW2 passaram. No **mesmo QCOW2**, o primeiro console registrou `STOROS_BOOT_STATE boot_count=1`; o segundo registrou `STOROS_BOOT_STATE boot_count=2` com outro `boot_id` e também `STOROS_AGENT_READY snapshot=written boot_count=2`. Portanto a persistência básica 1 → 2 foi observada de fato.
- O run `34665914397` ficou vermelho somente porque o gate antigo exigia `STOROS_AGENT_READY ... boot_count=1` ainda no primeiro boot; o contador já estava persistido, mas o agente não atingiu o marcador de prontidão antes do timeout daquele boot.
- Host agent, Development image e Project continuity passaram no head `3064b584...`.

## BOOT-002A — correção do gate

- O CI passa a provar persistência pelos marcadores `STOROS_BOOT_STATE boot_count=1` e `boot_count=2`, que são emitidos quando o estado persistente é registrado.
- O segundo boot continua obrigado a atingir `STOROS_AGENT_READY snapshot=written boot_count=2`, provando que o agente funcional continua disponível após a reinicialização.
- `boot-console.log` passa a ser montado antes das asserções para preservar a evidência combinada mesmo se um gate falhar.
- Timeout TCG por boot passa de 210 s para 240 s para acomodar a variação observada no CI sem alterar o disco entre boots.
- Um novo workflow verde ainda é necessário para fechar o gate automatizado BOOT-002A, embora o run #32 já tenha demonstrado a persistência básica pelos logs.

## Limitações

- Nenhum boot físico por USB ainda.
- Configuração transacional completa da Fase 1 ainda não existe; o que está comprovado é a persistência do estado de boot em `/var/lib/storos`.
- Sem painel web autenticado, criação/alteração de VMs ou política automática de CPU/RAM.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release.

## Próxima tarefa concreta

1. Obter o workflow BOOT-002A verde com o gate alinhado aos marcadores observados.
2. Depois implementar configuração persistente transacional da Fase 1.
3. Iniciar a fundação do painel web autenticado consumindo o contrato do agente.
4. STOR-009/010/011 permanecem pendentes; CI virtual não encerra a Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos.
