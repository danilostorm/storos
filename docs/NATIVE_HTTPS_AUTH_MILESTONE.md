# StorOS — integração HTTPS com autenticação nativa (opt-in)

## Implementação

A porta de laboratório HTTPS 18444 continua protegida por autenticação Basic e limitada à LAN do AEROCOOL. O gateway oferece as seguintes rotas:

- GET /api/native/status: informa se o login nativo está configurado
- POST /api/native/login: usuário e senha encaminhados a socket Unix privado, com verificação de Origin e Host
- GET /api/native/me: consulta da sessão via cookie HttpOnly
- POST /api/native/logout: exige sessão e token CSRF

O login funciona somente quando um administrador habilita explicitamente --auth-socket apontando para um socket Unix privado. O modo padrão está desativado.

A senha nunca fica em argumentos ou cookies. A sessão chega ao navegador apenas por cookie __Host- com Secure, HttpOnly e SameSite=Strict, sem Domain. O navegador guarda somente o token CSRF temporário em sessionStorage, jamais o token de sessão. O gateway fornece cache no-store.

O bridge tools/native_auth_bridge.py recusa arquivos que não sejam sockets Unix, diretórios pais sem permissão 0700, proprietário diferente do processo gateway, endpoints arbitrários e respostas grandes. Não intermedeia Docker, Compose, discos, shell ou contas de host. O backend existente continua só de leitura.

## Estado no laboratório

O gateway ativo não tem --auth-socket configurado: a autenticação nativa continua desativada, com Basic obrigatório. Nenhuma conta ou senha padrão foi criada e nenhum daemon administrativo com privilégios foi ligado.

Em Sistema > Segurança, a interface mostra um formulário de login somente quando o serviço de autenticação estiver provisionado e habilitado. A instalação de apps via socket continua limitada a VM opt-in e nunca é exposta pela ponte HTTPS.

## Testes

tests/test_native_auth_web.py executa gateway HTTP temporário em loopback e serviço privado de autenticação com socket Unix, validando Basic, cookie seguro, login, sessão, CSRF/logout, proteção Origin/Host, modo desativado e recusa de endpoints administrativos. São testes locais, não portam serviço administrativo para LAN.

## Limites restantes

Antes de ativar login nativo: conta provisionada em StorOS, socket restrito ao gateway, política de recuperação, rate limiting por IP, auditoria persistente, certificados adequados e revisão de segurança. Para escrita administrativa: daemon isolado, privilégios mínimos e testes/rollback. A imagem USB v0.5 continua não compilada; a v0.4 já teve boot UEFI e BIOS no QEMU.
