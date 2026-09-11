# Base de desenvolvimento Fedora/uCore

Decisão de 11/09/2026: Danilo respondeu “Fecho pode começar” à direção Fedora/uCore. Adotamos `ucore-hci:stable` como base do protótipo x86_64, sujeita à validação de boot e GPU. Não é homologação de produção.

O [uCore](https://github.com/ublue-os/ucore) oferece imagem Fedora CoreOS com ferramentas de servidor; a variante HCI inclui libvirt/KVM e virt-install. Isso reduz o trabalho inicial de empacotamento. Ainda precisamos desenvolver o painel e os controles StorOS. Preservamos a identidade e os arquivos de licença upstream; a identificação do protótipo fica em `/usr/share/storos/release`.

## Primeira implementação

[Containerfile](../Containerfile) deriva a imagem e inclui identificação e coletor somente leitura. [Workflow](../.github/workflows/image.yml) resolve a tag para digest, usa esse digest no build, verifica ferramentas e salva inventário de pacotes/evidências. O digest permite repetir a base exata enquanto disponível no registro. A tag pode mudar entre execuções: ainda não há base fixa de release.

Build local para desenvolvedores com Docker em Linux x86_64:

```sh
docker build -f Containerfile -t storos:development .
docker run --rm --network none --entrypoint bash storos:development /usr/libexec/storos/check-image.sh
```

Para reproduzir uma execução, passar `--build-arg BASE_IMAGE=<referência-com-digest>` registrada no artefato `image-evidence`. O workflow não publica imagem, não instala em discos e não modifica o servidor MOS.

## Limites e próximos passos

Esta entrega verifica composição de imagem, não inicialização. Executar um comando dentro do container não comprova boot do sistema, funcionamento do libvirt nem aceleração de GPU.

1. Obter build verde e registrar versões efetivas de QEMU/kernel/driver.
2. Fixar digest e verificar assinatura upstream antes de distribuir imagens instaláveis; desenvolver assinatura própria e política de atualizações StorOS. O build inicial usa transporte HTTPS, mas ainda não verifica assinatura da base.
3. Preparar provisionamento descartável e teste de boot, rede, libvirt e reinício. Não usar imagem de desenvolvimento para rebase do MOS.
4. Executar matriz GPU em hardware e implementar o contrato CPU/RAM. Não considerar a variante NVIDIA como prova de compartilhamento entre VMs.
5. Só então preparar instalador e canal de releases com recuperação testada. Rollback do sistema não restaura os dados das VMs.

Fase 0 permanece aberta. MOS é referência e ambiente atual do usuário; não será modificado por esta entrega.
