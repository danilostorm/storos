# Changelog

Histórico de atualizações do projeto. Documentação tem identificadores próprios; não representa versões funcionais do sistema.

## 2026-09-11 — DEV-001 — Agente funcional e descoberta de VMs

- **Motivo:** iniciar a parte funcional autorizada por Danilo; evitar a falha de descoberta silenciosa observada no protótipo Guardian.
- **Mudou:** agente Python, CLI storosctl, unidade systemd, snapshot atômico e descoberta de VMs por UUID usando libvirt somente leitura. Integração na imagem e workflow de testes adicionados.
- **Verificação:** 10 testes locais passaram. Ciclo real daemon/CLI neste ambiente gravou e releu `missing_virsh` corretamente, com código 2. CI executa integração com o driver simulado do libvirt; consultar checks do commit para resultado remoto.
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
