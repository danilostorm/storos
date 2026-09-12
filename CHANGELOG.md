# Changelog

Histórico de atualizações do projeto. Documentação tem identificadores próprios; não representa versões funcionais do sistema.

## 2026-09-12 — CFG-001A — Gate por prontidão e prova persistente do painel

- **Motivo:** o run Bootable media `34671399200`, head `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`, passou build da imagem, smoke check e QCOW2, mas o primeiro QEMU foi encerrado pelo limite fixo de 240 s antes de o primeiro boot terminar. A segunda execução chegou ao agente como `boot_count=1`, mostrando que o gate media tempo de TCG, não dois boots lógicos completos.
- **Evidência da falha anterior:** no primeiro console o sistema ainda executava trabalho único de primeiro boot e chegava à inicialização de `storos-agent.service` perto do limite. No segundo console apareceram `STOROS_BOOT_STATE boot_count=1` e `STOROS_AGENT_READY snapshot=written boot_count=1`. No mesmo head, Host agent `34671399198`, Development image `34671399204` e Project continuity `34671399235` ficaram verdes.
- **Mudou:** novo `storosctl web-marker` autentica localmente em `/api/config`, compara a resposta com o documento persistido e emite `STOROS_WEB_READY` com geração e fingerprints SHA-256 da configuração/token, sem imprimir o segredo bruto. `storos-web.service` executa esse marker em `ExecStartPost` e publica o resultado no console. O token ganha `fsync` do diretório depois da troca atômica.
- **CI:** o boot deixa de ser encerrado cegamente após 240 s. O primeiro boot pode aguardar até 420 s e o segundo até 300 s, mas ambos são encerrados assim que `STOROS_WEB_READY` aparece. O mesmo QCOW2 é reutilizado. O gate exige agente + painel prontos nos dois boots, `boot_count=1 → 2`, `config_generation=1` e fingerprints idênticos de configuração e token. A prova final esperada é `STOROS_WEB_PERSISTENCE_OK`.
- **Verificação local:** 9 testes focados de configuração/painel passaram, incluindo autenticação real do marker e confirmação de que o token não aparece em sua saída. O workflow foi validado como YAML e o bloco Bash do gate passou em `bash -n`.
- **Limites:** resultado remoto deste incremento ainda precisa ficar verde antes de declarar CFG-001 concluído. Sem boot físico USB, TLS/RBAC, escrita no libvirt, política automática de CPU/RAM ou GPU compartilhada.
- **Próximo passo:** obter os quatro checks verdes; com `STOROS_WEB_PERSISTENCE_OK`, fechar CFG-001 e iniciar modelos de VM + fila/reconciliação em dry-run.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`; contrato em [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 2026-09-12 — CFG-001 — Configuração transacional e painel autenticado

- **Motivo:** após BOOT-002A comprovar dois boots no mesmo QCOW2 com persistência `boot_count=1 → 2`, iniciar a Fase 1 de configuração persistente e a fundação do painel web sem conceder escrita prematura ao libvirt.
- **Mudou:** novo store em `/var/lib/storos/config` com geração monotônica, histórico por revisão, lock local, validação completa, `expected_generation` para concorrência otimista e rollback que cria nova geração. `storosctl` passa a rotear comandos de configuração/token sem retirar os comandos do agente. Novo `storos-web.service` entrega `/healthz`, painel HTML, `/api/status` e `/api/config`, exige autenticação para dados administrativos e recusa métodos mutáveis. O listener padrão é `127.0.0.1:8080`; exposição sem TLS fora do loopback exige opt-in explícito. `features.vm_write_enabled=true` é rejeitado nesta fase.
- **Segurança:** token administrativo aleatório persiste em `/var/lib/storos/auth/admin.token` com modo `0600`; o service roda sem capabilities, com filesystem protegido e somente `/var/lib/storos` gravável. Nenhum token é embutido na imagem ou documentação.
- **Verificação local:** testes do store e painel passaram, incluindo apply/rollback 1→2→3, conflito de geração, bloqueio de escrita em VM, requisito explícito para LAN sem TLS, persistência/permissão do token, autenticação das APIs e rejeição HTTP 405 para mutações. `check-image.sh` também passa a verificar os módulos, preset, dois services, configuração inicial e modo do token.
- **Verificação remota:** a primeira execução Host agent `34670864403` no commit `49c563e225c4dcbd72ae5413f1c80789b3c5b10a` executou 21 testes; 20 passaram e 1 falhou por typo no próprio teste (`settings['wec']` em vez de `settings['web']`). O corretivo seguinte deixou Host agent `34671066203` e Project continuity `34671066176` verdes no head `c77c676774fe39c7d3fbfa70caabbfe363f747a5`. Nesse mesmo head, Development image `34671066182` confirmou que os dois services foram habilitados pelo preset, mas o smoke check falhou por um caminho digitado como `/usr/lib/system/storos-web.service` em vez de `/usr/lib/systemd/system/storos-web.service`. O corretivo `ed1d5ff18e3c376cd0aafaf267f134f5c73919df` deixou Host agent, Development image e Project continuity verdes; o Bootable media correspondente é analisado na entrada CFG-001A.
- **Limites:** painel ainda somente leitura, sem TLS integrado, RBAC, criação/start/stop de VM, política automática de CPU/RAM ou GPU compartilhada. Nenhum boot físico por USB foi executado.
- **Próximo passo:** validar imagem/boot com `storos-web.service` habilitado, confirmar que config/token sobrevivem ao segundo boot sem expor segredo e então iniciar modelos de configuração de VM + fila/reconciliação ainda com escrita no libvirt bloqueada.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base anterior `250fb9e972ff472376658dbc3ac17a7dd2617ecd`; arquitetura em [docs/ARQUITETURA.md](docs/ARQUITETURA.md) e contrato em [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 2026-09-11 — BOOT-002A — Evidência 1 → 2 e correção do gate

- **Motivo:** o run BOOT-002 provou a persistência básica no mesmo QCOW2, mas o job ficou vermelho por exigir um marcador de prontidão do agente no primeiro boot antes de o timeout TCG terminar.
- **Evidência:** no run `34665914397`, head `3064b5849330e4405cc4dda4a8921f083440389e`, build e QCOW2 passaram. O primeiro console registrou `STOROS_BOOT_STATE boot_count=1`; o segundo registrou `STOROS_BOOT_STATE boot_count=2` com `boot_id` diferente e também `STOROS_AGENT_READY snapshot=written boot_count=2`. Isso demonstra que `/var/lib/storos/boot-state.json` sobreviveu ao segundo boot do mesmo disco.
- **Mudou:** o gate passa a validar persistência pelos dois marcadores `STOROS_BOOT_STATE`, mantém a exigência de `STOROS_AGENT_READY` no segundo boot e grava `boot-console.log` antes das asserções. O timeout TCG por boot sobe de 210 s para 240 s para acomodar a variação observada.
- **Verificação:** Host agent, Development image e Project continuity já passaram no head anterior. O novo `Bootable media` ainda precisa ficar verde para fechar o gate automatizado BOOT-002A.
- **Limites:** persistência básica de estado está comprovada pelos logs; configuração transacional completa, boot físico por USB, painel web e GPU compartilhada continuam pendentes.
- **Próximo passo:** obter o gate corrigido verde e então iniciar configuração persistente transacional e a fundação do painel autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run `34665914397`, base `3064b5849330e4405cc4dda4a8921f083440389e`.

## 2026-09-11 — BOOT-002 — Persistência entre dois boots no mesmo QCOW2

- **Motivo:** após o primeiro boot completo validado, provar que estado StorOS em `/var/lib/storos` sobrevive a reinicialização real da mesma imagem de disco.
- **Mudou:** `storosctl` ganhou registro persistente do `boot_id` do kernel com escrita atômica/fsync e contador de boots distintos. `storos-agent.service` usa `StateDirectory=storos`, registra o boot antes do daemon e emite `STOROS_AGENT_READY ... boot_count=N` após o primeiro snapshot. O workflow passa a bootar o mesmo QCOW2 duas vezes e exige `boot_count=1` e depois `boot_count=2`.
- **Verificação anterior:** o run `34665004511` no commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce` passou integralmente: build, QCOW2, OVMF/QEMU, agente e upload do disco ficaram verdes. Isso fecha a primeira prova de boot + agente do StorOS em VM descartável.
- **Verificação deste incremento:** testes unitários cobrem incremento único por `boot_id`, permissões do estado e rejeição de ID inválido. A prova de dois boots depende do novo workflow remoto e não deve ser marcada como concluída antes do check verde.
- **Limites:** ainda sem boot físico por USB, painel web ou GPU compartilhada. O contador comprova persistência básica do estado, não ainda a configuração transacional completa da Fase 1.
- **Próximo passo:** obter o workflow de dois boots verde; depois iniciar configuração persistente transacional e painel web autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`.

## 2026-09-11 — BOOT-001B — Preset de primeiro boot e prova do agente

- **Motivo:** o run `34651227029` gerou e validou o QCOW2, iniciou o StorOS via OVMF e chegou ao login serial, mas o primeiro boot executou `systemd preset-all` e removeu `/etc/systemd/system/multi-user.target.wants/storos-agent.service` porque a imagem ainda não tinha política de preset própria.
- **Mudou:** adicionada a política vendor `10-storos.preset` para habilitar `storos-agent.service` no primeiro boot; o Containerfile passa a usar `systemctl preset`; a unidade passa a puxar `virtqemud.socket` e só emite `STOROS_AGENT_READY snapshot=written` no console depois de o primeiro snapshot existir. O CI agora usa esse marcador como prova de boot + agente funcional.
- **Verificação:** o console do run `34651227029` mostrou aplicação de preset, remoção explícita do link do agente e, depois, boot completo até `localhost login:` com `virtqemud`, `sshd` e targets do sistema ativos. A correção foi validada pelo run `34665004511` no commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`, que passou inclusive o gate `STOROS_AGENT_READY snapshot=written`.
- **Limites:** ainda não houve boot físico por USB, persistência após reinício, painel web ou teste de GPU. O QCOW2 continua sendo artefato de laboratório.
- **Próximo passo:** validar dois boots no mesmo QCOW2 e persistência em `/var/lib/storos`.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `5b1aff0ce80a9f3b9eadf7017678bdce08d890ef`.

## 2026-09-11 — BOOT-001 — Pipeline QCOW2 e prova automatizada de boot

- **Motivo:** avançar do OCI validado para uma mídia virtual realmente inicializável, sem transformar ISO em requisito do StorOS.
- **Mudou:** workflow `boot-media.yml` para construir a imagem bootc de desenvolvimento, passá-la por um registro local efêmero do runner, gerar QCOW2 com o Image Builder oficial, inicializar o disco em QEMU/TCG e confirmar pelo console serial que o systemd alcançou `storos-agent.service`. Adicionada configuração do Image Builder para console serial e lint bootc no workflow. O workflow roda em push da branch e em pull request para deixar a prova visível no PR.
- **Verificação:** sintaxe Bash e TOML revisadas antes da publicação. O resultado real do build/boot remoto deve ser consultado no workflow disparado pelo incremento; esta entrada não afirma sucesso do boot antes do CI terminar.
- **Limites:** ainda não houve boot físico por USB, persistência após reinício, painel web ou teste de GPU. QCOW2 é artefato de laboratório, não release.
- **Próximo passo:** obter o primeiro workflow verde; se o console comprovar a inicialização do agente StorOS, registrar a evidência e testar persistência/reboot antes de avançar ao painel.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `83feeec44cbf55a878b503bc03e4a7ceceb8c548`; fluxo descrito em [BOOT_MEDIA.md](docs/BOOT_MEDIA.md).

## 2026-09-11 — DEV-001 — Agente funcional e descoberta de VMs

- **Motivo:** iniciar a parte funcional autorizada por Danilo; evitar a falha de descoberta silenciosa observada no protótipo Guardian.
- **Mudou:** agente Python, CLI storosctl, unidade systemd, snapshot atômico e descoberta de VMs por UUID usando libvirt somente leitura. Integração na imagem e workflow de testes adicionados.
- **Verificação:** 10 testes locais passaram. Ciclo real daemon/CLI local reportou virsh ausente com diagnóstico explícito e código 2. CI executa integração com o driver simulado do libvirt; consultar checks do commit para resultado remoto.
- **Limites:** não houve boot StorOS ou consulta ao host de Danilo; nenhum ajuste de recursos, VM criada ou painel web. Snapshot é temporário, não histórico. Fase 0 permanece aberta.
- **Próximo passo:** confirmar check da imagem, validar boot/serviço e avançar para configuração persistente e painel autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base ee334162f9aedc8c837b7fb43a2e12ef4bf90eb0; contrato e comandos em docs/AGENT.md.

## 2026-09-11 — PH0-004 — Mídia de boot, sem ISO obrigatória

- **Motivo:** Danilo apontou que o fluxo MOS/Unraid é preparar mídia e inicializar o sistema; o assistente vinha tratando ISO como marco obrigatório.
- **Mudou:** README, roadmap, arquitetura e base Fedora passam a descrever mídia de boot e configuração web. BOOT_MEDIA.md separa OCI, imagem de disco, ZIP e ISO opcional; não presume que uCore rode integralmente em RAM.
- **Referências:** consultados guia oficial de mídia MOS e downloads/instalador Unraid. O Unraid atual também oferece ISO opcional; não registrar ausência universal desse formato.
- **Verificação:** revisão documental e links relativos locais. Sem mudança na receita ou novo teste de boot; builds anteriores continuam como evidência de composição.
- **Próximo passo:** empacotar e testar disco virtual inicializável; definir persistência e comportamento da mídia física.
- **Referência de trabalho:** [PR #2](https://github.com/danilostorm/storos/pull/2), base 1d7b10cd932ce90a339245bffb54a8d3872be3d3. Entradas históricas preservadas.

## 2026-09-11 — PH0-003 — Primeiro build validado e base fixada

- **Mudou:** fixado o digest uCore testado no Containerfile e no workflow; evidências essenciais preservadas em docs/BUILD_EVIDENCE.md.
- **Motivo:** tornar a base de desenvolvimento reproduzível e registrar o primeiro resultado real, seguindo a autorização de continuidade.
- **Verificação:** [build 34632041207](https://github.com/danilostorm/storos/actions/runs/34632041207) passou no commit 0258381f4d3d0982bd9113fdbb331db29fb290a9; QEMU 10.2.2 e libvirt 12.0.0 presentes. Continuidade passou. A fixação do mesmo digest é verificada pelo novo CI deste commit.
- **Limites:** nenhum boot, GPU compartilhada ou instalação; assinatura upstream ainda pendente. Artefato remoto contém evidências, não ISO.
- **Próximo passo:** verificar assinatura da base e adaptar protocolo de boot descartável; não solicitar nova escolha de distribuição.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2); título e descrição do PR atualizados para incluir o protótipo Fedora/uCore.

## 2026-09-11 — PH0-002 — Protótipo Fedora/uCore

- **Motivo:** Danilo autorizou começar com Fedora/uCore (“Fecho pode começar”).
- **Mudou:** Containerfile derivado de ucore-hci, identificação, check de ferramentas e workflow de build com inventário e digest da base; decisão arquitetural registrada.
- **Verificação:** sintaxe shell e continuidade locais; resultado do build remoto deve ser consultado no PR.
- **Limites:** sem boot, instalador, assinatura própria, GPU testada ou mudanças no MOS; receita experimental.
- **Próximo passo:** obter build verde, fixar/verificar base e preparar boot descartável.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base 6fe21efeb5e9b9cc9ce37d50e262e363e252caec.

## 2026-09-11 — PH0-001 — Aprovação e início da Fase 0

- **Decisão:** Danilo aprovou a revisão 2 com “Ta aprovado.”; PR #1 mesclado em `3746474390e96175278ea39bd9b8bf1982d4bb25`.
- **Mudou:** aprovação e progresso alinhados; adicionadas triagem GPU/base, protocolo de duas VMs e coleta de inventário somente leitura.
- **Pesquisa:** matrizes oficiais NVIDIA vGPU, Windows Server GPU-P e AMD GIM, mais alternativas Mesa VirGL/Venus. Placas citadas não homologadas; Linux/Windows tratados separadamente.
- **Verificação:** coletor executado localmente com JSON válido; verificação de continuidade/links. Consultar Actions do PR para resultado remoto.
- **Limites:** nenhum teste físico, driver alterado ou sistema instalado; sem acesso ao host de Danilo. Fase 0 em andamento.
- **Próximo passo:** obter inventário e identificar laboratório; testar combinações reais antes de decidir a base.
- **Referência:** branch `phase0/gpu-feasibility`, baseada no merge do [PR #1](https://github.com/danilostorm/storos/pull/1).

## 2026-09-11 — DOC-002 — Revisão 2 e continuidade

- **Mudou:** foco principal em VMs compartilhando CPU, RAM e GPU; base operacional em aberto; GPU simultânea passa à Fase 0. NAS/Docker/apps tornam-se complementares.
- **Motivo:** orientação explícita de Danilo nesta conversa; ele também pediu histórico para continuidade com outro chat/IA.
- **Documentação:** README, roadmap, arquitetura, referências e aprovação alinhados. Estimativas antigas retiradas até validar a GPU.
- **Continuidade:** AGENTS.md define atualização obrigatória deste arquivo e PROJECT_STATE.md; workflow e script verificam registros e links relativos.
- **Verificação:** revisão de coerência e links locais; testes do verificador com intervalo válido e ausência intencional de registro. Resultado do GitHub Actions deve ser consultado no PR; não presumir sucesso antes da execução.
- **Limites:** nenhum teste de GPU, build de SO, implementação ou alteração no servidor. Execução da Fase 0 ainda pendente.
- **Referência:** [PR #1](https://github.com/danilostorm/storos/pull/1), branch proposal/storos-roadmap. Base anterior: 689871f2d6df26f8c78b4e72a26491de9ffc2588.

## 2026-09-11 — DOC-001 — Planejamento inicial (registro retrospectivo)

- Criados README, roadmap revisão 1, arquitetura, referências e decisões para aprovação.
- Proposta inicial centrada em MOS/Devuan, NAS, virtualização, apps, backup e Workspaces.
- Pesquisa documental de MOS, Proxmox, OMV, Unraid, TrueNAS, CasaOS e ASTER; links locais verificados.
- Publicado no [PR #1](https://github.com/danilostorm/storos/pull/1), commit 689871f2d6df26f8c78b4e72a26491de9ffc2588. Inicialização de main: e09a081e80ab50f841b536905f89269e53cc56ee.
- Sem sistema implementado ou hardware homologado. Prioridades desta revisão foram substituídas por DOC-002; histórico mantido.
