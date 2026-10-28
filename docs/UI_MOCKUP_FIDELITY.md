# StorOS v0.4 visual — implementação do mockup enviado pelo usuário

Referência: captura do usuário de 1536 × 1024 pixels, 27/10/2026, com sidebar escura, hero de servidores, seis KPIs, duas linhas de cartões, loja, Compose, gráficos de monitoramento, custos e tarefas. Não incorporamos os números fictícios da referência.

## O que foi reconstruído

- Barra lateral com grupos de armazenamento, Docker, Apps, VMs, rede, sistema e custos; expansão e páginas acessíveis por links.
- Cabeçalho com campo de busca, tema, notificações e identificação honesta de acesso local, sem simular login de admin.
- Banner escuro com imagem extraída somente da área decorativa da referência fornecida pelo usuário e painel de host/uptime reais.
- KPIs, tabelas, catálogo com cartões, projetos Compose, painel de custos, monitoramento e tarefas.
- Layout desktop inspirado nas posições/tamanhos do mockup, com versões responsivas para notebook/mobile.
- Catálogo/consulta Docker Hub e gerador de Compose anteriores preservados como páginas próprias.
- Ícones vetoriais locais, sem dependências de CDN.

## Regras dos dados

- Endpoint /api/overview: leitura real de CPU via diferenças em /proc/stat, dispositivos lsblk, rede ip -json e projetos docker compose ls; acesso pode ser bloqueado pela conta do painel.
- CPU/RAM/uptime em /api/status e /api/overview são leituras da instância StorOS, não do servidor Unraid hospedeiro.
- No Fedora imutável, o uso da raiz pode representar um overlay de poucos MiB; a UI prefere o volume persistente /var quando aplicável. O texto informa o ponto de montagem.
- Conta de administrador, custos reais, progresso de backups, array/paridade, SMART, VMs instaladas e containers executados NÃO são inventados. Ausência de integração exibe travessão/indisponibilidade.
- Um cartão da loja é uma prévia de uma imagem/Compose, NÃO um container instalado. O painel não fornece acesso direto ao docker.sock nem mutações em discos.
- Gráfico CPU coleta amostras reais apenas enquanto a página está aberta; não representa histórico remoto.

## Validação

- HTML carregado com Firefox headless a 1536×1024 numa única VM preexistente, a versão RAW/USB segue independente.
- Componentes HTML/CSS e JS servidos com sucesso; API real e acesso TLS protegido por senha foram testados.
- Prévia web de laboratório: https://192.168.30.10:18444/ — hospedada como processo temporário na VM StorOS-BootTest-v030, sem reconstrução de imagem nem nova VM.
- Ainda não há equivalência visual garantida pixel por pixel em todas as resoluções e estados de dados; o mockup é referência de design. Precisa revisão visual do usuário.
- Preview HTTPS não é persistente após reboot do host. A imagem USB v0.3.1 gravável anteriormente NÃO contém esse novo layout; nova build bootc/RAW deve ser feita após aceitação visual e testes.

## Variante USB com layout atualizado
O Containerfile.ui-v04 deriva da base USB Preview v0.3.1 que já mascara SSH e não injeta administrador. Só acrescenta os arquivos HTML/CSS/JS, imagem de banner e observabilidade atual. O script installer/build-ui-v04.sh recompila a imagem RAW em VM Fedora; **não** grava pendrives nem atualiza a imagem antiga automaticamente.

## Resultado de boot RAW v0.4 em QEMU

- A imagem de 10 GiB passou SHA-256 e inicializou por UEFI em uma VM de testes já existente, com overlay novo e backup integral do libvirt XML antigo e NVRAM.
- Firefox local apresentou o novo painel inspirado no mockup, com CPU/RAM/uso real e campos não disponíveis sem valores inventados.
- Captura de boot exibiu CPU transitória alta (medição real durante inicialização), não valor do mockup.
- Rede real ens3/IPv4 confirmada pelo QEMU, mas ausente na API se comando ip estiver indisponível. Código fonte foi corrigido com leitura via ioctl/sysfs, posterior ao RAW v0.4.
- A imagem RAW v0.4 ainda rotula a tela v0.3. O HTML no GitHub foi corrigido após a compilação, entrando numa próxima imagem.
- A fidelidade pixel por pixel permanece sujeita à revisão visual e à resolução física usada.
