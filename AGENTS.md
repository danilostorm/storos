# StorOS — instruções de continuidade

- Antes de editar, leia `PROJECT_STATE.md`, `CHANGELOG.md`, `ROADMAP.md` e os requisitos de segurança.
- Não operar discos físicos nem modificar o Unraid de produção. Compilação OSBuild/rpm-ostree exclusivamente na VM Fedora isolada.
- Não versionar imagens RAW/QCOW2, chaves SSH, tokens, dumps, credenciais, resultados de análise com dados privados.
- Diferenciar rigorosamente: OCI construída, imagem gerada, UEFI boot, API HTTP e GUI visualmente testada.
- Não declarar suporte a arrays, GPU simultânea, virtualização dinâmica ou produção antes de testes.
- Toda mudança publicar junto notas em `CHANGELOG.md` e `PROJECT_STATE.md`.
- Histórico do projeto anterior preservado em `archive/antes-storos-usb-2026-10-27` no GitHub.
