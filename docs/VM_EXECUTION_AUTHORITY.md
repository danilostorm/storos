# VM-004D — identidade local, autorização e capacidades deny-only

## Objetivo

VM-004D acrescenta uma autoridade verificável ao limite futuro `JOBS → COMPUTE` sem criar executor nem habilitar escrita em VMs.

A etapa separa três perguntas:

1. quem é o principal local observado pelo sistema operacional;
2. quais ações e VMs a política permite a esse principal;
3. quais ações o backend declara realmente capazes de mutação.

Uma resposta positiva nas duas primeiras perguntas não autoriza execução enquanto a terceira continuar negativa e `features.vm_write_enabled=false`.

## Identidade

A identidade de execução é separada do token administrativo do painel web. O token web não é promovido a credencial de execução.

O entrypoint persistente usa `geteuid()` e `getegid()` do processo local e compara o par UID/GID com uma política explícita. Identidade desconhecida ou desabilitada falha fechada.

`evaluate_execution_authority()` aceita UID/GID como entrada apenas para avaliação determinística e testes. O caminho persistente `run_execution_authority_check()` obtém esses valores do próprio sistema operacional antes da decisão.

Não há senha, bearer token ou segredo novo neste estágio.
## Política

A política schema 1 contém geração monotônica explícita e uma lista de identidades. Cada identidade possui:

- `identity_id` estável para auditoria;
- `uid` e `gid` locais;
- estado `enabled`;
- scopes `vm:action:<tipo>` ou `vm:action:*`;
- seletores de VM por UUID ou `*`.

Identidades e pares UID/GID duplicados são rejeitados. Ações fora do catálogo VM-004B também são rejeitadas.

O arquivo de política é validado antes de uso e gravado atomicamente com modo `0640`; o diretório usa `0750`. Nesta etapa não existe endpoint web nem comando remoto para alterar a política.

## Autorização

Depois da autenticação local, cada ação é autorizada de forma independente. A decisão exige simultaneamente:

- identidade autenticada e habilitada;
- scope correspondente à ação ou wildcard explícito;
- UUID da VM permitido ou wildcard explícito.

A autorização pode retornar `granted=true`. Isso representa somente a decisão de política; não significa que a ação possa ser aplicada.
## Negociação de capacidades

`DenyOnlyCapabilityProvider` consulta o contrato de backend já existente e preserva:

- `mutating_available=false`;
- todas as ações mutáveis com `supported=false`;
- `apply_method_available=false`;
- ausência física de método `apply`.

Para ações conhecidas, a negociação confirma apenas `contract_supported=true`. `mutating_supported` e `eligible` continuam sempre `false`.

Qualquer provider que exponha `apply`, declare mutação disponível ou torne uma ação elegível é rejeitado pelo VM-004D.

## Decisão e auditoria

A avaliação relê tarefa/preflight compatíveis com VM-004A e exige o mesmo `plan_fingerprint_sha256` na tarefa, plano e observação do preflight.

Cada ação registra separadamente autenticação/autorização, capacidade negociada e um resultado VM-004B `not_attempted`, `executed=false`, `applied=false`.

O registro final permanece:

- `status=denied`;
- `can_execute=false`;
- `executed=false`;
- `capabilities_satisfied=false`;
- `mutating_backend_available=false`;
- `feature_gate_enabled=false`.
Os registros persistidos usam `/var/lib/storos/execution-authority/decisions`, diretório `0750`, arquivos `0640`, escrita atômica e `fsync`.

## Relação com o preflight anterior

O preflight VM-004A continua deliberadamente bloqueado e ainda carrega `authorization_unavailable`. VM-004D não reescreve esse registro nem o transforma em autorização reutilizável.

Isso é intencional: a nova autoridade pode demonstrar que identidade e política estão corretas, mas o conjunto completo ainda deve falhar fechado porque preflight, feature gate e backend mutável não estão habilitados para execução.

Uma futura etapa de aplicação real deverá readquirir locks, reler tarefa/intenção/configuração, obter observação fresca, reautenticar o chamador, reevaluar política e capacidades e só então considerar qualquer mutação. Nenhum admission/authority record antigo pode ser tratado como ticket de execução.

## Fora de escopo

VM-004D não adiciona:

- executor ou worker;
- `virsh`/libvirt mutável;
- endpoint web mutável;
- habilitação de `features.vm_write_enabled`;
- autenticação remota/TLS/RBAC web;
- GPU, passthrough, SR-IOV ou mediated devices;
- boot físico USB.

Uma etapa posterior que introduza backend mutável ou executor exige autorização explícita separada antes da implementação/uso real.
