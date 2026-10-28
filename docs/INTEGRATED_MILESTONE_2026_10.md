# StorOS: integração de login, Apps e USB (laboratório)

> **Atualização em 28/10/2026:** as notas abaixo descrevem o marco anterior à compilação. A v0.5 **já foi gerada**, transferida com SHA-256 verificado e inicializada com GUI em QEMU/OVMF e SeaBIOS. Consulte [o status atual de USB](USB_V05_BUILD_STATUS.md). Instalação web de aplicativos, USB físico e NAS de produção continuam pendentes.

## Implementações

- backend/app_manager.py: templates do catálogo interno, plano Docker Compose determinístico, confirmação SHA-256 e somente volumes nomeados. Sem aceitar entradas arbitrárias ou montagem de diretórios do host.
- backend/auth_socket.py: endpoints privados /v1/apps/plan, /v1/apps/install e /v1/apps/installed sob sessão admin e CSRF; modo de implantação desabilitado por padrão.
- tools/storosctl.py: CLI local via Unix socket, com getpass e confirmação escrita; sem senha em argumentos.
- tools/check_usb_image.py: inspeciona arquivos RAW/IMG regulares sem montar/escrever, verificando GPT, BIOS Boot, EFI, root, limites e SHA-256 opcional.
- installer/Containerfile.ui-v05 e installer/build-ui-v05.sh: incluem CLI e exigem os novos módulos no build, ainda restrito ao Fedora BuildLab.

## Evidências

- 105 testes passaram no AEROCOOL, incluindo fluxo de autenticação, CSRF, testes de Compose e detecção da estrutura USB.
- O Compose de Nginx foi produzido e validado pelo Docker Compose real dentro da VM StorOS, com a opção config --quiet. Nenhuma imagem baixada nem container iniciado.
- Não foi habilitado o daemon administrativo. O usuário storadmin da VM não tem acesso ao grupo Docker; a execução real exige um serviço com permissões separadas e auditoria/rollback. Não vamos conceder privilégio equivalente a root automaticamente.
- A imagem StorOS v0.4 de 10 GiB passou na inspeção de GPT com partições BIOS/EFI/root. Em trabalhos anteriores, v0.4 alcançou a GUI em QEMU SeaBIOS e OVMF.
- A nova imagem USB v0.5 ainda não existe. A tentativa anterior de compilação foi bloqueada pela conexão e não foi contornada.

## Operação de laboratório

Inspeção de imagem preservada:

    python3 tools/check_usb_image.py /mnt/user/rea/StorOS/output/StorOS-v0.4-USB-Preview.img

Testes de código:

    python3 -m unittest discover -s tests -q

O modo --enable-lab-apps do daemon por socket exige uma conta criada separadamente em diretório privado 0700, sessão administrativa válida, CSRF e confirmação do hash, além de execução dentro de VM. Ele NÃO está ativado no AEROCOOL ou no painel HTTPS. Não instale o daemon em host físico neste estágio.

## Pendências fundamentais

- Login nativo no navegador, proxy seguro, HTTPS, cookies, RBAC, políticas de auditoria e recuperação de conta.
- Loja com catálogo amplo e botão Instalar realmente operacional, atualização de aplicações e estados persistentes.
- Administração de Docker Compose e containers com identidade de serviço, permissões isoladas, rollback e acompanhamento de progresso.
- Array/paridade e pools Btrfs/ZFS confiáveis, SMB/NFS, usuários, VMs, backup e atualizações atômicas.
- Compilação autorizada da imagem USB v0.5, testes com os dois firmwares, instalação/persistência e teste no notebook físico.
- Eventual engenharia reversa binária com Ghidra. A análise existente cobre componentes de interface da Main, não toda a implementação do Unraid.

Este marco é uma base técnica de laboratório, NÃO um NAS pronto para dados de produção. O painel 18444 permanece de leitura; o botão Install ainda não opera nele.

## Controle de falhas do Compose

O projeto mantém estado privado preparado, implantando, implantado ou falhou. Se o Docker Compose falhar, o StorOS registra falha e mantém o projeto para diagnóstico, sem apagar containers ou volumes automaticamente. A lista de projetos é um inventário de configurações: o campo running permanece vazio até existir uma sonda real do daemon.

## Verificação de runtime pós-instalação (28/10/2026)
- O gerenciamento privado exige uma resposta `docker compose ps --all --format json` associada ao projeto e serviço esperados após o `up -d`; retorno zero de `up -d` isoladamente não constitui sucesso.
- Listagem de aplicativos consulta execução ao vivo para implantações prévias, preservando distinção entre `state` histórico e `running` observado. Falha de sonda gera `running: null`.
- 115 testes passaram no AEROCOOL em checkout temporário com runners Docker simulados. Nenhum teste desta etapa iniciou container real ou habilitou instalação via navegador.
