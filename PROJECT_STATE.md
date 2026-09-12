# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CFG-001A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste incremento: `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para GPU/hardware. A Fase 1 tem agente, persistência básica, store transacional e painel autenticado somente leitura; CFG-001A fecha a prova de boot do painel.

## Evidência concluída antes de CFG-001A

- Run `34665004511`, commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`: primeiro boot StorOS + agente comprovado.
- Run `34668185335`, commit `250fb9e972ff472376658dbc3ac17a7dd2617ecd`: o mesmo QCOW2 iniciou duas vezes, `boot_count=1 → 2`, segundo boot com `STOROS_AGENT_READY`; Host agent, Development image e Project continuity também verdes.
- No head `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`, Host agent `34671399198`, Development image `34671399204` e Project continuity `34671399235` ficaram verdes. Isso valida os testes do store/painel e a integração dos dois services na imagem.

## Causa real do Bootable media #40

- Run `34671399200`, head `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`: build bootc, smoke check, geração e inspeção do QCOW2 passaram.
- O primeiro QEMU foi encerrado aos 240 s antes de alcançar o agente; o console mostra tarefas pesadas de primeiro boot e só chega à inicialização de `storos-agent.service` perto do limite.
- A segunda execução do mesmo QCOW2 chegou ao agente e registrou `STOROS_BOOT_STATE boot_count=1` e `STOROS_AGENT_READY snapshot=written boot_count=1`. Portanto a falha do gate não demonstrou perda de persistência: o primeiro boot lógico só terminou durante a segunda execução do QEMU.
- O timeout fixo de 240 s era inadequado para o trabalho único do primeiro boot sob TCG depois da ampliação da imagem.

## CFG-001A em implementação

- `storosctl web-marker` faz uma requisição HTTP Basic local autenticada a `/api/config`, confirma que a resposta é exatamente a configuração persistida e publica `STOROS_WEB_READY`.
- O marcador não imprime o token. Ele publica geração, SHA-256 canônico da configuração e SHA-256 do token aleatório, permitindo comparar identidade entre boots sem expor a credencial.
- `storos-web.service` executa o marcador em `ExecStartPost` e envia stdout/stderr ao journal + console para o gate serial.
- `ensure_admin_token` passa a fazer `fsync` também no diretório depois da troca atômica, alinhando a durabilidade do token à do store de configuração.
- O workflow deixa de usar dois timeouts cegos. Cada QEMU roda até `STOROS_WEB_READY`, com teto de 420 s no primeiro boot e 300 s no segundo; depois é encerrado e o mesmo QCOW2 é reutilizado.
- O gate exige em ambos os boots agente e painel prontos, `boot_count=1 → 2`, `config_generation=1` e fingerprints idênticos de configuração/token.
- Testes locais do store e painel passaram: 9 testes focados, incluindo autenticação real do novo marcador e verificação de que o token bruto não aparece na saída. YAML do workflow e sintaxe Bash do gate também foram validados localmente.

## Limitações

- Nenhum boot físico por USB ainda.
- O painel não cria, edita, inicia, pausa ou remove VMs.
- Sem TLS integrado e sem RBAC/múltiplos usuários nesta fundação.
- Sem política automática de CPU/RAM aplicada ao libvirt.
- QEMU do CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada. RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Obter Host agent, Development image, Project continuity e Bootable media verdes no head CFG-001A.
2. No Bootable media, exigir `STOROS_WEB_PERSISTENCE_OK` com hashes de config/token idênticos entre dois boots e sem segredo bruto nos logs.
3. Se o gate ficar verde, marcar CFG-001 concluído e iniciar a camada de tarefas/reconciliação + modelos de configuração de VM, mantendo escrita no libvirt desativada.
4. Depois preparar a primeira operação de VM em modo dry-run/plan antes de qualquer mutação real.
5. STOR-009/010/011 permanecem pendentes; CI virtual não encerra Fase 0 nem comprova GPU compartilhada.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos.
