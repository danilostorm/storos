# VM-001 — intenção, planejamento e tarefas dry-run

Este incremento cria a primeira camada de reconciliação de VMs do StorOS, **sem autoridade para alterar o hipervisor**. O agente continua sendo a fonte de estado observado em modo somente leitura; o planner compara esse estado com um documento de intenção e produz somente um plano auditável.

## Intenção de VM v1

O arquivo de intenção é JSON e aceita exatamente estes campos:

```json
{
  "schema_version": 1,
  "uuid": "11111111-2222-3333-4444-555555555555",
  "name": "windows-gamer",
  "desired_state": "running",
  "resources": {
    "vcpus": 8,
    "memory_mib": 16384
  }
}
```

- `uuid` é a identidade estável da VM.
- `name` é validado, mas não substitui o UUID como identidade.
- `desired_state` aceita `running` ou `stopped`.
- `resources.vcpus` é uma quantidade de vCPUs; ainda não define pinning/NUMA.
- `resources.memory_mib` é memória fixa desejada neste contrato inicial; mínimos/máximos dinâmicos pertencem à Fase 2.
- Campos desconhecidos são rejeitados para impedir que parâmetros arbitrários virem comandos implícitos.

## Planner

`storos_vm.py` compara a intenção com o snapshot do [agente](AGENT.md). A saída tem `mode=dry_run`, `can_apply=false`, hash SHA-256 da intenção e do snapshot e uma lista ordenada de ações propostas. Toda ação contém `executable=false`.

Tipos atualmente descritos pelo planner:

- `create_vm`
- `rename_vm`
- `set_vcpus`
- `set_memory`
- `start_vm`
- `shutdown_vm`
- ações de diagnóstico bloqueantes: `refresh_snapshot`, `inspect_inventory`, `inspect_vcpus` e `inspect_memory`

Esses nomes são **descrições de intenção**, não chamadas libvirt. Não existe executor no VM-001.

### Regras de segurança

- A CLI lê o snapshot por `storos_agent.read_snapshot(..., max_age=30)`. Coleta antiga é marcada como `stale` e o planner responde `blocked`/`refresh_snapshot`.
- Se o inventário libvirt estiver `partial` e a VM desejada não aparecer, o planner **não** propõe `create_vm`; a ausência não é considerada comprovada.
- Se vCPU ou memória configurável observada estiverem indisponíveis, o plano fica `blocked` e pede inspeção em vez de supor valores.
- RAM é comparada com `max_memory_reported_kib`, não com `memory_reported_kib`, porque o segundo não representa consumo dos aplicativos e não deve ser usado como configuração desejada.
- Inventário `unavailable`, UUID duplicado ou documento incompatível falham sem gerar plano aplicável.

## Tarefas persistentes

`storos_tasks.py` grava registros em `/var/lib/storos/tasks/<task_id>.json` com escrita temporária, `fsync`, `os.replace` e `fsync` do diretório. O diretório usa modo `0750` e os registros `0640`.

Cada tarefa contém:

- UUID próprio da tarefa;
- horário de criação;
- `kind=vm_reconcile`;
- `mode=dry_run`;
- `executable=false`;
- status `planned`, `blocked` ou `converged`;
- plano completo que originou o registro.

O ledger rejeita qualquer plano que declare `can_apply=true` ou qualquer ação com `executable` diferente de `false`.

## CLI

Gerar plano sem gravar tarefa:

```bash
storosctl vm-plan --intent-file vm.json
```

Por padrão o snapshot é `/run/storos/status.json`. Para um arquivo específico:

```bash
storosctl vm-plan --intent-file vm.json --snapshot /caminho/status.json
```

Registrar a reconciliação dry-run:

```bash
storosctl vm-reconcile-dry-run --intent-file vm.json
```

Consultar o ledger:

```bash
storosctl task-list
storosctl task-show --task-id <uuid>
```

Os testes podem redirecionar o ledger com `--task-root`.

## O que o VM-001 não faz

- Não executa `virsh define`, `start`, `shutdown`, `setvcpus`, `setmem` ou qualquer mutação equivalente.
- Não habilita `features.vm_write_enabled`; a [configuração](CONFIGURATION.md) continua exigindo `false`.
- Não adiciona endpoint web mutável; o painel permanece somente leitura.
- Não implementa discos, rede, firmware, passthrough ou GPU compartilhada.
- Não transforma a lista de ações em autorização. Uma futura camada de aplicação deverá ter locks, precondições, releitura do estado, auditoria, falha verificável e feature gate separado antes de tocar o hipervisor.

A posição dessa camada na arquitetura está registrada em [ARQUITETURA.md](ARQUITETURA.md).
