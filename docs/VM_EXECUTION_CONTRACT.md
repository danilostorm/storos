# VM-004B — Contrato de execução deny-only

## Objetivo

Formalizar a futura fronteira `JOBS → COMPUTE` antes de existir qualquer executor real. Esta etapa define tipos de ação, capacidades do backend, decisão de autorização e forma do resultado sem habilitar mutação de VM.

VM-004B é **contract-only**. O nome passa a identificar esta subtarefa a partir desta decisão arquitetural; não altera as fases do roadmap.

## Invariantes

- `features.vm_write_enabled=false` continua obrigatório e não pode ser habilitado por este contrato.
- Não existe worker/executor.
- Não existe comando CLI de apply/execute.
- Não existe endpoint web mutável.
- Não existe chamada `virsh`/libvirt mutável nesta camada.
- O preflight VM-004A continua bloqueando por feature gate, autorização e backend mutável indisponíveis.
- Um resultado desta etapa nunca pode declarar `executed=true`, `applied=true` ou estado pós-aplicação.

## Catálogo fechado de ações

`storos_execution_contract.py` formaliza somente as ações não bloqueantes que o planner atual já sabe descrever:

- `create_vm`
- `rename_vm`
- `set_vcpus`
- `set_memory`
- `start_vm`
- `shutdown_vm`
- `set_firmware_mode`
- `attach_disk`
- `reconfigure_disk`
- `attach_interface`
- `reconfigure_interface`

Ações de inspeção/bloqueio não pertencem ao adaptador mutável. Uma ação desconhecida é rejeitada em vez de cair em shell genérico ou comportamento implícito.

## Payload tipado

Antes de uma ação poder atravessar uma futura implementação do adaptador, o contrato valida a forma descrita pelo planner:

- criação: UUID, nome, vCPU, RAM e hardware v2 opcional;
- rename: nomes anterior/novo;
- CPU: inteiros dentro dos limites já usados pelo planner;
- RAM: MiB desejado e forma observada compatível;
- lifecycle: apenas transições conhecidas `stopped→running`, `absent→running` e `running→stopped`;
- firmware: `bios|efi`;
- discos: target, bus, source local absoluto, formato, readonly e boot order;
- interfaces: MAC, `network|bridge`, source correspondente e modelo.

A ação deve continuar `executable=false` e `blocked=false`. O contrato não transforma o plano dry-run em tarefa executável.

## Capacidades do backend

O único backend desta etapa é lógico e se identifica como:

- `backend_id=disabled`;
- `backend_kind=none`;
- `mutating_available=false`;
- todas as ações com `supported=false` e `reason_code=contract_only`.

Isso separa o formato futuro da capacidade real. Uma implementação libvirt mutável deverá aparecer em etapa posterior e terá de declarar capacidades ação por ação; não pode herdar suporte por suposição.

## Identidade e autorização

O contrato recebe uma identidade textual explícita, tipo de ação e UUID da VM. A decisão atual é sempre:

- `granted=false`;
- `reason_code=authorization_unavailable`;
- `scopes=[]`.

O token administrativo atual autentica leitura do painel; ele **não** é promovido implicitamente a autorização de escrita. RBAC/scopes e a origem confiável da identidade precisam de etapa própria antes de qualquer grant.

## Resultado e verificação futura

VM-004B só aceita resultado `status=not_attempted`, `executed=false`, `applied=false` e `observed_after_apply=null`.

O catálogo já documenta a verificação esperada e uma classificação de compensação para cada ação. Essas descrições não executam rollback. Uma etapa mutável futura deverá distinguir:

1. comando aceito pelo backend;
2. resultado da chamada;
3. estado observado após nova coleta;
4. convergência ou divergência em relação à intenção;
5. compensação permitida e segura, quando existir.

Falha de aplicação nunca deverá ser registrada como sucesso só porque uma chamada retornou sem erro.

## Relação com VM-004A

VM-004A continua responsável por locks, releitura de tarefa/intenção/snapshot/configuração, fingerprints, drift e auditoria de preflight. VM-004B não remove nem satisfaz os três bloqueios deliberados do preflight; apenas define o formato que uma etapa posterior terá de implementar para autorização e backend.

## Critério de aceite deste lote

- catálogo do contrato coincide com a whitelist de ações mutáveis conhecida pelo preflight;
- payloads válidos do planner são aceitos e formas inválidas/bloqueadas são rejeitadas;
- ação desconhecida é rejeitada;
- backend anuncia zero capacidades mutáveis;
- autorização é sempre negada;
- resultado forjado como aplicado/executado é rejeitado;
- módulo entra na imagem de desenvolvimento e o build prova o modo deny-only;
- suíte, continuidade, Development image e Bootable media ficam verdes no head publicado.

## Fora do escopo

Executor/worker, `virsh define/start/shutdown`, hotplug, delete/detach automático, Secure Boot/NVRAM gerenciado, passthrough, SR-IOV, mediated devices, GPU compartilhada, política dinâmica CPU/RAM, RBAC real, endpoint web de aplicação e boot físico USB continuam fora deste lote.
