# StorOS: estado funcional verificado

| Módulo | Implementação atual | Operações de escrita |
|---|---|---|
| CPU, memória e uptime | Observações do Linux convidado | Não |
| Discos, partições e sistema de arquivos | lsblk, montagens, uso e SMART quando acessível | Não |
| Array e pools | Seções de Main; nenhum array/pool real configurado | Não |
| Disco de boot | Detectado pelas montagens do sistema | Não |
| Dispositivos adicionais | Detecção, sem declarar automaticamente que estão livres | Não |
| Compartilhamentos SMB/NFS | Configurações lidas no sistema convidado | Não |
| Usuários | Contas locais sem expor credenciais | Não |
| Docker imagens, volumes, redes e containers | Consulta se o daemon autorizar | Não |
| Compose | Instalado, catálogo com preview; deploy por painel indisponível | Não |
| Loja de apps | Catálogo, busca Docker Hub e modelos Compose | Instalação em um clique pendente |
| Virtualização | Inventário libvirt quando disponível | Não |
| Rede | IP e interfaces reais do convidado | Não |
| Sistema/serviços | Kernel, distro e serviços existentes | Não |
| Monitoramento | Amostras enquanto a página está aberta | Não |
| Custos | Simulador, não cobrança real | Não |
| ISOs, modelos, logs, backup, tarefas, alertas, updates | Informam indisponibilidade, sem dados fictícios | Não |
| USB v0.4 UEFI | Boot testado anteriormente em QEMU | N/A |
| USB Legacy BIOS | Ainda não homologado no notebook antigo | N/A |

Prévia HTTPS: 192.168.30.10:18444. Estes módulos mais recentes ainda não fazem parte da imagem RAW USB v0.4 anterior.

Próximo marco técnico para ativar ações administrativas: identidade e RBAC nativos, daemon privilegiado com ações allowlist, persistência, confirmação segura e testes em discos virtuais descartáveis com recuperação de falhas.
