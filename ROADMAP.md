# Roadmap StorOS — proposta 1

Data: **11/09/2026**. Responsável pela aprovação: **Danilo**. Estado de todas as fases: **propostas, não iniciadas**.

## 1. Objetivo e recorte

Criar uma distribuição para servidor doméstico e pequenas equipes que una arquivos, aplicativos, VMs e postos de trabalho. A experiência deve permitir começar sem terminal, com opções avançadas disponíveis quando necessárias.

Recomendação: derivar componentes auditados do MOS, manter inicialmente sua base Devuan e criar uma camada StorOS de interface, configuração, tarefas e políticas. Confirmar a viabilidade de reconstrução da distribuição na Fase 0; o repositório `mos-releases` sozinho não contém todo o sistema. [Base e fontes](docs/REFERENCIAS.md).

Primeiro produto estável: **um servidor x86-64 com NAS, VMs, apps, Guardian e backup/restore**. Múltiplos postos de trabalho terão protótipo próprio; cluster e HA ficam após essa base. ARM64, Kubernetes, nuvem pública e GPU compartilhada entre várias VMs não entram no compromisso da primeira versão.

## 2. Diferenciais que serão verificáveis

- Criar VM escolhendo quantidade de vCPUs e faixa de RAM, sem exigir seleção de núcleos físicos.
- Painel distingue configuração pendente, gravada, aplicada e aplicação com erro. Reabrir a tela não perde valores.
- Descoberta de VMs independente de ativar o gerenciamento; diagnóstico explícito de falha ou incompatibilidade.
- Reserva do host considerada antes de iniciar VMs, além de ajustes enquanto elas estão ligadas.
- Armazenamento escolhido por uso: mídia pouco alterada, arquivos importantes ou discos de VMs. Mostrar proteção e limitações de cada opção.
- Backup e restauração fazem parte da entrega, incluindo recuperação em outro disco de sistema.
- Toda ação automática tem motivo, limite, registro e caminho de recuperação.
- Interface em português e inglês, responsiva, com modo simples e avançado; funcionamento local sem conta em nuvem obrigatória.

## 3. Sequência de entregas

As versões abaixo identificam marcos propostos, não releases disponíveis. P0 significa indispensável para a primeira versão; P1, expansão importante; P2, pesquisa ou etapa posterior.

| Fase / marco | Prioridade | Entrega | Dependências | Esforço indicativo |
| --- | --- | --- | --- | --- |
| 0 — Fundação | P0 | Auditoria MOS, matriz de licenças, build de referência, desenho de UX e testes de viabilidade | Aprovação do plano | 2–3 semanas |
| 1 — v0.1 | P0 | Imagem de laboratório StorOS, instalação e painel básico | 0 aprovada | 3–5 semanas |
| 2 — v0.2 | P0 | NAS, discos, compartilhamentos e proteção | 1 | 4–6 semanas |
| 3 — v0.3 | P0 | VMs, LXC e Guardian integrado | 1; armazenamento de VM validado na 2 | 4–6 semanas |
| 4 — v0.4 | P0 | Apps, Compose e contrato de plugins | 2 e 3 | 3–5 semanas |
| 5 — v0.5 | P0 | Backup, restauração e migração assistida | 2–4 | 3–5 semanas |
| 6 — v0.6 experimental | P1 | Dois postos de trabalho e perfis para jogos/criação | 3 e 5; hardware validado | 4–6 semanas |
| 7 — v1.0 | P0 | Estabilização, atualização/recuperação e suporte documentado | 1–5; retirar funções experimentais que não passarem nos testes | 4–6 semanas |
| 8 — v1.x | P1 | ZFS avançado, gestão multisservidor e expansão de Workspaces | 1.0 | Reestimar após 1.0 |
| 9 — v2.x | P2 | Cluster/HA, migração e armazenamento distribuído opcional | 8 e laboratório de cluster | Reestimar após prova de conceito |

Estimativa de planejamento, não prazo contratado: fases 0–7 somam **27–42 semanas**, antes de contingência. Pressupõe dois desenvolvedores dedicados, apoio recorrente de QA/infraestrutura e hardware disponível. Reservar aproximadamente 30% para integração e incompatibilidades: **35–55 semanas**. Com uma pessoa ou trabalho parcial, revisar o cronograma. A Fase 6 pode seguir trilha separada para não atrasar NAS/virtualização. Ao fim da Fase 0, entregar estimativas revisadas por componente; assistência de IA não substitui testes físicos, revisão e manutenção.

## 4. Escopo e aceite por fase

### Fase 0 — Tornar o projeto construível

Entregas:

- Inventário MOS: API, frontend, rootfs, kernel, bootloader, pacotes, drivers, Hub e ferramentas de build. Fixar versões/commits e registrar procedência.
- Preservar licenças e créditos; definir licença do código novo e política de contribuição. Não presumir uma licença única para toda a imagem.
- Construir um artefato de referência em ambiente limpo; mapear dependências externas, runners, downloads e chaves de assinatura próprios.
- Comparar custo de manter Devuan com migrar a base; recomendação inicial é Devuan. Mudança de base exige nova decisão registrada.
- Prototipar fluxo de instalação, criação de VM e recuperação. Fazer teste exploratório de GPU/IOMMU/NUMA e dois postos para reduzir risco cedo.
- Definir equipamentos de laboratório, backlog, estratégia de branches e acompanhamento de segurança upstream.

Aceite: documentação suficiente para reconstruir a referência; lista de componentes com origem/licença; nenhuma dependência secreta do upstream sem substituição planejada; três fluxos revisáveis por Danilo. Se não houver build reproduzível operacionalmente, apresentar bloqueio e alternativa antes de avançar. Reprodutibilidade bit a bit é meta posterior, não presumida.

### Fase 1 — Sistema base e painel

Entregas: identidade StorOS; imagem x86-64 UEFI para laboratório; instalação em SSD/NVMe com identificação do disco; rede, usuários, horário, armazenamento persistente de configuração; painel de saúde; fila de tarefas; logs; HTTPS e autenticação; papéis administrador/operador/leitor e trilha de auditoria.

Atualizações terão canais laboratório/beta/estável, assinatura, origem identificada e versão anterior recuperável. A recuperação deve considerar migração de configuração; voltar o sistema não deve tentar reverter arquivos dos usuários.

Aceite: instalar sem selecionar discos de dados automaticamente; reiniciar 10 vezes preservando configuração; restaurar configuração em instalação limpa; rejeitar ação sem permissão; recuperar acesso após configuração de rede inválida. Não disponibilizar shell genérico na API administrativa.

### Fase 2 — NAS e armazenamento

Entregas: inventário com serial/UUID, SMART, temperatura e alertas; SMB/NFS; usuários/grupos/ACL; quotas; tarefas de scrub/sync; diagnóstico de espaço, disco ausente e pool degradado.

Dois perfis separados:

| Perfil | Tecnologia proposta | Uso e restrição |
| --- | --- | --- |
| Mídia flexível | mergerfs + SnapRAID, reaproveitando a base MOS | Discos de tamanhos variados e arquivos pouco alterados; paridade por sincronização, não proteção contínua de gravações |
| Dados e VMs | ZFS, começando por disco único para laboratório e espelhos para redundância | Datasets, snapshots e integridade; capacidade e redundância mostradas antes da criação; versão do módulo validada com kernel |

Não oferecer migração/conversão automática entre esses perfis sem copiar e verificar dados. Não usar SnapRAID como destino principal de discos de VMs ou bancos ativos. Snapshot/paridade não substituem backup independente. RAIDZ, expansão avançada e replicação ZFS completa podem ser ampliados na Fase 8; não habilitar silenciosamente recursos que impeçam importar o pool em uma versão anterior.

Aceite: teste de permissões por dois usuários; indisponibilidade de disco sem recriar/formatações automáticas; recuperação de um conjunto de arquivos com hashes; reconstrução em espelho testada; sync/scrub interrompidos com diagnóstico e recuperação documentada.

### Fase 3 — Compute e Guardian nativos

Entregas: criar/importar/iniciar/parar/clonar VMs KVM; consoles; templates e cloud-init quando suportado; LXC; bridge/VLAN; GPU/USB passthrough assistido; descoberta contínua por UUID. Arquivos XML avançados terão campos preservados ou conflitos explícitos ao editar.

Na criação da VM:

- **vCPUs:** quantidade visível ao guest, por exemplo 16.
- **CPU automática:** escalonamento sem pinning obrigatório; modo avançado permite pinning e preferência NUMA.
- **RAM:** mínimo, inicial e máximo; por exemplo 4/8/16 GiB, sujeito à necessidade do guest e à capacidade do host.
- **Prioridade:** baixa/normal/alta; mostrar impacto e reserva disponível antes de iniciar.

Guardian: reserva CPU/RAM do host; admissão de novas VMs; controle de quota; memória com balloon e estatísticas recentes; histerese, intervalos mínimos, prioridades, pausa e restauração. Se balloon não funcionar, indicar RAM fixa e não reduzi-la automaticamente. Hotplug de vCPU é um modo distinto e opcional: alterar quota não altera a contagem visível de vCPUs. Planejar RAM de ZFS/serviços junto com as VMs. Nunca prometer memória física adicional por overcommit.

O plugin Resource Guardian existente é um protótipo reutilizável após revisão, não prova de prontidão de produção. Seus incidentes de configuração, descoberta e afinidade viram testes de regressão do StorOS.

Aceite: salvar/reabrir/reiniciar preservando políticas; listar VM sem habilitar ajustes; recusar início quando não houver reserva; testar disputa de recursos entre duas VMs e serviço NAS; guest sem balloon não sofre redução; ações recuperáveis após reiniciar daemon; afinidade externa não sobrescrita; guest Windows e Linux validados. Reservar via quota não significa reservar núcleos físicos exclusivos.

### Fase 4 — Apps e plugins

Entregas: catálogo com busca/categorias; instalação Compose/OCI; volumes persistentes; portas, credenciais e permissões visíveis antes da instalação; backup de configuração; logs/saúde; atualização com checagem de compatibilidade. Templates iniciais candidatos: Jellyfin, Plex, Home Assistant e ferramentas de backup, cada um conforme seus termos.

Plugins terão manifesto versionado, API tipada, escopos de acesso e canal de distribuição assinado. Aplicativos comuns rodam em containers; plugins com acesso ao host exigem permissão explícita. Não prometer compatibilidade automática com todos os plugins MOS, Unraid ou OMV; criar adaptadores apenas para contratos documentados.

Aceite: instalar, atualizar e remover dois apps sem apagar volumes por padrão; falha de download não deixa instalação marcada como concluída; rejeitar pacote adulterado e permissão indevida; documentação de como publicar um plugin.

### Fase 5 — Backup e migração

Entregas: políticas de configuração, arquivos, volumes e VMs; agendamento, retenção, criptografia e testes de recuperação; backup local e remoto via motores existentes a selecionar na Fase 0 (ex.: restic/Borg); replicação ZFS quando habilitada. Definir consistência de aplicação e uso de guest agent; distinguir backup consistente de aplicação de cópia consistente apenas após crash.

Migração inicial: inventário/exportação MOS; importação de discos QCOW2/raw e definição de VM com revisão; cópia de dados de Unraid/OMV/TrueNAS por SMB/NFS/rsync; importação de Compose com validação. Migração in-place de MOS, conversão de pools e importação de todas as configurações de concorrentes ficam fora da promessa inicial.

Aceite: restaurar VM que inicializa, app com seus dados e arquivos com hashes; recuperar em novo disco do sistema; testar perda do catálogo e recuperação de chaves; documentar RPO/RTO medidos para conjunto de teste. Meta inicial de laboratório: RPO de 24 h com backup diário e RTO de 60 min para VM de 20 GiB em LAN/SSD, sem declarar SLA geral.

### Fase 6 — Workspaces experimental

Objetivo inspirado no ASTER: duas pessoas usarem o mesmo servidor ao mesmo tempo, com telas, entrada e áudio independentes.

Caminho inicial recomendado: **uma VM por pessoa**, com atribuição explícita de GPU/USB/áudio ou acesso remoto de cliente leve. Testar primeiro dois postos Linux; adicionar Windows com licenciamento e drivers apropriados. A ideia de multiseat Linux compartilhando o mesmo host gráfico é uma trilha de pesquisa separada, considerando a base Devuan e o gerenciador de sessões disponível.

Não presumir que uma GPU de consumo possa ser dividida entre VMs, que várias saídas de uma placa sejam dispositivos independentes, nem que todos os jogos/anti-cheats funcionem em VM. Não incorporar ASTER como código aberto por ser gratuito em alguma edição. Validar reset da GPU, grupos IOMMU, isolamento USB, áudio e recuperação do console do host.

Aceite: dois usuários simultâneos por 8 h, teclado/mouse/áudio sem cruzamento, reconexão de periféricos e reinício de um posto sem derrubar o outro; relatório de latência/desempenho no hardware usado. Publicar lista de GPUs e limitações, incluindo testes na RTX 3080 Ti/RX 550 somente se esses dispositivos estiverem disponíveis no laboratório.

### Fase 7 — v1.0 estável

Entregas: auditoria de permissões, atualização assinada, recuperação de falhas, documentação PT-BR/EN, acessibilidade por teclado, matriz de hardware, pacotes de diagnóstico sem segredos e canal de reporte de vulnerabilidades. Workspaces só entra estável para combinações aprovadas; demais permanecem experimentais fora do compromisso v1.0.

Aceite: 30 dias de teste contínuo em pelo menos duas máquinas físicas diferentes; nenhum bloqueador conhecido de perda de dados no escopo suportado; restauração completa ensaiada; queda de energia simulada em laboratório; três ciclos de atualização e recuperação; teste E2E do fluxo principal sem terminal. Meta do painel: leitura de estado p95 abaixo de 500 ms em LAN, excluindo tarefas longas, que retornam ID/progresso. Medir custo de CPU/RAM ocioso e publicar metodologia antes de anunciar mínimos oficiais.

### Fases 8 e 9 — expansão

Fase 8: administrar vários nós, inventário agregado, backup remoto, alertas, perfis por hardware, ZFS avançado e Workspaces ampliado. Gestão multisservidor não equivale a HA.

Fase 9: prova de conceito com quorum, fencing, rede dedicada e armazenamento compatível; comparar Corosync/Pacemaker e soluções existentes antes de criar coordenação própria. Ceph é opcional, não requisito para um NAS doméstico. Migração ao vivo depende de CPU, storage e dispositivos; passthrough não tem promessa geral de migração transparente.

Aceite HA: laboratório com pelo menos três nós votantes (ou desenho de quorum formalmente validado), falha de nó e partição de rede sem iniciar dois escritores no mesmo disco; tempos de recuperação medidos. Não lançar HA apenas porque é possível mandar iniciar uma VM em outro host.

## 5. Ordem do backlog inicial

| ID | Trabalho | Resultado esperado | Responsável proposto |
| --- | --- | --- | --- |
| STOR-001 | Inventário e licenças upstream | Matriz por componente e commit | Engenharia de plataforma |
| STOR-002 | Build MOS de referência | Artefato e instrução reproduzível | Plataforma |
| STOR-003 | UX de instalação e VM | Protótipo revisado por Danilo | Interface/produto |
| STOR-004 | Contrato de configuração e tarefas | API, estado persistente e testes | Backend |
| STOR-005 | Laboratório e recuperação | Inventário de discos/VMs descartáveis | QA/infraestrutura |
| STOR-006 | Guardian: contrato e falhas conhecidas | Regressões de salvar, descobrir, aplicar e restaurar | Backend/QA |
| STOR-007 | Viabilidade GPU/Workspaces | Relatório sem promessa de compatibilidade universal | Plataforma/QA |
| STOR-008 | Revisão de escopo e esforço | Go/no-go para Fase 1 | Danilo |

Os responsáveis são funções necessárias, não pessoas já contratadas. Os IDs são backlog documental; ainda não foram abertas issues de implementação.

## 6. Aprovação

Revisar [as decisões propostas](docs/APROVACAO.md). Aprovar este roadmap autoriza iniciar a Fase 0; não aprova migração do servidor de uso diário, formatação de discos, publicação de ISO estável ou promessa de compatibilidade. Mudanças de prioridade e resultados dos testes serão registrados em novas revisões.
