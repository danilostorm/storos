# StorOS

**Virtualização com CPU, RAM e GPU compartilhadas entre máquinas virtuais.**

Projeto em desenvolvimento inicial para várias VMs usarem o hardware do mesmo servidor simultaneamente. NAS, Docker e catálogo de apps são complementares. Fedora/uCore HCI é a base do protótipo; a homologação ainda depende de testes.

**Estado: Fase 0 em andamento; primeiro build da composição da imagem aprovado no CI.** Ainda não há mídia de boot pronta, painel StorOS ou GPU homologada.

## Para continuar o projeto

1. Leia [AGENTS.md](AGENTS.md): regras para pessoas e assistentes.
2. Leia [PROJECT_STATE.md](PROJECT_STATE.md): onde paramos, decisões e próxima tarefa.
3. Consulte [CHANGELOG.md](CHANGELOG.md): histórico das atualizações.
4. Revise [ROADMAP.md](ROADMAP.md) e [aprovações](docs/APROVACAO.md).

Outros documentos: [arquitetura](docs/ARQUITETURA.md), [referências](docs/REFERENCIAS.md) e [PR #1](https://github.com/danilostorm/storos/pull/1).

Pesquisa inicial: [triagem GPU e bases](docs/FASE0_GPU.md), [protocolo de laboratório](docs/FASE0_LAB.md) e coletor de inventário. Testes físicos pendentes.

## Prioridades

| Prioridade | Entrega pretendida |
| --- | --- |
| P0 | Validar GPU simultânea entre VMs e escolher hardware/base compatíveis |
| P0 | Distribuir CPU e RAM disponível por demanda, prioridade e reserva do host |
| P0 | Criar e administrar VMs pelo painel, com estado aplicado verificável |
| P0 | Isolamento, backup e recuperação |
| P1 | Múltiplos usuários/postos simultâneos |
| P2 | NAS, Docker, apps e, posteriormente, multisservidor/cluster |

Passthrough exclusivo é uma opção auxiliar, não a entrega do requisito de GPU compartilhada. RTX 3080 Ti/RX 550 citadas por Danilo são candidatas a investigação, sem suporte comprovado.

Toda atualização publicada deve atualizar changelog e estado do projeto, com mudanças, verificações, pendências e próximos passos.

## Desenvolvimento iniciado

Base do protótipo: **Fedora/uCore HCI**. [Decisão, build e limitações](docs/BASE_FEDORA.md). A entrega pretendida é preparar a mídia, dar boot e configurar pelo navegador; [ISO não é requisito](docs/BOOT_MEDIA.md).

O primeiro build passou; veja [versões e evidências](docs/BUILD_EVIDENCE.md). O próximo marco é inicializar a imagem em uma VM descartável.

O [agente do host](docs/AGENT.md) é o primeiro componente funcional: inventário, descoberta de VMs por UUID, serviço periódico e interface `storosctl`. A integração é testada no CI; boot e VMs reais continuam pendentes.
