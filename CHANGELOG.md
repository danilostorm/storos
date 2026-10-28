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

## Correção de interface após ensaio v0.3.0
- Corrigido formatador de capacidade binária (a versão v0.3.0 exibia MiB/GiB deslocados por uma unidade na GUI, sem afetar valores do backend).
- Inventário de discos físicos deixa de apresentar zram como disco físico.
- A imagem v0.3.0 do laboratório ainda possui o bug visual; a correção entrará na próxima imagem compilada.

## v0.3.1 USB Preview — segurança inicial e testes RAW
- Adicionado build sem personalização de usuário/chave de laboratório e com SSH mascarado, exclusivo para teste em notebook pelo USB.
- Testador QEMU de imagens RAW usa disco overlay QCOW2, rede NAT e VNC somente loopback, preservando o arquivo original.
- Imagem RAW v0.3.0 de laboratório validada com GPT/EFI e boot UEFI em VM separada, Docker/Compose, painel e módulos de apps/custos HTTP 200.
- A v0.3.1 precisa passar em teste de boot próprio antes de ser recomendada para gravação física.
- **Homologação limitada v0.3.1**: boot RAW UEFI em VM isolada, GUI renderizada, SHA256 do `.img` igual ao RAW do builder, portas 22/80/8765 não expostas na rede da VM. Publicada a rotina de teste por VNC/guest agent não privilegiado.

## 2026-10-27 — Reformulação visual fiel ao mockup (preview web)
- Sidebar, topo, hero, KPIs e cartões remodelados seguindo a captura original enviada pelo usuário; nenhuma métrica da captura é reproduzida como dado operacional.
- Leituras reais via /api/overview (CPU, disco e rede) e APIs anteriores; ações administrativas continuam bloqueadas.
- Corrigido falso 100% de ocupação do overlay raiz em sistemas ostree, usando o volume persistente /var quando aplicável.
- Prévia HTTPS separada na porta 18444 com autenticação, usando a VM v0.3 já existente. Versão 18443 e imagem USB v0.3.1 permanecem sem alterações.
- Cinco VMs antigas StorOS foram desligadas normalmente; discos e definições permanecem intactos.
- Iniciado estudo estático documentado do boot Unraid 7.3.4 a partir do menu de Syslinux, com script independente e sem executar componentes proprietários. Ghidra ainda pendente.

## 2026-10-27 — RAW v0.4 com novo painel validado
- RAW transferido ao AEROCOOL, hash SHA-256 confirmado e GPT/EFI verificados.
- Boot GUI UEFI confirmado na VM de teste existente, preservando definição antiga, NVRAM e disco de teste para rollback.
- BuildLab desligado após compilação, liberando memória. Duas VMs StorOS permanecem ligadas.
- Fonte corrigida depois do RAW: UI passa a exibir v0.4 e rede tem leitura alternativa sem iproute2. Próximo RAW necessário para incorporá-las.

## 2026-10-28 — Etapa 1: navegação recolhível e legibilidade
- Menu lateral desktop agora recolhe a uma barra de 74px e pode ser expandido novamente; ícones preservam títulos e rótulos acessíveis.
- Grupos Armazenamento, Docker, Aplicativos, VMs e Sistema podem recolher/expandir submenus de forma independente.
- Layout móvel usa gaveta com botão de abertura, fechamento ao selecionar item, clicar fora ou pressionar Escape.
- Aumentados textos padrão de menus, subtítulos, tabelas, botões e cartões. Controle A+ alterna três níveis de tamanho e lembra a preferência neste navegador.
- Nova folha CSS corrige barra de rolagem horizontal de tabelas no Firefox.
- Prévia HTTPS 18444 atualizada sem criar VM ou reconstruir USB. Imagem v0.4 USB existente permanece inalterada.
- Interface continua apenas de leitura; páginas não integradas mostram campos vazios, sem fingir que são gerenciadores ativos.
