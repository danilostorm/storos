# VM-003A — observação tipada de hardware virtual

## Decisão

Antes de ampliar a intenção ou o planner para firmware, discos e rede, o StorOS precisa observar esses recursos de forma confiável. O VM-003A modifica somente a fronteira de observação do hipervisor: depois de ler identidade, estado, vCPU e memória, o agente consulta a definição persistente da VM em modo somente leitura e converte um subconjunto para dados tipados.

Nenhuma autoridade de comando é adicionada. `features.vm_write_enabled=false` continua obrigatório e o planner permanece `dry_run`.

## Contrato observado

O snapshot continua em `schema_version: 1`. A extensão é aditiva: cada VM pode conter `hardware`.

Quando a coleta é válida, o agente observa:

- firmware: modo EFI/BIOS/desconhecido, Secure Boot quando explicitamente determinável e presença de NVRAM;
- discos: dispositivo/tipo, target e barramento, origem, formato, somente leitura e ordem de boot quando declarada;
- interfaces: tipo, MAC, origem, modelo, target e estado do link quando declarado.

A definição persistente é preferida ao estado transitório de runtime porque o próximo planner precisará comparar intenção com configuração durável.

## Falha fechada

Identidade e hardware têm falhas separadas.

- Se a identidade básica da VM não puder ser validada, a VM não é materializada naquele ciclo e o inventário fica parcial.
- Se a identidade for válida, mas a definição de hardware não puder ser lida ou validada, a VM continua no inventário com `hardware.status=unavailable` e o inventário geral fica `partial`.
- Hardware não observado nunca é traduzido como hardware ausente.

O parser limita o tamanho do documento, valida o UUID e recusa construções XML fora do subconjunto seguro aceito pelo agente.

## Compatibilidade

O `schema_version` do snapshot permanece 1 para não quebrar o planner e o painel já existentes. Consumidores antigos podem ignorar o campo `hardware`. VM-003A não altera o schema de intenção persistida e não cria ações novas no ledger.

## Próxima fronteira

VM-003B poderá adicionar um subconjunto de firmware, discos e rede ao contrato de intenção e ao planner, mas ainda exclusivamente em validação e `dry_run`. Antes disso, os gates de testes, imagem e boot do VM-003A precisam ficar verdes.

Qualquer escrita real no libvirt permanece uma etapa posterior separada, sujeita a autenticação, feature gate explícito, locks, precondições, releitura de estado, capacidade, timeout, verificação observada e auditoria.

## Limitações

Este incremento não comprova hotplug, passthrough, SR-IOV, mediated devices, vGPU ou compartilhamento simultâneo de GPU. Também não substitui teste físico por USB ou homologação das GPUs do laboratório.
