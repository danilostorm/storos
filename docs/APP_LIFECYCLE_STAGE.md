# StorOS: ciclo de vida de aplicativos (laboratorio)

## Implementado

- AppManager.control permite start, stop e restart apenas para projetos Docker Compose previamente cadastrados pelo catalogo interno do StorOS.
- Cada chamada valida o nome do app, hash SHA-256 do Compose aprovado, diretorio privado 0700, arquivo Compose regular privado 0600, ausencia de symlinks, conteudo igual ao manifesto do catalogo e execucao dentro de VM por systemd-detect-virt --vm.
- Nao executa docker compose down, delete, prune, remocao de volumes, comandos arbitrarios ou montagens de diretorios host.
- O backend registra stopped apos parada confirmada e deployed apos inicio/reinicio confirmado por docker compose ps. Falhas sao registradas como failed, sem anunciar sucesso ficticio.
- POST /v1/apps/control no servico Unix requer sessao de administrador, CSRF e registra auditoria antes da acao. Servico continua desabilitado por padrao.
- tools/storosctl.py oferece start, stop e restart com senha via getpass e confirmacao por nome digitado.
- Consultas de estado tambem verificam hash da configuracao antes de chamar Docker Compose.

## Testes e comprovacoes

125 testes automatizados aprovados incluindo ciclo de vida simulado com argumentos Docker predefinidos, mudanca de estado, recusa de Compose alterado, symlink, hash incorreto, app nao cadastrado, execucao fora de VM, acesso sem admin ou CSRF e confirmacao incorreta.

A imagem USB v0.5 antiga foi novamente validada por SHA-256 e estrutura GPT com BIOS Boot, EFI System e root. Os testes anteriores documentaram GUI UEFI/OVMF e Legacy/SeaBIOS. Notebook real ainda requer teste.

## Limites

O gateway HTTPS publico do laboratorio continua apenas leitura, sem controle de install/start/stop/restart. Nenhum servico de apps administrativo foi ativado nem container real iniciado/parado. Nova imagem USB sera necessaria para incorporar estas alteracoes.

Para producao ainda faltam daemon com permissoes minimas e segregacao, autenticacao HTTPS nativa e RBAC completo, testes Docker reais em VM descartavel, recovery, projetos Compose multissservico, atualizacao de imagens, backup e rollback.
