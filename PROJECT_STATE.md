# Estado do projeto — ponto de retomada

Atualizado em **11/09/2026**, atualização **BOOT-001**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: danilostorm/storos.
- Roadmap revisão 2 aprovado; [PR #1](https://github.com/danilostorm/storos/pull/1) mesclado.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- Base desta atualização: `83feeec44cbf55a878b503bc03e4a7ceceb8c548`; conferir o head atual antes de editar.
- Fase 0 continua aberta para hardware/GPU. A Fase 1 já tem agente de descoberta; BOOT-001 adiciona a pipeline para transformar a imagem bootc em QCOW2 e provar boot via console. O workflow roda em push e pull request para que a prova fique visível no PR. O resultado remoto deve ser consultado antes de marcar o boot como validado.

## Decisões confirmadas

Danilo aprovou a revisão 2 com **“Ta aprovado.”** nesta conversa. Prioridade: VMs compartilhando CPU/RAM/GPU, especialmente GPU simultânea. A base pode mudar; MOS não é obrigatório. Docker/NAS são complementares. Changelog e estado são obrigatórios em cada atualização publicada.

Nova aprovação “Fecho pode começar” autoriza Fedora/uCore HCI como base do protótipo e início de código/CI. Detalhes em [BASE_FEDORA.md](docs/BASE_FEDORA.md). Isso não homologa GPU e não autoriza modificar produção, firmware ou drivers do servidor atual.

A correção posterior de Danilo confirmou que **ISO instalável não é requisito**. A experiência desejada é preparar mídia, dar boot e configurar pelo navegador. QCOW2/RAW são formatos de laboratório/empacotamento; ISO pode existir opcionalmente.

## Concluído nesta atualização

- Adicionado workflow `.github/workflows/boot-media.yml` para construir a imagem bootc derivada do StorOS, colocá-la em um registro Docker local efêmero do runner, gerar QCOW2 com `osbuild/bootc-image-builder-action` e inicializá-la em QEMU usando TCG.
- O workflow só considera o boot comprovado quando o console serial mostra o systemd alcançando `storos-agent.service` (`StorOS read-only host and VM observer`); depois disso grava `STOROS_BOOT_OK` apenas no artefato de evidência do CI.
- Nenhuma credencial padrão ou serviço adicional foi criado apenas para o teste.
- O workflow executa `bootc container lint` antes do empacotamento e mantém o `check-image.sh` existente com o driver `test:///default`.
- Configuração do Image Builder adiciona console serial e `systemd.show_status=yes` ao kernel para tornar o boot de CI observável.
- O workflow foi ligado também ao evento de pull request para facilitar inspeção pelo PR #2.
- Sintaxe dos novos trechos Bash e TOML foi revisada antes da publicação. O resultado do GitHub Actions do incremento BOOT-001 ainda precisa ser consultado; não registrar boot bem-sucedido apenas porque o workflow foi criado.

### Trabalho funcional anterior preservado

- Agente e CLI `storosctl`, com consulta de UUIDs/estado/recursos informados pelo libvirt, conexão somente leitura e falhas explícitas.
- Serviço systemd do agente incluído e habilitado na imagem. Snapshot atômico local, com detecção de coleta antiga; nenhum endpoint de rede.
- Dez testes locais passaram no incremento DEV-001; integração simulada usa `test:///default`.
- Containerfile, identidade do protótipo e digest uCore fixado; primeiro build de composição passou com QEMU 10.2.2 e libvirt 12.0.0.
- Triagem GPU, protocolo de laboratório e roadmap continuam válidos; nenhuma placa está homologada.

## Verificação e limitações

- BOOT-001 ainda depende do resultado remoto do novo workflow para comprovar geração do QCOW2 e chegada ao marcador de boot.
- Nenhum boot físico por USB foi executado nesta sessão.
- Persistência de configuração após reinício ainda não foi implementada/testada.
- Sem painel web, criação/alteração de VMs ou políticas automáticas de CPU/RAM.
- Sem `/dev/kvm` ou hardware GPU do usuário neste ambiente; QEMU do CI usa TCG para prova funcional de boot, não benchmark.
- Sem teste de GPU compartilhada. RTX 3080 Ti/RX 550 continuam candidatas citadas, não homologadas.
- A imagem intermediária `storos-ci` fica em um registro local efêmero do runner e não é release do StorOS.

## Próxima tarefa concreta

1. Consultar o workflow **Bootable media** deste incremento. Se falhar, corrigir o primeiro erro real sem esconder a falha. Se passar, registrar run/commit como primeira evidência de boot StorOS em VM descartável.
2. Depois do primeiro boot verde, testar **dois boots consecutivos** no mesmo QCOW2 e persistência de um valor em `/var`/configuração para provar sobrevivência ao reinício.
3. Em seguida, implementar configuração persistente transacional e a fundação do painel web autenticado, consumindo o contrato de descoberta existente.
4. STOR-009/010/011 continuam pendentes para GPU/base/hardware; não encerrar Fase 0 com CI virtual apenas.
5. Não anunciar GPU compartilhada, ajustes automáticos, mídia USB pronta ou suporte de produção sem evidência correspondente.

## Para uma nova IA

Leia AGENTS.md e confira Git/PR. A aprovação acima já foi dada; não peça novamente para começar. O Resource Guardian é um projeto MOS separado, não uma versão funcional do StorOS. Não repetir a revisão NAS inicial nem presumir que documentação ou workflow criado equivale a boot validado.
