# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **DOC-002**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Branch de trabalho: proposal/storos-roadmap.
- Revisão: [PR #1](https://github.com/danilostorm/storos/pull/1), proposta não mesclada no momento deste registro.
- Base anterior desta atualização: 689871f2d6df26f8c78b4e72a26491de9ffc2588. Consulte o head atual do PR antes de editar.
- Fase atual: planejamento; roadmap revisão 2. Ainda não existe implementação, ISO ou laboratório homologado.

## Decisões confirmadas

Danilo liberou a escolha de outra base operacional e definiu prioridade em VMs com CPU/RAM/GPU compartilhadas, especialmente GPU simultânea. Docker e outros complementos não são o foco. Solicitou atualização do roadmap e changelog obrigatório para continuidade.

A revisão documental está autorizada. A Fase 0 permanece proposta para aprovação de execução. Não há base/driver escolhidos, GPU comprovada, licença final do código novo ou prazo fechado.

## Concluído nesta atualização

- Roadmap e arquitetura reposicionados para viabilidade GPU antes da escolha da base.
- Critérios distinguem GPU simultânea de passthrough exclusivo e de acesso remoto.
- Instruções AGENTS, changelog, este estado e verificação automática de continuidade adicionados.
- Referências históricas preservadas e prioridades alinhadas.

## Verificação e limitações

- Links relativos Markdown e coerência documental verificados localmente.
- Verificador exercitado com mudança válida e com ausência de changelog, que deve falhar.
- Consultar o resultado real de Actions no PR; o check de continuidade não certifica hardware ou sistema.
- Nenhum teste físico, benchmark, build de distribuição ou alteração no servidor foi executado.
- Nenhuma credencial/acesso ao host StorOS está configurada aqui. RTX 3080 Ti/RX 550 são placas citadas, não homologadas.
- Não há proteção de branch confirmada para tornar o check obrigatório ao merge.

## Próxima tarefa concreta

1. Conferir PR/head e eventual nova orientação/aprovação de Danilo; não assumir aprovação por causa deste arquivo.
2. Quando autorizada a Fase 0, começar por STOR-009: matriz de suporte GPU/driver/guest/hipervisor/licença com fontes oficiais por versão/modelo.
3. Separar resultados documentados de resultados testados. Identificar equipamento disponível e propor laboratório descartável antes de modificar hosts.
4. Comparar bases em STOR-010 e preparar protocolo de duas VMs em STOR-011. Não escolher MOS automaticamente nem repetir a arquitetura NAS da revisão 1.
5. Encerrar a pesquisa com relatório go/no-go, alternativas/custos e estimativas revistas; atualizar changelog e estado.

## Para uma nova IA

Leia AGENTS.md primeiro. O README de main pode conter só a inicialização enquanto o PR está aberto; use a branch de trabalho acima. A memória do chat pode chamar este projeto de plugin Unraid, mas isso não descreve o StorOS: o Guardian era um projeto MOS separado e é somente referência técnica. Consulte o Git antes de refazer trabalho ou anunciar progresso.
