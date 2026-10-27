# Arquitetura e roadmap do StorOS

## Princípios
- Universal Blue uCore baseado em Fedora CoreOS, com base imutável, boot via USB e serviços isolados.
- Dados têm prioridade absoluta: funções destrutivas desligadas por padrão e confirmação dupla no futuro.
- Observabilidade primeiro, gestão autenticada depois, automação apenas após testes.
- Código próprio e tecnologias abertas; não reaproveitar código fechado do Unraid.

## Módulos
1. **storos-ui:** dashboard de saúde, capacidade, VMs, apps, backups e alertas.
2. **storos-api:** configuração declarativa versionada, RBAC, auditoria, OpenAPI, controle de tarefas.
3. **storos-agent:** execução de tarefas privilegiadas via allowlist/polkit e validação de discos por WWN/UUID.
4. **storos-storage:** Btrfs, XFS, pools ZFS opcionais, snapshots, scrubs, SMART; mergerfs/SnapRAID opcional e identificado como paridade não em tempo real.
5. **storos-compute:** libvirt/KVM, bridge de rede, GPU passthrough somente com validação.
6. **storos-apps:** Podman, Compose via ferramenta compatível, catálogo auditado e backups consistentes.
7. **storos-installer:** imagem RAW inicializável via bootc/osbuild após protótipo de VM; rollback e partição do sistema separada.

## Roadmap
- **0.1 – Feito inicialmente:** projeto independente, APIs locais somente de leitura, interface.
- **0.2 – Próximo:** empacotamento na VM Fedora Server, autenticação, leitura de discos via udev/SMART, eventos e logs.
- **0.3:** pools criados apenas em arquivos de loop/disk images de laboratório; testes de falhas.
- **0.4:** gestão de containers e VMs dentro da VM, permissões e auditoria.
- **0.5:** instalador de teste, atualizações transacionais/rollback, backups e benchmarks.
- **1.0:** somente após testes de restauração, quedas de energia, SMART e migração com consentimento.

## Comparação honesta
Unraid tem paridade em tempo real em array de discos independentes; SnapRAID não é equivalente. ZFS/Btrfs RAID também usam outro modelo de proteção/capacidade. O diferencial do StorOS deverá ser UX, automação segura, API documentada, telemetria e integração. O desempenho e robustez terão de ser medidos, não pressupostos.

## Segurança do desenvolvimento
Servidor AEROCOOL está em produção, com VMs e containers ativos.
Não alterar array, syslinux, boot USB, /etc, libvirt das VMs, nem Docker em execução.
Executar ferramentas de análise em VM dedicada com diretório compartilhado somente de leitura.
Criar testes com discos virtuais, sem acesso a block devices reais.
