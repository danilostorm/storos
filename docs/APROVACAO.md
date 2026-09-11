# Aprovação da proposta StorOS

**Pendente de aprovação de Danilo.** Documento de decisão, não autorização já concedida para implementar ou migrar o servidor.

## Pacote recomendado

| Decisão | Recomendação | Consequência |
| --- | --- | --- |
| Base | Derivar MOS mantendo Devuan inicialmente | Menor mudança inicial; exige auditar/reconstruir múltiplos componentes |
| Primeira versão | NAS + VMs/LXC + apps + Guardian + backup em um nó | Produto utilizável antes de enfrentar HA |
| Recursos da VM | Seleção simples de vCPU e RAM, automação nativa opcional | Dispensa o fluxo de configurar primeiro e cadastrar novamente no plugin |
| Armazenamento | Perfis distintos: mídia flexível e ZFS para usos adequados | Evita tratar paridade por sync como proteção contínua |
| Workspaces | VMs por pessoa; protótipo de dois postos | Depende de GPUs/periféricos; pode seguir trilha experimental |
| Cluster | Multisservidor antes de HA | Atrasar a promessa de alta disponibilidade até ter quorum/fencing testados |
| Código e distribuição | Aberto, preservando licenças upstream; proposta AGPLv3 para painel/API novos | Código correspondente e atribuições fazem parte da distribuição |
| Comercial | Sem cobrança ou planos definidos nesta fase | Suporte pago pode ser discutido depois sem bloquear uso local |
| Prazo | Estimar de novo após Fase 0 | Faixas do roadmap não são compromisso de entrega |
| Marca | StorOS como nome de trabalho | Verificar marca/domínio antes de lançamento comercial |

## Como aprovar

Danilo pode aprovar este PR ou responder: **“Aprovo o roadmap StorOS e o início da Fase 0.”** Para ajustar, indicar as decisões/fases que deseja mudar. A aprovação deve ser registrada no PR antes de alterar o estado deste documento.

A entrega seguinte à aprovação será o inventário técnico, build de referência, protótipo dos fluxos e relatório de viabilidade. O encerramento da Fase 0 terá nova revisão para fixar o escopo de implementação.

## Evidências entregues para esta revisão

- [Roadmap](../ROADMAP.md) com escopo, dependências, estimativas, critérios de aceite e backlog.
- [Referências](REFERENCIAS.md) de todos os sistemas citados, com fontes e limites de reaproveitamento.
- [Arquitetura](ARQUITETURA.md), incluindo o fluxo desejado de CPU/RAM automáticas e múltiplos postos.

Nenhum código do MOS foi importado, nenhum sistema operacional foi instalado e nenhuma VM/disco do servidor foi alterado nesta proposta. A criação destes documentos no GitHub foi solicitada por Danilo; a implementação aguarda esta aprovação.
