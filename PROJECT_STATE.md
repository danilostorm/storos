# Estado do projeto — ponto de retomada

Atualizado em **13/09/2026**. Lote atual: **VM-004D preparado para publicação/validação**.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`; PR #2 aberto e **não autorizado para merge**.
- Base do lote: `ca168a5c63a2be9925b7468a18599167ecb7c508`.
- VM-004C está fechado remotamente.
- VM-004D adiciona uma nova fronteira local de decisão, ainda deny-only.
- `features.vm_write_enabled=false` permanece obrigatório.
- Fase 0 segue aberta para laboratório físico/GPU.

## Evidência da base

VM-004C no head `ca168a5c...`: Project continuity `34760366989`; Host agent `34760367022` com **89/89 testes**; Development image `34760367038`; Bootable media `34760367055`.

QCOW2 SHA-256: `a03311a1718e4c73315f62a7aed69efb559c66a2a37dd06ff186c38c6e262cfc`. O mesmo disco iniciou duas vezes e emitiu os marcadores de boot e persistência esperados.

## VM-004D

Detalhes: `docs/VM_EXECUTION_AUTHORITY.md` e `docs/ARQUITETURA.md`.

- Novo módulo `src/storos_execution_authority.py`.
- Novo conjunto de testes `tests/test_execution_authority.py`.
- `Containerfile` inclui o módulo e smoke deny-only.
- Nenhuma ação de VM é executada por esta etapa.

## Verificação local

- **13/13** testes específicos passaram.
- **102/102** testes da suíte integral passaram.
- Verificador de continuidade passou no commit candidato local.
- `git diff --check` não encontrou erros.

## Limitações

- Recursos de execução permanecem fora deste lote.
- CPU/RAM dinâmicas e GPU compartilhada continuam pendentes de etapas posteriores.
- QEMU/TCG de CI não substitui teste físico.

## Próxima tarefa concreta

Publicar o lote sobre `ca168a5c...`, confirmar o diff base→candidato e obter Project continuity, Host agent, Development image e Bootable media verdes no head exato.

## Continuidade

- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` e `PROJECT_STATE.md` no mesmo lote.
- **Não mesclar o PR #2 sem instrução explícita.**
