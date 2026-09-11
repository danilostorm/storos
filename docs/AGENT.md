# Primeiro componente funcional: agente do host

O StorOS passa a incluir `storosctl` e o serviço `storos-agent`. Esta é a primeira parte executável da gestão de VMs: inventário e descoberta somente leitura. O painel web e os ajustes automáticos serão consumidores futuros desses dados.

## O que funciona neste componente

- Consulta do inventário Linux: CPU lógica, RAM total, kernel e dispositivos gráficos encontrados.
- Descoberta de VMs ligadas e desligadas em `qemu:///system`, sem precisar ativar políticas ou cadastrá-las novamente.
- Identificação por UUID; renomear a VM não troca sua identidade.
- Estado, vCPUs e valores de memória informados pelo libvirt. Esses valores de RAM não medem consumo de aplicativos nem comprovam balloon funcionando.
- Diagnósticos distintos para conexão indisponível, inventário vazio, resposta parcial e coleta antiga.
- Atualização periódica e escrita atômica do snapshot local. O serviço é incluído e habilitado na imagem de desenvolvimento; não foi iniciado no servidor de Danilo.

## Interface inicial

Na imagem StorOS construída, os comandos administrativos são:

```sh
sudo storosctl discover
sudo storosctl status
sudo storosctl status --json
```

`discover` consulta o host diretamente. `status` lê a última coleta em `/run/storos/status.json`; precisa de permissão para esse arquivo. A consulta retorna código 2 se o inventário estiver incompleto, indisponível ou antigo. Somente consulta completa e atual retorna 0. JSON usa `schema_version: 1`.

O diretório em `/run` é temporário. As VMs continuam registradas pelo libvirt; o agente redescobre os UUIDs após reiniciar. Não há banco de políticas ou histórico persistente neste componente.

O serviço consulta a cada 10 segundos após a coleta, com orçamento de 20 segundos por descoberta e até 5 segundos por comando. A interface considera antigos os snapshots com mais de 30 segundos, ou com horário excessivamente no futuro. Até 1024 VMs por coleta; truncamento ou desaparecimento de VM gera estado parcial.

## Desenvolvimento e validação

Sem instalar nada no host, dentro do checkout:

```sh
PYTHONPATH=src:scripts python3 src/storos_agent.py discover --json
PYTHONPATH=src:scripts python3 -m unittest discover -s tests -v
```

O primeiro comando informa libvirt indisponível se a ferramenta, socket ou permissão não existir; não substitui isso por uma lista vazia de sucesso.

O check da imagem executa `storosctl discover --uri test:///default --json` contra o [driver de teste oficial do libvirt](https://libvirt.org/drvtest.html). Esse resultado tem `source: simulation`: testa a integração com a ferramenta instalada, sem iniciar uma VM real. A conexão real usa [virsh somente leitura](https://libvirt.org/manpages/virsh.html).

Dez testes locais cobrem identidade/renomeação, VM desligada, ausência de conexão, lista vazia, VM desaparecendo, resposta inválida, timeout, comandos somente leitura, snapshot antigo e preservação do arquivo anterior em falha de escrita. Também foi executado o ciclo `daemon --once` e leitura pela CLI neste ambiente: `missing_virsh` reportado corretamente.

## Limites e próximo incremento

Não existe servidor HTTP ou porta aberta por esse agente. Ele não cria, inicia ou altera VMs; CPU/RAM/GPU automáticas ainda não estão implementadas. O serviço systemd em boot real, SELinux e permissões do socket libvirt precisam ser testados no sistema inicializado. O check de habilitação da unidade durante o build não comprova sua execução em boot.

O próximo incremento é validar boot e agente na VM descartável, depois adicionar configuração persistente e interface web autenticada. A futura interface deve mostrar coleta antiga e erro de conexão, sem transformar falha em “nenhuma VM”.
