# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **DEV-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Roadmap revisão 2 aprovado; [PR #1](https://github.com/danilostorm/storos/pull/1) mesclado.
- Base desta atualização: `ee334162f9aedc8c837b7fb43a2e12ef4bf90eb0` no PR #2.
- Branch: `phase0/gpu-feasibility`; consultar seu PR/head antes de editar.
- Fase 0 com boot/hardware pendentes; primeiro componente da Fase 1 implementado: agente de inventário, descoberta de VMs e CLI. Sem mídia de boot pronta ou painel StorOS. ISO não é requisito.

## Decisões confirmadas

Danilo aprovou a revisão 2 com **“Ta aprovado.”** nesta conversa. Prioridade: VMs compartilhando CPU/RAM/GPU, especialmente GPU simultânea. A base pode mudar; MOS não é obrigatório. Docker/NAS são complementares. Changelog e estado são obrigatórios em cada atualização publicada.

Nova aprovação “Fecho pode começar” autoriza Fedora/uCore HCI como base do protótipo e início de código/CI. Detalhes em [BASE_FEDORA.md](docs/BASE_FEDORA.md). Isso não homologa GPU e não autoriza modificar produção, firmware ou drivers do servidor atual.

## Concluído nesta atualização

- Implementados agente e CLI storosctl, com consulta de UUIDs/estado/recursos informados pelo libvirt, conexão somente leitura e falhas explícitas.
- Serviço systemd incluído e habilitado na receita da imagem. Snapshot atômico local, com detecção de coleta antiga; nenhum endpoint de rede.
- Dez testes locais passaram; ciclo daemon/CLI exercitado com virsh ausente. Documentado em [AGENT.md](docs/AGENT.md). Check da imagem agora integra com `test:///default`; verificar resultado remoto.

- Corrigido o marco de entrega após observação de Danilo: mídia de boot pronta, com configuração web, sem obrigatoriedade de ISO. Ver [BOOT_MEDIA.md](docs/BOOT_MEDIA.md).
- Documentados os fluxos oficiais MOS/Unraid e a distinção entre imagem OCI, mídia inicializável e sistema integralmente em RAM. Apenas documentação alterada; sem novo teste de boot.

- Containerfile, identidade do protótipo e verificação de ferramentas adicionados.
- Primeiro build passou; QEMU 10.2.2 e libvirt 12.0.0 encontrados. Digest da base fixado para builds seguintes; evidências em [BUILD_EVIDENCE.md](docs/BUILD_EVIDENCE.md).
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
- Base de desenvolvimento definida; homologação final, licenças finais, custos e prazo pendentes. Não há proteção de branch confirmada para exigir o check ao merge.

## Próxima tarefa concreta

1. Conferir CI do agente e imagem no PR #2; resolver falhas de integração se houver. Verificar assinatura upstream e preparar boot em VM descartável, validando também o serviço storos-agent, SELinux e consulta real ao libvirt. Seguir BOOT_MEDIA.md: ISO não é requisito; OCI não é mídia USB pronta. Não pedir a Danilo para escolher novamente a distribuição.
2. Após boot e agente validados, desenvolver configuração persistente e painel autenticado sobre o contrato de descoberta. Não anunciar ajustes automáticos existentes: a CLI atual somente observa.
2. STOR-009: completar matriz com modelo/versão real e requisitos de licença. Triagem iniciada, homologação pendente.
3. STOR-010: comparar bases após inventário. Linux KVM/QEMU com VirGL/Venus é hipótese de laboratório, não decisão final nem promessa para Windows.
4. STOR-011: executar protocolo em guests/discos descartáveis quando houver equipamento e acesso apropriados. Protocolo preparado, testes pendentes.
5. STOR-012/014: produzir go/no-go, alternativas/custos e estimativas com evidências. Não encerrar Fase 0 com pesquisa documental isolada.

## Para uma nova IA

Leia AGENTS.md e confira Git/PR. A aprovação acima já foi dada; não peça novamente para continuar a pesquisa. O Resource Guardian é um projeto MOS separado, não uma versão funcional do StorOS. Não repetir a revisão NAS inicial nem presumir que documentos significam implementação.
