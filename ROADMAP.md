# Roadmap StorOS

1. **P0 — Sistema independente USB**: build bootc Fedora CoreOS/uCore, QCOW2/RAW e boot UEFI/BIOS, persistência e recuperação, sem acesso destrutivo aos discos reais. Parcial em laboratório.
2. **P0 — GUI/Web**: monitoramento somente leitura; modo console gráfico local opcional (sem expor a API na rede), autenticação/RBAC antes de controle remoto. Em implementação.
3. **P1 — NAS confiável**: descoberta/identidade dos discos, montagem segura, pools ZFS/btrfs, snapshots, recuperação e testes de falhas antes de qualquer gestão de volumes. Não implementado.
4. **P1 — VMs e apps**: painel para libvirt, containers rootless, templates, métricas. Não implementado.
5. **P1/P2 — Compartilhamento CPU/RAM/GPU entre VMs**: preservar objetivo do projeto original; matriz de viabilidade de vGPU/MIG/SR-IOV/licenças por hardware, testes de GPU simultânea, sem confundir passthrough com compartilhamento. Não implementado.
6. **P2 — Segurança e distribuição**: assinatura da imagem, updates atômicos/rollback, guias de gravação USB, CI, backup/restore, métricas e homologação. Não implementado.

Não se comprometer com desempenho superior ao Unraid antes de benchmark e testes.
