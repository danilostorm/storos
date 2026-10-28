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

## Acesso LAN / noVNC no laboratório
- A VM `StorOS-BootTest-GUI-Default` usa VNC 5917 e WebSocket 5717, ambos em loopback host; a porta WebSocket foi adicionada ao XML do libvirt, corrigindo o motivo do “Failed to connect to server” no noVNC.
- A VM segue em NAT `192.168.122.200`. O dashboard na VM ainda é `127.0.0.1:8765`. Para LAN, usa gateway experimental autenticado em `https://192.168.30.10:18443/` com túnel SSH.
- Não funciona após reboot do host sem reiniciar os serviços temporários. Certificado TLS autoassinado, credenciais no laboratório fora do controle de versão.

## StorOS v0.3 — APP CENTER + custos do Tower (2026-10-27)
- Código-fonte publicado no GitHub com lógica de custos adaptada do Tower Command Center do próprio usuário (ZIEL); sem copiar credenciais/configuração/consumo real do ZIEL.
- Backend: `/api/apps/catalog`, `/api/apps/engine`, `/api/apps/compose`, `/api/apps/hub`, `/api/billing/model` e `/api/billing/estimate` (todos em leitura, não iniciam containers nem escrevem configurações).
- Interface gráfica: loja de seis apps, busca no Docker Hub, prévia de Compose e simulador mensal de energia/internet/hora ativa; ainda sem histórico coletado ou gerenciamento com RBAC.
- Todos os seis modelos Compose passaram `docker compose config --quiet`, os testes unitários locais passaram e respostas HTTP do backend validaram os novos endpoints.
- OCI uCore v0.3 com Docker Engine/Compose presentes e habilitados por systemd. **QCOW2/RAW v0.3 ainda não são considerados homologados até boot/HTTP/Docker/GUI no laboratório.**
- Próximo ensaio de notebook via balenaEtcher exige imagem sem chave de laboratório, checksum, teste RAW em QEMU e checklist `docs/USB_NOTEBOOK_TEST.md`.

### Validação da imagem v0.3.0 GUI
- QCOW2 gerado e verificado com `qemu-img check`; boot UEFI na VM `StorOS-BootTest-v030` em `192.168.122.70`.
- LightDM, Firefox kiosk, Docker, containerd e painel do StorOS ativos; `docker compose version` confirma Compose 5.6.0.
- Tela VNC capturada. HTTP 200 em `/`, `/apps.js`, `/api/apps/catalog`, `/api/apps/engine`, `/api/apps/hub`, `/api/apps/compose`, `/api/billing/model`, `/api/billing/estimate`.
- Gateway HTTPS LAN autenticado redirecionado via SSH para a nova VM; acesso sem senha HTTP 401 e POST 405.
- Screenshot revelou bug de unidade da memória e zram tratado como disco físico. Fonte corrigida após o build; requer nova imagem. A versão v0.3.0 ainda não está homologada para notebook.

### 2026-10-27 — versão USB Preview v0.3.1 testada
- `StorOS-v0.3.1-USB-Preview.img`: imagem RAW de 10 GiB em `/mnt/user/rea/StorOS/output/`, checksum SHA256 igual ao da origem Fedora, GPT/EFI confirmado.
- VM isolada `StorOS-BootTest-RAW-Preview031` iniciou por overlay QCOW2 da imagem RAW e exibiu o StorOS no console VNC, incluindo correção de unidades/zram.
- QEMU guest agent respondeu, porta SSH 22 e portas HTTP 80/8765 não estão acessíveis na LAN da VM. SSH está mascarado na imagem OCI e nenhum blueprint de usuário/chave é utilizado nesta versão.
- `tools/verify-usb-vm.sh` implementa teste externo não privilegiado da VM e salva captura. Não foi necessário enfraquecer SELinux.
- **Status de release**: preview para boot/GUI de notebook; não é NAS para produção nem possui instalação de apps com um clique, controle de discos, conta de administrador configurável ou suporte validado de Wi-Fi/Secure Boot.

## 2026-10-28 — Checagem pós-deploy de aplicativos (código)
- Implementado controle de execução do Compose: um `up -d` com retorno zero não é mais suficiente para registrar `deployed` se o serviço não continuar em `running`.
- O inventário privado pode retornar `running: true/false/null` conforme resposta real do Docker; `null` significa ausência de observação confiável, não parada confirmada.
- 115 testes unitários executados em cópia temporária do repositório no AEROCOOL e aprovados; testes Docker usam runner simulado.
- Sem habilitação do daemon de apps no Unraid, sem instalação web, sem manipulação de discos físicos e sem nova imagem USB. A aprovação desses testes não equivale a homologação de deployment real.
