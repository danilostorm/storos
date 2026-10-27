# Changelog StorOS

## 2026-10-27 — Build USB e laboratório Fedora
- Criado protótipo read-only do painel/API com arquivos integrados à imagem bootc uCore.
- Laboratório Fedora 44 isolado no AEROCOOL, com ferramentas podman, rpm-ostree e image-builder.
- Criados arquivos QCOW2 e RAW de 10 GiB para imagem USB, sem tocar discos físicos.
- Imagem inicial v0.1.0: iniciou via UEFI; painel não iniciado; arquivos sem permissão de leitura.
- Corrigida v0.1.1: unit systemd, permissões e acesso SSH; comprovados boot UEFI, login SSH e HTTP 200 em localhost.
- Criados scripts de build e laboratório com verificações para impedir gravação no host.
- Separada prévia GUI opcional com LightDM/Xorg/Openbox/Firefox e conta local sem privilégio; **não homologada ainda**.
- Backup do planejamento antigo em branch archive antes da substituição da main autorizada pelo usuário.

**Limitações:** a imagem RAW não foi gravada nem validada num USB físico; a GUI depende de build e teste de sessão gráfica; NAS e virtualização ainda não disponíveis.
