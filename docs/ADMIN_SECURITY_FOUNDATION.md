# StorOS — base de identidade e seguranca (sem administracao ativa)

## Implementado

- backend/security_core.py é uma biblioteca isolada, sem rotas de login ou processos privilegiados.
- Senhas: hashlib.scrypt (N=16384, r=8, p=1), salt aleatório de 128 bits e hash de 256 bits, sem armazenar senha em texto puro.
- AccountStore: cria uma única conta admin em diretório privado 0700, arquivo 0600, proíbe sobrescrita e links simbólicos. Nenhuma conta real foi criada no AEROCOOL.
- LoginThrottle: cinco falhas por usuário em 300 segundos, estado somente em memória.
- SessionRegistry: token aleatório e token CSRF, SHA256 do token em memória, expiração por inatividade de 30 min e absoluta de 8 h, revogação explícita, cookies seguros __Host-, HttpOnly, Secure e SameSite=Strict.
- policy_allows: admite somente ações de leitura explicitamente listadas, para papéis viewer/admin; todas as operações de alteração são negadas.
- AuditLog: escreve só metadados de decisão autorizados, sem senhas ou tokens, arquivo 0600.
- /api/security/status informa o estado real sem consultar credenciais.
- Menu Sistema > Segurança mostra login nativo e administração desativados.

## Não implementado

Esta etapa NÃO habilita autenticação web nativa. A porta 18444 continua usando a autenticação Basic do gateway do laboratório. Não há daemon de administração instalado ou acesso root do painel; Docker, virtualização e discos permanecem em leitura.

Antes de produção, são necessários serviço separado com Unix socket, autenticação do chamador, proteção de origem HTTPS, política por recurso, rate limiting por IP/conta, recuperação/troca de senha, armazenamento de segredos, auditoria com retenção, sessões multiprocesso e rollback. O SessionRegistry é single-process, intencionalmente in-memory.

Operações potencialmente destrutivas exigem testes isolados em discos virtuais, backup, autorização explícita, confirmação e rollback. Nenhum disco do Unraid será conectado ao laboratório.

## Verificação

Os 81 testes automatizados incluem bootstrapping único, permissões, recusa de symlinks, hashing, limites de login, expiração de sessões, CSRF, cookies e bloqueio das ações administrativas.

A imagem v0.5 USB continua não compilada por restrição anterior na execução remota. A revisão web não altera a imagem USB.
