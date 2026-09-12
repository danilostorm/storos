# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, fechamento **VM-003A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002 está fechado remotamente.
- WEB-VM-001 está fechado remotamente no head `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`.
- **VM-003A está fechado remotamente** no head `6108e0ec45f79e7a399f7f96733076effe3a2f47`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## VM-003A — fechamento remoto

O VM-003A acrescentou observação tipada e somente leitura de firmware, discos e interfaces ao snapshot do agente, sem alterar o schema de intenção, sem criar ações aplicáveis e sem habilitar escrita no hipervisor.

No head `6108e0ec45f79e7a399f7f96733076effe3a2f47` os quatro gates aplicáveis ficaram verdes:

- Project continuity `34713932768`: verde.
- Host agent `34713932769`: verde, **50/50 testes**.
- Development image `34713932991`: verde.
- Bootable media `34713932817`, job `103607586216`: verde.

O smoke da imagem confirmou duas vezes, com libvirt 12.0.0 e QEMU 10.2.2 empacotados no StorOS:

`StorOS discovery and virtual hardware observation passed against libvirt test driver (no real VM).`

Esse gate exige ao menos uma VM simulada e `hardware.status=ok`, estrutura tipada de firmware e listas válidas de discos/interfaces; portanto o fechamento não depende apenas de importação sintática do módulo.

O Bootable media gerou e inspecionou o QCOW2 e inicializou **o mesmo disco duas vezes** com o QEMU 10.2.2 da própria imagem StorOS. Foram comprovados:

- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`;
- `boot_count=1 → 2`;
- agente e painel autenticado prontos nos dois boots;
- `config_generation=1` nos dois boots;
- fingerprints de configuração e token preservados entre os boots;
- QCOW2 SHA-256 `d8075fbaa6693d7087db689922741a171b3e752cb1242072ec9f3b5b5ce1b091`;
- `storos-boot-evidence` ID `10304262931`, digest `sha256:5fc0a60aaff96e107512cbf1596d7589e085e5caf5801e8f539b81dc369e3100`;
- `storos-qcow2` ID `10304721991`, digest do artefato `sha256:a191ed814adc020ae79f097231df9c95cf25a7f9de28842d513aaf0343c0c4e4`.

## Contrato observado fechado no VM-003A

`src/storos_agent.py` continua lendo identidade básica por `dominfo` e usa a definição persistente da VM em modo somente leitura para acrescentar `hardware` ao snapshot schema 1:

- firmware EFI/BIOS/desconhecido;
- Secure Boot apenas quando explicitamente determinável;
- presença de NVRAM;
- discos: dispositivo/tipo, target/bus, origem, formato, somente leitura e ordem de boot;
- interfaces: tipo, MAC, origem, modelo, target e estado de link.

Fail-closed permanece obrigatório:

- falha de identidade impede materializar a VM naquele ciclo e usa `scope=identity`;
- falha apenas de hardware preserva a VM com `hardware.status=unavailable`, usa `scope=hardware` e torna o inventário `partial`;
- hardware não observado nunca é convertido em hardware ausente;
- o parser limita o documento, valida UUID e rejeita XML fora do subconjunto aceito.

A decisão arquitetural permanece em [docs/VM_HARDWARE_OBSERVER.md](docs/VM_HARDWARE_OBSERVER.md) e o contrato do agente em [docs/AGENT.md](docs/AGENT.md).

## Segurança preservada

- Todas as consultas do agente ao libvirt continuam somente leitura.
- Nenhum endpoint web ganhou autoridade de escrita.
- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada.
- Planos continuam `mode=dry_run`, `can_apply=false`; ações/tarefas continuam `executable=false`.
- `features.vm_write_enabled=true` continua rejeitado pela configuração.
- O painel continua autenticado e somente leitura; listener padrão permanece no loopback.

## Limitações atuais

- Sem criação/start/stop real de VM pelo control plane StorOS.
- O contrato persistido de intenção continua schema 1 e cobre somente UUID/nome/estado/vCPU/RAM fixa.
- Firmware/discos/rede estão **observados**, mas ainda não são campos de intenção nem inputs de reconciliação.
- Sem política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark de desempenho.
- Nenhum teste físico de GPU compartilhada foi realizado.
- A observação básica de hardware virtual não comprova passthrough, SR-IOV, mediated devices ou vGPU.
- O QCOW2 continua sendo artefato de laboratório, não release para instalação pelo usuário.

## Próxima tarefa concreta — VM-003B

1. Ampliar o contrato de intenção de forma **backward-compatible**, mantendo registros schema 1 válidos e seus hashes históricos intactos.
2. Introduzir um novo schema apenas para novas intenções que incluam um subconjunto estreito e tipado de firmware/discos/rede.
3. Fazer o planner usar esses campos somente quando a observação `hardware.status=ok`; snapshot parcial/ausente deve bloquear em vez de presumir mudanças.
4. Manter todas as novas ações `executable=false`, plano `mode=dry_run` e `can_apply=false`.
5. Não codificar caminhos de firmware do host na intenção; usar abstrações como BIOS/EFI.
6. Adicionar testes de compatibilidade schema 1, hashing/revisões, convergência e fail-closed antes de qualquer exposição web adicional.
7. Só depois dos gates remotos verdes considerar VM-003B fechado. Executor real, GPU e mídia física continuam etapas separadas.

## Continuidade

- O histórico anterior de `CHANGELOG.md` foi restaurado a partir do head validado `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`; as entradas novas permanecem apenas como acréscimos no topo.
- O QCOW2 continua sendo laboratório interno até a base ficar sólida. A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- Danilo autorizou continuar sem pular etapas. Não pedir nova autorização para seguir o roadmap.
- Obedecer `AGENTS.md` em toda publicação.
- **Não mesclar o PR #2 sem instrução explícita.**
