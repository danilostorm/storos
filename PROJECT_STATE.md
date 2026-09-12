# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CFG-001D**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base anterior deste fechamento: `496e3bfbba637519c1fabe32414ea0a64ac018da`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- Fase 0 continua aberta para validação física de GPU/hardware.
- **CFG-001 está concluído:** a Fase 1 possui agente somente leitura, persistência básica de boot, configuração transacional e painel autenticado somente leitura com persistência comprovada entre dois boots do mesmo QCOW2.

## Evidência de fechamento do CFG-001

- Head validado: `496e3bfbba637519c1fabe32414ea0a64ac018da`.
- Host agent `34693451988`: verde.
- Development image `34693452020`: verde.
- Project continuity `34693451976`: verde.
- Bootable media `34693452040`: verde após rerun limpo do job.
- No primeiro boot do mesmo QCOW2: `STOROS_BOOT_STATE boot_count=1`, `STOROS_AGENT_READY snapshot=written boot_count=1` e `STOROS_WEB_READY auth=ok config_generation=1`.
- No segundo boot: `boot_count=2` com `boot_id` diferente, agente pronto novamente e painel autenticado novamente com `config_generation=1`.
- Os fingerprints SHA-256 da configuração e do token administrativo foram idênticos entre os dois boots; a credencial bruta não foi impressa pelos marcadores.
- O gate emitiu `STOROS_BOOT_OK`, `STOROS_PERSISTENCE_OK` e `STOROS_WEB_PERSISTENCE_OK`.
- Artefato verde `storos-boot-evidence`: ID `10298937312`, digest `sha256:ac25baaf918e1217bda3ac5064c46370685a1d0c279f8fb232b355522153ed82`.
- QCOW2 validado no run: SHA-256 `72772b43e2f11eca2f935ad717c0bf36774308bf9f729a3fa217f1b22011ee84`.

## Tentativa 1 do Bootable media #47

- A primeira tentativa do run `34693452040` passou build bootc, geração do QCOW2 e inspeção, mas congelou antes de qualquer service StorOS alcançar prontidão.
- O console registrou falha do manager do systemd durante os generators sob QEMU/TCG e o diagnóstico do gate terminou com `web=0` e `agent=0`.
- O mesmo commit, sem mudança de código, passou integralmente em um rerun limpo no job `103559632566`.
- Essa ocorrência fica preservada como instabilidade do ambiente TCG/runner e não é usada como evidência de falha da camada de configuração/painel.

## Estado funcional atual

- `storos-agent.service` observa libvirt em modo somente leitura e publica snapshot atômico em `/run/storos/status.json`.
- Estado de boot persiste em `/var/lib/storos/boot-state.json` e diferencia boots reais por `boot_id` do kernel.
- Configuração persiste em `/var/lib/storos/config` com geração monotônica, revisões, lock local, escrita atômica/fsync, concorrência otimista e rollback que cria nova geração.
- Token administrativo persiste em `/var/lib/storos/auth/admin.token` com modo `0600` e escrita durável.
- `storos-web.service` inicia em paralelo ao aquecimento do agente, escuta por padrão em `127.0.0.1:8080`, autentica dados administrativos e permanece somente leitura.
- `/api/status` retorna `503` enquanto o snapshot observado ainda não existe; `/api/config` não depende do agente.
- `features.vm_write_enabled=false` é obrigatório e qualquer tentativa de ativá-lo continua rejeitada.
- O workflow de boot só considera cada boot pronto quando **agente e painel autenticado** estão prontos no mesmo console.

## Limitações atuais

- Nenhum boot físico por USB ainda.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- O painel ainda não cria, edita, inicia, pausa ou remove VMs.
- Nenhuma mutação libvirt está habilitada.
- Sem política automática de CPU/RAM aplicada ao hipervisor.
- QEMU no CI usa TCG e não representa desempenho real.
- Sem teste físico de GPU compartilhada; RTX 3080 Ti/RX 550 continuam não homologadas.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta — VM-001

1. Definir um modelo versionado de **intenção de VM** com identificador/nome, vCPU, memória e requisitos básicos, sem traduzir ainda para mutações libvirt.
2. Criar um **planner/reconciler dry-run** que compare intenção com estado observado e gere uma lista auditável de ações propostas.
3. Criar a fundação de tarefas persistentes para registrar planos, sem executor mutável nesta etapa.
4. Expor os planos inicialmente pela CLI/testes; o painel continua somente leitura.
5. Manter `features.vm_write_enabled=false` durante todo VM-001.
6. Só depois de contratos, testes e auditoria verdes preparar uma operação de VM em modo plan/dry-run antes de discutir qualquer escrita real.
7. STOR-009/010/011 e a validação de GPU física permanecem pendentes; CI virtual não encerra Fase 0.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Antes de publicar qualquer novo lote, obedecer `AGENTS.md` e atualizar `CHANGELOG.md` + `PROJECT_STATE.md` juntos. Não mesclar o PR #2 sem instrução explícita.
