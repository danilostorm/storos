# Aprovação — revisão 2

## Direção confirmada por Danilo

- VMs com compartilhamento de CPU, RAM e GPU são o foco principal.
- A base operacional pode mudar; MOS não é obrigatório.
- Docker e complementos têm prioridade menor.
- Atualizar roadmap e exigir changelog/estado para continuidade entre chats e IAs.

Esta revisão documental foi autorizada. Isso não comprova viabilidade nem autoriza alterações no servidor.

## Decisões para execução

| Decisão | Proposta |
| --- | --- |
| Primeiro trabalho | Fase 0: GPU simultânea e comparação de bases |
| Placas atuais | Investigar RTX 3080 Ti/RX 550; suporte desconhecido |
| Caso incompatível | Apresentar hardware/plataforma e custos alternativos |
| Base | Escolher após evidências, preservando licenças |
| Produto inicial | Compute + Guardian + GPU compartilhada + recuperação |
| Prazo | Reestimar após viabilidade; estimativa antiga retirada |
| Produção | Fora dos testes iniciais; laboratório descartável |

O [PR #1](https://github.com/danilostorm/storos/pull/1) permanece para revisão. A resposta **“Aprovo a revisão 2 e o início da Fase 0”** registra autorização de execução. Registrar futuras aprovações no estado do projeto; não inferir homologação pela existência dos documentos.

Documentos: [roadmap](../ROADMAP.md), [arquitetura](ARQUITETURA.md), [referências](REFERENCIAS.md), [estado](../PROJECT_STATE.md), [changelog](../CHANGELOG.md).
