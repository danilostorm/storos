# Primeiro build da base StorOS

Registro: 11/09/2026. Receita testada: commit `0258381f4d3d0982bd9113fdbb331db29fb290a9`.

[Execução concluída com sucesso](https://github.com/danilostorm/storos/actions/runs/34632041207).

| Item | Evidência observada no job |
| --- | --- |
| Base | `ghcr.io/ublue-os/ucore-hci@sha256:7dbb268b3d556e8bfa95bb922185c6a2ad9f580896bf25c6d3a81df541732464` |
| Pacote QEMU | `qemu-10.2.2-1.fc44` |
| Pacote libvirt | `libvirt-daemon-kvm-12.0.0-3.fc44.x86_64` |
| Ferramentas | virsh, virt-install, qemu-system-x86_64 e python3 encontrados |
| Coletor | Sintaxe Python validada dentro da imagem |
| Check | Passou durante build e na execução do container sem rede |

O digest acima foi fixado como padrão do Containerfile após o teste. Trocar a base passa a exigir alteração explícita no Git, com changelog e nova validação. Overrides via argumento de build são exclusivos de experimentos e não herdam este resultado.

O artefato `image-evidence` guarda metadados e lista de pacotes por 14 dias; os dados essenciais ficam neste arquivo para continuidade. A imagem resultante não foi enviada a um registro nem disponibilizada como instalador.

## O que o teste não demonstra

Não houve boot de StorOS, conexão com libvirt em execução, guest instalado ou uso de GPU. O kernel do runner não é o kernel da imagem; não o registrar como kernel do StorOS. Assinatura upstream ainda não foi verificada pelo workflow. Digest fixa conteúdo, mas não certifica seu editor.

O próximo teste é de inicialização e persistência em disco virtual descartável. O upstream documenta um [protocolo de VM com QEMU/Podman](https://github.com/ublue-os/ucore/blob/main/ucore/vm-test.md), referência a adaptar; ele não foi executado aqui. Não pedir que Danilo escolha a distribuição novamente: Fedora/uCore já foi autorizado para desenvolvimento.

GPU permanece sob o [protocolo da Fase 0](FASE0_LAB.md). As versões construídas precisam ser confrontadas com os requisitos de cada rota gráfica; build verde não equivale a suporte VirGL/Venus ou Windows.
