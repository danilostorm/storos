# Roadmap StorOS

1. **P0 — Sistema independente USB**: build bootc Fedora CoreOS/uCore, QCOW2/RAW e boot UEFI/BIOS, persistência e recuperação, sem acesso destrutivo aos discos reais. Parcial em laboratório.
2. **P0 — GUI/Web**: monitoramento somente leitura; modo console gráfico local opcional (sem expor a API na rede), autenticação/RBAC antes de controle remoto. Em implementação.
3. **P1 — NAS confiável**: descoberta/identidade dos discos, montagem segura, pools ZFS/btrfs, snapshots, recuperação e testes de falhas antes de qualquer gestão de volumes. Não implementado.
4. **P1 — VMs e apps**: painel para libvirt, containers rootless, templates, métricas. Não implementado.
5. **P1/P2 — Compartilhamento CPU/RAM/GPU entre VMs**: preservar objetivo do projeto original; matriz de viabilidade de vGPU/MIG/SR-IOV/licenças por hardware, testes de GPU simultânea, sem confundir passthrough com compartilhamento. Não implementado.
6. **P2 — Segurança e distribuição**: assinatura da imagem, updates atômicos/rollback, guias de gravação USB, CI, backup/restore, métricas e homologação. Não implementado.

Não se comprometer com desempenho superior ao Unraid antes de benchmark e testes.

## Ideias reaproveitáveis do Tower Command Center (código do usuário)
- **Custos:** cálculo estimado implantado em v0.3; depois coletor de histórico, editor de tarifas/planos e rateio automático por VM/container.
- **Observabilidade:** gráfico de CPU/RAM/temperatura/rede por período, SMART, continuidade de internet/host, eventos com severidade e reconhecimento.
- **Virtualização:** métricas individuais de rede, RAM, vCPU, energia estimada e tempo ativo, separando serviços indisponíveis de ativos.
- **Apps:** métricas e notificações individuais, gerência de stacks Compose e integrações OCI.
- **Administração:** backups verificados, autenticação/RBAC, registro de auditoria e perfis de usuário.
- **Proteção de dados:** políticas de falha de discos, uso/paridade; hardware real somente após testes de restauração.
