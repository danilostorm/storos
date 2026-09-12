# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-003A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002 está fechado remotamente.
- WEB-VM-001 está **fechado remotamente** no head funcional/documental `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`.
- VM-003A está em validação: observação somente leitura de firmware, discos e interfaces foi implementada, a suíte está verde e o smoke da imagem foi endurecido para exigir o novo hardware observado; gates finais desse head ainda precisam fechar.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## WEB-VM-001 — fechamento remoto

No head `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef` os quatro gates aplicáveis ficaram verdes:

- Project continuity `34712230631`: verde.
- Host agent `34712230846`: verde; suíte integral com **47/47 testes**.
- Development image `34712230629`: verde.
- Bootable media `34712230653`, job `103602983309`: verde.

O Bootable media construiu e inspecionou o mesmo QCOW2 e o inicializou duas vezes com QEMU 10.2.2 da própria imagem StorOS. O gate registrou:

- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`;
- `boot_count=1 → 2`;
- painel autenticado e agente prontos nos dois boots;
- `config_generation=1` e fingerprints persistentes de configuração/token;
- QCOW2 SHA-256 `a081b7480d19d85fd5a014e2ba8327d37c4fc8b11f2beac6cd8f6997aae333a8`;
- artefato `storos-boot-evidence` ID `10303234826`, digest do ZIP `sha256:2d84494a73c4f82a789b55410edf392cd8b0b1a48974953de7849eca194e2010`;
- artefato `storos-qcow2` ID `10303549406`, digest do ZIP `sha256:c8117f02ee200068e18bdd059ee3f8a61206e4d87f6a153d7b805258aa308198`.

Isso fecha a projeção read-only de intenções, planos e tarefas no painel. Nenhuma escrita em VM foi habilitada.

## VM-003A — observação de hardware virtual

### Objetivo

Antes de colocar firmware, discos ou rede na intenção/planner, observar esses recursos de forma tipada e conservadora no snapshot do agente.

### Implementação

`src/storos_agent.py` agora mantém a leitura básica por `dominfo` e acrescenta uma consulta somente leitura à definição persistente da VM. O campo aditivo `hardware` observa:

- firmware EFI/BIOS/desconhecido;
- Secure Boot quando explicitamente determinável;
- presença de NVRAM;
- discos: dispositivo/tipo, target/bus, origem, formato, somente leitura e ordem de boot;
- interfaces: tipo, MAC, origem, modelo, target e estado de link.

O snapshot continua `schema_version: 1`; consumidores atuais podem ignorar `hardware`.

A decisão arquitetural e os limites estão em [docs/VM_HARDWARE_OBSERVER.md](docs/VM_HARDWARE_OBSERVER.md). [docs/AGENT.md](docs/AGENT.md) foi atualizado para refletir o estado atual do componente.

### Fail-closed

- Se identidade básica falhar, a VM não é materializada naquele ciclo e o erro recebe `scope=identity`.
- Se identidade for válida mas a observação de hardware falhar, a VM continua visível com `hardware.status=unavailable`, erro `scope=hardware` e inventário geral `partial`.
- Hardware não observado não é tratado como ausente.
- O parser limita o documento, valida o UUID e rejeita construções XML fora do subconjunto seguro aceito.

### Evidência até agora

A primeira publicação do agente foi o commit `4257da8a989e837bb72fd0d5571c5ea8098f1f7a`. O Host agent correspondente, run `34713090955`, executou 47 testes: **45 passaram e 2 falharam**. As duas falhas eram mocks antigos que devolviam texto de `dominfo` para a nova consulta de XML; não houve falha do parser real nem do smoke da imagem. O Development image desse head ficou verde.

Os mocks foram corrigidos e a cobertura ampliada no commit `847520c1cbac7d56d56f121dd81e6f46964f5516`. O Host agent `34713412563` ficou verde com **50/50 testes**. A cobertura nova inclui firmware, Secure Boot/NVRAM, discos, interfaces, UUID divergente, declaração XML recusada e preservação da VM em estado parcial quando apenas hardware não pode ser observado.

No head documental `4e96badc0a055c6ec2ca3720b7fa120105f2bce9`, Project continuity `34713608860` ficou verde e Host agent `34713608846` repetiu **50/50 testes verdes**.

### Gate de imagem endurecido

O commit `02b4f085c0cbdf47fefd4e7796398ce58210adb9` endurece `image/check-image.sh`. O smoke `test:///default` agora só passa se:

- a descoberta simulada estiver `status=ok`;
- existir ao menos uma VM;
- cada VM possuir `hardware`;
- cada `hardware.status` for `ok`;
- `firmware` tiver a estrutura tipada esperada;
- `disks` e `interfaces` forem listas válidas.

Assim, o Development image passa a provar que o parser de hardware funciona com o libvirt instalado dentro da imagem, e não apenas que o módulo Python importa. Como essa mudança altera o head, Development image e Bootable media precisam ser confirmados novamente antes de fechar VM-003A.

## Segurança preservada

- Todas as consultas ao libvirt continuam usando o caminho somente leitura do agente.
- Nenhum endpoint web ganhou autoridade de escrita.
- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada.
- Planos continuam `mode=dry_run`, `can_apply=false`; ações/tarefas continuam `executable=false`.
- `features.vm_write_enabled=true` continua rejeitado pela configuração.
- O painel continua autenticado e somente leitura; listener padrão permanece no loopback.

## Limitações atuais

- Sem criação/start/stop real de VM pelo control plane StorOS.
- O contrato de intenção ainda cobre apenas UUID/nome/estado/vCPU/RAM fixa; firmware/discos/rede são somente observados no VM-003A.
- Sem política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark de desempenho.
- Nenhum teste físico de GPU compartilhada foi realizado.
- A observação básica de hardware virtual não comprova passthrough, SR-IOV, mediated devices ou vGPU.
- O QCOW2 continua sendo artefato de laboratório, não release para Danilo instalar.

## Próxima tarefa concreta

1. Fechar Project continuity, Host agent, Development image e Bootable media no head final que contém o smoke endurecido, sem relaxar critérios.
2. Confirmar no log da imagem que `test:///default` emite a mensagem de observação de hardware virtual aprovada.
3. Confirmar dois boots do mesmo QCOW2 e os marcadores de persistência já exigidos.
4. Registrar o fechamento VM-003A com os IDs/digests finais.
5. Iniciar VM-003B: ampliar o contrato de intenção e o planner para um subconjunto explicitamente validado de firmware/discos/rede, ainda apenas em `dry_run` e sem executor.
6. Manter QCOW2 como laboratório interno e preparar mídia física USB apenas quando a base virtual continuar estável.
7. STOR-009/010/011 e validação física de GPU permanecem pendentes.

## Continuidade

- O histórico anterior de `CHANGELOG.md` foi restaurado a partir do head validado `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`; as entradas novas do VM-003A/WEB-VM-001A permanecem apenas como acréscimos no topo. Essa correção é documental e não altera comportamento funcional.

Danilo autorizou continuar sem pular etapas e confirmou que o QCOW2 deve permanecer como laboratório interno até a base ficar sólida. O objetivo de entrega ao usuário continua sendo mídia física/pendrive em etapa posterior. Não pedir nova autorização para seguir este roadmap. Obedecer `AGENTS.md` em toda publicação. **Não mesclar o PR #2 sem instrução explícita.**
