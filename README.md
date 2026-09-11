# StorOS

**Seu servidor, seus arquivos e seus computadores em um único painel.**

Proposta de sistema aberto derivado do MOS, com identidade própria, para NAS, máquinas virtuais, aplicativos e postos de trabalho. Foco inicial: homelabs, criadores de conteúdo e pequenos negócios.

**Estado: proposta para aprovação de Danilo — 11/09/2026.** Este repositório contém planejamento. Não há ISO, instalador, versão funcional ou compatibilidade de hardware certificada.

## Documentos para aprovação

- [Roadmap e critérios de entrega](ROADMAP.md)
- [Comparativo das referências e fontes](docs/REFERENCIAS.md)
- [Arquitetura proposta e experiência de uso](docs/ARQUITETURA.md)
- [Decisões para aprovação](docs/APROVACAO.md)

## Proposta central

| Área | O que queremos entregar |
| --- | --- |
| StorOS Storage | Compartilhamentos simples; armazenamento flexível para mídia e ZFS para cargas apropriadas |
| StorOS Compute | VMs KVM, LXC e controle de GPU/USB pelo painel |
| StorOS Guardian | CPU/RAM automáticas integradas à criação da VM, com mínimos, tetos e reserva do servidor |
| StorOS Apps | Catálogo de aplicativos, Compose e plugins com permissões declaradas |
| StorOS Backup | Backups, restauração testada e migração assistida |
| StorOS Workspaces | Mais de um posto de trabalho no mesmo servidor, começando por VMs isoladas |
| StorOS Cluster | Administração de vários servidores e, depois, alta disponibilidade |

Os nomes dos módulos são propostas. A marca StorOS ainda precisa de verificação de disponibilidade antes de divulgação comercial.

O objetivo é selecionar boas capacidades e construir uma experiência coerente. Não instalar os painéis de todos os produtos no mesmo host. Recursos descritos como futuros não estão implementados.
