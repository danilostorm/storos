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

## Aprovação registrada em 11/09/2026

Danilo respondeu **“Ta aprovado.”** à revisão 2. Essa aprovação autoriza integrar o roadmap e iniciar a Fase 0, sem exigir outra frase específica.

O [PR #1](https://github.com/danilostorm/storos/pull/1) foi mesclado em main no commit `3746474390e96175278ea39bd9b8bf1982d4bb25`. Pesquisa documental e preparação do laboratório começaram. Base final, go/no-go e homologação dependem das evidências da Fase 0.

Não foram autorizadas migração de produção, alterações de firmware/drivers ou modificações no servidor atual. O laboratório físico ainda precisa ser identificado. Documentação não comprova funcionamento do hardware.

Documentos: [roadmap](../ROADMAP.md), [arquitetura](ARQUITETURA.md), [referências](REFERENCIAS.md), [estado](../PROJECT_STATE.md), [changelog](../CHANGELOG.md).

## Base de desenvolvimento autorizada

Em 11/09/2026, Danilo respondeu **“Fecho pode começar”** à proposta Fedora/uCore. Autorizados protótipo da imagem, código e CI; decisão técnica detalhada em [BASE_FEDORA.md](BASE_FEDORA.md). Isso não autoriza instalar no servidor atual nem homologa GPU.
