# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, fechamento funcional **VM-004A**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, PR #2 aberto e não autorizado para merge.
- VM-002, WEB-VM-001 e VM-003A permanecem fechados.
- VM-003B está fechado funcional e documentalmente.
- **VM-004A está fechado funcionalmente** no head `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4`; este lote registra o fechamento documental.
- `features.vm_write_enabled=false` permanece obrigatório.
- Não existe executor, worker mutável, endpoint web de aplicação, autorização de escrita ou backend libvirt mutável.
- Fase 0 continua aberta para laboratório físico/GPU.

## VM-004A — fechamento remoto

O VM-004A materializa a fronteira fail-closed imediatamente anterior a um futuro adaptador mutável, sem conceder capacidade de executar mudanças.

Head funcional validado: `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4`.

Quatro gates de push ficaram verdes:

- Project continuity `34722963474`;
- Host agent `34722963483`, job `103632055853`: **74/74 testes**;
- Development image `34722963475`, job `103632056077`;
- Bootable media `34722963476`, job `103632056071`.

A suíte cobre fingerprints estáveis, ledger schema 2/3, fluxo CLI, compatibilidade histórica, locks/auditoria, drift de intenção/snapshot/plano, snapshot stale, ação desconhecida, rejeição de plano executável na fronteira do ledger e painel web somente leitura.

## Contrato fechado no VM-004A

### Fingerprints e tarefas

- O `snapshot_sha256` histórico continua preservado para auditoria/compatibilidade.
- Fingerprints semânticos versionados de snapshot e plano evitam drift falso causado apenas por idade/frescor derivada.
- Novas tarefas `vm_reconcile` usam schema 3 com geração/hash da intenção e fingerprints estáveis.
- Tarefas schema 2 continuam legíveis para histórico/API, mas não são elegíveis ao preflight por não possuírem todas as precondições modernas.

### Preflight

`storos_preflight.py`:

- recebe somente tarefa persistida validada pelo ledger;
- deriva e adquire locks de VM/recurso em ordem determinística;
- relê tarefa, intenção, snapshot fresco e configuração sob lock;
- recalcula plano/fingerprints e detecta drift;
- bloqueia snapshot stale e ação desconhecida/bloqueada;
- grava auditoria persistente em `/var/lib/storos/preflight`;
- nunca chama `virsh` mutável nem outro backend de aplicação.

Mesmo quando não há drift, o resultado permanece bloqueado porque o gate de escrita, a autorização e o backend mutável estão indisponíveis. O contrato continua `can_execute=false` e `executed=false`.

## Evidência da imagem

O Development image confirmou com libvirt 12.0.0/QEMU 10.2.2 que:

- descoberta/hardware observado continuam funcionando no driver de teste;
- intenções schema 1/2 permanecem dry-run;
- o preflight VM-004A permanece bloqueado e não executável.

Artefato:

- `image-evidence` ID `10306154568`;
- digest `sha256:c9c99c39edd0dcb624bd466b8d7d8b71f6e4522c83e41acc7973e05f3ab8598f`.

## Prova de boot/persistência

O Bootable media gerou e inspecionou um QCOW2 e inicializou **o mesmo disco duas vezes** com QEMU 10.2.2 da imagem StorOS.

Foram emitidos:

- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`.

Artefatos:

- QCOW2 SHA-256 `f8bbb35ab5feb333d4bc544da5081d1c74cd3e0ceff2cbd267eee35a63e2862e`;
- `storos-boot-evidence` ID `10307126883`, digest `sha256:caab500492f2426172a295e1c63294d13603a8ed401c19cd331d96fb5c1240bc`;
- `storos-qcow2` ID `10306997232`, digest `sha256:b9ef5d46f174977025cef4a272aa00470a0c0ee16447b7fad129a757a4cf4825`.

## Falha intermediária preservada

A primeira publicação VM-004A, `f3f1b1a5983019214cf5ebca32cbee6492d8d0a1`, teve continuidade verde mas Host agent vermelho porque um helper de teste chamado `run()` sobrescreveu `unittest.TestCase.run()`. A correção em `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4` renomeou o helper para `_run_preflight()` sem alterar a lógica de produção. O head corretivo repetiu todos os gates e é a única base usada para o fechamento funcional.

## Segurança preservada

- Escrita em VMs continua desabilitada.
- Sem executor ou worker mutável.
- Sem endpoint web de aplicação.
- Sem autorização de escrita.
- Sem backend libvirt mutável.
- Sem remoção automática de hardware não gerenciado.
- Sem gerenciamento de Secure Boot/NVRAM.
- Sem passthrough, SR-IOV, mediated devices ou GPU.
- Sem boot físico USB.
- QCOW2 continua artefato de laboratório, não release de instalação.

## Limitações atuais

- O control plane StorOS ainda não cria/inicia/para/importa VMs de verdade.
- Não existe política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico em pendrive foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark.
- Nenhuma GPU foi homologada para compartilhamento simultâneo.

## Próxima tarefa concreta

Projetar o **contrato do adaptador de escrita e da autorização da Fase 1**, mantendo qualquer capacidade mutável explicitamente desabilitada por padrão.

A próxima etapa deve, antes de executar qualquer mudança real:

1. definir interface tipada do adaptador por ação suportada, sem shell arbitrário;
2. definir identidade/autorização explícita para aplicação;
3. mapear capacidades do backend e erros observáveis;
4. manter preflight, locks, hashes e auditoria como precondições obrigatórias;
5. modelar resultado aplicado versus observado e rollback/compensação quando tecnicamente possível;
6. manter `features.vm_write_enabled=false` durante o desenho/testes de contrato;
7. exigir uma etapa posterior separada e validada antes de permitir `define/start/shutdown` ou equivalente.

O roadmap não define um identificador oficial para essa próxima subtarefa; não inventar rótulo até a etapa ser formalizada.

## Continuidade

- O head funcional fechado do VM-004A é `66e4d9341a5ca9a9ff57f12d3a5612188d77ecb4`.
- Este fechamento documental deve repetir continuidade, suíte, imagem e boot no novo head antes de ser tratado como encerramento formal.
- Após esses gates verdes, não criar outro commit somente para registrar os próprios gates, evitando ciclo documental recursivo.
- Obedecer `AGENTS.md`.
- `CHANGELOG.md` permanece somente aditivo.
- Toda publicação altera `CHANGELOG.md` e `PROJECT_STATE.md` no mesmo lote.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- **Não mesclar o PR #2 sem instrução explícita.**
