# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **BOOT-001B**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Roadmap revisão 2 aprovado; [PR #1](https://github.com/danilostorm/storos/pull/1) mesclado.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base desta atualização: `5b1aff0ce80a9f3b9eadf7017678bdce08d890ef`; conferir o head atual antes de editar.
- Fase 0 continua aberta para hardware/GPU. A Fase 1 já tem agente de descoberta. BOOT-001 já gera QCOW2 e o run `34651227029` comprovou que a imagem passa por OVMF/GRUB/kernel e chega ao login serial; BOOT-001B corrige a ativação do agente no primeiro boot.

## Decisões confirmadas

Danilo aprovou a revisão 2 com **“Ta aprovado.”**. Prioridade: VMs compartilhando CPU/RAM/GPU, especialmente GPU simultânea. A base pode mudar; MOS não é obrigatório. Docker/NAS são complementares. Changelog e estado são obrigatórios em cada atualização publicada.

Danilo também autorizou Fedora/uCore HCI como base do protótipo e início de código/CI. Isso não homologa GPU nem autoriza modificar produção, firmware ou drivers do servidor atual.

ISO instalável não é requisito. A experiência desejada é preparar mídia, dar boot e configurar pelo navegador. QCOW2/RAW são formatos de laboratório/empacotamento; ISO pode existir opcionalmente.

## Concluído / evidência atual

- A imagem bootc de desenvolvimento compõe com uCore HCI fixado por digest e contém QEMU/libvirt e o agente StorOS.
- O workflow `Bootable media` constrói a imagem, executa `bootc container lint`, gera QCOW2 com bootc-image-builder, valida com `qemu-img` e inicia em QEMU/TCG usando OVMF pflash CODE + VARS.
- O bloqueio anterior do `disk.yaml`/XFS foi corrigido com a definição de disco compatível do StorOS; o QCOW2 já é gerado e inspecionado com sucesso.
- O run `34651227029` chegou ao login serial. O console mostrou `systemd` aplicando a política de preset e removendo explicitamente `/etc/systemd/system/multi-user.target.wants/storos-agent.service`; essa é a causa real de o marcador anterior não aparecer.
- BOOT-001B adiciona `/usr/lib/systemd/system-preset/10-storos.preset` com `enable storos-agent.service`, troca a composição para `systemctl preset`, faz a unidade puxar `virtqemud.socket` e publica `STOROS_AGENT_READY snapshot=written` no console apenas depois de existir `/run/storos/status.json`.
- O CI passa a exigir esse marcador, portanto um check verde prova boot, ativação do serviço e primeira gravação do agente; o resultado remoto deste incremento ainda deve ser consultado antes de marcar essa prova como concluída.

### Trabalho funcional anterior preservado

- Agente e CLI `storosctl`, com consulta de UUIDs/estado/recursos informados pelo libvirt, conexão somente leitura e falhas explícitas.
- Snapshot atômico local em `/run/storos/status.json`, com detecção de coleta antiga; nenhum endpoint de rede.
- Dez testes locais passaram no incremento DEV-001; integração simulada usa `test:///default`.
- Triagem GPU, protocolo de laboratório e roadmap continuam válidos; nenhuma placa está homologada.

## Verificação e limitações

- Run `34651227029`: QCOW2 válido e boot real em VM descartável até `localhost login:`; o agente não iniciou porque o primeiro-boot preset removeu o link de enable. Esse run é evidência de boot do sistema, mas não fecha ainda a prova do agente.
- BOOT-001B precisa de um novo workflow verde com `STOROS_AGENT_READY snapshot=written` antes de declarar o agente validado no boot.
- Nenhum boot físico por USB foi executado.
- Persistência de configuração após reinício ainda não foi implementada/testada.
- Sem painel web, criação/alteração de VMs ou políticas automáticas de CPU/RAM.
- QEMU do CI usa TCG; isso é prova funcional de boot, não benchmark.
- Sem teste de GPU compartilhada. RTX 3080 Ti/RX 550 continuam candidatas citadas, não homologadas.
- A imagem intermediária `storos-ci` fica em registro local efêmero do runner e não é release do StorOS.

## Próxima tarefa concreta

1. Consultar o `Bootable media` disparado por BOOT-001B. Aceite: QCOW2 válido e console contendo `STOROS_AGENT_READY snapshot=written`.
2. Com o primeiro boot + agente verdes, testar dois boots consecutivos no mesmo QCOW2 e persistência real em `/var/lib/storos`, identificando boots distintos pelo `boot_id` do kernel.
3. Depois, implementar configuração persistente transacional e a fundação do painel web autenticado, consumindo o contrato de descoberta existente.
4. STOR-009/010/011 continuam pendentes para GPU/base/hardware; CI virtual não encerra a Fase 0.
5. Não anunciar GPU compartilhada, ajustes automáticos, mídia USB pronta ou suporte de produção sem evidência correspondente.

## Para uma nova IA

Leia AGENTS.md e confira Git/PR. A aprovação para continuar já foi dada. Não repetir a revisão NAS inicial nem presumir que documentação ou workflow criado equivale a validação. O próximo ponto é fechar BOOT-001B no CI e então testar persistência de dois boots.
