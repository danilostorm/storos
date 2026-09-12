# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CI-BOOT-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior desta atualização: `6b9e157b394b637403fa50af653cd4bd64a15b14`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- CFG-001 está concluído: agente somente leitura, persistência de boot, configuração transacional e painel autenticado somente leitura têm prova remota entre dois boots do mesmo QCOW2.
- VM-001 está concluído funcionalmente no head `45bd655269d8ef45f1c6f5ace9ff82ce3f8454fc`: intenção de VM schema v1, planner dry-run e ledger persistente de tarefas foram validados sem executor mutável.
- Fase 0 continua aberta para hardware/GPU. RTX 3080 Ti/RX 550 permanecem não homologadas para compartilhamento simultâneo.

## Evidência preservada do VM-001

- Host agent `34699051160` (#69): verde.
- Project continuity `34699051144` (#81): verde.
- Development image `34699051205` (#75): verde.
- Bootable media `34699051187` (#49), job `103567451447`: verde.
- O mesmo QCOW2 foi iniciado duas vezes com `boot_count=1 → 2`, agente e painel autenticado prontos nos dois boots, `config_generation=1` preservada e fingerprints idênticos de configuração/token.
- O gate emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.
- `features.vm_write_enabled=false` continua obrigatório; não existe executor/adaptador libvirt mutável.

## CI-BOOT-001 — diagnóstico e correção em andamento

O commit documental `6b9e157b394b637403fa50af653cd4bd64a15b14` não alterou código funcional, mas o Bootable media #51 (`34700188781`) falhou em duas tentativas consecutivas no primeiro boot TCG. Build bootc, smoke da imagem, geração e inspeção do QCOW2 passaram em ambas.

Nas duas tentativas, nenhum marcador StorOS chegou a existir: `web=0`, `agent=0`, sem `STOROS_BOOT_STATE`; o segundo boot nem começou. O guest chegou ao switch-root e depois o `systemd 259.8-1.fc44` falhou antes dos serviços StorOS com `Failed to fork off sandboxing environment for executing generators: Protocol error`, seguido de `Failed to start up manager.` e congelamento do manager.

A tentativa 2 também registrou `clocksource: Watchdog remote CPU 1 read timed out` antes da falha. Os dois jobs usavam `-smp 2`. Os QCOW2 foram gerados separadamente e tinham hashes diferentes, mas reproduziram a mesma assinatura pré-StorOS. O merge ref do PR foi comparado ao head e não possui diferenças de arquivo, descartando mudança funcional trazida pela `main` como causa.

### Ajuste desta atualização

- O guest QEMU/TCG do **gate de CI** passa de `-smp 2` para `-smp 1` para remover a variável SMP/clock watchdog do teste de correção de boot.
- Isso não muda recursos suportados pelo StorOS nem prova desempenho/compartilhamento de CPU; TCG continua sendo apenas um probe funcional de boot.
- O loop detecta explicitamente a assinatura fatal do manager (`generator Protocol error` + `Failed to start up manager.`) e encerra o diagnóstico cedo com `guest_fatal=1`, em vez de consumir todo o timeout e parecer um timeout de painel/agente.
- Os limites continuam **420 s no primeiro boot e 300 s no segundo**.
- Os critérios de sucesso não foram relaxados: cada boot ainda precisa de agente + painel, o mesmo QCOW2 precisa avançar `boot_count=1 → 2`, e configuração/token devem persistir.

### Evidência das falhas preservada

- Run Bootable media #51: `34700188781`.
- Tentativa 1: job `103570462206`, artefato `storos-boot-evidence` ID `10299648872`, digest `sha256:476a86fc34493001e8bb05eb60cf1bf07120acb6bcd736042f1cb51e47b38ca9`.
- Tentativa 2: job `103585516180`, artefato ID `10300784701`, digest `sha256:7605de8c239c4f83a640b6da01ebcdb1307a1b4a6b8091cce57b4c5dcab7347e`.
- A tentativa 2 teve `boot-second.log` vazio porque o primeiro boot falhou antes de StorOS.

## VM-002 — preparado, ainda não publicado

O próximo incremento funcional foi preparado localmente, mas **não deve ser publicado por cima de um gate de boot quebrado**. O staging atual contém:

- store persistente/versionado por VM em `/var/lib/storos/vm-intents`, com geração monotônica, revisões, escrita atômica/fsync e lock local;
- `expected_generation` obrigatório (`0` na criação) e rollback criando nova geração;
- fingerprint SHA-256 da intenção e validação anti-adulteração;
- binding do plano a `intent_generation`, `config_generation`, hashes da intenção/configuração/snapshot e `lock_scope=vm:<uuid>`;
- lock por VM para criação de tarefa vinculada, sem executor;
- comandos `vm-intent-apply/show/list/history/rollback`, `vm-plan-stored` e `vm-reconcile-stored-dry-run`;
- smoke de imagem que exige novamente `can_apply=false` e `executable=false`.

### Verificação local do VM-002

- **28/28 testes** dos arquivos destinados ao repositório passaram no staging corrigido, incluindo regressão VM-001, store/revisões, precondições/binding, locks/tarefas e CLI persistente.
- `py_compile` dos módulos relevantes passou.
- `bash -n image/check-image.sh` passou.
- Essa evidência é apenas local; VM-002 não tem CI remoto porque ainda não foi publicado.

## Limitações atuais

- `features.vm_write_enabled=false` continua obrigatório.
- Nenhuma mutação libvirt está habilitada; nenhum `virsh define/start/shutdown/setvcpus/setmem` é executado pelo planner/ledger.
- Não existe worker/executor de tarefas.
- O painel web continua somente leitura e ainda não expõe intenção/plano/tarefas.
- O contrato de VM ainda não cobre discos, rede, firmware, dispositivos, passthrough, mínimos/máximos dinâmicos de RAM ou GPU.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB ainda.
- QEMU/TCG do CI não representa desempenho real; o novo `-smp 1` é deliberadamente apenas para estabilidade do probe de boot.
- Sem teste físico de GPU compartilhada; RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Rodar o Bootable media com o gate TCG de 1 vCPU e confirmar que a falha pré-StorOS desaparece sem aumentar timeout.
2. Exigir novamente os marcadores completos de dois boots e persistência; se houver falha StorOS real, diagnosticar em vez de mascarar.
3. Somente após o gate voltar a ficar verde, publicar VM-002 em um único lote com código, testes, documentação, `CHANGELOG.md` e este estado.
4. Manter VM-002 estritamente em plan/dry-run, sem executor e com `features.vm_write_enabled=false`.
5. Depois do VM-002 remoto verde, avançar para exposição somente leitura no painel e só então desenhar o executor controlado futuro.
6. STOR-009/010/011, boot físico e validação física de GPU continuam pendentes; CI virtual não encerra Fase 0.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Obedecer `AGENTS.md` em toda publicação. **Não mesclar o PR #2 sem instrução explícita.**
