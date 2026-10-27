# StorOS — teste inicial em notebook pelo balenaEtcher (após homologação QCOW2/RAW)

**Este documento é uma preparação. O build v0.3.0 contém credencial SSH pública de laboratório e ainda não está homologado para hardware real.** Não use como servidor de produção, nem exponha à internet.

## Requisitos mínimos para a primeira prova de conceito
- Um pendrive **descartável** de pelo menos 16 GB (preferível 32 GB ou mais) e um notebook x86-64 com UEFI. A imagem RAW tem tabela de partições e bootloader; não é um instalador do Fedora a ser rodado dentro de outro sistema.
- Monitor/teclado e acesso ao menu de boot UEFI; GPU e placas de Wi-Fi dependem de driver/firmware, não validados em todos os notebooks.
- Backup dos arquivos do pendrive: balenaEtcher irá **apagar todo o conteúdo do pendrive selecionado**.
- Para os primeiros testes, não monte nem formate SSD/HDD internos. Preferencialmente desabilite o disco interno no firmware/UEFI ou teste em equipamento sem disco de dados importante.
- Não pressuponha suporte a Secure Boot. Caso a imagem não seja assinada/homologada, poderá exigir desativação temporária de Secure Boot apenas no notebook de testes.

## Sequência segura
1. Verificar o SHA256 do arquivo IMG/RAW. Não alterar a imagem depois da verificação.
2. Gravar o arquivo `.img` em um pendrive vazio via balenaEtcher (Flash from file → Select target → Flash), **conferindo capacidade e identificação da mídia**.
3. Reiniciar o notebook e escolher o dispositivo USB no menu de boot. Não executar instaladores nem comandos de `mkfs`, `fdisk`, `parted` contra discos de dados.
4. Confirmar tela StorOS (modo GUI), login de laboratório restrito e dados de CPU/RAM/discos somente em leitura.
5. Validar rede local, navegador, Docker/Compose e busca Docker Hub. Evitar instalar containers até ter mecanismo de credenciais/volumes persistentes seguros.
6. Reiniciar pelo USB, confirmar consistência e inspecionar logs. Se travar, registrar modelo do notebook, UEFI, mensagem e logs; não tentar reaproveitar automaticamente discos do Unraid.

## Critérios de aceite para disponibilizar a imagem
- QCOW2 com GUI, Docker Engine e Compose aprovado em VM separada.
- RAW gerado e verificado (partições/bootloader); idealmente boot teste RAW em VM independente.
- Remover credenciais de laboratório da imagem pública; implementar onboarding seguro e controles de acesso.
- Definir se modo GUI pode ser escolhido no boot e validar BIOS legado/UEFI conforme hardware alvo.
- Garantir integridade, persistência, atualização/rollback e teste de recuperação.

O balenaEtcher grava a imagem inteira; não é necessário particionar manualmente o USB. Sua compatibilidade de firmware/hardware físico só pode ser afirmada após o teste real.

## StorOS v0.3.1 USB Preview (sem acesso SSH remoto)
Há uma build de teste separada, feita pela VM Fedora a partir de `installer/Containerfile.usb-preview` e `installer/build-usb-preview.sh`. Essa variante:
- mantém a GUI local, Docker Compose e os módulos de catálogo e custos;
- inclui correção das unidades da interface e do filtro de zram;
- **não injeta usuário, senha ou chave SSH pelo blueprint**;
- mascara o serviço de SSH, impedindo login remoto por padrão;
- não fornece ainda assistente de criação de administrador, gerenciamento completo de discos ou instalação de apps com um clique.

O nome planejado do RAW é `StorOS-v0.3.1-USB-Preview.raw`. A imagem de laboratório `StorOS-v0.3.0-USB-LAB.raw.zst` contém autorização SSH específica dos testes e **não deve ser gravada no notebook**.

### Testes de aceitação para esta variante
Após compilar, confirme checksum, tabela GPT/EFI, boot UEFI do RAW por uma VM isolada, LightDM/Firefox, API local, Compose e ausência de porta SSH aberta. O único formato apropriado para gravar diretamente pelo Etcher é a imagem de disco RAW/IMG (não QCOW2).

Esta versão é uma **prova de conceito do boot e da interface**, não um sistema NAS com instalação persistente homologada. As funções de armazenamento, volumes de aplicativos, backup e updates ainda não são seguras para produção.

## Resultado verificado em 27/10/2026 — v0.3.1
- `StorOS-v0.3.1-USB-Preview.img` produzido com 10 GiB e tabela GPT incluindo ESP/UEFI, checksum SHA256 correspondente ao RAW da VM Fedora.
- Imagem bootada **diretamente como base RAW**, usando somente overlay QCOW2, na VM isolada `StorOS-BootTest-RAW-Preview031` (UEFI, sem disco físico repassado).
- GUI LightDM + Firefox renderizando o painel StorOS na tela VNC; a formatação de memória em GiB e o filtro de zram estão corrigidos.
- QEMU guest agent conectado. Rede NAT: nenhuma conexão TCP nas portas 22, 80 e 8765; o backend HTTP permanece em loopback.
- Como o agente do QEMU está confinado pelo SELinux, comandos administrativos executados através dele podem retornar acesso negado. Não enfraquecer SELinux para burlar essa restrição. Validamos a imagem e a conectividade a partir do host e a GUI pelo VNC.
- Docker e Compose estão presentes na camada OCI da imagem e foram validados na v0.3.0; **ainda não houve ensaio de instalação de apps por UI na v0.3.1**.

Arquivo final no Unraid: `/mnt/user/rea/StorOS/output/StorOS-v0.3.1-USB-Preview.img`.
SHA256: `e1050333df2f3d421e9858be41973188b71ddc165e32f19441587ff05850fce4`.

Primeiro teste físico: gravar no **pendrive vazio** (mínimo 16 GB), selecionar USB pelo menu UEFI, deixar disco interno desligado/desconectado quando possível e validar painel na tela. O sistema ainda não conta com onboarding administrativo, auto-configuração de Wi-Fi, tolerância a falhas ou controle completo de volumes. Não usá-lo como substituto de Unraid.
