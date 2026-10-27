# Pesquisa controlada com REA e Ghidra

## Descobertas no host (2026-10-27)
- AEROCOOL executa Unraid 7.4.0-rc.2.
- `/mnt/user/rea` contém instaladores/arquivos Unraid 7.3.4 e outros artefatos; não contém a CLI REA instalada.
- Node.js encontrado: v22.18.0, **abaixo do mínimo do REA (22.19+)**.
- Ghidra e Java não encontrados nos caminhos e comandos comuns consultados.
- `unraider-7.2-3.x` / `help.txt` mencionam mudanças de GUID/licença. **Excluir completamente do trabalho**.

## Preparação recomendada EM VM de laboratório
1. Instalar Fedora Server 44 na VM, sem acesso de gravação aos discos reais.
2. Instalar Node.js 24 compatível e JDK exigido pela versão oficial escolhida do Ghidra (consultar README do release; versões recentes exigem JDK 25).
3. Baixar Ghidra exclusivamente da release oficial em https://github.com/NationalSecurityAgency/ghidra/releases .
4. Instalar REA por distribuição oficial `rea-agents` documentada em https://rea.tools/get-started/ .
5. Definir `GHIDRA_INSTALL_DIR` e `JAVA_HOME`; rodar `npx -y rea-agents@latest doctor --provider ghidra --json`.
6. Configurar o MCP no agente de desenvolvimento selecionado, após revisar as alterações.
7. Registrar cada análise com: pergunta de interoperabilidade, alvo autorizado, evidência, limitações e implementação original.

## Alvos de investigação
- Fluxos observáveis: adicionar pool, compartilhar diretório, alertas SMART, executar backup, criar VM, criar container.
- Compatibilidade com arquivos abertos e padrões (SMB/NFS/ZFS/Btrfs/KVM/OCI).
- Medir comportamento de sistema e requisitos de UX; descrever especificações independentes.

## Fora do escopo
- Ferramentas para falsificar GUID, adulterar chaves, burlar licença ou execução de imagens Unraid modificadas.
- Reutilizar código proprietário, firmware ou assets do Unraid no StorOS.
- Descompilar drivers para transplante direto em Fedora.

REA e Ghidra ainda precisam ser instalados e validados antes de dizer que a análise binária efetiva começou.
