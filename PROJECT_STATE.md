# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CFG-001B**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste incremento: `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. A Fase 1 já tem agente, persistência básica, store transacional e painel autenticado somente leitura; CFG-001B corrige a ordem de inicialização antes da prova final de persistência do painel.

## Evidência concluída antes de CFG-001B

- Run `34665004511`, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: primeiro boot StorOS + agente comprovado.
- Run `34668185335`, commit `250fb9e972ff472376658dbc3ac17a7dd2617ecd`: o mesmo QCOW2 iniciou duas vezes, `boot_count=1 → 2`, segundo boot com `STOROS_AGENT_READY`; Host agent, Development image e Project continuity também verdes.
- No head `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`, Host agent `34671399198`, Development image `34671399204` e Project continuity `34671399235` ficaram verdes, validando testes do store/painel e integração dos services na imagem.
- No head `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`, Host agent `34672437628`, Development image `34672437583` e Project continuity `34672437600` ficaram verdes. O `web-marker` autenticado, o fsync do token e a composição da imagem passaram antes do teste de boot.

## Diagnóstico do Bootable media #43

- Run `34672437568`, head `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`: build bootc, smoke check, geração e inspeção do QCOW2 passaram.
- No primeiro boot TCG, `STOROS_BOOT_STATE boot_count=1` apareceu por volta de 243 s e `STOROS_AGENT_READY snapshot=written boot_count=1` por volta de 322 s.
- Depois do agente, `config-init` confirmou geração 1 por volta de 356 s e `STOROS_WEB_TOKEN_READY` apareceu por volta de 395 s.
- O teto de 420 s encerrou o QEMU antes de `STOROS_WEB_READY`; portanto o workflow não iniciou o segundo boot e não produziu `STOROS_WEB_PERSISTENCE_OK`.
- A unidade web ainda tinha `After=storos-agent.service`, serializando configuração/token/HTTP atrás do inventário libvirt. O resultado não demonstra corrupção de config/token; demonstra que a dependência de ordem era desnecessária e deixava pouca margem sob TCG.
- Artefato de evidência do run: `storos-boot-evidence` ID `10291671744`, digest `sha256:7d440e819bfc209d01b76bb141035c7153beea2fcb6b7b2ad4b39f156f8faf91`.

## CFG-001B em implementação

- `storos-web.service` mantém `Wants=storos-agent.service`, mas remove `After=storos-agent.service` e passa a usar `After=network.target`.
- Painel e agente podem aquecer em paralelo. `/api/config` e a autenticação não dependem do snapshot do agente.
- `/api/status` continua representando estado observado e responde `503` enquanto `/run/storos/status.json` ainda não existe; isso preserva diagnóstico correto sem bloquear o caminho administrativo.
- `ExecStartPost=/usr/bin/storosctl web-marker --wait 60` continua sendo a prova autenticada de prontidão do painel e não imprime o token bruto.
- `check-image.sh` passa a exigir `Wants=storos-agent.service`, `After=network.target` e a rejeitar explicitamente `After=storos-agent.service`, evitando regressão da serialização.
- [CONFIGURATION.md](docs/CONFIGURATION.md) e [ARQUITETURA.md](docs/ARQUITETURA.md) registram a independência entre prontidão administrativa e inventário observado.
- A unidade corrigida e as asserções de ordenação foram validadas localmente; o resultado remoto deste lote ainda precisa ficar verde antes de CFG-001 ser marcado como concluído.

## Limitações

- Nenhum boot físico por USB ainda.
- O painel não cria, edita, inicia, pausa ou remove VMs.
- Sem TLS integrado e sem RBAC/múltiplos usuários nesta fundação.
- Sem política automática de CPU/RAM aplicada ao libvirt.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Obter Host agent, Development image, Project continuity e Bootable media verdes no head CFG-001B.
2. No Bootable media, exigir dois boots lógicos do mesmo QCOW2, `boot_count=1 → 2`, `STOROS_WEB_READY` autenticado em ambos e fingerprints idênticos de config/token.
3. Somente com `STOROS_WEB_PERSISTENCE_OK`, marcar CFG-001 concluído.
4. Depois iniciar modelos de configuração de VM + fila/reconciliação em dry-run, mantendo escrita no libvirt desativada.
5. STOR-009/010/011 permanecem pendentes; CI virtual não encerra Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos.
