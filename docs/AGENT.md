# Agente do host e inventário observado

O StorOS inclui `storosctl` e o serviço `storos-agent`. O agente é a fronteira de **observação somente leitura** do hipervisor: coleta inventário local, redescobre VMs por UUID e grava um snapshot tipado consumido pela CLI, pelo planner dry-run e pelo painel autenticado.

Ele não cria, inicia, para, redefine ou altera recursos de VMs. Todas as consultas ao libvirt continuam locais e usam `virsh --readonly --no-pkttyagent`.

## O que funciona neste componente

- Consulta do inventário Linux: CPU lógica, RAM total, kernel e dispositivos gráficos encontrados.
- Descoberta de VMs ligadas e desligadas em `qemu:///system`, sem precisar ativar políticas ou cadastrá-las novamente.
- Identificação por UUID; renomear a VM não troca sua identidade.
- Estado, vCPUs e valores de memória informados pelo libvirt. Esses valores de RAM não medem consumo de aplicativos nem comprovam balloon funcionando.
- Observação tipada do hardware virtual persistente por `virsh dumpxml --inactive`: firmware, Secure Boot quando explicitamente declarada a feature, presença de NVRAM, discos e interfaces de rede.
- Diagnósticos distintos para conexão indisponível, inventário vazio, identidade parcial, hardware virtual indisponível e coleta antiga.
- Atualização periódica e escrita atômica do snapshot local em `/run/storos/status.json`.

### Hardware virtual observado

O VM-003A adicionou, por VM, um objeto `hardware` sem mudar o `schema_version: 1` do snapshot. A extensão é aditiva para preservar consumidores existentes.

Quando disponível, `hardware.status=ok` contém:

- `firmware.mode`: `efi`, `bios` ou `unknown`;
- `firmware.secure_boot`: `true`, `false` ou `null` quando o XML não permite concluir;
- `firmware.nvram_present`;
- `disks[]`: tipo/dispositivo, target e bus, origem, formato, somente leitura e ordem de boot quando declarada;
- `interfaces[]`: tipo, MAC, origem, modelo, target e estado do link quando declarados.

`loader secure='yes'` **não é tratado como Secure Boot habilitado**. No contrato do libvirt, esse atributo informa que o firmware é capaz de Secure Boot; ele não liga/desliga a feature. O agente só preenche `firmware.secure_boot` quando encontra a feature explícita `firmware/feature name='secure-boot'` com `enabled=yes|no`. Sem essa declaração, o valor fica `null`.

A identidade básica vem de `dominfo`; o hardware vem de `dumpxml --inactive`. Se a identidade puder ser lida mas o XML de hardware falhar, a VM **continua presente** no snapshot, `hardware.status` passa a `unavailable` e o inventário geral vira `partial`. O agente não inventa hardware ausente nem transforma falha de leitura em estado vazio.

O parser valida que o UUID do XML é o UUID consultado, limita o documento a 1 MiB e rejeita declarações `DOCTYPE`/`ENTITY`. Isso reduz superfície de parsing e impede que XML inconsistente seja tratado como observação válida.

## Interface administrativa

Na imagem StorOS construída:

```sh
sudo storosctl discover
sudo storosctl status
sudo storosctl status --json
```

`discover` consulta o host diretamente. `status` lê a última coleta em `/run/storos/status.json`; precisa de permissão para esse arquivo. A consulta retorna código 2 se o inventário estiver incompleto, indisponível ou antigo. Somente consulta completa e atual retorna 0.

O diretório em `/run` é temporário. As VMs continuam registradas pelo libvirt; o agente redescobre UUIDs após reiniciar. Intenções e tarefas persistentes pertencem a componentes separados em `/var/lib/storos`; o agente não as modifica.

O serviço consulta a cada 10 segundos após a coleta, com orçamento de 20 segundos por descoberta e até 5 segundos por comando. A interface considera antigos os snapshots com mais de 30 segundos, ou com horário excessivamente no futuro. Até 1024 VMs por coleta; truncamento, desaparecimento de VM ou falha parcial de hardware gera estado parcial.

## Desenvolvimento e validação

Dentro do checkout:

```sh
PYTHONPATH=src:scripts python3 src/storos_agent.py discover --json
PYTHONPATH=src:scripts python3 -m unittest discover -s tests -v
```

O primeiro comando informa libvirt indisponível se a ferramenta, socket ou permissão não existir; não substitui isso por uma lista vazia de sucesso.

O check da imagem executa descoberta contra `test:///default`, usando o driver de teste do libvirt. Esse resultado tem `source: simulation`: testa a integração e o parsing com as ferramentas realmente instaladas na imagem, sem certificar uma VM física ou hardware do usuário.

VM-003A foi fechado no head `6108e0ec45f79e7a399f7f96733076effe3a2f47`: Host agent passou **50/50 testes**, Development image ficou verde e o Bootable media validou o mesmo QCOW2 em dois boots. VM-003B adiciona testes de compatibilidade v1/v2 e um caso específico garantindo que `loader secure` não seja confundido com Secure Boot efetivamente declarado.

## Consumidores do snapshot

- O painel continua somente leitura.
- Intenções schema 1 continuam ignorando `hardware` para preservar comportamento/hashes históricos.
- Intenções schema 2 podem comparar um subconjunto gerenciado de firmware/discos/interfaces **somente quando `hardware.status=ok`**.
- Hardware indisponível ou inconclusivo deve bloquear a parte correspondente do plano, nunca virar ausência presumida.

O contrato de intenção/planner está em [VM_PLANNER.md](VM_PLANNER.md), e os limites do observador estão em [VM_HARDWARE_OBSERVER.md](VM_HARDWARE_OBSERVER.md).

## Limites atuais

- Nenhuma consulta do agente concede autoridade de escrita ao libvirt.
- `features.vm_write_enabled=false` continua obrigatório no control plane.
- Secure Boot, enrolled keys e regeneração de NVRAM não são gerenciados pelo planner VM-003B.
- O agente não mede ainda capacidade dinâmica de CPU/RAM nem suporte real a balloon/hotplug.
- Passthrough, mediated devices, SR-IOV/vGPU e compartilhamento simultâneo de GPU não são inferidos a partir do XML básico.
- RTX 3080 Ti/RX 550 continuam sem homologação física.
- Boot físico USB continua pendente; QCOW2 é laboratório interno.
