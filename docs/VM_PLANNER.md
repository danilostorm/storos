# VM-001/VM-002/VM-003B — intenção persistente, planejamento e tarefas dry-run

Esta camada do StorOS modela o estado desejado de VMs e produz planos auditáveis **sem autoridade para alterar o hipervisor**. O agente continua sendo a fonte do estado observado em modo somente leitura. `features.vm_write_enabled=false` permanece obrigatório e não existe executor libvirt mutável.

## Compatibilidade de schema

O StorOS aceita intenções de VM **schema 1 e schema 2**.

A compatibilidade é deliberada: um registro schema 1 já persistido é validado e devolvido no mesmo formato schema 1, sem campo `hardware` adicionado implicitamente. Isso preserva o `intent_sha256`, revisões antigas, rollback e precondições já gravadas. O store não migra uma intenção histórica silenciosamente.

Novas intenções podem usar schema 2. O schema do store continua independente do schema interno da intenção.

## Intenção de VM v1 — legado suportado

O contrato v1 continua aceitando exatamente:

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
- `resources.memory_mib` é memória fixa desejada nesta etapa.
- Campos desconhecidos são rejeitados.
- O planner v1 ignora o campo observado `hardware`; portanto snapshots novos não quebram intenções históricas.

## Intenção de VM v2 — subconjunto de hardware gerenciado

O schema 2 mantém todos os campos do v1 e acrescenta `hardware`:

```json
{
  "schema_version": 2,
  "uuid": "11111111-2222-3333-4444-555555555555",
  "name": "windows-gamer",
  "desired_state": "running",
  "resources": {
    "vcpus": 8,
    "memory_mib": 16384
  },
  "hardware": {
    "firmware": {
      "mode": "efi"
    },
    "disks": [
      {
        "target": "vda",
        "bus": "virtio",
        "source": {
          "kind": "file",
          "value": "/var/lib/libvirt/images/windows-gamer.qcow2"
        },
        "format": "qcow2",
        "readonly": false,
        "boot_order": 1
      }
    ],
    "interfaces": [
      {
        "mac": "52:54:00:12:34:56",
        "type": "network",
        "source": {
          "network": "default"
        },
        "model": "virtio"
      }
    ]
  }
}
```

### Firmware gerenciado

O v2 gerencia somente o modo abstrato:

- `bios`;
- `efi`.

`hardware.firmware` pode ser `null` para não gerenciar firmware. Caminhos de OVMF/loader/NVRAM do host **não entram na intenção**. Secure Boot, enrolled keys e regeneração de NVRAM também não fazem parte do VM-003B.

### Discos gerenciados

VM-003B aceita no máximo 64 discos gerenciados. Cada disco usa `target` como identidade dentro da intenção e aceita apenas o subconjunto:

- `bus`: `virtio`, `sata` ou `scsi`;
- `source.kind`: `file` ou `block`;
- `source.value`: caminho local absoluto;
- `format`: `raw` ou `qcow2`;
- `readonly`: booleano;
- `boot_order`: inteiro positivo ou `null`.

Targets duplicados são rejeitados. A lista é normalizada por `target`, tornando o hash independente da ordem enviada.

### Interfaces gerenciadas

VM-003B aceita no máximo 64 interfaces gerenciadas. O MAC é a identidade estável do item e é normalizado para minúsculas.

São aceitos apenas:

- `type=network` com `source.network`;
- `type=bridge` com `source.bridge`;
- `model` como token explícito, por exemplo `virtio`.

MACs duplicados são rejeitados e a lista é normalizada por MAC.

### Sem remoção implícita

As listas `hardware.disks` e `hardware.interfaces` representam **o subconjunto que o StorOS está gerenciando**, não uma declaração de que todo hardware extra deve ser removido. Um disco/interface observado que não aparece na intenção v2 é deixado intacto e não produz `detach_*`.

Isso evita que um primeiro contrato de reconciliação trate dispositivo não modelado, mídia temporária ou interface externa como lixo a remover.

## VM-002 — store persistente por UUID

`storos_vm_store.py` persiste a intenção em `/var/lib/storos/vm-intents/<uuid>/`:

- `current.json`: geração ativa;
- `revisions/000001.json`, `000002.json`, ...: histórico imutável por geração;
- `.lock`: lock exclusivo da VM durante alteração do store.

Cada registro contém `generation`, `updated_at`, `intent_sha256`, `intent` e `reason`. O SHA-256 é recalculado ao ler o registro; adulteração do conteúdo/hash faz a leitura falhar.

O store aceita gerações contendo v1 e v2 no mesmo histórico. Rollback de uma geração v2 para uma geração v1 cria nova geração **v1 com o mesmo conteúdo/hash da intenção alvo**, sem promover o documento para v2.

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

Tipos básicos já existentes:

- `create_vm`;
- `rename_vm`;
- `set_vcpus`;
- `set_memory`;
- `start_vm`;
- `shutdown_vm`;
- diagnósticos bloqueantes `refresh_snapshot`, `inspect_inventory`, `inspect_vcpus` e `inspect_memory`.

VM-003B acrescenta descrições **não executáveis**:

- `set_firmware_mode`;
- `attach_disk`;
- `reconfigure_disk`;
- `attach_interface`;
- `reconfigure_interface`;
- bloqueios `inspect_hardware`, `inspect_firmware`, `inspect_disk` e `inspect_interface`.

Esses nomes descrevem diferenças determinísticas. Não são comandos libvirt e nenhum worker os executa.

### Regras de segurança do planner

- A CLI lê o snapshot com `read_snapshot(..., max_age=30)`.
- Snapshot stale bloqueia a reconciliação.
- Inventário `partial` sem a VM não prova ausência e não permite propor `create_vm`.
- vCPU ou memória configurável ausentes geram inspeção bloqueante em vez de suposição.
- RAM é comparada com `max_memory_reported_kib`, não com memória usada pelo guest.
- Intenção v2 de uma VM existente exige `hardware.status=ok`. Hardware ausente/indisponível gera `inspect_hardware` e nenhuma diferença de firmware/disco/rede é inferida.
- Firmware observado como `unknown` gera `inspect_firmware`.
- Disco/interface gerenciado com identidade ambígua ou dados observados insuficientes gera inspeção bloqueante.
- Hardware observado extra que não está no subconjunto gerenciado não é removido.
- Inventário indisponível, UUID duplicado ou schema incompatível falham fechados.

Para uma VM totalmente ausente em inventário saudável, `create_vm.after` pode carregar o bloco hardware v2 como descrição do estado desejado, mas a ação continua `executable=false`.

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

## O que VM-003B não faz

- Não executa `virsh define`, `start`, `shutdown`, `attach-disk`, `attach-interface` ou qualquer mutação equivalente.
- Não habilita `features.vm_write_enabled`.
- Não adiciona worker/executor.
- Não torna o painel web mutável.
- Não remove discos/interfaces observados que não estejam no subconjunto gerenciado.
- Não gerencia Secure Boot, enrolled keys, NVRAM, pinning/NUMA, hotplug, passthrough, SR-IOV, mediated devices ou GPU compartilhada.
- Não codifica caminhos de firmware do host na intenção.
- Não transforma lock/precondição em autorização; eles continuam sendo fundação para uma futura camada de execução, que exigirá autenticação, feature gate, capacidade, releitura do estado, timeout, verificação posterior e auditoria.

A observação usada pelo v2 é definida em [VM_HARDWARE_OBSERVER.md](VM_HARDWARE_OBSERVER.md) e a posição dessa camada na arquitetura está registrada em [ARQUITETURA.md](ARQUITETURA.md).
