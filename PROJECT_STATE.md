# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CFG-001C**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste incremento: `1a7e372bc022f15978f5d43bce9fb4da689a4be5`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. A Fase 1 já tem agente, persistência básica, store transacional e painel autenticado somente leitura; CFG-001C alinha o gate de boot à inicialização concorrente de painel e agente.

## Evidência concluída

- Run `34665004511`, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: primeiro boot StorOS + agente comprovado.
- Run `34668185335`, commit `250fb9e972ff472376658dbc3ac17a7dd2617ecd`: o mesmo QCOW2 iniciou duas vezes, `boot_count=1 → 2`, segundo boot com `STOROS_AGENT_READY`; Host agent, Development image e Project continuity também verdes.
- No head `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`, Host agent `34672437628`, Development image `34672437583` e Project continuity `34672437600` ficaram verdes. O Bootable media `34672437568` comprovou `boot_count=1`, agente, config geração 1 e criação persistente do token no primeiro boot, mas não alcançou `STOROS_WEB_READY` antes de 420 s porque a unidade web ainda estava serializada atrás do agente.
- No head `1a7e372bc022f15978f5d43bce9fb4da689a4be5`, Host agent `34693093926`, Development image `34693093931` e Project continuity `34693093913` ficaram verdes. A imagem passou o smoke check que proíbe `After=storos-agent.service` e exige `After=network.target`.

## Correção de startup do CFG-001B

- `storos-web.service` mantém `Wants=storos-agent.service`, remove `After=storos-agent.service` e usa `After=network.target`.
- Painel e agente aquecem em paralelo. `/api/config` e autenticação não dependem do snapshot do agente.
- `/api/status` continua retornando `503` enquanto `/run/storos/status.json` ainda não existe; o estado observado não é falsificado.
- `ExecStartPost=/usr/bin/storosctl web-marker --wait 60` continua sendo a prova autenticada de prontidão do painel e não imprime o token bruto.

## CFG-001C — gate conjunto em implementação

- A revisão do workflow mostrou uma incompatibilidade com o startup paralelo: `boot_guest` encerrava QEMU assim que aparecia `STOROS_WEB_READY`, mas as asserções posteriores também exigiam `STOROS_AGENT_READY`.
- Com o painel agora podendo ficar pronto antes do agente, esse comportamento poderia encerrar um boot saudável cedo demais e produzir falso negativo.
- O loop passa a acompanhar separadamente `web_ready` e `agent_ready`; `ready=1` somente quando os dois marcadores já existem no mesmo console.
- O diagnóstico de timeout informa `(web=0/1, agent=0/1)`, permitindo distinguir painel indisponível de aquecimento lento do inventário.
- Os limites permanecem 420 s no primeiro boot e 300 s no segundo. O QEMU é encerrado assim que os dois componentes ficam prontos, não por espera fixa.
- A sintaxe Bash do gate conjunto foi validada localmente antes da publicação. O resultado remoto deste lote ainda precisa ficar verde antes de CFG-001 ser marcado como concluído.

## Limitações

- Nenhum boot físico por USB ainda.
- O painel não cria, edita, inicia, pausa ou remove VMs.
- Sem TLS integrado e sem RBAC/múltiplos usuários nesta fundação.
- Sem política automática de CPU/RAM aplicada ao libvirt.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Obter Host agent, Development image, Project continuity e Bootable media verdes no head CFG-001C.
2. No Bootable media, exigir dois boots lógicos do mesmo QCOW2, `boot_count=1 → 2`, `STOROS_AGENT_READY` e `STOROS_WEB_READY` em ambos e fingerprints idênticos de config/token.
3. Somente com `STOROS_WEB_PERSISTENCE_OK`, marcar CFG-001 concluído.
4. Depois iniciar modelos de configuração de VM + fila/reconciliação em dry-run, mantendo escrita no libvirt desativada.
5. STOR-009/010/011 permanecem pendentes; CI virtual não encerra Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos.
