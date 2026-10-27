# Inventário estrutural do pacote Unraid (somente metadados)

Este documento registra nomes/tamanhos do arquivo ZIP oficial disponibilizado
para análise de formato. Nenhum binário foi executado ou extraído.

- Arquivo: `unRAIDServer-7.3.4-x86_64.zip`
- Arquivos internos: **42**
- Total descomprimido: **1176.3 MiB**

| Item de maior tamanho | Tamanho (MiB) |
|---|---:|
| `bzmodules` | 765.94 |
| `bzfirmware` | 316.62 |
| `bzroot` | 82.71 |
| `bzimage` | 9.18 |
| `syslinux/syslinux_linux` | 0.26 |
| `syslinux/syslinux.exe` | 0.23 |
| `syslinux/syslinux` | 0.23 |
| `EFI/boot/libcom32.c32` | 0.19 |
| `EFI/boot/bootx64.efi` | 0.19 |
| `syslinux/libcom32.c32` | 0.18 |
| `memtest` | 0.14 |
| `EFI/boot/ldlinux.e64` | 0.13 |

## Observações
- A distribuição inclui imagens de inicialização (como `bzimage`, `bzroot`, `bzmodules` e `bzfirmware`).
- O pacote não é código-fonte livre do Unraid e não será incorporado ao StorOS.
- Estudo futuro: requisitos de boot e fluxos observáveis; comparação com componentes Fedora equivalentes.
- Material sobre adulteração de GUID ou licença foi excluído desta investigação.
