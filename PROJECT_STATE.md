# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **VM-002**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base funcional anterior ao VM-002: `ba15347d0dd699bb0154edd47cb49d44e72e71af`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- CFG-001 e VM-001 estão concluídos funcionalmente.
- VM-002 está **publicado no branch do PR**, ainda aguardando o CI remoto do head completo para fechamento.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## Evidência preservada antes do VM-002

No head `ba15347d0dd699bb0154edd47cb49d44e72e71af` todos os gates ficaram verdes:

- Host agent `34708197863` (#76): verde.
- Project continuity `34708197851` (#88): verde.
- Development image `34708197848` (#82): verde.
- Bootable media `34708197852` (#55): verde.

O Bootable media usa o QEMU 10.2.2 da própria imagem StorOS para o probe TCG. Os critérios continuam exigindo dois boots do mesmo QCOW2, agente + painel nos dois boots, `boot_count=1 → 2`, `config_generation=1` e fingerprints persistentes de configuração/token. Essa evidência valida a fundação virtual anterior ao VM-002; não substitui o CI do novo head.

## VM-002 — publicado

### Store de intenção por VM

Novo `src/storos_vm_store.py` persiste estado desejado em `/var/lib/storos/vm-intents/<uuid>/` com:

- `current.json` ativo;
- histórico `revisions/000001.json`, `000002.json`, ...;
- geração monotônica;
- `expected_generation` para concorrência otimista;
- criação segura com `expected_generation=0`;
- rollback que cria nova geração em vez de reescrever histórico;
- `intent_sha256` recalculado na leitura;
- escrita temporária + `fsync` + `os.replace` + `fsync` do diretório;
- lock exclusivo por UUID com modo `0600`.

### Tarefas e precondições

`storos_tasks.py` evoluiu para schema 2. Uma reconciliação dry-run agora exige precondições coerentes com o plano:

- `intent_generation`;
- `intent_sha256`;
- `snapshot_sha256`.

O ledger mantém `mode=dry_run`, `can_apply=false` no plano e `executable=false` na tarefa/ações. Locks por VM ficam em `/var/lib/storos/tasks/.locks/<vm_uuid>.lock`. Divergência de hash/precondição é rejeitada.

### CLI e imagem

`storosctl` ganhou:

- `vm-intent-apply`;
- `vm-intent-show`;
- `vm-intent-history`;
- `vm-intent-list`;
- `vm-intent-rollback`.

`vm-plan` aceita arquivo ad hoc ou intenção persistida por `--vm-uuid`. `vm-reconcile-dry-run` exige intenção persistida e grava a tarefa vinculada à geração/hash da intenção e ao snapshot observado.

O Containerfile inclui `storos_vm_store.py`. `image/check-image.sh` valida o módulo, persiste uma intenção de teste, planeja a partir do store e cria uma tarefa dry-run schema 2 com precondições.

## Verificação realizada antes da publicação

- O head anterior `ba15347...` tinha os quatro workflows verdes, incluindo Bootable media.
- O código do novo store e do ledger passou em **8 testes focados** executados neste ambiente para geração, update, rollback, detecção de adulteração, persistência/permissões, lock de tarefa, rejeição de ação executável e rejeição de drift de precondição.
- Os módulos novos/modificados foram compilados sintaticamente durante a preparação.
- `image/check-image.sh` passou em `bash -n`.
- A validação integral remota do head VM-002 ainda é obrigatória; não declarar VM-002 fechado até os workflows do head completo ficarem verdes.

## Segurança preservada

- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada ao store/ledger.
- O painel web continua somente leitura.
- `features.vm_write_enabled=true` continua sendo rejeitado pela configuração.
- Locks e precondições são apenas fundação de consistência; não constituem autorização para executar mudanças.
- Um executor futuro deverá reler geração/hash/snapshot, validar autorização/feature gate/capacidade, obter lock de execução, aplicar timeout, verificar o estado observado após a mudança e auditar o resultado.

## Limitações atuais

- Sem criação/start/stop real de VM pelo control plane StorOS.
- O contrato de VM ainda não cobre discos, rede, firmware, passthrough ou política dinâmica de CPU/RAM.
- O painel ainda não expõe intenção/plano/tarefas.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark de desempenho.
- Nenhum teste físico de GPU compartilhada foi realizado.
- O QCOW2 continua sendo artefato de laboratório, não release para Danilo instalar.

## Próxima tarefa concreta

1. Aguardar somente o resultado dos workflows disparados pelo **head completo do VM-002** e investigar qualquer falha real sem relaxar gates.
2. Com Host agent, Project continuity, Development image e Bootable media verdes, registrar o fechamento remoto VM-002.
3. Depois, avançar para exposição **somente leitura** de intenção/plano/tarefas no painel, sem executor.
4. Em paralelo ao roadmap de controle, preparar a futura mídia física USB somente depois que os gates virtuais continuarem estáveis; não substituir QCOW2 de laboratório pelo método do usuário antes da hora.
5. STOR-009/010/011 e validação física de GPU permanecem pendentes.

## Continuidade

Danilo autorizou continuar sem pular etapas e confirmou que o QCOW2 deve permanecer como laboratório interno até a base ficar sólida. O objetivo de entrega ao usuário continua sendo mídia física/pendrive em etapa posterior. Não pedir nova autorização para seguir este roadmap. Obedecer `AGENTS.md` em toda publicação. **Não mesclar o PR #2 sem instrução explícita.**
