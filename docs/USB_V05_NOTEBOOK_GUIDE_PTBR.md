# StorOS v0.5 — guia do primeiro teste no notebook

**Situação em 28/10/2026:** a imagem inicializou com GUI em QEMU/OVMF (UEFI) e QEMU/SeaBIOS (Legacy). O boot por pendrive em notebook físico ainda não foi testado. Esta versão é uma prévia do sistema e NÃO é um NAS pronto para produção.

## 1. Antes da gravação

- Pendrive **descartável de pelo menos 16 GB** (preferencialmente 32 GB); notebook com CPU **x86-64**. Modelos exclusivamente 32-bit não vão inicializar.
- O balenaEtcher apagará tudo no dispositivo USB escolhido. Salve seus dados antes.
- Se possível, desconecte discos internos contendo dados importantes durante o primeiro teste.
- Arquivo do AEROCOOL para o balenaEtcher: /mnt/user/rea/StorOS/output/StorOS-v0.5-USB-Preview.img
- SHA-256 esperado: de2ac025105f9b82e9fed350ba7664c9b46a3c19d905186cf93bbce59270d004
- Tamanho do arquivo: 10.737.418.240 bytes (10 GiB). Trata-se de imagem de DISCO, não de arquivos para copiar ao USB.

No PowerShell do Windows, após transferir o arquivo inteiro, verifique:

    Get-FileHash -Algorithm SHA256 "C:\caminho\StorOS-v0.5-USB-Preview.img"

O resultado deve corresponder ao checksum acima.

## 2. Gravar pelo balenaEtcher

1. Abra o balenaEtcher e selecione Flash from file.
2. Escolha o arquivo StorOS-v0.5-USB-Preview.img.
3. Em Select target, confira com atenção a identificação e o tamanho do pendrive. Não selecione SSD/HDD internos ou discos de produção.
4. Clique em Flash e finalize a verificação.
5. Remova o USB com segurança. Se o Windows pedir para formatar partições Linux, NÃO FORMATE.

Não use o modo ISO do Rufus nem copie manualmente os arquivos da imagem.

## 3. Notebook antigo / BIOS Legacy

1. Conecte o USB antes de ligar o notebook. Se existir porta USB 2.0, tente essa primeiro.
2. No menu de boot (tecla específica do fabricante: às vezes F12, F9, F11 ou Esc), escolha o pendrive. Alternativamente entre no setup BIOS.
3. Ative USB Boot e, se disponível, escolha modo USB-HDD ou Hard Disk, em vez de USB-FDD.
4. Em computadores UEFI, mantenha UEFI quando funcionar. Legacy/CSM é alternativa. O Secure Boot da imagem não foi homologado.
5. Se o pendrive não aparecer: teste outra porta e outro pendrive, e verifique o suporte USB-HDD do firmware. Isso não significa necessariamente que falta um bootloader Legacy.
6. Se o GRUB aparecer e o sistema travar, anote a última mensagem. Não faça reparos nos discos internos.
7. Se a GUI abrir, registre discos detectados, memória, rede, resolução e modo de boot.

O SeaBIOS do QEMU já carregou a GUI desta imagem em teste virtual; isso não garante compatibilidade com todos os BIOS, controladores USB ou GPUs de notebooks antigos.

## 4. Critérios de sucesso

- Pendrive aparece no menu de inicialização.
- GRUB e kernel Linux carregam.
- O Firefox em modo kiosk abre o painel StorOS.
- CPU, memória e discos exibem dados reais, ou campos vazios se não houver acesso.
- Reiniciar pelo USB preserva a capacidade de dar boot.
- Nenhum disco interno nem volume de dados sofre alterações.

Para diagnóstico, anote modelo/CPU/RAM do notebook, se o firmware é Legacy ou UEFI, modelo e tamanho do USB, última mensagem de erro e se o painel abriu. Fotos das telas de erro ajudam.

## 5. Limites importantes

- O StorOS v0.5 funciona como boot pelo pendrive; **não instala automaticamente o sistema em SSD/HDD interno**.
- Não use para migrar array, paridade, pools ou dados do Unraid.
- Não exponha o painel para a internet; a imagem base desabilita SSH do laboratório.
- Login web administrativo, instalação por clique, recuperação, atualização/rollback, expansão automática do armazenamento de boot e persistência de hardware físico ainda não foram homologados.
- Este é o primeiro teste de interface e compatibilidade de boot, não um teste para armazenar dados valiosos.

Documento técnico: docs/USB_V05_BUILD_STATUS.md.
