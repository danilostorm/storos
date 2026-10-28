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

## Interface renovada inspirada no mockup do projeto
A prévia web de desenvolvimento em `https://192.168.30.10:18444/` usa a VM de testes `StorOS-BootTest-v030`, com os mesmos dados reais do uCore e autenticação do gateway local. Não é a interface incorporada ao USB v0.3.1 já compilado: será incorporada em build posterior, quando testada visualmente. Funcionalidades sem integração exibem vazio/indisponível e não simulam VMs, Docker, RAID, custos ou tarefas. Consulte [fidelidade e dados reais](docs/UI_MOCKUP_FIDELITY.md) e [engenharia reversa estrutural](docs/REVERSE_ENGINEERING_PROGRESS.md).

Durante os ensaios, cinco VMs antigas foram desligadas normalmente, preservando os arquivos das imagens. O AEROCOOL manteve somente o BuildLab, a v030 utilizada pelo painel e a USB Preview mais recente em execução. Sem exclusão de discos.

### Imagem StorOS v0.4 para testar GUI pelo USB
A imagem inicializável verificada está em output/StorOS-v0.4-USB-Preview.img no AEROCOOL. O teste de boot UEFI pela VM existente foi aprovado. Consulte docs/USB_NOTEBOOK_TEST.md para SHA256, limitações e cuidados. Esta é uma edição de teste de GUI e observabilidade, não um substituto homologado para Unraid.

### Navegação e fontes na prévia web
A partir da etapa 1 de interface, o menu pode ser recolhido com o botão no canto superior esquerdo, e os grupos da barra lateral podem ser expandidos de forma independente. O controle **A+** no topo aumenta os textos em até dois níveis adicionais, com preferências salvas apenas no navegador. No celular, o botão abre uma gaveta lateral. Veja [o escopo e os testes](docs/NAVIGATION_STAGE_1.md).

O recurso está disponível na prévia web do AEROCOOL, porta **18444**. Ainda precisa entrar em uma nova imagem de instalação USB; a imagem v0.4 já gerada anteriormente não muda.

### Armazenamento — etapa 2 na prévia web
O painel em https://192.168.30.10:18444/#storage inclui inventário real do StorOS convidado, com partições, montagens, ocupação e SMART quando disponível. Em #shares, mostra configurações SMB/NFS detectadas. Nenhuma destas páginas controla os discos Unraid do hospedeiro ou executa alterações. Detalhes e limites: docs/STORAGE_STAGE_2.md. A imagem USB v0.4 anterior ainda não inclui este módulo.

### Main / Discos e inventário de módulos
A página de Discos tem seções distintas para array, pools, boot, outros dispositivos e operações, como observado na organização da aba Main do Unraid. Informações vêm exclusivamente da instância StorOS, e não dos discos do host AEROCOOL. Na VM de teste, a classificação identifica apenas vda (boot) e deixa array/pools como não configurados. Não significa que paridade ou pools funcionem.

As páginas de Usuários, Imagens Docker, Redes Docker, Volumes Docker, Redes libvirt, Sistema e Monitoramento receberam consultas reais somente leitura quando permitidas. Recursos administrativos ausentes mostram limites explícitos.

Consulte docs/FEATURE_STATUS_2026_10.md para a matriz de funções e docs/UNRAID_MAIN_REVERSE_ENGINEERING.md para evidências da análise estrutural do Unraid. Não se trata de paridade funcional completa nem de um NAS homologado. A imagem USB antiga não inclui esta atualização.

### Importar template XML do Unraid (prévia)
Na Loja de Aplicativos, selecione um arquivo Container XML v2 para converter, somente no navegador, os campos compatíveis em um projeto Compose de referência. Não são enviadas senhas nem arquivos ao servidor; paths de host são transformados em volumes nomeados. Esta é uma prévia, não instalação com um clique. A instalação segura requer autenticação nativa, permissões e um daemon de gestão isolado.

### v0.5 — fonte pronta, aguardando compilação
Os arquivos de construção estão em installer/Containerfile.ui-v05 e installer/build-ui-v05.sh; o processo deve ser executado somente na VM Fedora BuildLab. Os testes de fonte passaram, mas a geração do RAW v0.5 ficou bloqueada pela conexão e nenhuma nova imagem foi publicada. A v0.4 anterior foi testada graficamente em QEMU tanto UEFI quanto Legacy BIOS, sem alteração de discos físicos. Consulte docs/USB_V05_BUILD_STATUS.md.

### Fundamentos de autenticacao — etapa inicial
A biblioteca backend/security_core.py contém os fundamentos de identidade; o painel permite consultar o estado em Sistema > Segurança. Scrypt com salt, sessões e CSRF, limite de tentativas e política de recusa de escrita estão cobertos por testes, mas login nativo e serviço administrativo ainda NÃO foram ativados. Detalhes em docs/ADMIN_SECURITY_FOUNDATION.md.

### Autenticação por socket Unix (laboratório)
O módulo backend/auth_socket.py oferece login, consulta de sessão e logout com CSRF em socket Unix privado. Ainda NÃO está conectado ao login web ou a serviços privilegiados, e nenhuma conta administrativa real foi provisionada. Consulte docs/AUTH_SOCKET_STAGE.md. A imagem USB v0.5 permanece pendente.

### Docker Compose e USB: integração experimental
O backend/app_manager.py e a CLI local tools/storosctl.py implementam plano/instalação controlados exclusivamente em VM, com autenticação Unix e confirmação SHA-256. O modo de instalação está desligado por padrão, não há botão Install operacional no navegador. O validador tools/check_usb_image.py verifica imagens sem montar nem gravar discos. Veja docs/INTEGRATED_MILESTONE_2026_10.md. A imagem USB v0.5 continua não compilada.
