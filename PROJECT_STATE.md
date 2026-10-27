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
- `installer/Containerfile.gui`: OCI GUI compilada com Xorg/LightDM/Openbox/Firefox; primeiro QCOW2 GUI iniciou via UEFI e respondeu HTTP 200, mas ainda não abriu sessão X11 no VNC pois o modo headless era default e QEMU guest agent é confinado por SELinux. Build separado com target graphical.target default está em preparação/validação.
- Entrega da imagem USB ao usuário; RAW ainda não foi testado em hardware USB físico.

## Pendências
- Autenticação/RBAC no painel para acesso remoto; hoje escuta apenas `127.0.0.1`.
- Inicialização/estado persistente do USB em hardware real, identificação exclusiva e segurança de mídia de boot, atualizações/rollback, recuperação.
- Funções NAS, paridade, volumes, snapshots, VMs, GPU compartilhada e catálogo de apps ainda não implementados.
- GUI exige confirmação de desktop no VNC e UX de seleção GUI/headless no boot.

## Próximas verificações
1. Build GUI OCI e disco QCOW2, boot isolado com vídeo VNC; validar sessão, Firefox e painel.
2. Testar RAW em disco VIRTUAL usando QEMU/OVMF, depois pendrive descartável físico.
3. Implementar modo GUI selecionável sem autologin inseguro de administração; conta kiosk read-only.
4. Planejar virtualização compartilhada CPU/RAM/GPU como trilha separada da infraestrutura NAS.

O planejamento original de setembro permanece acessível no GitHub em `archive/antes-storos-usb-2026-10-27`.
