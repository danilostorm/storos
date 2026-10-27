# StorOS

**Status:** versão 0.1, laboratório. Alternativa NAS e virtualização construída de forma independente sobre o Fedora Server.

## Objetivo

Desenvolver um sistema de armazenamento e gerenciamento de servidores mais simples, confiável e observável, com painel único para discos, pools, containers, VMs, redes, backups e alertas.

A primeira entrega atual é um **protótipo funcional de painel e API SOMENTE LEITURA**. **O requisito principal do produto é ser um sistema operacional independente e inicializável pelo pendrive.** O builder inicial de RAW/QCOW2 está preparado, mas ainda não compilou uma imagem testada e não gerencia discos.

## Desenvolvimento no AEROCOOL

- Código: `/mnt/user/rea/StorOS`
- O Unraid atual não foi modificado.
- Não montamos/desmontamos discos, não formatamos nem reiniciamos serviços.
- Interface de pré-visualização (iniciada manualmente): `python3 backend/server.py --port 8765`
- Acesso somente pelo próprio host, ou túnel SSH: `ssh -L 8765:127.0.0.1:8765 root@192.168.30.10`; abra `http://127.0.0.1:8765` no computador.
- Testes: `python3 -m unittest discover -s tests -v`
- Nenhuma API modifica o sistema; o protótipo usa apenas `/proc`, `lsblk`, `docker ps` e `virsh list`.

## Arquitetura planejada

- **Sistema-base:** Universal Blue uCore baseado em Fedora CoreOS, como conceito adotado no Unraid 8; NÃO Fedora 8.
- **Painel:** aplicação web própria, interface responsiva.
- **Backend de produção:** API autenticada e agentes com privilégios mínimos; a API atual é apenas demonstração.
- **Storage:** Btrfs/XFS inicialmente, ZFS opcional quando testado e suportado; alternativa de discos heterogêneos com mergerfs + SnapRAID, cujo parity é agendado (não equivalente ao tempo real do Unraid).
- **Virtualização:** libvirt/KVM.
- **Containers:** Podman e interface compatível com OCI; Docker opcional.
- **Rede:** NetworkManager, WireGuard, SMB, NFS.
- **Backups:** snapshots, cópias verificadas e recuperação testada.

## Regras importantes

1. Trabalhar em VMs e discos virtuais descartáveis antes de qualquer hardware real.
2. Nunca migrar ou montar automaticamente discos do Unraid.
3. REA e Ghidra podem fornecer evidência de comportamento/interoperabilidade. Não copiar componentes proprietários ou mexer em GUID/licenças.
4. Não expor a API experimental à internet nem iniciar como serviço em produção.
5. Não prometer proteção de dados sem testes de restauração, falha de disco e corrupção.

Veja [Requisitos de boot USB](docs/REQUISITOS.md), [Compilação de RAW/QCOW2](installer/README.md), [Arquitetura](docs/ARQUITETURA.md) e [Pesquisa REA/Ghidra](docs/ENGENHARIA_REVERSA.md).


## Modo gráfico local (GUI) — experimental
Assim como o modo GUI do Unraid, o StorOS terá uma opção **local** para exibir seu painel via navegador no monitor ou console VNC da VM, sem abrir sua API na rede. A implementação experimental está em [docs/GUI_MODE.md](docs/GUI_MODE.md) e [installer/Containerfile.gui](installer/Containerfile.gui). Ela usa LightDM, Xorg, Openbox e Firefox em modo kiosk, com uma conta sem privilégios. O modo padrão continua headless. A imagem **headless v0.1.1** já passou nos testes UEFI/HTTP; não confundir com homologação da versão GUI.

## Repositório e histórico
Este código sucede o planejamento de virtualização do StorOS iniciado em setembro de 2026. A branch `archive/antes-storos-usb-2026-10-27` mantém integralmente o estado anterior. A intenção de gerenciamento de VMs e compartilhamento de recursos permanece no [roadmap](ROADMAP.md), mas ainda não foi implementada.

⚠ **Somente laboratório**: ainda não é alternativa segura ao Unraid em produção. Nenhuma operação de gerenciamento ou formatação de disco físico está habilitada.


## Console noVNC e painel HTTPS do laboratório
- noVNC: Unraid → VMs → `StorOS-BootTest-GUI-Default` → VNC Remote. O script agora configura WebSocket 5717 no QEMU, limitado ao loopback do AEROCOOL e acessível via proxy do Unraid com sessão autenticada.
- Painel web externo de testes: `https://192.168.30.10:18443/` com autenticação local no gateway `tools/lan_gateway.py`. Certificado autoassinado. A VM não expõe sua API diretamente pela LAN. Não é um acesso de produção.

## Novos módulos em v0.3 (em desenvolvimento)
- **Loja de Apps:** catálogo local, busca pública no Docker Hub e modelos de Docker Compose. O painel ainda não instala aplicativos por motivos de segurança.
- **Custos:** simulador com o modelo de rateio do seu Tower Command Center (ZIEL), incluindo CPU, RAM, GPU dedicada, eletricidade, hora ativa e internet proporcional aos GB. Sem coleta automática/histórico até o próximo módulo.
- **Docker/Compose:** componentes já vêm na base uCore. Imagem GUI v0.3 habilita o daemon Docker para avaliação na VM separada.
- Especificação detalhada em [App Center e custos](docs/APP_CENTER_AND_COSTS.md).

### Próxima etapa: pendrive no notebook
O protocolo de homologação e gravação via balenaEtcher está em [docs/USB_NOTEBOOK_TEST.md](docs/USB_NOTEBOOK_TEST.md). **Não usar uma imagem de laboratório que inclui chaves SSH pré-configuradas como release pública.**
