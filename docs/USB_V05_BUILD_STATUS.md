# StorOS v0.5 USB Preview — estado verificado em 28/10/2026

## Situação atual: imagem gerada e aprovada em QEMU (não homologada em hardware)

A etapa anteriormente bloqueada de compilação foi executada com sucesso na VM isolada **StorOS-BuildLab**, Fedora 44, pelo `installer/build-ui-v05.sh`. O build terminou com código zero e a confirmação `STOROS_V05_RAW_STRUCTURE_VERIFIED`.

| Verificação | Evidência confirmada |
| --- | --- |
| Imagem OCI `localhost/storos:ui-v05` | Construída e validada pelo script; base com sshd mascarado |
| RAW completo | 10 GiB lógicos (10.737.418.240 bytes), cerca de 4,3 GiB ocupados |
| GPT | 4 partições, incluindo BIOS Boot, EFI System, /boot e raiz Linux |
| SHA-256 no Fedora e no AEROCOOL | Valores idênticos; check do arquivo inteiro em ambos |
| Boot UEFI/OVMF | Kernel Linux, QEMU guest agent e GUI Firefox/StorOS v0.5 verificados |
| Boot BIOS Legacy/SeaBIOS | GRUB, kernel, QEMU guest agent e GUI Firefox/StorOS v0.5 verificados |
| Acesso LAN da VM UEFI | Portas 22, 80 e 8765 não acessíveis; conforme o perfil de preview |
| Rede da VM BIOS | Nenhuma interface de rede anexada |
| Boot em pendrive/notebook físico | **Não testado** |
| Gestão NAS, paridade, recuperação | **Não homologadas nem habilitadas para produção** |

### Arquivos de evidência no AEROCOOL

- Imagem: `/mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.raw`
- Checksum: `/mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.raw.sha256`
- Relatório de integridade após transferência: `/mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.raw.host-check.json`
- Screenshot UEFI: `/mnt/user/rea/StorOS/lab/StorOS-BootTest-RAW-v050-verified.png`
- Screenshot BIOS: `/mnt/user/rea/StorOS/lab/v050-bios-fourth.png`
- SHA-256 integral: `de2ac025105f9b82e9fed350ba7664c9b46a3c19d905186cf93bbce59270d004`

Os screenshots são apenas evidências internas do laboratório; não são publicados no Git. A imagem v0.4 em `output/StorOS-v0.4-USB-Preview.img` foi preservada.

### Testes executados

- Na BuildLab, os 115 testes disponíveis na revisão de código sincronizada passaram antes do build. A correção do teste Docker/Podman consta da PR #5.
- Na `main` posterior, **116 testes** passaram no AEROCOOL, incluindo o novo verificador estático SeaBIOS da PR #6.
- O build do bootc/OSBuild gerou o RAW, executou a checagem `sfdisk`, gravou o SHA-256 e retornou código 0.
- O transporte esparso via SSH/rsync foi seguido de verificação integral de SHA-256/GPT pelo AEROCOOL. Não houve gravação em dispositivos físicos.
- A VM `StorOS-BootTest-RAW-v050` (OVMF) usou overlay QCOW2. O QEMU guest agent respondeu, DHCP atribuiu IPv4 e a GUI v0.5 foi vista no VNC. `tools/verify-usb-vm.sh` passou.
- A VM `StorOS-BootTest-RAW-v050-BIOS` (SeaBIOS) usou overlay QCOW2 diferente, sem NIC. O QEMU guest agent respondeu e a mesma GUI v0.5 foi vista no VNC.
- BuildLab, VM UEFI e VM BIOS foram desligadas normalmente após os testes. Discos do Unraid e o RAW original não foram alterados.

## Arquivo de distribuição para balenaEtcher (28/10/2026)

- A partir do RAW validado foi criada uma cópia esparsa de disco inteiro: /mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.img.
- A comparação SHA-256 de 10 GiB retornou o mesmo valor integral do RAW: de2ac025105f9b82e9fed350ba7664c9b46a3c19d905186cf93bbce59270d004.
- A cópia contém GPT, BIOS Boot, EFI System e raiz Linux, inspecionadas com tools/check_usb_image.py. Arquivos .sha256 e .structure.json ficam ao lado.
- Não foi gravado pendrive físico. O resultado de boot QEMU não comprova compatibilidade com BIOS/USB/GPU específicos.
- Guia para notebook: docs/USB_V05_NOTEBOOK_GUIDE_PTBR.md; cópia no diretório output: StorOS-v0.5-LEIA-ME.txt.

## Reproduzir validações sem mexer em disco físico

O script de build **não deve ser reexecutado sobre o destino atual**: recusa sobreposição do RAW. Para repetir os ensaios de boot, use as VMs já cadastradas ou crie novas VMs **com nomes inéditos**, overlays exclusivos e apenas o arquivo RAW regular abaixo. As VMs já criadas recusam redefinição pelos scripts de segurança.

```bash
# Apenas dentro do laboratório AEROCOOL, se ainda não existir a VM solicitada
bash tools/test-boot-raw.sh \
  /mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.raw \
  StorOS-BootTest-RAW-v051 5731

bash tools/test-boot-raw-bios.sh \
  /mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.raw \
  StorOS-BootTest-RAW-v051-BIOS
```

O teste SeaBIOS **não tem rede**; para UEFI, a VM NAT expõe apenas o tráfego necessário ao laboratório. Inspecione a tela VNC e o agente QEMU: iniciar uma VM não significa que a GUI foi validada.

## Limites e próximo marco

**USB físico ainda não validado.** Falta testar o pendrive descartável e o notebook (detecção BIOS/UEFI, Wi-Fi, Secure Boot, drivers, reinícios e persistência), além de credenciais configuráveis, atualizações/rollback, recuperação e política de distribuição. Não divulgar a v0.5 como release final ou NAS confiável.

A loja ainda tem catálogo parcial; os testes de instalação Compose usam simulação e o botão Install web permanece indisponível. Array e paridade, pools ZFS/Btrfs reais, gestão SMB/NFS/usuários, VMs, backup e recuperação também exigem implementação e ensaios. **Nenhum container foi realmente instalado nessa etapa.**

## Histórico das etapas anteriores

- A tentativa anterior de build da v0.5 tinha sido bloqueada por controles da conexão; esse impedimento foi superado com a compilação documentada acima.
- A v0.4 já havia chegado à GUI em QEMU/OVMF e SeaBIOS, inclusive em teste Legacy de 3 GiB/2 vCPU.
- O script v0.5 já exigia Fedora + VM, `flock`, staging, revisão estrutural e checksum; o RAW é publicado apenas após essas verificações. O marcador `.structure-ok` **não** certifica boot.
- A v0.5 é uma prévia técnica; não confundir os resultados QEMU com compatibilidade USB física ou confiabilidade de armazenamento de produção.
