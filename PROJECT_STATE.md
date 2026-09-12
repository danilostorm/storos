# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, lote **VM-004A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, PR #2 aberto e não autorizado para merge.
- VM-002, WEB-VM-001 e VM-003A permanecem fechados.
- VM-003B está fechado funcional e documentalmente.
- Head funcional VM-003B: `a8e0e9895efd24e4814c87297feefb34e5d123bb`.
- Head documental VM-003B: `874db3cb783bc4c18e9ca0c42f46963d06480f86`.
- VM-004A está em implementação e validação remota; ainda não é executor.
- Primeira publicação VM-004A: `f3f1b1a5983019214cf5ebca32cbee6492d8d0a1`.
- A flag de escrita em VM continua obrigatoriamente desabilitada.
- Nenhum backend mutável, endpoint web de escrita ou autorização de aplicação foi introduzido.
- Fase 0 continua aberta para laboratório físico/GPU.

## VM-003B — fechamento documental confirmado

O head documental `874db3cb783bc4c18e9ca0c42f46963d06480f86` repetiu os quatro gates:

- Project continuity `34717404728`: verde;
- Host agent `34717404729`: 63/63 testes;
- Development image `34717404730`: verde;
- Bootable media `34717404733`, job `103617073406`: verde.

Artefatos principais:

- `image-evidence` ID `10305900646`, digest `sha256:4f609548ae0aa0b98941ad59dd9420136b1c46e2ff18ec92210adb659636198e`;
- QCOW2 SHA-256 `5af00fe1802072a080f3ce2cfa94d2d62312d037ecebbe67132f4fecdd8a8998`;
- `storos-boot-evidence` ID `10305392144`, digest `sha256:eaa1e78cda0ba7103e87f1e1d6d31bbd7dbf74d330358f9e74df6f2cba70fba2`;
- `storos-qcow2` ID `10305182438`, digest `sha256:0a9c20020afca1054788eff4de88f8301cc65928a6c132e3c1b437c172b29996`.

O mesmo QCOW2 foi inicializado duas vezes e comprovou os três marcadores de boot/persistência já usados pelo projeto.

## VM-004A — preflight fail-closed

Objetivo: materializar a fronteira de segurança imediatamente anterior a um futuro executor, ainda sem capacidade de executar mudanças.

A decisão está documentada em `docs/VM_PREFLIGHT.md`.

O lote adiciona:

- fingerprints semânticos versionados para snapshot e plano;
- ledger schema 3 com geração/hash da intenção, hash legado e fingerprints estáveis;
- leitura backward-compatible de tarefas schema 2;
- locks determinísticos por VM/recurso;
- releitura de tarefa, intenção, snapshot fresco e configuração sob lock;
- detecção de drift de intenção, snapshot e plano;
- auditoria persistente de preflight;
- CLI de preflight e leitura de seus registros;
- smoke da imagem exigindo resultado bloqueado.

### Bloqueios deliberados

Mesmo com tarefa consistente, o VM-004A registra que o gate de escrita, a autorização e o backend mutável não estão disponíveis. Todo resultado continua bloqueado, sem possibilidade de execução.

## Primeira validação remota VM-004A

No head `f3f1b1a5983019214cf5ebca32cbee6492d8d0a1`:

- Project continuity `34720322042`, job `103624880437`: verde.
- Host agent `34720322040`, job `103624880382`: falhou no harness de teste, não na lógica do preflight.
- Os testes anteriores e os novos testes de fingerprints passaram antes da falha.
- O `unittest` encontrou um helper local chamado `run(self, paths, task_id)`, que sobrescreveu `unittest.TestCase.run()` e causou `TypeError` antes de executar os métodos de teste da classe.
- Correção: renomear o helper para `_run_preflight()` e atualizar suas chamadas.
- O caso que garante rejeição de ação marcada executável continua coberto na fronteira do ledger em `tests/test_tasks.py`; o preflight continua coberto para ação desconhecida, drift, stale e bloqueios deliberados.
- Development image e Bootable media do head anterior não serão usados como evidência final; o head corretivo deve repetir os quatro gates.

## Segurança preservada

- Escrita em VMs continua desabilitada.
- Sem executor ou worker mutável.
- Sem endpoint web de aplicação.
- Sem autorização de escrita.
- Sem remoção automática de hardware não gerenciado.
- Sem gerenciamento de Secure Boot/NVRAM.
- Sem passthrough, SR-IOV, mediated devices ou GPU.
- Sem boot físico USB.
- QCOW2 continua artefato de laboratório.

## Validação pendente

VM-004A só poderá ser fechado após o head corretivo passar:

1. Project continuity;
2. suíte integral;
3. Development image com o novo smoke;
4. Bootable media com dois boots do mesmo QCOW2;
5. comparação do changelog confirmando histórico somente aditivo.

Qualquer falha deve ser corrigida na causa, sem reduzir critérios.

## Continuidade

- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` e `PROJECT_STATE.md` no mesmo lote.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- Não mesclar o PR #2 sem instrução explícita.
