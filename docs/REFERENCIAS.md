# Referências, reaproveitamento e limites

Pesquisa documental em fontes oficiais consultadas em **11/09/2026**. Não é benchmark executado nem ranking absoluto. A coluna StorOS descreve escolhas propostas, não funcionalidades existentes. A existência de uma capacidade em outro produto não demonstra que ela possa ser portada diretamente.

## Comparativo orientado ao produto

| Referência | Capacidade observada | Proposta StorOS | Etapa |
| --- | --- | --- | --- |
| MOS | Base Devuan, Docker/LXC/QEMU, mergerfs/SnapRAID e módulos opcionais | Ponto de partida da distribuição e migração de conhecimento do Guardian | 0–4 |
| Proxmox VE | Administração KVM/LXC, backups, rede, cluster e HA | Compute organizado, API, tarefas, backups; cluster depois da base de nó único | 3, 5, 8–9 |
| OpenMediaVault | Administração de compartilhamentos, permissões, SMART e serviços NAS | NAS compreensível, diagnóstico e opções avançadas acessíveis | 2 |
| Unraid | NAS flexível, expansão de discos, apps e VMs em experiência integrada | Facilidade para mídia e aplicações; implementar com componentes de origem/licença verificadas | 2–4 |
| TrueNAS | Gestão de armazenamento baseada em OpenZFS | Datasets, integridade, snapshots e recuperação com interface nativa | 2, 5, 8 |
| CasaOS | Experiência de nuvem pessoal, apps e widgets simples | Home orientada a tarefas e catálogo fácil de usar | 1, 4 |
| IBIK ASTER | Múltiplos postos com periféricos independentes; site anuncia edições Windows e Linux | Workspaces: VMs por usuário primeiro, multiseat do host como pesquisa | 0, 6 |

Fontes do comparativo: [MOS](https://github.com/mos-nas/mos-releases#readme), [Proxmox](https://www.proxmox.com/en/products/proxmox-virtual-environment/features), [OMV](https://www.openmediavault.org/features.html), [Unraid](https://unraid.net/product), [TrueNAS](https://www.truenas.com/truenas-community-edition/), [CasaOS](https://github.com/IceWhaleTech/CasaOS#readme), [ASTER](https://ibiksoft.com/).

Não atribuir ao TrueNAS Community toda função anunciada para Enterprise. Não chamar ASTER de exclusivamente Windows: a página oficial também anuncia uma edição Linux gratuita com suporte limitado. Gratuidade não comprova licença de código aberto ou permissão de redistribuição.

## Base MOS verificada

O README descreve Devuan como base e separa os repositórios da distribuição. `mos-releases` coordena os artefatos; kernel, rootfs, frontend e API ficam em outros projetos. O README também informa ZFS como driver opcional sem interface no escopo descrito. A proposta de UI ZFS do StorOS é trabalho adicional. [Descrição oficial](https://github.com/mos-nas/mos-releases#readme).

| Componente | Evidência de licença | Tratamento proposto |
| --- | --- | --- |
| Scripts de mos-releases | [LICENSE GPLv3](https://github.com/mos-nas/mos-releases/blob/master/LICENSE) | Preservar licença/créditos dos scripts incorporados |
| mos-api | [LICENSE AGPLv3](https://github.com/mos-nas/mos-api/blob/master/LICENSE) | Manter os termos e oferecer o código correspondente das modificações conforme aplicável |
| mos-frontend | [LICENSE AGPLv3](https://github.com/mos-nas/mos-frontend/blob/master/LICENSE) | Mesma análise por componente; branding próprio sem remover atribuições |
| Rootfs, kernel, drivers e pacotes | Repositórios relacionados no README; auditoria completa pendente | Inventariar antes de redistribuir |
| Código StorOS novo | Ainda não implementado ou licenciado | Proposta AGPLv3 para painel/API; decisão formal na Fase 0 |
| Resource Guardian | [Repositório existente](https://github.com/danilostorm/mos-plugins) | Revisar proveniência, licença, código e resultados no MOS antes de incorporar |

A licença do empacotador não relicencia toda a imagem. Manter SBOM, avisos de terceiros, fontes correspondentes e referências aos commits usados. Não remover créditos ou condições de distribuição ao trocar o nome do produto. Texto legal da licença: [AGPLv3 no repositório do MOS](https://github.com/mos-nas/mos-api/blob/master/LICENSE). Esta matriz é levantamento de engenharia; a compatibilidade final depende dos arquivos e versões efetivamente incorporados.

Unraid e ASTER são referências de funcionalidade/experiência. Não há proposta de copiar seus binários, código não licenciado para esse fim, ativação ou marcas. Qualquer integração opcional dependerá dos termos específicos e de instalação/licenciamento apropriados. Componentes abertos utilizados por esses produtos podem ser avaliados individualmente por sua origem.

## Limitações técnicas que mudam o roadmap

- SnapRAID protege o estado sincronizado e é voltado a dados adequados a esse modelo; não equivale a paridade contínua. Por isso o perfil de mídia e o perfil de VMs ficam separados. [FAQ oficial](https://www.snapraid.it/faq).
- libvirt distingue contagem de vCPUs, afinidade e parâmetros de recursos. O modo automático não deve confundir alterar quota com adicionar/remover vCPUs. A memória dinâmica depende do guest e de seus dispositivos. [Manual virsh](https://www.libvirt.org/manpages/virsh.html).
- ASTER é referência de vários postos num PC; o caminho proposto com VMs tem arquitetura diferente. A página do fabricante não certifica StorOS/Devuan nem garante compartilhamento arbitrário de GPU. [Fabricante](https://ibiksoft.com/).
- HA exige coordenação de cluster, não apenas gerenciamento remoto; a existência desse recurso no Proxmox orienta requisitos, mas não fornece compatibilidade automática para um fork MOS. [Recursos Proxmox](https://www.proxmox.com/en/products/proxmox-virtual-environment/features).

## O que falta pesquisar na Fase 0

Versões/commits de todos os componentes; build completo e atualizações; contratos do Hub; matriz ZFS/kernel; suporte de sessão gráfica em Devuan; restrições por GPU/driver; termos de Windows, apps e drivers; verificação do nome StorOS; alternativas de backup e coordenação de cluster. Os resultados podem alterar escopo e estimativas.
