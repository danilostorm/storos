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
