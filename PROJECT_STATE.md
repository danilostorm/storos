# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **PH0-002**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Roadmap revisão 2 aprovado; [PR #1](https://github.com/danilostorm/storos/pull/1) mesclado.
- Base desta atualização: `6fe21efeb5e9b9cc9ce37d50e262e363e252caec` no PR #2.
- Branch: `phase0/gpu-feasibility`; consultar seu PR/head antes de editar.
- Fase 0 em andamento: pesquisa documental e preparação do laboratório. Sem ISO, sistema implementado ou hardware homologado.

## Decisões confirmadas

Danilo aprovou a revisão 2 com **“Ta aprovado.”** nesta conversa. Prioridade: VMs compartilhando CPU/RAM/GPU, especialmente GPU simultânea. A base pode mudar; MOS não é obrigatório. Docker/NAS são complementares. Changelog e estado são obrigatórios em cada atualização publicada.

Nova aprovação “Fecho pode começar” autoriza Fedora/uCore HCI como base do protótipo e início de código/CI. Detalhes em [BASE_FEDORA.md](docs/BASE_FEDORA.md). Isso não homologa GPU e não autoriza modificar produção, firmware ou drivers do servidor atual.

## Concluído nesta atualização

- Containerfile, identidade do protótipo e verificação de ferramentas adicionados.
- Workflow constrói imagem por digest resolvido e coleta evidências; resultado remoto deve ser consultado no PR #2.
- Sem distribuição/instalação da imagem; assinatura upstream e boot são próximos gates.

- Aprovação registrada e roadmap integrado.
- [Triagem GPU e bases](docs/FASE0_GPU.md) com fontes oficiais NVIDIA, Microsoft, AMD e Mesa; virtualização do fabricante e aceleração de APIs para guests Linux tratadas separadamente.
- [Protocolo de laboratório](docs/FASE0_LAB.md) e coletor Python somente leitura preparados.
- Suporte das placas citadas permanece não comprovado. Ausência em listas oficiais não significa impossibilidade de toda alternativa.

## Verificação e limitações

- Coletor executado somente no ambiente de desenvolvimento; JSON válido. Não valida o host de Danilo.
- Verificador de continuidade e links relativos executado localmente; consultar Actions do PR para resultado remoto.
- Sem /dev/kvm ou /dev/dri disponíveis neste ambiente. Nenhum guest, teste de GPU ou benchmark executado.
- Sem acesso ao host do usuário ou inventário confirmado. RTX 3080 Ti/RX 550 são candidatas citadas, não homologadas.
- Base, versões, licenças finais, custos e prazo pendentes. Não há proteção de branch confirmada para exigir o check ao merge.

## Próxima tarefa concreta

1. Conferir workflow de imagem do PR #2, resolver falhas de build, fixar digest/verificar assinatura e preparar boot descartável. Identificar host de laboratório e obter inventário com `python3 scripts/collect_host.py`; levantar versões de QEMU/Mesa e workloads/guests desejados.
2. STOR-009: completar matriz com modelo/versão real e requisitos de licença. Triagem iniciada, homologação pendente.
3. STOR-010: comparar bases após inventário. Linux KVM/QEMU com VirGL/Venus é hipótese de laboratório, não decisão final nem promessa para Windows.
4. STOR-011: executar protocolo em guests/discos descartáveis quando houver equipamento e acesso apropriados. Protocolo preparado, testes pendentes.
5. STOR-012/014: produzir go/no-go, alternativas/custos e estimativas com evidências. Não encerrar Fase 0 com pesquisa documental isolada.

## Para uma nova IA

Leia AGENTS.md e confira Git/PR. A aprovação acima já foi dada; não peça novamente para continuar a pesquisa. O Resource Guardian é um projeto MOS separado, não uma versão funcional do StorOS. Não repetir a revisão NAS inicial nem presumir que documentos significam implementação.
