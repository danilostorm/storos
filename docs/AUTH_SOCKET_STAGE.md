# StorOS — autenticação nativa por socket Unix (laboratório)

## Estado real

O serviço independente está em backend/auth_socket.py. Usa somente um socket Unix em diretório privado 0700, socket 0600, contas em arquivo 0600 e auditoria local. Ele NÃO é servido pelo HTTPS atual, não está habilitado no boot, não cria contas por padrão, não executa comandos de root e não manipula Docker, VM, discos, usuários ou shares.

Operações suportadas:
- GET /v1/health: estado básico
- POST /v1/login: conta pré-existente, limitação de tentativas e emissão de sessão temporária
- GET /v1/me: nome e papel após Bearer token válido, sem segredos
- POST /v1/logout: exige sessão e CSRF, revoga sessão

Nenhuma rota administrativa do host está exposta. A auditoria guarda somente metadados.

## Segurança

- Diretório absoluto com permissão 0700 e arquivo regular de contas 0600, sem symlink.
- Socket existente é recusado para evitar sobrescrever outros serviços.
- Sem IP nem porta TCP; acesso exige permissão Unix no socket.
- Corpo JSON limitado a 2048 bytes e campos exatos.
- Cinco tentativas incorretas em 300 segundos bloqueiam a conta no processo.
- Sessões apenas em memória, expiração e revogação; token armazenado como SHA-256.
- Ações de alteração do host continuam proibidas mesmo para admin.
- A falha da auditoria bloqueia emissão de nova sessão e logout.

## Testes

tests/test_auth_socket.py cria conta fictícia e arquivos temporários, executa requisições reais contra socket Unix local, testa login, sessão, CSRF, logout, limite de tentativas, permissões, ausência de credenciais nos logs e proibição de ações administrativas. Ao final o servidor e dados temporários são apagados. Não usa VMs nem discos de produção.

## Ainda não implementado

O serviço não representa login nativo web. A porta HTTPS atual mantém autenticação Basic do gateway de laboratório. Não há daemon privilegiado instalado nem identidade real criada.

Para um login nativo no navegador são necessários proxy HTTPS para o socket com proteção de origem, cookies seguros e CSRF, conta/recovery, sessões multiprocesso, limitação por IP, implantação systemd com usuário dedicado e revisão de segurança. Tudo isso deverá anteceder operações de escrita.

A imagem USB v0.5 permanece não compilada; este código existe apenas no repositório e no laboratório.
