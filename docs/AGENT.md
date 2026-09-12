# Agente do host e inventário observado

O StorOS inclui `storosctl` e o serviço `storos-agent`. O agente é a fronteira de **observação somente leitura** do hipervisor: coleta inventário local, redescobre VMs por UUID e grava um snapshot tipado consumido pela CLI, pelo planner dry-run e pelo painel autenticado.

Ele não cria, inicia, para, redefine ou altera recursos de VMs. Todas as consultas ao libvirt continuam locais e usam `virsh --readonly --no-pkttyagent`.

## O que funciona neste componente

- Consulta do inventário Linux: CPU lógica, RAM total, kernel e dispositivos gráficos encontrados.
- Descoberta de VMs ligadas e desligadas em `qemu:///system`, sem precisar ativar políticas ou cadastrá-las novamente.
- Identificação por UUID; renomear a VM não troca sua identidade.
- Estado, vCPUs e valores de memória informados pelo libvirt. Esses valores de RAM não medem consumo de aplicativos nem comprovam balloon funcionando.
- Observação tipada do hardware virtual persistente por `virsh dumpxml --inactive`: firmware, Secure Boot quando declarado, presença de NVRAM, discos e interfaces de rede.
- Diagnósticos distintos para conexão indisponível, inventário vazio, identidade parcial, hardware virtual indisponível e coleta antiga.
- Atualização periódica e escrita atômica do snapshot local em `/run/storos/status.json`.

### Hardware virtual observado

O incremento VM-003A adiciona, por VM, um objeto `hardware` sem mudar o `schema_version: 1` do snapshot. A extensão é aditiva para preservar consumidores existentes.

Quando disponível, `hardware.status=ok` contém:

- `firmware.mode`: `efi`, `bios` ou `unknown`;
- `firmware.secure_boot`: `true`, `false` ou `null` quando o XML não permite concluir;
- `firmware.nvram_present`;
- `disks[]`: tipo/dispositivo, target e bus, origem, formato, somente leitura e ordem de boot quando declarada;
- `interfaces[]`: tipo, MAC, origem, modelo, target e estado do link quando declarados.

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

O check da imagem executa descoberta contra `test:///default`, usando o driver de teste do libvirt. Esse resultado tem `source: simulation`: testa a integração e o parsing com as ferramentas realmente instaladas na imagem, sem certificar uma VM física ou o hardware do Danilo.

No incremento VM-003A, a suíte remota passou **50/50 testes** no run Host agent `34713412563`. A cobertura inclui identidade/renomeação, VM desligada, ausência de conexão, lista vazia, VM desaparecendo, resposta inválida, timeout, comandos somente leitura, snapshot antigo, escrita atômica, parsing de firmware/discos/interfaces, rejeição de UUID divergente/declaração XML e preservação da VM como `partial` quando apenas a leitura de hardware falha.

O agente e o painel já foram comprovados em boots virtuais anteriores do mesmo QCOW2. Isso valida integração funcional em laboratório QEMU/TCG, não instalação física por USB nem compatibilidade de GPU.

## Limites atuais

- Nenhuma consulta do agente concede autoridade de escrita ao libvirt.
- `features.vm_write_enabled=false` continua obrigatório no control plane.
- O contrato de intenção/planner ainda não usa firmware, discos ou rede; VM-003A apenas observa esses campos.
- O agente não mede ainda capacidade dinâmica de CPU/RAM nem suporte real a balloon/hotplug.
- Passthrough, mediated devices, SR-IOV/vGPU e compartilhamento simultâneo de GPU não são inferidos a partir do XML básico.
- RTX 3080 Ti/RX 550 continuam sem homologação física.

O próximo passo é fechar os gates de imagem/boot do VM-003A. Só depois o VM-003B pode ampliar o contrato de intenção e o planner **ainda dry-run** para um subconjunto de firmware/discos/rede, mantendo qualquer executor real separado e bloqueado.
