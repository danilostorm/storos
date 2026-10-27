# Estado do StorOS — 27/10/2026

## Local
Desenvolvimento primário no AEROCOOL: `/mnt/user/rea/StorOS`. VM Fedora de compilação `StorOS-BuildLab` em rede NAT; VMs `StorOS-BootTest` e `StorOS-BootTest-011` são descartáveis. O host de produção permanece Unraid.

## Comprovado
- OCI uCore `localhost/storos:v0.1.1` compilada.
- QCOW2 e RAW v0.1.1 (10 GiB virtuais) gerados com OSBuild na VM Fedora.
- QCOW2 v0.1.1 verificou sem erros, iniciou via UEFI até Linux, obteve IPv4, aceitou login SSH por chave, iniciou painel systemd e respondeu HTTP 200 em localhost (`/` e `/api/status`).
- Arquivos de backend/web ficaram 0644 após correção.
- Discos/VMs de laboratório são isolados dos discos reais; nenhuma gravação em pendrive físico.

## Em andamento
- `installer/Containerfile.gui`: OCI GUI compilada com Xorg/LightDM/Openbox/Firefox; primeiro QCOW2 GUI iniciou via UEFI e respondeu HTTP 200, mas ainda não abriu sessão X11 no VNC pois o modo headless era default e QEMU guest agent é confinado por SELinux. A segunda imagem `StorOS-gui-default.qcow2` foi gerada e validada; VM `StorOS-BootTest-GUI-Default` (UEFI) iniciou, LightDM/Xorg/Firefox abriram automaticamente o painel em VNC, com HTTP 200 no dashboard e API. GUI confirmada VISUALMENTE via screenshot do VNC. A imagem GUI ainda não foi gravada em pendrive físico e ainda tem acesso inicial de laboratório.
- Entrega da imagem USB ao usuário; RAW ainda não foi testado em hardware USB físico.

## Pendências
- Autenticação/RBAC no painel para acesso remoto; hoje escuta apenas `127.0.0.1`.
- Inicialização/estado persistente do USB em hardware real, identificação exclusiva e segurança de mídia de boot, atualizações/rollback, recuperação.
- Funções NAS, paridade, volumes, snapshots, VMs, GPU compartilhada e catálogo de apps ainda não implementados.
- GUI na VM confirmada em VNC; UX de escolha GUI/headless no menu de boot e boot em USB físico ainda não implementados.

## Próximas verificações
1. Criar mecanismo de seleção GUI/headless pelo menu de boot sem rebuild e remover credenciais de laboratório da distribuição pública.
2. Testar RAW em disco VIRTUAL usando QEMU/OVMF, depois pendrive descartável físico.
3. Implementar modo GUI selecionável sem autologin inseguro de administração; conta kiosk read-only.
4. Planejar virtualização compartilhada CPU/RAM/GPU como trilha separada da infraestrutura NAS.

O planejamento original de setembro permanece acessível no GitHub em `archive/antes-storos-usb-2026-10-27`.
