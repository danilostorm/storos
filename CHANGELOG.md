# Changelog

Histórico de atualizações do projeto. Documentação tem identificadores próprios; não representa versões funcionais do sistema.

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
