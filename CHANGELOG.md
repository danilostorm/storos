# Changelog StorOS

## 2026-10-28 — USB v0.5 criada e com GUI validada em UEFI + Legacy no QEMU
- Na VM isolada Fedora 44 BuildLab, compilada `localhost/storos:ui-v05` com base SSH mascarada. O OSBuild gerou o RAW v0.5 de 10 GiB (10.737.418.240 bytes), quatro partições GPT e finalizou com `STOROS_V05_RAW_STRUCTURE_VERIFIED`.
- Verificados GPT/BIOS Boot/EFI/raiz e SHA-256 integral no Fedora e no AEROCOOL, após transferência esparsa: `de2ac025105f9b82e9fed350ba7664c9b46a3c19d905186cf93bbce59270d004`.
- UEFI/OVMF: a VM `StorOS-BootTest-RAW-v050` inicializou o Linux, respondeu ao guest agent, obteve IPv4 e exibiu a GUI v0.5 em VNC; teste externo confirmou portas 22/80/8765 inacessíveis.
- Legacy/SeaBIOS: a VM `StorOS-BootTest-RAW-v050-BIOS` inicializou o Linux, respondeu ao guest agent e exibiu a GUI v0.5 em VNC, sem placa de rede.
- Ambas usaram overlays QCOW2, não gravaram o RAW original ou dispositivos físicos. BuildLab e VMs de teste foram desligadas; v0.4 continua preservada.
- 115 testes passaram dentro da VM Fedora (fonte para a imagem), e 116 na `main` do AEROCOOL após integração da ferramenta de teste BIOS.
- **Somente homologação virtual**: sem teste em pendrive/notebook, persistência/rollback, app Docker instalado, gestão de array/paridade/pools, backup/restore, compartilhamentos ou VMs de produção. Consulte `docs/USB_V05_BUILD_STATUS.md`.


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

## 2026-10-28 — Etapa 2: inventário real de armazenamento
- API /api/storage de leitura somente: discos, partições, montagem, uso, SMART disponível e configuração SMB/NFS.
- Páginas Armazenamento e Compartilhamentos agora apresentam dados reais e explicam limitações.
- Seções Samba virtuais [homes], [global], [printers] e [print$] excluídas da contagem.
- Teste pela VM existente: disco VirtIO 10 GiB, quatro partições, nenhuma share efetiva; SMART físico não exposto.
- HTTPS autenticado, POST bloqueado, nenhuma VM ou disco alterado.
- Imagem USB v0.4 anterior não inclui esta etapa.

## 2026-10-28 — Main/Discos e módulos do sistema inspirados no Unraid
- Adicionada navegação explícita Armazenamento > Discos, com Main organizada em Array, Pools, Boot, Outros Dispositivos e Operações.
- Identificação do disco de boot por montagens reais. Array/pools inexistentes não são simulados, e discos extras nunca são presumidos como livres ou formatáveis.
- Leituras de velocidade média por disco em sysfs de Linux; só exibidas depois de duas coletas válidas. Contadores de erros sem fonte confiável aparecem vazios.
- API /api/modules e páginas de consulta reais para usuários, imagens, redes e volumes Docker, redes libvirt e serviços do sistema.
- Funcionalidades administrativas ainda não implementadas têm aviso explícito, sem botões falsamente operacionais.
- Estudo estático reproduzível do código PHP/Page da Main e plugin Unassigned Devices presente no AEROCOOL. Nada de código proprietário foi incorporado ao StorOS.
- Mantida a política HTTP de somente leitura, API no loopback, gateway HTTPS autenticado. A atualização é web; RAW USB v0.4 anterior não foi recompilado.
- Adicionada a importação local de templates Unraid XML v2 na Loja. Gera Compose de prévia sem upload, sem executar Docker ou copiar caminhos arbitrários do Unraid. Importações perigosas são sinalizadas para revisão.

## 2026-10-27 — Preparação v0.5 e validação Legacy (sem release)
- BIOS Legacy/SeaBIOS da imagem v0.4 finalmente confirmado até o Firefox kiosk com QEMU temporário (3 GiB RAM, 2 vCPU, NIC desconectada, overlay QCOW2). UEFI da mesma imagem já havia sido confirmado.
- A imagem existente do AEROCOOL não foi modificada. Portanto o notebook antigo pode estar falhando na detecção USB/firmware, e não na etapa do GRUB.
- Preparada fonte StorOS v0.5 com os módulos recentes e receita uCore/bootc baseada na imagem SSH-disabled; testes executados no AEROCOOL e Fedora BuildLab.
- A execução do build remoto foi bloqueada pelos controles da conexão, por isso **não existe IMG v0.5 para gravar**. Consulte docs/USB_V05_BUILD_STATUS.md antes de rodar em laboratório.

## 2026-10-27 — Fundamentos de segurança administrativa
- Primitivas de identidade com scrypt+salt, arquivo privado de criação única, limitação de falhas, sessões temporárias/CSRF, papéis e autorização negada para alterações.
- Auditoria com metadados permitidos, sem capturar senha, sessão ou cookies.
- API somente leitura /api/security/status e página Sistema > Segurança mostram estado real, com login nativo e operações de escrita desativados.
- Nenhum serviço privilegiado ou conta administrativa real criado; gateway de laboratório segue como único login web.

## 2026-10-27 — Autenticação nativa isolada
- Adicionado backend/auth_socket.py com socket Unix privado e endpoints locais de login, sessão, health e logout com CSRF.
- Sem porta TCP, sem integração com o gateway e sem operações privilegiadas.
- Testes HTTP reais em socket Unix cobrem CSRF, limite de tentativas, permissões e bloqueio de ações administrativas.
- Nenhuma conta administrativa real ou operação de escrita foi ativada.

## 2026-10-27 — Apps e USB integrados no código de laboratório
- Gerenciador de catálogo controlado com plano Docker Compose, volumes nomeados, SHA-256, execução opcional somente em VM e auditoria.
- Endpoints privados de apps no serviço Unix com admin/CSRF, desabilitados por padrão.
- CLI storosctl com getpass e confirmação; validador somente leitura de USB GPT/BIOS/EFI.
- Compose Nginx aceito pelo parser real da VM sem criar containers.
- Nenhuma VM nova ou disco de produção alterado; imagem USB v0.5 ainda não compilada.
- Projetos Compose agora preservam estado privado de preparação, deploy e falha; erros nunca são apresentados como implantação concluída.

## 2026-10-28 — Ponte HTTPS de login nativo opcional
- Gateway dispõe de rotas restritas de sessão/login/logout via Unix socket habilitáveis apenas por --auth-socket.
- Cookie Secure, HttpOnly, SameSite=Strict, controles Origin/Host e CSRF; Basic Auth original obrigatório.
- Página Sistema > Segurança exibe formulário somente após habilitação expressa do serviço, não por padrão.
- Integração testada com sockets temporários, sem liberar operações privilegiadas e sem criar contas do host.
- Sem alteração da imagem USB existente; v0.5 ainda não compilada.

## 2026-10-28 — Verificação real de containers no gerenciador (laboratório)
- Após o `docker compose up -d`, o gerenciador valida via `docker compose ps --all --format json` se o serviço e projeto esperados estão efetivamente em estado `running`.
- Se o container não estiver em execução, se a resposta for inesperada ou se o Docker falhar, a implantação é marcada como `failed`; os arquivos e volumes não são removidos automaticamente.
- A listagem privada reconsulta o estado de execução dos projetos implantados ou falhos; quando o Docker está indisponível, apresenta `running: null` em vez de inferir uma condição falsa.
- Novos testes cobrem parada imediata, identificação incorreta, mudança posterior de estado e JSON em linhas: 115 testes aprovados no AEROCOOL usando mocks para execução Docker.
- **Nenhum container real foi instalado**, a instalação via HTTPS continua bloqueada e a imagem USB v0.5 não foi gerada nesta etapa.

## 2026-10-28 — Segurança no empacotamento USB v0.5 (código, sem build)
- Build v0.5 recebe lock exclusivo e trabalha em diretório temporário privado; evita publicar saída parcial como imagem final.
- Antes de apresentar o RAW de saída, valida tabela GPT com partições BIOS, EFI e Linux via verificador somente leitura, além de gravar SHA-256 relativo ao próprio arquivo.
- Os arquivos de relatório e marcador `.structure-ok` são publicados apenas após validação de estrutura; o marcador **não** significa boot homologado nem autoriza gravação em pendrive de produção.
- Em falha, a área temporária é preservada para diagnóstico. A fonte e a imagem v0.4 não foram alteradas por essa preparação.
- Script passou por `bash -n` e 115 testes no AEROCOOL; **o build Fedora da v0.5 não foi executado nesta etapa**.

## 2026-10-28 — Teste de runtime independente do Docker no builder
- O teste de consulta de estado do aplicativo mantém o mock de disponibilidade do Docker também na asserção de inventário, evitando depender de Docker instalado no Fedora BuildLab (que usa Podman).
- A lógica de produção não foi alterada. Os 115 testes passaram na VM Fedora e no AEROCOOL; testes de Compose são simulados.

## 2026-10-28 — Ensaio BIOS Legacy isolado para imagens USB
- Adicionado `tools/test-boot-raw-bios.sh` para criar uma VM SeaBIOS descartável com overlay QCOW2 e sem placa de rede, sem anexar discos físicos e sem modificar a imagem RAW original.
- VNC limitado a `127.0.0.1`; o script não considera a mera inicialização de QEMU como boot validado. Teste de screenshot e `guest-ping` são etapas separadas.

## 2026-10-28 — IMG v0.5 preparado para balenaEtcher
- Criada cópia esparsa .img do RAW v0.5 com comparação integral de SHA-256, verificação GPT/BIOS/EFI/root e preservação do original.
- Guia PT-BR para notebook Legacy/UEFI e balenaEtcher em docs/USB_V05_NOTEBOOK_GUIDE_PTBR.md.
- Nenhum USB físico gravado; sem teste real em notebook, array, paridade ou autorização administrativa de produção.
