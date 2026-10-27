# StorOS — engenharia reversa limpa: boot e estrutura

**Situação:** análise estática parcial do boot Unraid; Ghidra e descompilação profunda ainda não executados. Não afirmar equivalência funcional com o Unraid.

## Base e método

Arquivo fornecido: /mnt/user/rea/unRAIDServer-7.3.4-x86_64.zip. Reproduzir com: python3 tools/analyze_unraid_boot.py /mnt/user/rea/unRAIDServer-7.3.4-x86_64.zip.

O script Python usa zipfile em leitura e inspeciona exclusivamente lista/tamanho de entradas e a configuração textual de boot. Nenhum executável proprietário é extraído ou executado, nenhuma licença é lida e os dados não são incorporados ao StorOS.

Identificadas 49 entradas ZIP, incluindo diretórios, e 42 arquivos sem diretórios. Imagens principais: bzmodules aproximadamente 803 MB, bzfirmware 332 MB, bzroot 87 MB, bzimage 9,6 MB (decimais).

## Descobertas confirmadas

- EFI/Syslinux: bootx64.efi, EFI/boot/syslinux.cfg, arquivos em syslinux/, incluindo menu.
- O menu declara cinco alternativas: Unraid OS, Unraid OS GUI Mode, Unraid OS Safe Mode, Unraid OS GUI Safe Mode e Memtest86+.
- As variantes GUI acrescentam um initramfs separado, bzroot-gui, sobre bzroot. As variantes seguras usam a flag de inicialização unraidsafemode. São fatos constatados no menu, **não** garantias sobre o comportamento da implementação interna.
- O StorOS atual inicia com Fedora uCore/bootc, GRUB, GPT/EFI e systemd graphical.target. Não utiliza e nem copia binários do Unraid. O futuro menu StorOS Server/GUI/Recovery será implementado independentemente, com testes por modo.
- A distribuição Unraid possui estrutura de configuração de rede, mas apenas sua presença não comprova funcionalidade de bonding, bridging ou taxas somadas no StorOS.
- O novo painel é HTML/CSS/JS original sobre dados reais de Linux. Aparência semelhante não equivale à engenharia reversa dos recursos de array, paridade, VMs, plugins ou atualizações.

## Próximas investigações

Executar Ghidra apenas em laboratório isolado, com autorização e hashes dos alvos; registrar fluxos/formatos e produzir implementações independentes. Não analisar mecanismos de licença, chaves, ativação ou identidade USB. Estudar opções de boot, hardware e API de gerenciamento; implementar autenticação e RBAC antes de qualquer operação mutável com discos ou containers. Todos os testes devem usar VMs e discos virtuais, nunca os discos do AEROCOOL.

Conclusão: a engenharia reversa estrutural do menu foi feita e documentada; a engenharia reversa profunda e a paridade de funções ainda estão pendentes.
