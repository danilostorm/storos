# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CFG-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste incremento: `250fb9e972ff472376658dbc3ac17a7dd2617ecd`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. A Fase 1 já tem agente, boot/persistência comprovados e agora avança para configuração transacional e painel autenticado.

## Evidência concluída

- O workflow `Bootable media` gera QCOW2 bootável a partir da imagem bootc StorOS, usando OVMF/QEMU TCG.
- Run `34665004511`, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: primeiro boot StorOS + agente comprovado com `STOROS_AGENT_READY snapshot=written`.
- Run `34668185335`, commit `250fb9e972ff472376658dbc3ac17a7dd2617ecd`: o mesmo QCOW2 foi iniciado duas vezes, o estado persistente avançou de `boot_count=1` para `boot_count=2`, o segundo boot confirmou `STOROS_AGENT_READY`, e o QCOW2 foi publicado como artefato. Host agent, Development image e Project continuity também ficaram verdes no mesmo head.

## CFG-001 em implementação

- Novo store persistente em `/var/lib/storos/config`, com `current.json`, revisões por geração e lock local.
- Aplicações usam validação completa, geração monotônica e `expected_generation` opcional para rejeitar escrita concorrente obsoleta.
- O protocolo grava a revisão antes de substituir `current.json` atomicamente; rollback cria uma nova geração e preserva histórico.
- `features.vm_write_enabled` permanece obrigatoriamente `false`; o validador rejeita tentativa de habilitar escrita em VMs.
- Novo `storos-web.service`: painel HTTP autenticado e somente leitura, padrão `127.0.0.1:8080`, `/healthz`, `/`, `/api/status` e `/api/config`.
- Autenticação administrativa usa token aleatório local em `/var/lib/storos/auth/admin.token`, modo `0600`; métodos mutáveis são recusados.
- Exposição fora do loopback exige opt-in explícito `allow_insecure_lan=true`, porque TLS integrado ainda não existe.
- `storosctl` ganha `config-init`, `config-show`, `config-history`, `config-apply`, `config-rollback`, `web-token-init` e `web-token-show` sem retirar os comandos do agente.
- Testes locais do novo store/painel passaram antes da publicação. A validação remota deste incremento ainda precisa ficar verde antes de marcar CFG-001 como concluído.

## Limitações

- Nenhum boot físico por USB ainda.
- O painel não cria, edita, inicia, pausa ou remove VMs.
- Sem TLS integrado e sem RBAC/múltiplos usuários nesta fundação.
- Sem política automática de CPU/RAM aplicada ao libvirt.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Obter Host agent, Development image, Project continuity e Bootable media verdes no commit CFG-001, incluindo `storos-web.service` habilitado na imagem.
2. Confirmar em boot QCOW2 que o painel inicia sem impedir o marcador do agente e que a configuração/token sobrevivem ao segundo boot.
3. Fazer o primeiro teste funcional do painel no sistema iniciado e registrar evidência sem expor token no log.
4. Depois criar a camada de tarefas/reconciliação e modelos de configuração de VM, mantendo escrita no libvirt desativada até validação separada.
5. STOR-009/010/011 permanecem pendentes; CI virtual não encerra a Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos.
