# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-003B**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002 está fechado remotamente.
- WEB-VM-001 está fechado remotamente no head `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`.
- **VM-003A está fechado remotamente** no head `6108e0ec45f79e7a399f7f96733076effe3a2f47`.
- **VM-003B está publicado e em validação remota**; ainda não deve ser marcado como concluído.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## VM-003A — fechamento remoto preservado

No head `6108e0ec45f79e7a399f7f96733076effe3a2f47` os quatro gates aplicáveis ficaram verdes:

- Project continuity `34713932768`;
- Host agent `34713932769`, **50/50 testes**;
- Development image `34713932991`;
- Bootable media `34713932817`, job `103607586216`.

O smoke da imagem confirmou observação de hardware com libvirt 12.0.0/QEMU 10.2.2. O mesmo QCOW2 foi inicializado duas vezes e emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`, com `boot_count=1 → 2`, agente/painel autenticado nos dois boots e fingerprints persistentes.

Evidência: QCOW2 SHA-256 `d8075fbaa6693d7087db689922741a171b3e752cb1242072ec9f3b5b5ce1b091`; `storos-boot-evidence` ID `10304262931`, digest `sha256:5fc0a60aaff96e107512cbf1596d7589e085e5caf5801e8f539b81dc369e3100`; `storos-qcow2` ID `10304721991`, digest `sha256:a191ed814adc020ae79f097231df9c95cf25a7f9de28842d513aaf0343c0c4e4`.

## VM-003B — contrato hardware de intenção v2

### Compatibilidade

`storos_vm.py` agora aceita schema 1 e schema 2.

- Schema 1 continua com a forma histórica exata: UUID, nome, estado, vCPU e RAM fixa.
- A validação de um documento v1 **não adiciona `hardware`**. Isso preserva hashes, revisões e rollbacks existentes.
- Schema 2 acrescenta `hardware` para novas intenções.
- O schema do store permanece 1; uma linha de revisões pode conter intenções v1 e v2.
- Rollback para uma revisão v1 cria nova geração v1 e reutiliza o conteúdo/hash da intenção alvo.

Implementação principal publicada em `f55d190e4dcf9329a3417f4a23cc5722397dea63`.

### Subconjunto v2

O bloco `hardware` contém exatamente `firmware`, `disks` e `interfaces`.

Firmware:

- `firmware` pode ser `null` para não ser gerenciado;
- quando gerenciado, aceita somente `mode=bios|efi`;
- nenhum caminho OVMF/loader/NVRAM do host entra na intenção;
- Secure Boot/enrolled keys/NVRAM continuam fora do contrato VM-003B.

Discos:

- no máximo 64 itens;
- identidade pelo `target`;
- buses suportados: `virtio`, `sata`, `scsi`;
- fontes locais `file` ou `block`, com caminho absoluto;
- formatos `raw` ou `qcow2`;
- `readonly` booleano e `boot_order` opcional;
- target duplicado é rejeitado;
- lista é normalizada por target para hash determinístico.

Interfaces:

- no máximo 64 itens;
- identidade pelo MAC, normalizado para minúsculas;
- `type=network` exige `source.network`;
- `type=bridge` exige `source.bridge`;
- modelo é explícito;
- MAC duplicado é rejeitado;
- lista é normalizada por MAC.

As listas são **subconjuntos gerenciados**. Discos/interfaces observados que não aparecem na intenção não geram remoção automática.

### Planner v2

Para VM existente, o planner só compara firmware/discos/interfaces se `hardware.status=ok`.

Novas descrições dry-run:

- `set_firmware_mode`;
- `attach_disk`;
- `reconfigure_disk`;
- `attach_interface`;
- `reconfigure_interface`;
- bloqueios `inspect_hardware`, `inspect_firmware`, `inspect_disk`, `inspect_interface`.

Hardware indisponível gera `inspect_hardware` e nenhuma mudança de hardware é inferida. Firmware `unknown`, identidade ambígua ou dados observados incompletos também bloqueiam a parte correspondente.

Todas as ações continuam `executable=false`; plano continua `mode=dry_run` e `can_apply=false`.

### Correção semântica de Secure Boot

Durante a revisão do VM-003B, a documentação oficial do libvirt confirmou que `loader secure='yes'` informa **capacidade** de Secure Boot do firmware e não habilita/desabilita a feature. Como o planner v2 não gerencia Secure Boot, o observador foi endurecido antes de qualquer uso futuro desse campo:

- `409f77c5fdcf7a5d0e531c7586d25cf3554b68c5`: `storos_agent.py` deixa de inferir `secure_boot` a partir de `loader@secure`; somente `firmware/feature name='secure-boot' enabled='yes|no'` define `true|false`; caso contrário permanece `null`.
- `84927ecd77ba7d1fde98363381a009cacb253f1c`: teste dedicado prova que `loader secure=yes` sem feature explícita resulta em `secure_boot=None`.
- `7ca50e9a7e3e3aadb15440c5e51160027b5f4f6a`: `docs/AGENT.md` registra essa semântica.

### Cobertura publicada

- `802399c3eb7a1925ceb9ed6acc3b1257316be2d2`: testes do planner/validador v2, incluindo compatibilidade v1, normalização, duplicatas, convergência, diferenças determinísticas, attach sem detach, hardware extra ignorado e fail-closed.
- `43daed4f5dd0ad60d0dbc30b9846d44e3f439154`: store v1/v2, incluindo round-trip v2 e prova v1 → v2 → rollback-v1 com preservação do hash da intenção v1.
- `780173c0817b6e26cd0ab4279ae51d387e16cc09`: smoke da imagem mantém o fluxo schema 1 e acrescenta intenção schema 2 construída a partir da VM do `test:///default`; o plano v2 deve convergir sem qualquer ação executável.
- `79f5bb09d20fcad94ae497cf3b49b9722c30688a`: contrato atualizado em `docs/VM_PLANNER.md`.
- `4febbc02b9439b0054bc670e1a32c0b81444bdf5`: arquitetura atualizada com as fronteiras VM-003A/VM-003B.

Os resultados remotos do **novo head final após a correção Secure Boot** ainda precisam ser confirmados. Nenhum check anterior deve ser usado como fechamento do VM-003B.

## Segurança preservada

- Agente/libvirt continuam somente leitura.
- Nenhum endpoint web ganhou autoridade de escrita.
- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada.
- `features.vm_write_enabled=true` continua rejeitado.
- Planos continuam `dry_run`/`can_apply=false`; tarefas e ações continuam `executable=false`.
- Não há detach automático de hardware não gerenciado.
- Secure Boot, NVRAM, hotplug, passthrough, SR-IOV, mediated devices e GPU não foram promovidos para intenção v2.

## Limitações atuais

- Sem criação/start/stop real de VM pelo control plane StorOS.
- VM-003B ainda precisa passar Host agent, Project continuity, Development image e Bootable media no head final.
- Sem política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark.
- Nenhum teste físico de GPU compartilhada foi realizado.
- O QCOW2 continua artefato de laboratório, não release de instalação.

## Próxima tarefa concreta

1. Fechar `CHANGELOG.md` no mesmo lote lógico da correção Secure Boot.
2. Executar/confirmar a suíte integral do head final e corrigir qualquer regressão do schema v2.
3. Confirmar o smoke da imagem para **schema 1 e schema 2**.
4. Confirmar o mesmo QCOW2 em dois boots sem regressão de persistência.
5. Registrar IDs/digests finais e só então marcar VM-003B como concluído.
6. Não iniciar executor real, GPU ou mídia física antes desse fechamento.

## Continuidade

- O histórico de `CHANGELOG.md` deve permanecer somente aditivo; não reescrever entradas antigas.
- QCOW2 continua laboratório interno. A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- Danilo autorizou continuar sem pular etapas. Não pedir nova autorização para seguir o roadmap.
- Obedecer `AGENTS.md` em toda publicação.
- **Não mesclar o PR #2 sem instrução explícita.**
