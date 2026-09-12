# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **WEB-VM-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002 está **fechado remotamente** no head `9f7366e84819f5053efc44c129a7a8f8c0d68286`.
- WEB-VM-001 está publicado no branch: projeção autenticada e somente leitura de intenções, planos e tarefas no painel/API.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## Fechamento remoto do VM-002

No head `9f7366e84819f5053efc44c129a7a8f8c0d68286` os gates do VM-002 ficaram verdes:

- Host agent `34710051568`: verde; suíte integral com **42/42 testes**.
- Project continuity `34710051542`: verde.
- Development image `34710051546`: verde; smoke dentro da imagem confirmou intenção persistida e reconciliação ainda exclusivamente dry-run.
- Bootable media `34710051552`, job `103597090745`: verde.

O Bootable media construiu e inspecionou o QCOW2 e inicializou **o mesmo disco duas vezes** usando QEMU 10.2.2 da própria imagem StorOS. O gate registrou `boot_count=1 → 2`, agente e painel autenticado nos dois boots, `config_generation=1` e fingerprints idênticos de configuração/token.

Provas preservadas:

- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`;
- QCOW2 SHA-256 `cde00c270df09e3f28cc0b4341a55dfa88ed8d50d1bfcd59678e4bc4329211b6`;
- artefato `storos-boot-evidence` ID `10303516398`, digest `sha256:780236c38216fe6df3464d650c418c2c24894dd32af9ec830204720467092730`;
- artefato `storos-qcow2` ID `10303451532`, digest do ZIP `sha256:536591efcc59a5872e41bfef1fcdcbd1cbb20ffbda1319726d7c284860b57cee`.

Essa evidência fecha VM-002 como fundação de consistência. Ela não habilita escrita em VM nem transforma o QCOW2 em release para o usuário.

## VM-002 — estado entregue

### Store de intenção por VM

`src/storos_vm_store.py` persiste estado desejado em `/var/lib/storos/vm-intents/<uuid>/` com `current.json`, histórico por revisão, geração monotônica, `expected_generation`, rollback por nova geração, `intent_sha256`, escrita atômica/fsync e lock por UUID.

### Tarefas e precondições

`storos_tasks.py` usa schema 2. Cada reconciliação dry-run carrega `intent_generation`, `intent_sha256` e `snapshot_sha256`. O ledger mantém `mode=dry_run`, `can_apply=false` e `executable=false`; drift de precondição é rejeitado. Não existe executor.

### CLI

`storosctl` possui `vm-intent-apply/show/history/list/rollback`; `vm-plan` aceita intenção ad hoc ou persistida; `vm-reconcile-dry-run` exige intenção persistida e grava a tarefa vinculada à geração/hash e ao snapshot observado.

## WEB-VM-001 — painel/API somente leitura

O novo incremento estende `storos_web.py` sem adicionar autoridade de comando. Endpoints autenticados publicados:

- `GET /api/vms/intents` — lista intenções persistidas;
- `GET /api/vms/intents/<uuid>` — mostra uma intenção validada;
- `GET /api/vms/intents/<uuid>/plan` — calcula em memória um plano determinístico a partir da intenção atual e do snapshot observado;
- `GET /api/tasks` — lista o ledger dry-run;
- `GET /api/tasks/<task_id>` — mostra um registro de tarefa.

O cálculo de plano não cria tarefa e não grava estado. Snapshot ausente/corrompido/incompatível retorna indisponibilidade em vez de gerar plano por suposição. `POST`, `PUT`, `PATCH` e `DELETE` continuam retornando `405` no painel autenticado.

O HTML inicial também mostra contagem de intenções/tarefas e uma tabela simples de intenções, mantendo explicitamente **Escrita em VMs: bloqueada**.

## Verificação WEB-VM-001 até este ponto

- A nova implementação e os testes foram publicados nos commits `f9d12acc7e451600ee9a533f6b3d97d7e9a651f1` e `2018e205dea05e0dd36066371b36de80ecfc1b9e`.
- Sintaxe Python da implementação e dos testes foi validada antes da publicação.
- Host agent do head arquitetural `59aa924aefa8d1960ecc5703e2f363339743e9c0`, run `34712075217`, ficou verde com a suíte que inclui os novos testes web.
- O Project continuity desse head ficou vermelho somente porque esta atualização obrigatória de `CHANGELOG.md`/`PROJECT_STATE.md` ainda não estava presente; não foi tratado como falha funcional.
- Development image do mesmo head ainda precisa ser confirmado após a publicação do lote documental final.
- WEB-VM-001 não deve ser marcado como fechado até os gates aplicáveis do head funcional/documental ficarem verdes.

## Segurança preservada

- Nenhum endpoint web chama `apply_vm_intent`, `rollback_vm_intent` ou `create_dry_run_task`.
- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada.
- Planos continuam `mode=dry_run`, `can_apply=false`; ações/tarefas continuam `executable=false`.
- `features.vm_write_enabled=true` continua rejeitado pela configuração.
- O painel continua autenticado e somente leitura; o listener padrão continua no loopback.

## Limitações atuais

- Sem criação/start/stop real de VM pelo control plane StorOS.
- O contrato de VM ainda não cobre discos, rede, firmware, passthrough ou política dinâmica de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark de desempenho.
- Nenhum teste físico de GPU compartilhada foi realizado.
- O QCOW2 continua sendo artefato de laboratório, não release para Danilo instalar.

## Próxima tarefa concreta

1. Fechar os gates remotos aplicáveis do WEB-VM-001 sem relaxar critérios.
2. Se o painel read-only permanecer verde na imagem/boot, registrar o fechamento WEB-VM-001.
3. Em seguida avançar para o próximo contrato de VM — discos, firmware e rede — ainda primeiro em modelo/validação/dry-run, antes de qualquer executor.
4. Manter QCOW2 como laboratório interno e só preparar mídia física USB quando a base virtual continuar estável.
5. STOR-009/010/011 e validação física de GPU permanecem pendentes.

## Continuidade

Danilo autorizou continuar sem pular etapas e confirmou que o QCOW2 deve permanecer como laboratório interno até a base ficar sólida. O objetivo de entrega ao usuário continua sendo mídia física/pendrive em etapa posterior. Não pedir nova autorização para seguir este roadmap. Obedecer `AGENTS.md` em toda publicação. **Não mesclar o PR #2 sem instrução explícita.**
