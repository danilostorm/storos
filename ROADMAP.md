# Roadmap StorOS — revisão 2

**11/09/2026.** Responsável pelo produto: Danilo. Estado: revisão 2 aprovada; pesquisa da Fase 0 em andamento. Substitui a revisão 1 centrada em NAS/MOS, preservada no histórico Git.

## Direção confirmada

Foco principal: **VMs compartilhando CPU, RAM e GPU**, sem obrigar o uso exclusivo do dispositivo por uma VM. A base operacional pode mudar. Docker, NAS e apps deixam de conduzir as primeiras entregas.

Compartilhar RAM significa redistribuir memória física disponível entre guests isolados, não dar acesso livre à memória de outra VM. GPU compartilhada significa duas ou mais VMs usando a mesma placa simultaneamente para a carga pretendida. Alternar passthrough entre VMs ou oferecer desktop remoto não satisfaz isso por si só.

## GPU antes da escolha do sistema

A Fase 0 verifica combinações de GPU, driver, hipervisor e guest. Fedora/uCore HCI é a base de desenvolvimento autorizada; não há promessa de suporte à RTX 3080 Ti/RX 550. Veja [decisão](docs/BASE_FEDORA.md).

Candidatos a comparar: MOS/Devuan, Debian/Linux com KVM/libvirt, Proxmox e alternativa Windows/Hyper-V para estudo de viabilidade. Essa lista não afirma suporte ao hardware do usuário. Uma alternativa proprietária não será apresentada como distribuição totalmente aberta nem adotada sem decisão explícita.

Investigar virtualização de GPU suportada pelo fabricante, SR-IOV, dispositivos mediados e particionamento onde documentados. Não presumir disponibilidade; não contornar licenças ou desbloquear recursos por patch não autorizado. Trocar o sistema não cria suporte ausente no hardware.

Se as placas atuais não atenderem, apresentar hardware compatível, outra plataforma documentada ou revisão do requisito. Não substituir silenciosamente compartilhamento por GPU exclusiva.

## Matriz obrigatória de viabilidade

| Item | Evidência exigida por combinação |
| --- | --- |
| Plataforma | Sistema, kernel/hipervisor, versões e manutenção |
| Hardware | Modelo, ID PCI, firmware, motherboard e IOMMU |
| Drivers/licença | Versões host/guest, suporte oficial, termos e custos |
| Guests | Linux e/ou Windows efetivamente testados |
| GPU | VMs simultâneas; 3D, computação e encode/decode avaliados separadamente |
| Recursos | VRAM, limites, isolamento, escalonamento e métricas disponíveis |
| Experiência | Latência, FPS/throughput e estabilidade no workload-alvo |
| Recuperação | Reinício de uma VM e falha de driver: impacto nas demais e no host |
| Restrições | Aplicativos, anti-cheat, displays locais, acesso remoto e migração |
| Resultado | Comprovado em teste, apenas documentado, não suportado ou não verificado |

Streaming ou computação não comprovam, isoladamente, adequação a dois desktops 3D. Comparar o mesmo workload e registrar resolução, qualidade, duração e configuração.

## Fases propostas

A composição da imagem de desenvolvimento foi iniciada na Fase 0; as entregas funcionais seguintes continuam pendentes. As estimativas da revisão 1 foram retiradas: a GPU pode mudar arquitetura, equipe e esforço.

| Fase | Prioridade | Entrega | Dependência / saída |
| --- | --- | --- | --- |
| 0 — Viabilidade | P0 | GPU simultânea, laboratório CPU/RAM, comparação de bases/licenças | Pesquisa autorizada e iniciada; laboratório e decisão de plataforma pendentes |
| 1 — Compute mínimo | P0 | VMs, estado persistente, tarefas, autenticação e painel | Base escolhida e reconstruível |
| 2 — CPU/RAM automáticas | P0 | Mínimos/máximos, prioridades, admissão e reserva do host | Fase 1; métricas confiáveis |
| 3 — GPU compartilhada | P0 | Integrar a combinação validada para várias VMs | Prova física na 0; gestão nas 1–2 |
| 4 — Experiência e usuários | P1 | Assistente, perfis, dispositivos, consoles e dois postos | Fases 1–3 |
| 5 — Beta recuperável | P0 | Backup, restore, atualizações, isolamento e teste contínuo | Fluxo de virtualização completo |
| 6 — v1.0 | P0 | Virtualização estável no hardware homologado | Beta aprovada e GPU simultânea comprovada no escopo anunciado |
| 7 — Complementos | P2 | NAS, Docker, apps e integrações | Base de VMs estabilizada |
| 8 — Multisservidor | P2 | Gestão de nós; cluster/HA como projeto posterior | Backup e coordenação maduros |

Pesquisa CPU/RAM pode acompanhar a investigação GPU. Isso não autoriza desenvolver uma distribuição extensa antes de decidir a base.

### Fase 0 — Viabilidade e escolha

Progresso: [triagem documental](docs/FASE0_GPU.md) iniciada e [protocolo de laboratório](docs/FASE0_LAB.md) preparado. Sem testes físicos; fase ainda aberta.

- Inventariar equipamento disponível e montar guests/discos descartáveis.
- Investigar primeiro as placas do Danilo; suporte a outro modelo não comprova suporte à placa dele.
- Levantar documentação oficial e testar combinações acessíveis. Ausência de equipamento não é resultado negativo.
- Demonstrar duas VMs usando a mesma GPU física simultaneamente, registrando uso em ambas e workload relevante.
- Testar redistribuição CPU/RAM entre duas VMs, sem acesso cruzado à memória e preservando o host.
- Comparar base, build, drivers, licenças, custos e limitações. Se GPU não for viável, registrar bloqueio e alternativas.
- Revisar estimativas após o resultado. Funções necessárias: plataforma/virtualização, interface/backend e QA com hardware; equipe ainda não definida.

Aceite: matriz com evidências, instruções reproduzíveis, decisão arquitetural e go/no-go de Danilo. MOS é candidato, não requisito.

### Fase 1 — Compute mínimo

Entregar criar/iniciar/parar/importar VMs, descoberta por UUID, API tipada, workers sem shell arbitrário, configuração transacional, tarefas com progresso, autenticação/permissões e auditoria. Preparar backup de configuração desde o início.

Aceite: duas VMs funcionais; configurações sobrevivem a 10 reinícios; salvar/reler confirma valores; falha de aplicação não aparece como sucesso; descoberta não depende de ativar automação; ação sem permissão é rejeitada.

### Fase 2 — CPU e RAM

Na criação: quantidade de vCPUs, RAM mínima/inicial/máxima, prioridade e perfil automático/manual. CPU automática não exige escolher núcleos físicos. Afinidade e NUMA ficam avançadas. Quota, contagem visível e hotplug são controles distintos.

RAM dinâmica exige mecanismo suportado e métricas atuais, piso seguro e histerese. Sem suporte comprovado, indicar limitação e manter RAM fixa. Validar o orçamento antes de iniciar uma VM; não contar memória potencialmente recuperável como livre antes de confirmar a recuperação.

Aceite: duas VMs disputam recursos com serviço do host; prioridades e reserva funcionam; métricas ausentes suspendem reduções; início sem capacidade é recusado/aguarda; diário de ações e restauração sobrevivem ao reinício; alterações externas não são sobrescritas. Medir latência e pressão de memória.

O Resource Guardian existente é protótipo e fonte de regressões, não componente automaticamente homologado para outra base.

### Fase 3 — GPU simultânea

Integrar a solução validada: descoberta de capacidade, atribuição das unidades virtuais suportadas, gestão de driver e limites reais de GPU/VRAM. Não exibir quotas ou telemetria fictícias quando o mecanismo não as oferecer.

Aceite: duas VMs usam a mesma placa no workload-alvo por 8 h; registrar desempenho isolado/concorrente, VRAM, interferência e falhas; reiniciar uma VM e avaliar impacto na outra; testar isolamento e impedir atribuição incompatível. Publicar matriz por modelos e versões.

GPU exclusiva permanece opção manual, mas não conclui esta fase. Não prometer migração ao vivo com GPU sem teste específico.

### Fase 4 — Interface e postos

Fluxo: sistema guest → disco → CPU → RAM → GPU → dispositivos/acesso → revisão → criar. Mostrar configurado, aplicado e observado lado a lado, com motivo de espera/recusa.

Perfis equilibrado, interativo/jogos e processamento são propostas a calibrar. Dois postos podem usar monitor/USB/áudio locais ou clientes remotos, conforme hardware. VMs por pessoa são o caminho inicial; sessões no mesmo host não substituem isolamento entre guests.

Aceite: criar/configurar duas VMs sem XML/terminal; dois usuários simultâneos sem cruzamento de entrada/áudio; operação por teclado e acessibilidade básica; configuração persiste após reabrir. Jogos/anti-cheat só têm compatibilidade declarada mediante teste.

### Fases 5 e 6 — Recuperação e estabilidade

Beta: backup consistente de VMs/configuração, chaves protegidas, restore em host limpo, diagnóstico sem segredos, atualização assinada e recuperação compatível com o esquema. Voltar a versão do sistema não reverte os arquivos dos usuários.

Aceite beta: restaurar VM inicializável e arquivos com hashes; testar falta de espaço, falha de rede e atualização interrompida; publicar RPO/RTO medidos no conjunto de teste, sem SLA universal.

Aceite v1.0: 30 dias de teste contínuo, pelo menos duas máquinas físicas no escopo declarado, três ciclos de atualização/recuperação, nenhum bloqueador conhecido de perda de dados e GPU simultânea comprovada na combinação anunciada. Se só um conjunto for homologado, limitar formalmente o lançamento após revisão de Danilo.

### Fases 7 e 8 — Complementos

Reaproveitar componentes maduros para NAS/Docker/apps. Separar mídia com paridade por sincronização de discos de VMs ativos. Gestão multisservidor precede HA; quorum, fencing, storage e migração terão critérios próprios. Essas áreas não devem atrasar o foco principal.

## Backlog imediato

| ID | Entrega |
| --- | --- |
| STOR-009 | Matriz GPU/driver/guest/licença |
| STOR-010 | Comparação de bases e decisão com trade-offs |
| STOR-011 | Laboratório descartável e protocolo de duas VMs |
| STOR-012 | Relatório de viabilidade e alternativas |
| STOR-013 | Contrato CPU/RAM/GPU e desenho do assistente |
| STOR-014 | Estimativas revistas após go/no-go |

STOR-001–008 permanecem no histórico da revisão 1 e precisam ser reclassificados se virarem issues; não foram executados. Os IDs novos também são backlog documental.

## Continuidade e aprovação

Toda atualização publicada mantém [CHANGELOG.md](CHANGELOG.md) e [PROJECT_STATE.md](PROJECT_STATE.md), conforme [AGENTS.md](AGENTS.md). Registrar fatos, testes, falhas, bloqueios e próxima tarefa. Pesquisa não equivale a implementação.

Danilo aprovou esta revisão e o início da Fase 0 com “Ta aprovado.” em 11/09/2026. Escopo e limites de execução seguem [APROVACAO.md](docs/APROVACAO.md).
