# Changelog StorOS

## 2026-10-27 — Build USB e laboratório Fedora
- Criado protótipo read-only do painel/API com arquivos integrados à imagem bootc uCore.
- Laboratório Fedora 44 isolado no AEROCOOL, com ferramentas podman, rpm-ostree e image-builder.
- Criados arquivos QCOW2 e RAW de 10 GiB para imagem USB, sem tocar discos físicos.
- Imagem inicial v0.1.0: iniciou via UEFI; painel não iniciado; arquivos sem permissão de leitura.
- Corrigida v0.1.1: unit systemd, permissões e acesso SSH; comprovados boot UEFI, login SSH e HTTP 200 em localhost.
- Criados scripts de build e laboratório com verificações para impedir gravação no host.
- Separada prévia GUI opcional com LightDM/Xorg/Openbox/Firefox e conta local sem privilégio; **não homologada ainda**.
- Backup do planejamento antigo em branch archive antes da substituição da main autorizada pelo usuário.

**Limitações:** a imagem RAW não foi gravada nem validada num USB físico; a GUI depende de build e teste de sessão gráfica; NAS e virtualização ainda não disponíveis.

## 2026-10-27 — GUI local v0.2.1 (experimental)
- Preparada imagem GUI que escolhe graphical.target na própria imagem, sem executar mudanças remotas sob o SELinux restrito do agente QEMU.
- Primeira imagem GUI OCI e QCOW2 compiladas; comprovados boot UEFI, SSH, Firefox/Xorg/LightDM instalados e HTTP 200. Sessão gráfica visível ainda em teste, sem homologação.

## 2026-10-27 — Confirmação visual GUI
- Imagem GUI `StorOS-gui-default.qcow2` construída com OSBuild; `qemu-img check` aprovou.
- VM `StorOS-BootTest-GUI-Default` iniciou UEFI, recebeu IP interno `192.168.122.200`, `graphical.target`, LightDM, Xorg, Firefox kiosk e painel na tela VNC.
- `storos-dashboard.service` ativo; GET `/` e GET `/api/status` retornaram HTTP 200. Verificação de processo mostrou Firefox executado pela conta sem privilégios `storos-gui`.
- Captura de evidência somente no laboratório do AEROCOOL em `/mnt/user/rea/StorOS/lab/storos-gui-default-screen3.png`; não publicar screenshots internas nem chaves de laboratório.
- **Não comprovado:** USB físico com GUI, BIOS legado, boot selector, atualizações/rollback e recursos de NAS/VM.

## 2026-10-27 — Console noVNC e HTTPS LAN
- Corrigida VM de teste com atributo libvirt `websocket=5717`; restringido acesso às portas VNC/WebSocket em loopback; handshake HTTP 101 verificado.
- Criado gateway HTTPS LAN autenticado no AEROCOOL, com túnel SSH, recursos permitidos somente de leitura e credenciais fora do Git.
- Gateway testado: sem senha HTTP 401; senha incorreta HTTP 401; senha correta HTTP 200; API status HTTP 200; recurso desconhecido 404; POST 405.

## 2026-10-27 — v0.3 App Center + custos do Tower (em laboratório)
- Integração de módulo de estimativa de energia, internet e tempo ativo inspirado diretamente no código do Tower Command Center, de autoria do usuário (ZIEL).
- Catálogo local, pesquisa de imagens via Docker Hub HTTPS, prévia de Docker Compose para seis apps. Sem instalação privilegiada pelo painel.
- Nova seção de custos com perfil CPU/plataforma/RAM/GPU, tarifa de energia, horas e rateio do plano de internet.
- Imagem GUI estendida para inicialização do Docker Engine/Compose incluído no uCore, sujeita a teste de boot em VM.
- Dados do ZIEL, credenciais e histórico operacional não foram copiados para o StorOS.
