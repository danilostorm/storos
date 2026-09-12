# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, atualização **CI-BOOT-002**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base desta atualização: `6b54ac40aef0e73b87286dc04163849a9fcbd61e`.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- CFG-001 e VM-001 continuam funcionalmente concluídos. VM-001 foi validado remotamente sem executor mutável.
- `features.vm_write_enabled=false` permanece obrigatório.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## Evidência preservada do VM-001

- Head funcional: `45bd655269d8ef45f1c6f5ace9ff82ce3f8454fc`.
- Host agent `34699051160` (#69): verde.
- Project continuity `34699051144` (#81): verde.
- Development image `34699051205` (#75): verde.
- Bootable media `34699051187` (#49), job `103567451447`: verde.
- O mesmo QCOW2 atingiu `boot_count=1 → 2`, agente e painel autenticado ficaram prontos nos dois boots e configuração/token persistiram com fingerprints idênticos.

## CI-BOOT-002 — QEMU do próprio StorOS no probe

O ajuste CI-BOOT-001 trocou o guest TCG do gate para 1 vCPU e adicionou detecção explícita da falha fatal pré-StorOS. No head `6b54ac40aef0e73b87286dc04163849a9fcbd61e`, três checks ficaram verdes:

- Project continuity `34706993943` (#86): verde.
- Host agent `34706993894` (#74): verde.
- Development image `34706993935` (#80): verde.

O Bootable media permaneceu instável:

- PR run `34706993875` (#53), job `103588730179`: vermelho. Uma execução de 1 vCPU chegou muito mais longe, inclusive ao login e ao início dos serviços StorOS, mas não alcançou os dois marcadores antes de 420 s.
- Push run `34706993402` (#52), job `103588730068`: vermelho e reproduziu a mesma assinatura fatal pré-StorOS mesmo com 1 vCPU: `Failed to fork off sandboxing environment for executing generators: Protocol error` + `Failed to start up manager.`. Isso invalida a hipótese de que reduzir SMP, por si só, resolvia a causa.
- O runner Ubuntu usa QEMU 8.2.2, enquanto a imagem StorOS construída contém QEMU 10.2.2. A diferença de comportamento entre runs do mesmo commit reforça que o problema está no probe TCG/runner, não em uma alteração funcional StorOS.

### Ajuste desta atualização

- O boot de validação deixa de usar `qemu-system-x86_64` instalado no Ubuntu runner.
- O workflow executa `/usr/sbin/qemu-system-x86_64` da **própria imagem StorOS construída**, em um container Docker `--network none`.
- O container recebe apenas o QCOW2 e os arquivos OVMF necessários por bind mount; o QCOW2 permanece gravável para provar persistência entre os dois boots.
- O probe volta a 2 vCPUs para evitar a penalidade de tempo observada em 1 vCPU, mas continua usando TCG. Não há pressuposto de nested KVM.
- O workflow registra explicitamente a versão do QEMU da imagem antes do boot.
- A detecção `guest_fatal=1` permanece.
- Os limites continuam 420 s no primeiro boot e 300 s no segundo.
- Os critérios não foram relaxados: sucesso ainda exige `STOROS_BOOT_STATE`, `STOROS_AGENT_READY` e `STOROS_WEB_READY` nos dois boots, `boot_count=1 → 2`, `config_generation=1` e fingerprints persistentes de configuração/token.

### Verificação local do ajuste

- O bloco Bash do novo probe passou em `bash -n`.
- Nenhuma opção de segurança do guest foi desabilitada.
- Nenhuma falha pré-StorOS passa a ser aceita como sucesso.
- Resultado remoto desta atualização ainda deve ser obtido antes de liberar VM-002.

## VM-002 — preparado, ainda não publicado

O staging VM-002 foi reconstruído sobre o head atual e permanece retido até o gate de boot voltar a ficar verde. Escopo preparado:

- store persistente/versionado por VM em `/var/lib/storos/vm-intents`;
- geração/revisões, `expected_generation`, rollback por nova geração e SHA-256 anti-adulteração;
- locks por VM/tarefa;
- binding do plano a geração/hash da intenção, configuração e snapshot observado;
- tarefas de reconciliação continuam exclusivamente `dry_run`, `can_apply=false` e `executable=false`;
- CLI persistente `vm-intent-*`, `vm-plan-stored` e `vm-reconcile-stored-dry-run`;
- documentação de contrato/arquitetura e smoke de imagem preparados.

### Verificação local do VM-002

- **39/39 testes** passaram no staging atual, incluindo regressão VM-001 e os novos testes de store, locks, precondições, tarefas e CLI.
- `py_compile` passou nos módulos envolvidos.
- `bash -n image/check-image.sh` passou.
- Os novos módulos não introduzem `virsh`, `subprocess`, `os.system` ou shell arbitrário para mutação do hipervisor.
- Essa evidência é apenas local: VM-002 ainda não foi publicado e não tem CI remoto.

## Limitações atuais

- Nenhuma mutação libvirt está habilitada; não existe worker/executor.
- O painel web continua somente leitura e ainda não expõe intenção/plano/tarefas.
- O contrato de VM ainda não cobre discos, rede, firmware, passthrough, política dinâmica de CPU/RAM ou GPU.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark de desempenho.
- Nenhum teste físico de GPU compartilhada foi realizado.
- O QCOW2 de CI é artefato de laboratório, não release de produção.

## Próxima tarefa concreta

1. Publicar CI-BOOT-002 e exigir o Bootable media verde usando QEMU 10.2.2 da imagem StorOS.
2. Se houver falha, diagnosticar o log exato sem aumentar timeout às cegas e sem mascarar falhas do guest.
3. Quando o gate de dois boots voltar a ficar verde, publicar VM-002 atomicamente com código, testes, documentação, `CHANGELOG.md` e este estado.
4. Manter VM-002 estritamente em plan/dry-run e `features.vm_write_enabled=false`.
5. Depois do VM-002 remoto verde, avançar para exposição somente leitura no painel e desenho do executor controlado futuro.
6. STOR-009/010/011, boot físico e validação física de GPU permanecem pendentes.

## Continuidade

Danilo já aprovou a direção e autorizou continuar. Não pedir nova autorização para seguir o roadmap atual. Obedecer `AGENTS.md` em toda publicação. **Não mesclar o PR #2 sem instrução explícita.**
