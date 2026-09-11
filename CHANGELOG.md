# Changelog

Histórico de atualizações do projeto. Documentação tem identificadores próprios; não representa versões funcionais do sistema.

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
