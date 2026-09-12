# VM-001/VM-002 — intenção persistente, planejamento e tarefas dry-run

Esta camada do StorOS modela o estado desejado de VMs e produz planos auditáveis **sem autoridade para alterar o hipervisor**. O agente continua sendo a fonte do estado observado em modo somente leitura. `features.vm_write_enabled=false` permanece obrigatório e não existe executor libvirt mutável.

## Intenção de VM v1

O contrato aceita exatamente:

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
- `name` não substitui o UUID.
- `desired_state` aceita `running` ou `stopped`.
- `resources.vcpus` ainda não define pinning/NUMA.
- `resources.memory_mib` é memória fixa desejada neste contrato inicial; política dinâmica pertence a uma etapa futura.
- Campos desconhecidos são rejeitados.

## VM-002 — store persistente por UUID

`storos_vm_store.py` persiste a intenção em `/var/lib/storos/vm-intents/<uuid>/`:

- `current.json`: geração ativa;
- `revisions/000001.json`, `000002.json`, ...: histórico imutável por geração;
- `.lock`: lock exclusivo da VM durante alteração do store.

Cada registro contém `generation`, `updated_at`, `intent_sha256`, `intent` e `reason`. O SHA-256 é recalculado ao ler o registro; adulteração do conteúdo/hash faz a leitura falhar.

### Concorrência otimista

`expected_generation` evita que um cliente sobrescreva silenciosamente uma versão que mudou desde sua leitura.

- criação pode usar `expected_generation=0` para exigir que a VM ainda não possua intenção persistida;
- atualização pode informar a geração corrente;
- divergência gera conflito e nenhuma nova revisão é publicada.

Rollback não reescreve o histórico. A revisão escolhida vira o conteúdo de uma **nova geração**, preservando a linha do tempo.

## Planner

`storos_vm.py` compara a intenção com o snapshot do agente. A saída sempre contém:

- `mode=dry_run`;
- `can_apply=false`;
- `intent_sha256`;
- `snapshot_sha256`;
- lista ordenada de ações em que cada item contém `executable=false`.

Tipos atualmente descritos:

- `create_vm`;
- `rename_vm`;
- `set_vcpus`;
- `set_memory`;
- `start_vm`;
- `shutdown_vm`;
- diagnósticos bloqueantes `refresh_snapshot`, `inspect_inventory`, `inspect_vcpus` e `inspect_memory`.

Esses nomes são descrições de intenção, não chamadas libvirt.

### Regras de segurança do planner

- A CLI lê o snapshot com `read_snapshot(..., max_age=30)`.
- Snapshot stale bloqueia a reconciliação.
- Inventário `partial` sem a VM não prova ausência e não permite propor `create_vm`.
- vCPU ou memória configurável ausentes geram inspeção bloqueante em vez de suposição.
- RAM é comparada com `max_memory_reported_kib`, não com memória usada pelo guest.
- Inventário indisponível, UUID duplicado ou schema incompatível falham fechados.

## Tarefas dry-run v2

`storos_tasks.py` grava `/var/lib/storos/tasks/<task_id>.json` com escrita temporária, `fsync`, `os.replace` e `fsync` do diretório. O diretório usa `0750`, arquivos `0640` e locks por VM ficam em `/var/lib/storos/tasks/.locks/<vm_uuid>.lock` com `0600`.

Cada tarefa contém:

- UUID da tarefa;
- UUID da VM;
- horário de criação;
- `kind=vm_reconcile`;
- `mode=dry_run`;
- `executable=false`;
- status `planned`, `blocked` ou `converged`;
- plano completo;
- precondições que vinculam a tarefa à geração/hash da intenção e ao hash do snapshot observado.

Exemplo de precondições:

```json
{
  "intent_generation": 3,
  "intent_sha256": "...",
  "snapshot_sha256": "..."
}
```

O ledger rejeita plano aplicável, ação executável ou divergência entre os hashes do plano e as precondições. Isso ainda **não autoriza aplicação futura**: um executor real deverá reler e revalidar todas as precondições imediatamente antes de qualquer mutação.

## CLI

Persistir uma intenção nova exigindo ausência anterior:

```bash
storosctl vm-intent-apply --intent-file vm.json --expected-generation 0
```

Consultar estado e histórico:

```bash
storosctl vm-intent-show --vm-uuid <uuid>
storosctl vm-intent-history --vm-uuid <uuid>
storosctl vm-intent-list
```

Atualizar com concorrência otimista:

```bash
storosctl vm-intent-apply --intent-file vm.json --expected-generation 3
```

Rollback por nova geração:

```bash
storosctl vm-intent-rollback --vm-uuid <uuid> --target-generation 1 --expected-generation 3
```

`vm-plan` pode usar um arquivo ad hoc para inspeção ou uma intenção persistida:

```bash
storosctl vm-plan --intent-file vm.json
storosctl vm-plan --vm-uuid <uuid>
```

Registrar reconciliação exige uma intenção persistida, para que a tarefa carregue geração/hash verificáveis:

```bash
storosctl vm-reconcile-dry-run --vm-uuid <uuid>
```

Consultar tarefas:

```bash
storosctl task-list
storosctl task-show --task-id <uuid>
```

Testes podem redirecionar os stores com `--intent-root`, `--task-root` e o snapshot com `--snapshot`.

## O que VM-002 não faz

- Não executa `virsh define`, `start`, `shutdown`, `setvcpus`, `setmem` ou mutação equivalente.
- Não habilita `features.vm_write_enabled`.
- Não adiciona worker/executor.
- Não torna o painel web mutável.
- Não implementa discos, rede, firmware, passthrough ou GPU compartilhada.
- Não transforma lock/precondição em autorização; eles são fundação para uma futura camada de execução, que continuará exigindo autenticação, feature gate, capacidade, releitura do estado, timeout, verificação posterior e auditoria.

A posição dessa camada na arquitetura está registrada em [ARQUITETURA.md](ARQUITETURA.md).
