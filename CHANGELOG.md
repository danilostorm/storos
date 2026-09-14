# Changelog

Histórico de atualizações do projeto. Documentação tem identificadores próprios; não representa versões funcionais do sistema.

## 2026-09-13 — VM-004D

- **Mudou:** adicionada a nova camada local de decisão do VM-004D, com testes e documentação correspondentes.
- **Verificação local:** **13/13** testes específicos e **102/102** testes integrais passaram.
- **Limites:** esta etapa não realiza mudanças reais em VMs.
- **Validação:** fechamento depende dos quatro gates remotos no head publicado.
- **Referência:** PR #2, base `ca168a5c63a2be9925b7468a18599167ecb7c508`.

## 2026-09-12 — VM-004C — Admission simulada deny-only

- **Base fechada:** VM-004B foi validado remotamente no head `27d233d1f6f115928219e5974cbfe0ac898ea13a`: Project continuity `34730616504`, Host agent `34730616508` (**81/81 testes**), Development image `34730616538` e Bootable media `34730616503` ficaram verdes.
- **Evidência VM-004B:** `image-evidence` ID `10308434031`, digest `sha256:f0714c001145d3c44034da0d9596f365a12b37fd7d6f9d8ae316781372656952`; QCOW2 SHA-256 `d834399388ec5da20d67150efe64832db1e992a85c3868edefb72cf6f1e50372`; `storos-boot-evidence` ID `10308459678`, digest `sha256:5e4ca31e806c350a1e7fc857bc80a393fb68dac12f632c147c802781483eb377`; `storos-qcow2` ID `10309940637`, digest `sha256:6555a48c2cb2fe5fa3d2e6bffd3e53c2c58088c27a4ca24c4f4be1a303b7697e`.
- **Motivo:** conectar preflight + contrato tipado + identidade declarada + capacidades de backend em uma fronteira auditável sem antecipar executor, autorização real ou mutação libvirt.
- **Admission:** novo `storos_execution_admission.py` executa preflight fresco, relê a tarefa e exige schema 3 `planned`/`dry_run`/`executable=false`, plano `changes_planned`/`can_apply=false` e os três bloqueios deliberados da etapa atual.
- **Vínculo anti-drift:** tarefa e preflight precisam concordar em `task_id`, `vm_uuid` e `plan_fingerprint_sha256`; divergência falha fechada antes de produzir registro válido.
- **Identidade:** `claimed_identity` é somente metadado de auditoria; todo registro grava `identity_authenticated=false`. O token administrativo do painel não é promovido a identidade/scopes de escrita.
- **Adaptador:** `DenyOnlySimulationAdapter` declara `mutating_available=false` e `apply_method_available=false`, não possui método `apply` e produz somente resultados `not_attempted`, `executed=false`, `applied=false`.
- **Auditoria:** admissions são persistidas em `/var/lib/storos/execution-admissions` com diretório `0750`, arquivo `0640`, escrita atômica e `fsync`; cada decisão continua `status=denied`, `can_execute=false`, `executed=false`.
- **Testes locais:** **8/8 testes** do VM-004C passaram, cobrindo denial/non-execution, ausência de `apply`, mismatch tarefa/preflight, drift de fingerprint, ação desconhecida, identidade forjada, persistência privada e registro corrompido.
- **Arquitetura:** [docs/VM_EXECUTION_ADMISSION.md](docs/VM_EXECUTION_ADMISSION.md) registra que os locks do preflight não autorizam replay: uma futura aplicação deverá readquirir locks e reler estado/autorização/capacidades imediatamente antes de qualquer mutação.
- **Segurança:** `features.vm_write_enabled=false` permanece obrigatório; sem worker, shell arbitrário, endpoint web mutável ou chamada libvirt de escrita.
- **Validação:** o head final deste lote deve repetir Project continuity, suíte integral, Development image e Bootable media antes de VM-004C ser tratado como fechado remotamente; esta entrada não antecipa sucesso do CI.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base validada `27d233d1f6f115928219e5974cbfe0ac898ea13a`.

## 2026-09-12 — VM-004B — Contrato de execução deny-only

- **Motivo:** formalizar a futura fronteira `JOBS → COMPUTE` depois do fechamento do VM-004A, sem pular diretamente de preflight para um executor libvirt real. O identificador VM-004B passa a nomear esta subtarefa arquitetural a partir deste registro.
- **Contrato:** novo `storos_execution_contract.py` define catálogo fechado das 11 ações mutáveis já conhecidas pelo planner/preflight, com escopo do recurso, classe de operação, verificação esperada e classificação de compensação. Ações de inspeção/bloqueio e tipos desconhecidos não entram no adaptador futuro.
- **Tipagem:** o contrato valida a forma atual dos payloads de criação, rename, vCPU, RAM, lifecycle, firmware, discos e interfaces. A ação ainda precisa chegar como `executable=false` e `blocked=false`; formato inválido ou tentativa de ação desconhecida falha fechada.
- **Backend/autorização:** o único backend desta etapa é `disabled/none`, com `mutating_available=false` e todas as ações `supported=false`. A decisão de autorização recebe identidade, ação e UUID, mas sempre retorna `granted=false`, `reason_code=authorization_unavailable` e nenhum scope.
- **Resultado:** VM-004B só aceita `status=not_attempted`, `executed=false`, `applied=false` e `observed_after_apply=null`; resultado forjado como aplicado/executado é rejeitado.
- **Imagem/testes:** o Containerfile inclui o novo módulo e executa uma prova deny-only no build. Antes da publicação, **7/7 testes isolados** do novo contrato passaram; a suíte também compara o catálogo com `SUPPORTED_ACTION_TYPES` do preflight.
- **Arquitetura:** [docs/VM_EXECUTION_CONTRACT.md](docs/VM_EXECUTION_CONTRACT.md) registra o contrato, invariantes e critérios. Não foi criado comando apply/execute, worker, endpoint mutável ou adaptador libvirt de escrita.
- **Segurança:** `features.vm_write_enabled=false` permanece obrigatório; os três bloqueios deliberados do VM-004A continuam ativos. O token administrativo atual não vira autorização de escrita.
- **Validação:** esta publicação deve repetir Project continuity, suíte integral, Development image e Bootable media antes de VM-004B ser tratado como validado remotamente; esta entrada não antecipa sucesso do CI.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base fechada `c247ff6ea636e0c8394cf37b7390fcd6f4d30ca0`.

## 2026-09-12 — VM-004A2 — Fechamento remoto do preflight fail-closed

- **Resultado:** VM-004A está fechado funcionalmente no head `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4`. Project continuity `34722963474`, Host agent `34722963483`, Development image `34722963475` e Bootable media `34722963476` ficaram verdes; a suíte remota executou **74/74 testes**.
- **Preflight:** tarefas schema 3, fingerprints semânticos, locks por VM/recurso, releitura sob lock, detecção de drift/stale e auditoria persistente foram validados mantendo todo resultado `blocked`, `can_execute=false` e `executed=false`.
- **Imagem:** o smoke da imagem confirmou que schemas de intenção 1/2 permanecem dry-run e que o VM-004A continua bloqueado/não executável. `image-evidence` ID `10306154568`, digest `sha256:c9c99c39edd0dcb624bd466b8d7d8b71f6e4522c83e41acc7973e05f3ab8598f`.
- **Prova de boot:** o Bootable media inicializou o mesmo QCOW2 duas vezes com QEMU 10.2.2 e emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.
- **Artefatos:** QCOW2 SHA-256 `f8bbb35ab5feb333d4bc544da5081d1c74cd3e0ceff2cbd267eee35a63e2862e`; `storos-boot-evidence` ID `10307126883`, digest `sha256:caab500492f2426172a295e1c63294d13603a8ed401c19cd331d96fb5c1240bc`; `storos-qcow2` ID `10306997232`, digest `sha256:b9ef5d46f174977025cef4a272aa00470a0c0ee16447b7fad129a757a4cf4825`.
- **Segurança preservada:** `features.vm_write_enabled=false`; autorização de escrita e backend mutável continuam indisponíveis; não existe executor, worker mutável, endpoint web de aplicação ou chamada libvirt de escrita.
- **Limites:** o fechamento comprova consistência do preflight, auditoria e persistência virtual em CI. Não comprova criação/start/stop real de VM pelo control plane, boot físico USB, passthrough ou GPU compartilhada.
- **Próximo passo:** definir o contrato do adaptador de escrita e da autorização da Fase 1, mantendo qualquer capacidade mutável explicitamente desabilitada até uma etapa posterior aprovada e validada.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), head funcional validado `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4`.

## 2026-09-12 — VM-004A1 — Correção do harness de preflight

- **Evidência:** no head `f3f1b1a5983019214cf5ebca32cbee6492d8d0a1`, Project continuity `34720322042` ficou verde; Host agent `34720322040`, job `103624880382`, falhou antes de executar `PreflightTests` por conflito com o runner do `unittest`.
- **Causa:** o helper do teste havia sido nomeado `run(self, paths, task_id)`, sobrescrevendo `unittest.TestCase.run()`; o runner chamou esse método com seu objeto de resultado e recebeu `TypeError` por argumento ausente.
- **Correção:** o helper passa a `_run_preflight()` e todas as chamadas do teste usam o novo nome. A lógica de produção do VM-004A não muda.
- **Cobertura:** a rejeição de ação executável continua validada no ledger por `tests/test_tasks.py`; o preflight mantém cobertura de drift, snapshot stale, ação desconhecida, compatibilidade schema 2 e bloqueios deliberados.
- **Validação:** o head corretivo deve repetir Project continuity, suíte integral, Development image e Bootable media; resultados do head anterior não serão usados para fechamento.
- **Segurança:** escrita em VM, autorização e backend mutável permanecem indisponíveis; nenhum executor foi introduzido.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2).

## 2026-09-12 — VM-004A — Preflight fail-closed sem executor

- **Motivo:** criar a fronteira verificável imediatamente anterior a um futuro `JOBS → COMPUTE` mutável sem antecipar autorização, feature gate habilitável ou backend de escrita.
- **Fingerprints:** novo `storos_fingerprints.py` preserva o `snapshot_sha256` histórico e adiciona fingerprints semânticos versionados para snapshot/plano. Campos apenas temporais/derivados de frescor deixam de causar drift falso, enquanto mudança observada continua alterando a precondição estável.
- **Ledger:** novas tarefas `vm_reconcile` passam ao schema 3 com geração/hash de intenção, hash legado do snapshot, fingerprint estável do snapshot e fingerprint do plano. Schema 2 continua legível para histórico/API, mas é inelegível ao preflight por não conter as novas precondições.
- **Preflight:** novo `storos_preflight.py` adquire locks determinísticos por VM/recurso, relê tarefa/intenção/snapshot/configuração sob lock, recalcula plano/fingerprints, detecta drift/stale/ação desconhecida e grava auditoria em `/var/lib/storos/preflight`.
- **Bloqueio obrigatório:** mesmo sem drift, todo preflight desta etapa registra `feature_gate_enabled=false`, `authorization_granted=false` e `mutating_backend_available=false`, resultando sempre em `status=blocked`, `can_execute=false` e `executed=false`.
- **CLI/imagem:** adicionados `vm-preflight`, `preflight-list` e `preflight-show`; o smoke da imagem passa a executar o preflight e exigir os três bloqueios deliberados. `features.vm_write_enabled=true` continua rejeitado.
- **Testes:** cobertura adicionada para estabilidade dos fingerprints, ledger schema 2→3, drift de intenção/snapshot/plano, snapshot stale, ação desconhecida, tentativa executável, auditoria/locks, fluxo CLI e painel read-only.
- **Arquitetura:** [docs/VM_PREFLIGHT.md](docs/VM_PREFLIGHT.md) registra a decisão. Não há `virsh` mutável, executor, endpoint web de aplicação, GPU, passthrough ou boot físico USB neste lote.
- **Validação:** publicação deste lote deve passar Project continuity, suíte integral, Development image e Bootable media antes de VM-004A ser considerado fechado; esta entrada não antecipa sucesso remoto.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base documental fechada `874db3cb783bc4c18e9ca0c42f46963d06480f86`.

## 2026-09-12 — VM-003B2 — Fechamento remoto da intenção hardware v2

- **Resultado:** VM-003B está concluído funcionalmente no head `a8e0e9895efd24e4814c87297feefb34e5d123bb`. Project continuity `34715892296`, Host agent `34715892293`, Development image `34715892321` e Bootable media `34715892313` ficaram verdes; a suíte remota executou **63/63 testes**.
- **Imagem:** o smoke passou durante a construção e novamente na imagem final com libvirt 12.0.0/QEMU 10.2.2, confirmando observação de hardware e que `VM intent schemas 1 and 2 remain dry-run only`. `image-evidence` ID `10303869538`, digest `sha256:a97e88a04ddfe595d5c25d4443af815ae0efcfb5845fcfc01fe5127243593c05`.
- **Compatibilidade:** intenções v1 continuam com forma/hash históricos; v2 adiciona firmware/discos/rede como subconjuntos gerenciados e tipados, sem detach implícito. Rollback v2→v1 preserva o conteúdo/hash da intenção v1. A semântica de Secure Boot foi endurecida para não tratar `loader secure=yes` como estado ativo.
- **Prova de boot:** o job `103612991227` gerou e inspecionou o QCOW2 e inicializou o mesmo disco duas vezes com o QEMU 10.2.2 da imagem StorOS. Foram emitidos `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`, com `boot_count=1 → 2`, `config_generation=1` e fingerprints persistentes de configuração/token.
- **Artefatos:** QCOW2 SHA-256 `7e1466e575254dfd8c40c7eff3dec5f683e24a43385fd36709f15a68922ff44c`; `storos-boot-evidence` ID `10304634825`, digest `sha256:d4bb72db8d61c5e100c13b697e697db39263fd078f5c963b14591f610ed8bbd8`; `storos-qcow2` ID `10304931834`, digest `sha256:20d06f112745fd9982c6382501eb5751691f77d3859e930bfe6e7afe9c410184`.
- **Segurança preservada:** `features.vm_write_enabled=false`, planos `dry_run`/`can_apply=false`, ações/tarefas `executable=false`; nenhum executor, endpoint web mutável ou chamada libvirt de escrita foi introduzido. QCOW2 continua artefato de laboratório.
- **Fechamento documental:** `PROJECT_STATE.md` e `CHANGELOG.md` são consolidados no mesmo commit atômico antes do início do VM-004A, conforme a política de continuidade do projeto.
- **Próximo passo:** VM-004A deve criar apenas a fronteira de preflight de execução — releitura de tarefa/intenção/snapshot, precondições e locks — mantendo o feature gate de escrita desligado e sem executar mutações.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), head funcional validado `a8e0e9895efd24e4814c87297feefb34e5d123bb`.

## 2026-09-12 — VM-003B1 — Secure Boot: capacidade não é estado

- **Motivo:** a revisão do contrato VM-003B confirmou na documentação oficial do libvirt que `loader secure='yes'` descreve capacidade do firmware para Secure Boot, não que a feature esteja efetivamente habilitada. O observador precisava eliminar essa ambiguidade antes de hardware observado sustentar decisões futuras.
- **Mudou:** `409f77c5fdcf7a5d0e531c7586d25cf3554b68c5` remove a inferência de `firmware.secure_boot` a partir de `loader@secure`. O campo só recebe `true|false` quando existe `firmware/feature name='secure-boot' enabled='yes|no'`; sem declaração explícita permanece `null`.
- **Teste:** `84927ecd77ba7d1fde98363381a009cacb253f1c` adiciona um caso dedicado com `loader secure=yes` sem a feature explícita e exige `secure_boot=None`, preservando EFI/NVRAM observados.
- **Documentação:** `7ca50e9a7e3e3aadb15440c5e51160027b5f4f6a` alinha `docs/AGENT.md` à semântica corrigida. O VM-003B continua sem gerenciar Secure Boot, enrolled keys ou NVRAM.
- **Segurança:** a correção é somente de observação e fail-closed; não adiciona executor, escrita libvirt ou endpoint mutável. `features.vm_write_enabled=false`, `mode=dry_run`, `can_apply=false` e `executable=false` permanecem invariáveis.
- **Validação:** esta correção cria novo head; Host agent, Project continuity, Development image e Bootable media desse head precisam ficar verdes antes de VM-003B ser fechado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2).

## 2026-09-12 — VM-003B — Intenção hardware v2 backward-compatible em dry-run

- **Motivo:** com VM-003A fechado, permitir que firmware/discos/rede observados entrem no contrato de intenção/planner sem quebrar gerações schema 1 e sem antecipar executor real.
- **Compatibilidade:** `storos_vm.py` passa a aceitar schema 1 e schema 2. Um documento v1 continua normalizado na forma histórica, sem `hardware` adicionado implicitamente; isso preserva hashes, revisões, rollbacks e precondições antigas. O store pode conter gerações v1 e v2 na mesma linha do tempo.
- **Schema 2:** acrescenta `hardware` com firmware opcional `bios|efi`; discos gerenciados por target com bus `virtio|sata|scsi`, source local `file|block`, formato `raw|qcow2`, readonly e boot order; interfaces gerenciadas por MAC com `network|bridge` e modelo explícito. Targets/MACs duplicados são rejeitados e listas são ordenadas deterministicamente.
- **Sem detach implícito:** as listas v2 são subconjuntos gerenciados. Hardware observado extra não é considerado lixo e não gera ação de remoção.
- **Planner:** hardware de VM existente só é comparado quando `hardware.status=ok`. Foram adicionadas descrições não executáveis `set_firmware_mode`, `attach_disk`, `reconfigure_disk`, `attach_interface`, `reconfigure_interface` e bloqueios `inspect_hardware`, `inspect_firmware`, `inspect_disk`, `inspect_interface`. Toda ação permanece `executable=false`, o plano continua `mode=dry_run` e `can_apply=false`.
- **Testes:** `802399c3eb7a1925ceb9ed6acc3b1257316be2d2` amplia a cobertura do planner/validador; `43daed4f5dd0ad60d0dbc30b9846d44e3f439154` cobre round-trip v2 e v1→v2→rollback-v1 preservando o hash v1. `780173c0817b6e26cd0ab4279ae51d387e16cc09` faz o smoke da imagem provar schema 1 e schema 2 contra `test:///default`.
- **Arquitetura/documentação:** `docs/VM_PLANNER.md` foi atualizado em `79f5bb09d20fcad94ae497cf3b49b9722c30688a`; `docs/ARQUITETURA.md` registra as fronteiras VM-003A/VM-003B em `4febbc02b9439b0054bc670e1a32c0b81444bdf5`.
- **Segurança/limites:** nenhum executor, endpoint mutável ou chamada libvirt de escrita foi adicionado; `features.vm_write_enabled=false` permanece obrigatório. Secure Boot/enrolled keys/NVRAM, hotplug, detach automático, pinning/NUMA, passthrough, SR-IOV, mediated devices e GPU continuam fora do VM-003B.
- **Validação:** publicação funcional/documental concluída; os workflows remotos do head final ainda precisam ficar verdes antes de VM-003B ser considerado fechado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2).

## 2026-09-12 — VM-003A2 — Fechamento remoto do observador de hardware virtual

- **Resultado:** VM-003A está concluído no head `6108e0ec45f79e7a399f7f96733076effe3a2f47`. Project continuity `34713932768`, Host agent `34713932769`, Development image `34713932991` e Bootable media `34713932817` ficaram verdes; a suíte remota executou **50/50 testes**.
- **Imagem:** o smoke endurecido passou dentro da imagem final com libvirt 12.0.0 e QEMU 10.2.2 e confirmou explicitamente `StorOS discovery and virtual hardware observation passed against libvirt test driver (no real VM).` O gate exige `hardware.status=ok`, firmware tipado e listas válidas de discos/interfaces em todas as VMs simuladas.
- **Prova de boot:** o job Bootable `103607586216` gerou/inspecionou o QCOW2 e inicializou o mesmo disco duas vezes com o QEMU 10.2.2 da imagem StorOS. Foram emitidos `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`, com `boot_count=1 → 2`, agente + painel autenticado nos dois boots, `config_generation=1` e fingerprints persistentes de configuração/token.
- **Artefatos:** QCOW2 SHA-256 `d8075fbaa6693d7087db689922741a171b3e752cb1242072ec9f3b5b5ce1b091`; `storos-boot-evidence` ID `10304262931`, digest `sha256:5fc0a60aaff96e107512cbf1596d7589e085e5caf5801e8f539b81dc369e3100`; `storos-qcow2` ID `10304721991`, digest do artefato `sha256:a191ed814adc020ae79f097231df9c95cf25a7f9de28842d513aaf0343c0c4e4`.
- **Segurança preservada:** observação de firmware/discos/rede continua somente leitura; `features.vm_write_enabled=false` permanece obrigatório; planner/tarefas continuam `dry_run`, `can_apply=false` e `executable=false`; nenhum executor ou chamada mutável ao libvirt foi introduzido.
- **Limites:** o fechamento comprova observação tipada e persistência virtual em CI, não criação/start/stop real de VM, passthrough, SR-IOV, mediated devices, vGPU, GPU compartilhada ou boot físico USB. O QCOW2 continua artefato de laboratório.
- **Próximo passo:** iniciar VM-003B com evolução backward-compatible da intenção/planner para um subconjunto estreito de firmware/discos/rede, ainda exclusivamente `dry_run`.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), head validado `6108e0ec45f79e7a399f7f96733076effe3a2f47`.

## 2026-09-12 — VM-003A1 — Smoke da imagem exige hardware observado

- **Motivo:** o smoke anterior aceitava `test:///default` quando a descoberta geral estava saudável, mas não exigia explicitamente que o novo campo `hardware` tivesse sido produzido e validado dentro da imagem final.
- **Mudou:** `image/check-image.sh` agora exige ao menos uma VM simulada, `hardware.status=ok` em todas elas, estrutura tipada de firmware e listas válidas de discos/interfaces.
- **Critério:** o Development image só pode ficar verde se a observação de hardware funcionar com o libvirt realmente empacotado na imagem; importar o módulo Python isoladamente não basta.
- **Segurança:** a mudança é somente de validação. Não adiciona executor, escrita libvirt ou autoridade ao painel; intenção e reconciliação continuam `dry_run`.
- **Verificação anterior preservada:** no head documental `4e96badc0a055c6ec2ca3720b7fa120105f2bce9`, Project continuity `34713608860` ficou verde e Host agent `34713608846` repetiu **50/50 testes verdes**. A mudança do smoke cria novo head e exige nova rodada dos gates pesados.
- **Limites:** ainda não é fechamento VM-003A; Development image e Bootable media do head final precisam ficar verdes.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), smoke endurecido em `02b4f085c0cbdf47fefd4e7796398ce58210adb9`.

## 2026-09-12 — VM-003A — Observação tipada de firmware, discos e rede

- **Motivo:** antes de ampliar a intenção/planner para firmware, discos ou rede, tornar o estado observado desses recursos explícito e testável, sem conceder autoridade de escrita ao hipervisor.
- **Mudou:** `storos_agent.py` passa a ler a definição persistente da VM em modo somente leitura e adiciona o campo aditivo `hardware` ao snapshot schema 1. São observados firmware EFI/BIOS/desconhecido, Secure Boot quando determinável, presença de NVRAM, discos e interfaces de rede com atributos tipados relevantes.
- **Fail-closed:** identidade e hardware têm falhas separadas. Falha de hardware preserva a VM com `hardware.status=unavailable`, registra erro `scope=hardware` e deixa o inventário `partial`; hardware não observado não vira hardware ausente. O parser limita o documento e valida o UUID antes de aceitar a observação.
- **Testes:** a primeira publicação `4257da8a989e837bb72fd0d5571c5ea8098f1f7a` deixou Host agent `34713090955` com 45/47 testes: duas falhas eram mocks antigos que devolviam texto de `dominfo` para a nova consulta de XML. O corretivo `847520c1cbac7d56d56f121dd81e6f46964f5516` atualizou os mocks e ampliou a cobertura; Host agent `34713412563` passou **50/50 testes** e Project continuity `34713412537` ficou verde.
- **Arquitetura:** [docs/VM_HARDWARE_OBSERVER.md](docs/VM_HARDWARE_OBSERVER.md) formaliza a fronteira somente leitura; [docs/AGENT.md](docs/AGENT.md) foi atualizado. VM-003A não altera o schema de intenção nem cria novas ações no planner.
- **Segurança:** `features.vm_write_enabled=false` permanece obrigatório; nenhum executor, endpoint mutável ou chamada libvirt de escrita foi adicionado.
- **Limites:** os gates de imagem/boot do head documental final ainda precisam fechar antes de VM-003A ser considerado concluído. A observação básica não comprova passthrough, SR-IOV, mediated devices, vGPU, GPU compartilhada ou boot físico USB.
- **Próximo passo:** fechar todos os gates no head final e só então iniciar VM-003B, ainda em validação/planner `dry_run`.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2).

## 2026-09-12 — WEB-VM-001A — Fechamento remoto do painel de VM somente leitura

- **Resultado:** WEB-VM-001 está concluído no head `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`. Project continuity `34712230631`, Host agent `34712230846`, Development image `34712230629` e Bootable media `34712230653` ficaram verdes; a suíte executou **47/47 testes**.
- **Prova de boot:** job `103602983309` gerou e inspecionou o QCOW2 e inicializou o mesmo disco duas vezes com QEMU 10.2.2 da própria imagem StorOS. Foram emitidos `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`, com `boot_count=1 → 2`, painel autenticado/agente nos dois boots e fingerprints persistentes de configuração/token.
- **Artefatos:** QCOW2 SHA-256 `a081b7480d19d85fd5a014e2ba8327d37c4fc8b11f2beac6cd8f6997aae333a8`; `storos-boot-evidence` ID `10303234826`, digest `sha256:2d84494a73c4f82a789b55410edf392cd8b0b1a48974953de7849eca194e2010`; `storos-qcow2` ID `10303549406`, digest `sha256:c8117f02ee200068e18bdd059ee3f8a61206e4d87f6a153d7b805258aa308198`.
- **Limites preservados:** o fechamento comprova o painel/API read-only e persistência virtual; não habilita criação/start/stop real de VM, não homologa GPU, não substitui boot físico USB e não transforma o QCOW2 em release para o usuário.
- **Próximo passo:** observar firmware/discos/rede de forma tipada antes de estender o contrato do planner.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run Bootable media `34712230653`.

## 2026-09-12 — WEB-VM-001 — Intenção, plano e tarefas no painel somente leitura

- **Motivo:** com VM-002 fechado remotamente, tornar a intenção persistida, o plano dry-run e o ledger auditável visíveis no painel sem antecipar qualquer executor ou endpoint de comando.
- **Mudou:** `storos_web.py` passa a expor, mediante autenticação, `GET /api/vms/intents`, `GET /api/vms/intents/<uuid>`, `GET /api/vms/intents/<uuid>/plan`, `GET /api/tasks` e `GET /api/tasks/<task_id>`. O HTML inicial mostra contagem de intenções/tarefas e uma tabela simples de intenções persistidas.
- **Fail-closed:** o endpoint de plano apenas chama o planner determinístico em memória; não cria tarefa e não grava estado. Snapshot observado ausente, ilegível ou incompatível retorna `503` em vez de produzir plano por suposição.
- **Segurança:** `POST`, `PUT`, `PATCH` e `DELETE` continuam retornando `405`; nenhum caminho web chama `apply_vm_intent`, `rollback_vm_intent`, `create_dry_run_task` ou mutação libvirt. Planos continuam `mode=dry_run`/`can_apply=false` e tarefas/ações continuam `executable=false`.
- **Testes:** a suíte web ganhou cobertura de autenticação das novas APIs, leitura de intenção, cálculo de plano, leitura do ledger, ausência de efeitos colaterais após POST rejeitado, `503` sem snapshot e resumo HTML. Host agent do head arquitetural `59aa924aefa8d1960ecc5703e2f363339743e9c0`, run `34712075217`, ficou verde. Development image e continuidade do lote final ainda precisam ser confirmados antes de fechar WEB-VM-001.
- **Arquitetura:** [docs/ARQUITETURA.md](docs/ARQUITETURA.md) registra que esta é apenas uma projeção de leitura do control plane, sem autoridade `UI/API → JOBS → COMPUTE` mutável.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), implementação `f9d12acc7e451600ee9a533f6b3d97d7e9a651f1` / testes `2018e205dea05e0dd36066371b36de80ecfc1b9e`.

## 2026-09-12 — VM-002A — Fechamento remoto da intenção persistente

- **Resultado:** VM-002 está concluído no head `9f7366e84819f5053efc44c129a7a8f8c0d68286`. Host agent `34710051568`, Project continuity `34710051542`, Development image `34710051546` e Bootable media `34710051552` ficaram verdes; a suíte remota executou **42/42 testes**.
- **Imagem:** o smoke dentro da imagem final confirmou que intenção persistida e reconciliação permanecem exclusivamente dry-run, sem worker/executor e sem escrita libvirt.
- **Prova de boot:** o job Bootable `103597090745` construiu/inspecionou o QCOW2 e inicializou o mesmo disco duas vezes com QEMU 10.2.2 da própria imagem StorOS. O gate comprovou `boot_count=1 → 2`, agente + painel autenticado nos dois boots, `config_generation=1` e fingerprints persistentes de configuração/token.
- **Provas explícitas:** `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`. QCOW2 SHA-256 `cde00c270df09e3f28cc0b4341a55dfa88ed8d50d1bfcd59678e4bc4329211b6`; `storos-boot-evidence` ID `10303516398`, digest `sha256:780236c38216fe6df3464d650c418c2c24894dd32af9ec830204720467092730`; `storos-qcow2` ID `10303451532`, digest do ZIP `sha256:536591efcc59a5872e41bfef1fcdcbd1cbb20ffbda1319726d7c284860b57cee`.
- **Limites preservados:** o fechamento comprova consistência/persistência virtual; não habilita criação/start/stop real de VM, não homologa GPU, não substitui boot físico USB e não transforma o QCOW2 em release para o usuário.
- **Próximo passo:** projetar intenção/plano/tarefas no painel somente leitura antes de desenhar qualquer executor.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run Bootable media `34710051552`.

## 2026-09-12 — VM-002 — Intenção persistente e precondições dry-run

- **Motivo:** após o head `ba15347d0dd699bb0154edd47cb49d44e72e71af` recuperar o gate completo de QCOW2 com Host agent, Project continuity, Development image e Bootable media verdes, avançar a reconciliação de VMs sem pular a etapa de consistência e sem conceder escrita prematura ao hipervisor.
- **Mudou:** novo `storos_vm_store.py` persiste intenção por UUID em `/var/lib/storos/vm-intents`, com `current.json`, revisões monotônicas, `expected_generation`, rollback por nova geração, SHA-256 da intenção, lock por VM, escrita atômica e `fsync`. `storosctl` ganha `vm-intent-apply/show/history/list/rollback`; `vm-plan` pode usar intenção persistida.
- **Tarefas/precondições:** `storos_tasks.py` passa ao schema 2 e vincula cada reconciliação dry-run a `intent_generation`, `intent_sha256` e `snapshot_sha256`, com lock por VM no ledger. Divergência de hash/precondição é rejeitada. `vm-reconcile-dry-run` agora exige intenção persistida, mas continua produzindo somente `can_apply=false` e `executable=false`.
- **Imagem/testes:** Containerfile inclui o store; `check-image.sh` persiste uma intenção, planeja a partir dela e grava uma tarefa dry-run com precondições. Foram adicionados testes de geração/update/rollback, detecção de adulteração, permissões, locks, precondições e fluxo CLI. Na preparação, 8 testes focados passaram, os módulos foram compilados sintaticamente e `bash -n image/check-image.sh` passou.
- **Segurança:** `features.vm_write_enabled=false` permanece obrigatório; nenhum worker/executor ou chamada libvirt mutável foi introduzido; painel continua somente leitura. Locks e hashes são fundamentos de consistência, não autorização para aplicação.
- **Limites:** o lote publicado ainda depende dos workflows remotos do head final para ser considerado fechado. Não há criação/start/stop real de VM, boot físico USB, política dinâmica de CPU/RAM, discos/rede/firmware/passthrough nem GPU compartilhada homologada.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base funcional anterior `ba15347d0dd699bb0154edd47cb49d44e72e71af`.

## 2026-09-12 — CI-BOOT-002 — Probe usa o QEMU da própria imagem StorOS

- **Motivo:** o ajuste CI-BOOT-001 com 1 vCPU não foi suficiente. No mesmo head `6b54ac40aef0e73b87286dc04163849a9fcbd61e`, o Bootable media de PR #53 (`34706993875`) avançou muito além das tentativas anteriores, mas não alcançou agente+painel dentro de 420 s; já o push #52 (`34706993402`) reproduziu a mesma falha fatal do `systemd` antes dos serviços StorOS mesmo com `-smp 1`.
- **Diagnóstico revisto:** reduzir SMP não elimina a causa. O runner Ubuntu fornece QEMU 8.2.2, enquanto a imagem StorOS construída contém QEMU 10.2.2. A diferença de comportamento entre execuções do mesmo commit confirma flutuação do probe TCG/runner e não autoriza classificar o problema como regressão do agente/painel.
- **Mudou:** o boot de validação passa a executar `/usr/sbin/qemu-system-x86_64` da própria imagem StorOS em Docker `--network none`, montando somente QCOW2 e OVMF. O pacote host `qemu-system-x86` deixa de ser necessário; `qemu-utils` continua para inspeção do disco. O probe volta a 2 vCPUs para evitar a penalidade de tempo observada em 1 vCPU, continua em TCG e não presume nested KVM.
- **Critério preservado:** a detecção `guest_fatal=1` permanece; limites continuam 420 s/300 s; sucesso ainda exige `STOROS_BOOT_STATE`, `STOROS_AGENT_READY` e `STOROS_WEB_READY` em dois boots do mesmo QCOW2, `boot_count=1 → 2`, `config_generation=1` e fingerprints persistentes de configuração/token. Nenhuma falha pré-StorOS é aceita como sucesso.
- **Verificação local:** o novo bloco Bash passou em `bash -n`. Nenhuma opção de segurança do guest foi desabilitada. Resultado remoto ainda é obrigatório antes da publicação do VM-002.
- **VM-002:** staging reconstruído sobre o head atual passou **39/39 testes**, `py_compile` e `bash -n`; continua não publicado enquanto o gate de boot estiver vermelho, mantendo `features.vm_write_enabled=false` e sem executor.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base anterior `6b54ac40aef0e73b87286dc04163849a9fcbd61e`.

## 2026-09-12 — CI-BOOT-001 — Gate TCG isolado de instabilidade SMP pré-StorOS

- **Motivo:** o Bootable media #51 (`34700188781`) falhou em duas tentativas consecutivas no primeiro boot, embora build bootc, smoke da imagem, geração e inspeção do QCOW2 tenham passado. Em ambas, `web=0`, `agent=0`, nenhum `STOROS_BOOT_STATE` foi emitido e o segundo boot nem começou.
- **Diagnóstico:** após switch-root, `systemd 259.8-1.fc44` falhou antes dos serviços StorOS com `Failed to fork off sandboxing environment for executing generators: Protocol error`, seguido de `Failed to start up manager.`. A tentativa 2 também registrou `clocksource: Watchdog remote CPU 1 read timed out`. Os dois jobs usavam `-smp 2`; QCOW2 distintos reproduziram a mesma assinatura. O merge ref do PR foi comparado ao head e não contém diferenças de arquivo, descartando alteração funcional trazida pela `main`.
- **Mudou:** o guest QEMU/TCG do gate de boot passa de `-smp 2` para `-smp 1`. Esse guest é somente probe de correção de boot, não benchmark nem prova de compartilhamento de CPU. O loop também detecta a assinatura fatal do manager e encerra cedo com `guest_fatal=1`, em vez de consumir toda a janela e parecer um timeout de agente/painel.
- **Critério preservado:** os limites permanecem 420 s/300 s e o sucesso continua exigindo agente + painel nos dois boots, `boot_count=1 → 2`, `config_generation=1` e fingerprints persistentes de configuração/token. Nenhuma falha pré-StorOS será aceita como sucesso.
- **Verificação local:** o bloco Bash revisado passou em `bash -n`. O resultado remoto desta correção ainda precisa ficar verde antes de publicar VM-002.
- **Evidência das falhas:** tentativa 1 job `103570462206`, artefato `10299648872`, digest `sha256:476a86fc34493001e8bb05eb60cf1bf07120acb6bcd736042f1cb51e47b38ca9`; tentativa 2 job `103585516180`, artefato `10300784701`, digest `sha256:7605de8c239c4f83a640b6da01ebcdb1307a1b4a6b8091cce57b4c5dcab7347e`.
- **VM-002:** implementação preparada localmente continua não publicada durante o reparo do gate. O staging corrigido passou 28/28 testes, `py_compile` e `bash -n`, mantendo `features.vm_write_enabled=false` e sem executor.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base anterior `6b9e157b394b637403fa50af653cd4bd64a15b14`.

## 2026-09-12 — VM-001A — Fechamento remoto do planner dry-run

- **Resultado:** VM-001 está concluído no head funcional `45bd655269d8ef45f1c6f5ace9ff82ce3f8454fc`. Host agent `34699051160` (#69), Project continuity `34699051144` (#81), Development image `34699051205` (#75) e Bootable media `34699051187` (#49) terminaram verdes.
- **Imagem/planner:** o Development image e o estágio `Build and stage bootc image` do Bootable executaram o smoke do planner/ledger dentro da imagem final, confirmando `vm-plan`, criação de tarefa dry-run e a invariável `can_apply=false`/`executable=false`.
- **Prova de boot:** o job Bootable `103567451447` inicializou o mesmo QCOW2 duas vezes. O primeiro boot registrou `boot_count=1`, `STOROS_WEB_READY auth=ok config_generation=1` e `STOROS_AGENT_READY snapshot=written boot_count=1`; o segundo registrou `boot_count=2` com novo `boot_id`, agente pronto e painel autenticado novamente. Os fingerprints de configuração e token permaneceram idênticos entre os boots.
- **Prova explícita:** o artefato emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`. `storos-boot-evidence`: ID `10299687818`, digest `sha256:63780ac5e92c2450ad4159adaf6484515cf2ab1521bb42dc19534898ec0f62c5`. O QCOW2 validado teve SHA-256 `ba9d51ebb91bc91e08d9e84d41be1f13a07c0efcf89a94527543027e6778538b`; artefato `storos-qcow2` ID `10300291526`.
- **Segurança preservada:** não existe worker/executor mutável; `features.vm_write_enabled=false` continua obrigatório; planner e ledger não executam `virsh define/start/shutdown/setvcpus/setmem`. Snapshot stale, inventário parcial e recurso observado ausente continuam bloqueando o plano em vez de presumir alterações.
- **Limites:** VM-001 comprova intenção/plano/tarefa dry-run e ausência de regressão no boot virtual. Ainda sem persistência de intenção desejada, locks/precondições de aplicação, discos/rede/firmware no contrato, política dinâmica CPU/RAM aplicada, boot físico USB ou GPU compartilhada comprovada.
- **Próximo passo:** VM-002 deve persistir intenção de VM e formalizar precondições/locks/revisões para futura aplicação, ainda sem executor libvirt real.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run Bootable media `34699051187`.

## 2026-09-12 — VM-001 — Planner de VM e ledger dry-run

- **Motivo:** após o fechamento do CFG-001, iniciar a camada de tarefas/reconciliação da Fase 1 sem conceder autoridade de escrita ao hipervisor.
- **Mudou:** novo `storos_vm.py` com intenção de VM schema v1 (UUID, nome, estado desejado, vCPU e RAM fixa) e planner determinístico que compara intenção com o snapshot observado. O plano descreve `create_vm`, `rename_vm`, `set_vcpus`, `set_memory`, `start_vm` e `shutdown_vm`, mas sempre usa `mode=dry_run`, `can_apply=false` e `executable=false` em todas as ações.
- **Segurança de observação:** a CLI usa `read_snapshot(..., max_age=30)`. Snapshot stale bloqueia com `refresh_snapshot`; inventário `partial` sem a VM não pode gerar `create_vm`; recurso observado ausente bloqueia CPU/RAM em vez de presumir valor. RAM é comparada com `max_memory_reported_kib`, não com memória usada.
- **Tarefas:** novo `storos_tasks.py` grava `/var/lib/storos/tasks/<task_id>.json` com UUID, timestamp, plano completo, escrita atômica/fsync e modos `0750/0640`. O ledger rejeita plano aplicável ou ação executável. Não existe worker/executor neste incremento.
- **CLI/imagem:** `storosctl` ganha `vm-plan`, `vm-reconcile-dry-run`, `task-list` e `task-show`. Containerfile inclui os módulos e `check-image.sh` executa planner + ledger contra `test:///default`, exigindo que nada seja aplicável/executável.
- **Verificação local:** 15 testes focados passaram para planner, ledger e CLI, incluindo schema estrito, convergência, diferenças CPU/RAM/estado, snapshot stale, inventário parcial, dados observados ausentes, UUID duplicado, persistência/permissões e rejeição de ação executável. O novo `check-image.sh` passou em `bash -n`.
- **Arquitetura/documentação:** [docs/VM_PLANNER.md](docs/VM_PLANNER.md) registra contrato/comandos/limites e [docs/ARQUITETURA.md](docs/ARQUITETURA.md) explicita que a passagem de tarefas para um adaptador mutável será uma camada futura separada com locks, precondições e auditoria.
- **Limites:** resultado remoto deste lote ainda precisa ficar verde antes de VM-001 ser concluído. `features.vm_write_enabled=false` permanece obrigatório; painel continua somente leitura; sem mutação libvirt, discos/rede/firmware, política dinâmica CPU/RAM, boot físico USB ou GPU compartilhada comprovada.
- **Próximo passo:** obter todos os checks verdes; depois registrar a evidência remota e avançar para persistência de intenção/precondições em dry-run antes de discutir qualquer executor real.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base anterior `4742ee4b9e3da2420c93f6fcd26424a331b16016`.

## 2026-09-12 — CFG-001D — Fechamento: configuração e painel persistentes comprovados

- **Resultado:** CFG-001 está concluído como fundação da Fase 1. No head `496e3bfbba637519c1fabe32414ea0a64ac018da`, Host agent `34693451988`, Development image `34693452020`, Project continuity `34693451976` e Bootable media `34693452040` ficaram verdes.
- **Prova de boot:** a tentativa 2 do Bootable media iniciou o mesmo QCOW2 duas vezes. O primeiro boot registrou `boot_count=1`, `STOROS_AGENT_READY` e `STOROS_WEB_READY auth=ok config_generation=1`; o segundo registrou `boot_count=2` com novo `boot_id` e repetiu agente/painel prontos. Os fingerprints de configuração e token administrativo foram idênticos entre os dois boots, sem publicar a credencial bruta.
- **Prova explícita:** o workflow emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`. O artefato `storos-boot-evidence` da tentativa verde é o ID `10298937312`, digest `sha256:ac25baaf918e1217bda3ac5064c46370685a1d0c279f8fb232b355522153ed82`. O QCOW2 validado teve SHA-256 `72772b43e2f11eca2f935ad717c0bf36774308bf9f729a3fa217f1b22011ee84`.
- **Tentativa anterior preservada:** a tentativa 1 do mesmo run falhou antes dos services StorOS, durante a subida do manager do systemd sob QEMU/TCG, com `web=0` e `agent=0`. O rerun limpo passou integralmente sem mudança de código; portanto essa ocorrência fica registrada como instabilidade do ambiente TCG/runner, não como prova de falha da configuração/painel.
- **Limites:** este fechamento comprova a fundação virtual em CI, não boot físico por USB. O painel continua somente leitura; sem TLS integrado, RBAC/múltiplos usuários, criação/start/stop de VM, política automática de CPU/RAM ou GPU compartilhada. `features.vm_write_enabled` permanece `false` e nenhuma mutação libvirt foi habilitada.
- **Próximo passo:** iniciar modelo de intenção de VM + fila/reconciliação em dry-run, produzindo planos auditáveis sem executar alterações no hipervisor.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run Bootable media `34693452040`.

## 2026-09-12 — CFG-001C — Gate exige painel e agente no mesmo boot

- **Motivo:** após CFG-001B permitir que painel e agente iniciem em paralelo, a revisão do workflow mostrou que `boot_guest` ainda encerrava o QEMU no primeiro `STOROS_WEB_READY`, embora as asserções posteriores também exigissem `STOROS_AGENT_READY`. Se o painel ficasse pronto primeiro, o próprio gate poderia matar um boot saudável antes do snapshot do agente.
- **Mudou:** o loop acompanha `web_ready` e `agent_ready` separadamente e só define o boot como pronto quando os dois marcadores já apareceram no mesmo console. O erro de timeout passa a informar `(web=0/1, agent=0/1)` para distinguir qual componente faltou. Os tetos permanecem 420 s no primeiro boot e 300 s no segundo.
- **Verificação local:** a sintaxe Bash do novo gate conjunto passou em `bash -n`. O head anterior `1a7e372bc022f15978f5d43bce9fb4da689a4be5` já deixou Host agent `34693093926`, Development image `34693093931` e Project continuity `34693093913` verdes; o Bootable media em execução foi supersedido antes de ser usado como evidência final porque o problema lógico do gate foi identificado antecipadamente.
- **Critério final:** cada boot precisa conter `STOROS_BOOT_STATE`, `STOROS_AGENT_READY` e `STOROS_WEB_READY`; o mesmo QCOW2 deve avançar `boot_count=1 → 2`, manter `config_generation=1` e preservar os fingerprints SHA-256 de configuração e token.
- **Limites:** CFG-001 continua aberto até o novo Bootable media produzir `STOROS_WEB_PERSISTENCE_OK`. Sem boot físico USB, TLS/RBAC, escrita no libvirt, política automática de CPU/RAM ou GPU compartilhada.
- **Próximo passo:** obter os quatro checks verdes; somente então fechar CFG-001 e iniciar modelos de VM + fila/reconciliação em dry-run.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `1a7e372bc022f15978f5d43bce9fb4da689a4be5`.

## 2026-09-12 — CFG-001B — Painel independente do aquecimento do agente

- **Motivo:** o Bootable media `34672437568`, head `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`, passou imagem e QCOW2, mas o primeiro boot TCG consumiu quase toda a janela de 420 s porque `storos-web.service` estava ordenado depois de `storos-agent.service`, embora `/api/config` e autenticação não dependam do inventário libvirt.
- **Evidência:** no primeiro boot apareceram `STOROS_BOOT_STATE boot_count=1` por volta de 243 s, `STOROS_AGENT_READY` por volta de 322 s, configuração geração 1 por volta de 356 s e `STOROS_WEB_TOKEN_READY` por volta de 395 s. O QEMU foi encerrado antes de `STOROS_WEB_READY`; o segundo boot não foi iniciado. No mesmo head, Host agent `34672437628`, Development image `34672437583` e Project continuity `34672437600` ficaram verdes.
- **Mudou:** `storos-web.service` mantém `Wants=storos-agent.service`, remove `After=storos-agent.service` e passa a usar `After=network.target`, permitindo que painel/config/token iniciem em paralelo ao primeiro snapshot. `/api/status` continua retornando `503` enquanto o snapshot não existe; `/api/config` permanece disponível de forma independente.
- **Proteção contra regressão:** `check-image.sh` exige `Wants=storos-agent.service` e `After=network.target` e falha se `After=storos-agent.service` reaparecer. A separação de prontidão administrativa e estado observado foi registrada em `CONFIGURATION.md` e `ARQUITETURA.md`.
- **Verificação local:** a unidade corrigida e as três asserções de ordenação passaram em validação textual. Nenhum resultado remoto deste lote é tratado como sucesso antes do novo CI.
- **Limites:** CFG-001 continua aberto até o workflow provar dois boots do mesmo QCOW2 com `STOROS_WEB_READY` autenticado e fingerprints idênticos de configuração/token. Sem boot físico USB, TLS/RBAC, escrita no libvirt, política automática de CPU/RAM ou GPU compartilhada.
- **Próximo passo:** obter os quatro checks verdes e `STOROS_WEB_PERSISTENCE_OK`; somente então fechar CFG-001 e iniciar modelos de VM + fila/reconciliação em dry-run.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `d368fba2c0b7fb3bba0994ed4d926bf988dcce4e`; contrato em [docs/CONFIGURATION.md](docs/CONFIGURATION.md) e arquitetura em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## 2026-09-12 — CFG-001A — Gate por prontidão e prova persistente do painel

- **Motivo:** o run Bootable media `34671399200`, head `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`, passou build da imagem, smoke check e QCOW2, mas o primeiro QEMU foi encerrado pelo limite fixo de 240 s antes de o primeiro boot terminar. A segunda execução chegou ao agente como `boot_count=1`, mostrando que o gate media tempo de TCG, não dois boots lógicos completos.
- **Evidência da falha anterior:** no primeiro console o sistema ainda executava trabalho único de primeiro boot e chegava à inicialização de `storos-agent.service` perto do limite. No segundo console apareceram `STOROS_BOOT_STATE boot_count=1` e `STOROS_AGENT_READY snapshot=written boot_count=1`. No mesmo head, Host agent `34671399198`, Development image `34671399204` e Project continuity `34671399235` ficaram verdes.
- **Mudou:** novo `storosctl web-marker` autentica localmente em `/api/config`, compara a resposta com o documento persistido e emite `STOROS_WEB_READY` com geração e fingerprints SHA-256 da configuração/token, sem imprimir o segredo bruto. `storos-web.service` executa esse marker em `ExecStartPost` e publica o resultado no console. O token ganha `fsync` do diretório depois da troca atômica.
- **CI:** o boot deixa de ser encerrado cegamente após 240 s. O primeiro boot pode aguardar até 420 s e o segundo até 300 s, mas ambos são encerrados assim que `STOROS_WEB_READY` aparece. O mesmo QCOW2 é reutilizado. O gate exige agente + painel prontos nos dois boots, `boot_count=1 → 2`, `config_generation=1` e fingerprints idênticos de configuração e token. A prova final esperada é `STOROS_WEB_PERSISTENCE_OK`.
- **Verificação local:** 9 testes focados de configuração/painel passaram, incluindo autenticação real do marker e confirmação de que o token não aparece em sua saída. O workflow foi validado como YAML e o bloco Bash do gate passou em `bash -n`.
- **Limites:** resultado remoto deste incremento ainda precisa ficar verde antes de declarar CFG-001 concluído. Sem boot físico USB, TLS/RBAC, escrita no libvirt, política automática de CPU/RAM ou GPU compartilhada.
- **Próximo passo:** obter os quatro checks verdes; com `STOROS_WEB_PERSISTENCE_OK`, fechar CFG-001 e iniciar modelos de VM + fila/reconciliação em dry-run.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `ed1d5ff18e3c376cd0aafaf267f134f5c73919df`; contrato em [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 2026-09-12 — CFG-001 — Configuração transacional e painel autenticado

- **Motivo:** após BOOT-002A comprovar dois boots no mesmo QCOW2 com persistência `boot_count=1 → 2`, iniciar a Fase 1 de configuração persistente e a fundação do painel web sem conceder escrita prematura ao libvirt.
- **Mudou:** novo store em `/var/lib/storos/config` com geração monotônica, histórico por revisão, lock local, validação completa, `expected_generation` para concorrência otimista e rollback que cria nova geração. `storosctl` passa a rotear comandos de configuração/token sem retirar os comandos do agente. Novo `storos-web.service` entrega `/healthz`, painel HTML, `/api/status` e `/api/config`, exige autenticação para dados administrativos e recusa métodos mutáveis. O listener padrão é `127.0.0.1:8080`; exposição sem TLS fora do loopback exige opt-in explícito. `features.vm_write_enabled=true` é rejeitado nesta fase.
- **Segurança:** token administrativo aleatório persiste em `/var/lib/storos/auth/admin.token` com modo `0600`; o service roda sem capabilities, com filesystem protegido e somente `/var/lib/storos` gravável. Nenhum token é embutido na imagem ou documentação.
- **Verificação local:** testes do store e painel passaram, incluindo apply/rollback 1→2→3, conflito de geração, bloqueio de escrita em VM, requisito explícito para LAN sem TLS, persistência/permissão do token, autenticação das APIs e rejeição HTTP 405 para mutações. `check-image.sh` também passa a verificar os módulos, preset, dois services, configuração inicial e modo do token.
- **Verificação remota:** a primeira execução Host agent `34670864403` no commit `49c563e225c4dcbd72ae5413f1c80789b3c5b10a` executou 21 testes; 20 passaram e 1 falhou por typo no próprio teste (`settings['wec']` em vez de `settings['web']`). O corretivo seguinte deixou Host agent `34671066203` e Project continuity `34671066176` verdes no head `c77c676774fe39c7d3fbfa70caabbfe363f747a5`. Nesse mesmo head, Development image `34671066182` confirmou que os dois services foram habilitados pelo preset, mas o smoke check falhou por um caminho digitado como `/usr/lib/system/storos-web.service` em vez de `/usr/lib/systemd/system/storos-web.service`. O corretivo `ed1d5ff18e3c376cd0aafaf267f134f5c73919df` deixou Host agent, Development image e Project continuity verdes; o Bootable media correspondente é analisado na entrada CFG-001A.
- **Limites:** painel ainda somente leitura, sem TLS integrado, RBAC, criação/start/stop de VM, política automática de CPU/RAM ou GPU compartilhada. Nenhum boot físico por USB foi executado.
- **Próximo passo:** validar imagem/boot com `storos-web.service` habilitado, confirmar que config/token sobrevivem ao segundo boot sem expor segredo e então iniciar modelos de configuração de VM + fila/reconciliação ainda com escrita no libvirt bloqueada.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base anterior `250fb9e972ff472376658dbc3ac17a7dd2617ecd`; arquitetura em [docs/ARQUITETURA.md](docs/ARQUITETURA.md) e contrato em [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 2026-09-11 — BOOT-002A — Evidência 1 → 2 e correção do gate

- **Motivo:** o run BOOT-002 provou a persistência básica no mesmo QCOW2, mas o job ficou vermelho por exigir um marcador de prontidão do agente no primeiro boot antes de o timeout TCG terminar.
- **Evidência:** no run `34665914397`, head `3064b5849330e4405cc4dda4a8921f083440389e`, build e QCOW2 passaram. O primeiro console registrou `STOROS_BOOT_STATE boot_count=1`; o segundo registrou `STOROS_BOOT_STATE boot_count=2` com `boot_id` diferente e também `STOROS_AGENT_READY snapshot=written boot_count=2`. Isso demonstra que `/var/lib/storos/boot-state.json` sobreviveu ao segundo boot do mesmo disco.
- **Mudou:** o gate passa a validar persistência pelos dois marcadores `STOROS_BOOT_STATE`, mantém a exigência de `STOROS_AGENT_READY` no segundo boot e grava `boot-console.log` antes das asserções. O timeout TCG por boot sobe de 210 s para 240 s para acomodar a variação observada.
- **Verificação:** Host agent, Development image e Project continuity já passaram no head anterior. O novo `Bootable media` ainda precisa ficar verde para fechar o gate automatizado BOOT-002A.
- **Limites:** persistência básica de estado está comprovada pelos logs; configuração transacional completa, boot físico por USB, painel web e GPU compartilhada continuam pendentes.
- **Próximo passo:** obter o gate corrigido verde e então iniciar configuração persistente transacional e a fundação do painel autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), run `34665914397`, base `3064b5849330e4405cc4dda4a8921f083440389e`.

## 2026-09-11 — BOOT-002 — Persistência entre dois boots no mesmo QCOW2

- **Motivo:** após o primeiro boot completo validado, provar que estado StorOS em `/var/lib/storos` sobrevive a reinicialização real da mesma imagem de disco.
- **Mudou:** `storosctl` ganhou registro persistente do `boot_id` do kernel com escrita atômica/fsync e contador de boots distintos. `storos-agent.service` usa `StateDirectory=storos`, registra o boot antes do daemon e emite `STOROS_AGENT_READY ... boot_count=N` após o primeiro snapshot. O workflow passa a bootar o mesmo QCOW2 duas vezes e exige `boot_count=1` e depois `boot_count=2`.
- **Verificação anterior:** o run `34665004511` no commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce` passou integralmente: build, QCOW2, OVMF/QEMU, agente e upload do disco ficaram verdes. Isso fecha a primeira prova de boot + agente do StorOS em VM descartável.
- **Verificação deste incremento:** testes unitários cobrem incremento único por `boot_id`, permissões do estado e rejeição de ID inválido. A prova de dois boots depende do novo workflow remoto e não deve ser marcada como concluída antes do check verde.
- **Limites:** ainda sem boot físico por USB, painel web ou GPU compartilhada. O contador comprova persistência básica do estado, não ainda a configuração transacional completa da Fase 1.
- **Próximo passo:** obter o workflow de dois boots verde; depois iniciar configuração persistente transacional e painel web autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`.

## 2026-09-11 — BOOT-001B — Preset de primeiro boot e prova do agente

- **Motivo:** o run `34651227029` gerou e validou o QCOW2, iniciou o StorOS via OVMF e chegou ao login serial, mas o primeiro boot executou `systemd preset-all` e removeu `/etc/systemd/system/multi-user.target.wants/storos-agent.service` porque a imagem ainda não tinha política de preset própria.
- **Mudou:** adicionada a política vendor `10-storos.preset` para habilitar `storos-agent.service` no primeiro boot; o Containerfile passa a usar `systemctl preset`; a unidade passa a puxar `virtqemud.socket` e só emite `STOROS_AGENT_READY snapshot=written` no console depois de o primeiro snapshot existir. O CI agora usa esse marcador como prova de boot + agente funcional.
- **Verificação:** o console do run `34651227029` mostrou aplicação de preset, remoção explícita do link do agente e, depois, boot completo até `localhost login:` com `virtqemud`, `sshd` e targets do sistema ativos. A correção foi validada pelo run `34665004511` no commit `12562cefeff3dc3dc3c84891e14a458b70fcd5ce`, que passou inclusive o gate `STOROS_AGENT_READY snapshot=written`.
- **Limites:** ainda não houve boot físico por USB, persistência após reinício, painel web ou teste de GPU. O QCOW2 continua sendo artefato de laboratório.
- **Próximo passo:** validar dois boots no mesmo QCOW2 e persistência em `/var/lib/storos`.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `5b1aff0ce80a9f3b9eadf7017678bdce08d890ef`.

## 2026-09-11 — BOOT-001 — Pipeline QCOW2 e prova automatizada de boot

- **Motivo:** avançar do OCI validado para uma mídia virtual realmente inicializável, sem transformar ISO em requisito do StorOS.
- **Mudou:** workflow `boot-media.yml` para construir a imagem bootc de desenvolvimento, passá-la por um registro local efêmero do runner, gerar QCOW2 com o Image Builder oficial, inicializar o disco em QEMU/TCG e confirmar pelo console serial que o systemd alcançou `storos-agent.service`. Adicionada configuração do Image Builder para console serial e lint bootc no workflow. O workflow roda em push da branch e em pull request para deixar a prova visível no PR.
- **Verificação:** sintaxe Bash e TOML revisadas antes da publicação. O resultado real do build/boot remoto deve ser consultado no workflow disparado pelo incremento; esta entrada não afirma sucesso do boot antes do CI terminar.
- **Limites:** ainda não houve boot físico por USB, persistência após reinício, painel web ou teste de GPU. QCOW2 é artefato de laboratório, não release.
- **Próximo passo:** obter o primeiro workflow verde; se o console comprovar a inicialização do agente StorOS, registrar a evidência e testar persistência/reboot antes de avançar ao painel.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base `83feeec44cbf55a878b503bc03e4a7ceceb8c548`; fluxo descrito em [BOOT_MEDIA.md](docs/BOOT_MEDIA.md).

## 2026-09-11 — DEV-001 — Agente funcional e descoberta de VMs

- **Motivo:** iniciar a parte funcional autorizada por Danilo; evitar a falha de descoberta silenciosa observada no protótipo Guardian.
- **Mudou:** agente Python, CLI storosctl, unidade systemd, snapshot atômico e descoberta de VMs por UUID usando libvirt somente leitura. Integração na imagem e workflow de testes adicionados.
- **Verificação:** 10 testes locais passaram. Ciclo real daemon/CLI local reportou virsh ausente com diagnóstico explícito e código 2. CI executa integração com o driver simulado do libvirt; consultar checks do commit para resultado remoto.
- **Limites:** não houve boot StorOS ou consulta ao host de Danilo; nenhum ajuste de recursos, VM criada ou painel web. Snapshot é temporário, não histórico. Fase 0 permanece aberta.
- **Próximo passo:** confirmar check da imagem, validar boot/serviço e avançar para configuração persistente e painel autenticado.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base ee334162f9aedc8c837b7fb43a2e12ef4bf90eb0; contrato e comandos em docs/AGENT.md.

## 2026-09-11 — PH0-004 — Mídia de boot, sem ISO obrigatória

- **Motivo:** Danilo apontou que o fluxo MOS/Unraid é preparar mídia e inicializar o sistema; o assistente vinha tratando ISO como marco obrigatório.
- **Mudou:** README, roadmap, arquitetura e base Fedora passam a descrever mídia de boot e configuração web. BOOT_MEDIA.md separa OCI, imagem de disco, ZIP e ISO opcional; não presume que uCore rode integralmente em RAM.
- **Referências:** consultados guia oficial de mídia MOS e downloads/instalador Unraid. O Unraid atual também oferece ISO opcional; não registrar ausência universal desse formato.
- **Verificação:** revisão documental e links relativos locais. Sem mudança na receita ou novo teste de boot; builds anteriores continuam como evidência de composição.
- **Próximo passo:** empacotar e testar disco virtual inicializável; definir persistência e comportamento da mídia física.
- **Referência de trabalho:** [PR #2](https://github.com/danilostorm/storos/pull/2), base 1d7b10cd932ce90a339245bffb54a8d3872be3d3. Entradas históricas preservadas.

## 2026-09-11 — PH0-003 — Primeiro build validado e base fixada

- **Mudou:** fixado o digest uCore testado no Containerfile e no workflow; evidências essenciais preservadas em docs/BUILD_EVIDENCE.md.
- **Motivo:** tornar a base de desenvolvimento reproduzível e registrar o primeiro resultado real, seguindo a autorização de continuidade.
- **Verificação:** [build 34632041207](https://github.com/danilostorm/storos/actions/runs/34632041207) passou no commit 0258381f4d3d0982bd9113fdbb331db29fb290a9; QEMU 10.2.2 e libvirt 12.0.0 presentes. Continuidade passou. A fixação do mesmo digest é verificada pelo novo CI deste commit.
- **Limites:** nenhum boot, GPU compartilhada ou instalação; assinatura upstream ainda pendente. Artefato remoto contém evidências, não ISO.
- **Próximo passo:** verificar assinatura da base e adaptar protocolo de boot descartável; não solicitar nova escolha de distribuição.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2); título e descrição do PR atualizados para incluir o protótipo Fedora/uCore.

## 2026-09-11 — PH0-002 — Protótipo Fedora/uCore

- **Motivo:** Danilo autorizou começar com Fedora/uCore (“Fecho pode começar”).
- **Mudou:** Containerfile derivado de ucore-hci, identificação, check de ferramentas e workflow de build com inventário e digest da base; decisão arquitetural registrada.
- **Verificação:** sintaxe shell e continuidade locais; resultado do build remoto deve ser consultado no PR.
- **Limites:** sem boot, instalador, assinatura própria, GPU testada ou mudanças no MOS; receita experimental.
- **Próximo passo:** obter build verde, fixar/verificar base e preparar boot descartável.
- **Referência:** [PR #2](https://github.com/danilostorm/storos/pull/2), base 6fe21efeb5e9b9cc9ce37d50e262e363e252caec.

## 2026-09-11 — PH0-001 — Aprovação e início da Fase 0

- **Decisão:** Danilo aprovou a revisão 2 com “Ta aprovado.”; PR #1 mesclado em `3746474390e96175278ea39bd9b8bf1982d4bb25`.
- **Mudou:** aprovação e progresso alinhados; adicionadas triagem GPU/base, protocolo de duas VMs e coleta de inventário somente leitura.
- **Pesquisa:** matrizes oficiais NVIDIA vGPU, Windows Server GPU-P e AMD GIM, mais alternativas Mesa VirGL/Venus. Placas citadas não homologadas; Linux/Windows tratados separadamente.
- **Verificação:** coletor executado localmente com JSON válido; verificação de continuidade/links. Consultar Actions do PR para resultado remoto.
- **Limites:** nenhum teste físico, driver alterado ou sistema instalado; sem acesso ao host de Danilo. Fase 0 em andamento.
- **Próximo passo:** obter inventário e identificar laboratório; testar combinações reais antes de decidir a base.
- **Referência:** branch `phase0/gpu-feasibility`, baseada no merge do [PR #1](https://github.com/danilostorm/storos/pull/1).

## 2026-09-11 — DOC-002 — Revisão 2 e continuidade

- **Mudou:** foco principal em VMs compartilhando CPU, RAM e GPU; base operacional em aberto; GPU simultânea passa à Fase 0. NAS/Docker/apps tornam-se complementares.
- **Motivo:** orientação explícita de Danilo nesta conversa; ele também pediu histórico para continuidade com outro chat/IA.
- **Documentação:** README, roadmap, arquitetura, referências e aprovação alinhados. Estimativas antigas retiradas até validar a GPU.
- **Continuidade:** AGENTS.md define atualização obrigatória deste arquivo e PROJECT_STATE.md; workflow e script verificam registros e links relativos.
- **Verificação:** revisão de coerência e links locais; testes do verificador com intervalo válido e ausência intencional de registro. Resultado do GitHub Actions deve ser consultado no PR; não presumir sucesso antes da execução.
- **Limites:** nenhum teste de GPU, build de SO, implementação ou alteração no servidor. Execução da Fase 0 ainda pendente.
- **Referência:** [PR #1](https://github.com/danilostorm/storos/pull/1), branch proposal/storos-roadmap. Base anterior: 689871f2d6df26f8c78b4e72a26491de9ffc2588.

## 2026-09-11 — DOC-001 — Planejamento inicial (registro retrospectivo)

- Criados README, roadmap revisão 1, arquitetura, referências e decisões para aprovação.
- Proposta inicial centrada em MOS/Devuan, NAS, virtualização, apps, backup e Workspaces.
- Pesquisa documental de MOS, Proxmox, OMV, Unraid, TrueNAS, CasaOS e ASTER; links locais verificados.
- Publicado no [PR #1](https://github.com/danilostorm/storos/pull/1), commit 689871f2d6df26f8c78b4e72a26491de9ffc2588. Inicialização de main: e09a081e80ab50f841b536905f89269e53cc56ee.
- Sem sistema implementado ou hardware homologado. Prioridades desta revisão foram substituídas por DOC-002; histórico mantido.
