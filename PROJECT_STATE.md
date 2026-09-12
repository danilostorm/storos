# Estado do projeto — ponto de retomada

Atualizado em **12/09/2026**, fechamento funcional **VM-003B**. Responsável pelas decisões: Danilo.

## Onde está o trabalho

- Repositório: `danilostorm/storos`.
- Branch: `phase0/gpu-feasibility`, [PR #2](https://github.com/danilostorm/storos/pull/2).
- VM-002 está fechado remotamente.
- WEB-VM-001 está fechado remotamente no head `550e8ac1a92de7fb6c89e7bcdd96581e45f533ef`.
- VM-003A está fechado remotamente no head `6108e0ec45f79e7a399f7f96733076effe3a2f47`.
- **VM-003B está fechado funcionalmente** no head `a8e0e9895efd24e4814c87297feefb34e5d123bb`; o novo head documental deste fechamento ainda deve passar os gates antes de iniciar a etapa seguinte.
- Fedora/uCore HCI continua como base autorizada do protótipo; ISO instalável não é requisito.
- `features.vm_write_enabled=false` permanece obrigatório; não existe worker/executor de mutação libvirt.
- Fase 0 continua aberta para hardware/GPU; RTX 3080 Ti/RX 550 seguem não homologadas para compartilhamento simultâneo.

## VM-003B — fechamento funcional remoto

O VM-003B estende intenção/planner para um subconjunto tipado de firmware, discos e rede, preservando integralmente intenções schema 1 já persistidas e mantendo toda reconciliação em `dry_run`.

No head funcional `a8e0e9895efd24e4814c87297feefb34e5d123bb` os quatro gates ficaram verdes:

- Project continuity `34715892296`;
- Host agent `34715892293`: **63/63 testes**;
- Development image `34715892321`, job `103612989742`;
- Bootable media `34715892313`, job `103612991227`.

O Development image confirmou, dentro da imagem final com libvirt 12.0.0 e QEMU 10.2.2, os dois marcadores funcionais do smoke:

- `StorOS discovery and virtual hardware observation passed against libvirt test driver (no real VM).`
- `StorOS image content check passed; VM intent schemas 1 and 2 remain dry-run only.`

Esse smoke passou durante a construção da imagem e novamente em execução isolada. Artefato `image-evidence`: ID `10303869538`, digest `sha256:a97e88a04ddfe595d5c25d4443af815ae0efcfb5845fcfc01fe5127243593c05`.

### Prova de boot/persistência

O Bootable media gerou um QCOW2 de 10 GiB virtual / ~2,22 GiB ocupado, inspecionou-o como `qcow2` compat 1.1 e inicializou **o mesmo disco duas vezes** com o QEMU 10.2.2 empacotado na própria imagem StorOS.

Foram emitidos:

- `STOROS_BOOT_OK`;
- `STOROS_PERSISTENCE_OK`;
- `STOROS_WEB_PERSISTENCE_OK`.

Detalhes comprovados pelos logs do artefato:

- primeiro boot: `boot_count=1`, `boot_id=ab79f354-8f8b-49dd-9ed7-588810f59a49`;
- segundo boot: `boot_count=2`, `boot_id=d1308e55-474c-479d-8e55-22c363ffa31f`;
- `config_generation=1` nos dois boots;
- `config_sha256=4a820303e19f686b0da10bea78bd5cdabc39a8a07be935e6540a801d0958d936` nos dois boots;
- `token_sha256=100e08e84180765bc9695d5c4d3a342a52d4759271da0a14406f265f4a546d2d` nos dois boots;
- agente e painel autenticado ficaram prontos nos dois boots.

Artefatos finais:

- QCOW2 SHA-256 `7e1466e575254dfd8c40c7eff3dec5f683e24a43385fd36709f15a68922ff44c`;
- `storos-boot-evidence` ID `10304634825`, digest `sha256:d4bb72db8d61c5e100c13b697e697db39263fd078f5c963b14591f610ed8bbd8`;
- `storos-qcow2` ID `10304931834`, digest do artefato `sha256:20d06f112745fd9982c6382501eb5751691f77d3859e930bfe6e7afe9c410184`.

## Contrato fechado no VM-003B

### Compatibilidade v1/v2

`storos_vm.py` aceita schema 1 e schema 2 sem migrar silenciosamente documentos antigos.

- Schema 1 mantém exatamente UUID, nome, estado, vCPU e RAM fixa.
- Validar v1 não acrescenta `hardware`; hashes históricos continuam válidos.
- Schema 2 acrescenta um bloco `hardware` para novas intenções.
- O store pode manter revisões v1 e v2 na mesma linha do tempo.
- Rollback de v2 para revisão v1 cria nova geração v1 preservando o conteúdo/hash da intenção alvo.

### Hardware gerenciado pelo schema 2

- firmware opcional por abstração `bios|efi`, sem caminhos OVMF do host;
- discos por target, buses `virtio|sata|scsi`, fonte local `file|block`, formato `raw|qcow2`, readonly e ordem de boot opcional;
- interfaces por MAC, fontes `network|bridge` e modelo explícito;
- targets/MACs duplicados são rejeitados;
- listas são normalizadas deterministicamente;
- listas representam **subconjuntos gerenciados**: hardware observado extra não gera detach automático.

O planner v2 descreve apenas ações não executáveis `set_firmware_mode`, `attach_disk`, `reconfigure_disk`, `attach_interface` e `reconfigure_interface`, além de bloqueios `inspect_hardware`, `inspect_firmware`, `inspect_disk` e `inspect_interface`.

Se `hardware.status!=ok`, firmware estiver `unknown` ou a identidade observada for insuficiente, o planner falha fechado e não presume alteração.

### Secure Boot

`loader secure='yes'` não é tratado como estado ativo de Secure Boot. O observador só produz `secure_boot=true|false` quando existe `firmware/feature name='secure-boot' enabled='yes|no'` explícito; caso contrário retorna `null`. O teste dedicado `test_loader_secure_is_capability_not_secure_boot_state` passou na suíte final.

Secure Boot, enrolled keys, NVRAM gerenciado, hotplug, passthrough, SR-IOV, mediated devices e GPU continuam fora da intenção VM-003B.

## Segurança preservada

- Agente/libvirt continuam somente leitura.
- Nenhum endpoint web ganhou autoridade de escrita.
- Nenhum executor foi adicionado.
- Nenhuma chamada mutável ao libvirt foi adicionada.
- `features.vm_write_enabled=true` continua rejeitado.
- Planos continuam `mode=dry_run`, `can_apply=false`; tarefas e ações continuam `executable=false`.
- Não existe detach automático de hardware não gerenciado.
- QCOW2 é artefato de laboratório, não release de instalação.

## Limitações atuais

- Sem criação/start/stop/import real de VM pelo control plane StorOS.
- Sem política dinâmica aplicada de CPU/RAM.
- Sem TLS integrado e sem RBAC/múltiplos usuários.
- Nenhum boot físico por USB foi executado.
- QEMU/TCG de CI é prova funcional, não benchmark.
- Nenhum teste físico de GPU compartilhada foi realizado.
- Passthrough/GPU continuam dependentes de laboratório físico e matriz de suporte.

## Próxima tarefa concreta — VM-004A

Antes de habilitar qualquer escrita real, criar a **fronteira de preflight de execução** separada do planner e do futuro executor.

1. Receber somente tarefa persistida `vm_reconcile` já validada pelo ledger.
2. Relê-la junto com intenção atual, geração/hash e snapshot fresco imediatamente antes de qualquer decisão.
3. Revalidar `intent_generation`, `intent_sha256`, `snapshot_sha256`, UUID e estado do plano.
4. Exigir explicitamente feature gate de escrita, autorização e backend/capacidade suportados; no VM-004A o gate continuará `false`, portanto o resultado deve ser bloqueado.
5. Modelar lock de execução por VM/recurso e resultado auditável de preflight, sem chamar `virsh define/start/shutdown` ou equivalente.
6. Cobrir drift, tarefa adulterada, snapshot stale, intenção atualizada, ação desconhecida e tentativa executável indevida.
7. Manter painel somente leitura e `features.vm_write_enabled=false` até uma etapa de escrita explicitamente separada.

VM-004A é fundação de segurança para a futura passagem `JOBS → COMPUTE`; **não é ainda o executor real**.

## Continuidade

- O head funcional fechado do VM-003B é `a8e0e9895efd24e4814c87297feefb34e5d123bb`.
- O novo head documental criado por este fechamento deve passar continuidade/testes/imagem/boot antes de iniciar VM-004A.
- `CHANGELOG.md` deve permanecer somente aditivo; não reescrever entradas antigas.
- A entrega final continua orientada a mídia física/pendrive em etapa posterior.
- Danilo autorizou continuar sem pular etapas. Não pedir nova autorização para seguir o roadmap.
- Obedecer `AGENTS.md` em toda publicação.
- **Não mesclar o PR #2 sem instrução explícita.**
