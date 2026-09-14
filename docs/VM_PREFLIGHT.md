# VM-004A — Preflight de execução sem executor

VM-004A cria a fronteira de segurança entre o ledger de reconciliação e um
futuro adaptador mutável. **Não executa ações de VM.** O resultado de preflight
é sempre `can_execute=false` e `executed=false` nesta etapa.

## Objetivo

Antes de existir qualquer caminho `JOBS → COMPUTE` mutável, uma tarefa precisa
ser relida sob lock e confrontada com a intenção atual, o snapshot observado
fresco e a configuração ativa. Divergência não é corrigida automaticamente:
o preflight falha fechado e exige novo planejamento.

## Tarefas e compatibilidade

O ledger passa a gravar novas tarefas como schema 3. Tarefas históricas schema
2 continuam legíveis por `task-show`/API, mas são inelegíveis ao preflight
porque não possuem fingerprints semânticos estáveis.

Schema 3 preserva as precondições existentes:

- `intent_generation`;
- `intent_sha256`;
- `snapshot_sha256` legado, mantido para auditoria.

E acrescenta:

- `snapshot_fingerprint_version=1`;
- `snapshot_fingerprint_sha256`;
- `plan_fingerprint_version=1`;
- `plan_fingerprint_sha256`.

O `snapshot_sha256` legado inclui a visão completa recebida pelo planner,
inclusive campos derivados de frescor. Ele não é removido nem reinterpretado.
O novo fingerprint de snapshot exclui apenas campos temporais/derivados
(`collection_started_at`, `collected_at`, `age_seconds`, `stale`) e ordena VMs
por UUID e erros de forma canônica. Assim, reler o mesmo estado alguns segundos
depois não cria drift falso, enquanto mudanças observadas continuam alterando
o fingerprint.

O fingerprint de plano exclui o hash legado do snapshot e a idade derivada,
mas mantém intenção, estado, ações, warnings e o fingerprint semântico do
snapshot.

## Lock de preflight

`/var/lib/storos/preflight/.locks/` usa locks exclusivos locais. As chaves de
recurso são derivadas somente do plano validado e incluem:

- `vm:<uuid>` sempre;
- `firmware:<uuid>` quando aplicável;
- `disk:<uuid>:<target>` para disco gerenciado;
- `interface:<mac>` para interface gerenciada.

Os nomes dos arquivos de lock são SHA-256 das chaves, evitando usar conteúdo
da tarefa como caminho. Locks são adquiridos em ordem determinística para
evitar deadlock entre preflights concorrentes.

## Revalidação sob lock

Depois de obter os locks, o preflight relê:

1. a tarefa persistida;
2. a intenção corrente;
3. o snapshot pelo mesmo `read_snapshot(..., max_age=30)`;
4. a configuração ativa.

Em seguida recalcula o plano com `plan_vm()` e os fingerprints estáveis.

Bloqueios explícitos cobrem, entre outros:

- tarefa schema 2 sem precondições estáveis;
- geração/hash de intenção divergentes;
- UUID divergente;
- snapshot stale;
- mudança semântica do snapshot;
- mudança semântica do plano;
- tarefa ou plano fora de `planned/changes_planned`;
- ação bloqueante;
- tipo de ação fora da whitelist VM-004A.

A whitelist contém apenas as ações já descritas pelo planner:
`create_vm`, `rename_vm`, `set_vcpus`, `set_memory`, `start_vm`,
`shutdown_vm`, `set_firmware_mode`, `attach_disk`, `reconfigure_disk`,
`attach_interface` e `reconfigure_interface`.

## Bloqueios deliberados do VM-004A

Mesmo quando todas as precondições coincidem, três requisitos permanecem
obrigatoriamente falsos:

- `feature_gate_enabled=false`;
- `authorization_granted=false`;
- `mutating_backend_available=false`.

`storos_config.py` continua rejeitando `features.vm_write_enabled=true`.
VM-004A não cria mecanismo de autorização e não contém adaptador libvirt
mutável. Portanto não existe caminho de código capaz de transformar um
preflight verde em execução.

## Auditoria

Cada tentativa válida de preflight é persistida em
`/var/lib/storos/preflight/<preflight_id>.json`, com modo `0640`, contendo:

- tarefa/VM;
- momento da checagem;
- requisitos;
- chaves de recurso bloqueadas;
- blockers codificados;
- geração/hash da intenção relida;
- idade/frescor do snapshot;
- fingerprints recalculados;
- estado/tipos de ação do plano atual.

Credenciais, token administrativo e XML bruto não são gravados.

Comandos:

```text
storosctl vm-preflight --task-id <uuid>
storosctl preflight-list
storosctl preflight-show --preflight-id <uuid>
```

Esses comandos são locais e auditáveis. O painel permanece somente leitura.

## Fora do escopo

VM-004A não implementa:

- `virsh define`, start, shutdown, hotplug ou qualquer mutação libvirt;
- autorização de usuário para aplicar tarefas;
- feature gate habilitável;
- confirmação pós-mudança;
- rollback de mutação;
- Secure Boot/NVRAM gerenciado;
- passthrough, SR-IOV, mediated devices ou GPU;
- boot físico USB.

A etapa seguinte só poderá discutir um adaptador mutável depois de os gates
remotos deste preflight ficarem verdes e de existir um contrato separado para
autorização, capacidade e verificação pós-aplicação.
