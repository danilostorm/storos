# StorOS

**Virtualização com CPU, RAM e GPU compartilhadas entre máquinas virtuais.**

Projeto em planejamento para várias VMs usarem o hardware do mesmo servidor simultaneamente. NAS, Docker e catálogo de apps são complementares. A base está aberta: MOS não é obrigatório.

**Estado: roadmap revisão 2, de 11/09/2026.** A mudança de foco e as regras de continuidade foram solicitadas por Danilo. Não existe ISO, sistema implementado ou GPU homologada.

## Para continuar o projeto

1. Leia [AGENTS.md](AGENTS.md): regras para pessoas e assistentes.
2. Leia [PROJECT_STATE.md](PROJECT_STATE.md): onde paramos, decisões e próxima tarefa.
3. Consulte [CHANGELOG.md](CHANGELOG.md): histórico das atualizações.
4. Revise [ROADMAP.md](ROADMAP.md) e [aprovações](docs/APROVACAO.md).

Outros documentos: [arquitetura](docs/ARQUITETURA.md), [referências](docs/REFERENCIAS.md) e [PR #1](https://github.com/danilostorm/storos/pull/1).

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
