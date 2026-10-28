# StorOS — etapa 1: navegação e legibilidade

Alterações aplicadas apenas ao painel web do laboratório, sem criar VMs, instalar
pacotes de sistema ou tocar nos discos do AEROCOOL.

- Botão de recolher/expandir a barra lateral no cabeçalho; modo compacto de 74px
  mantém ícones, títulos ao passar o mouse e rótulos acessíveis.
- Botões próprios para abrir/fechar os submenus, sem perder a ação de navegação
  do nome da seção.
- Menu lateral móvel como gaveta, com fundo escurecido e fechamento por toque
  fora, seleção de página ou tecla Escape.
- Aumento do tamanho padrão dos textos de menu, tabelas, indicadores,
  formulários e botões. Controle A+ no topo alterna entre 3 tamanhos.
- Preferências armazenadas somente no navegador, com fallback seguro se
  localStorage estiver indisponível.
- O painel permanece apenas de leitura, com as APIs existentes; clicar em um
  recurso ainda não implementado abre seu aviso, não executa ação administrativa.

## Escopo ainda não implementado

Menu legível não significa recurso funcional. Este marco não habilita escrita
em discos, criação de usuários, armazenamento SMB/NFS, atualização de plugins,
instalação de apps com um clique, Docker Compose up/down nem criação de VMs.

## Validação

- Testes Python do projeto, validação sintática do JS com Node.
- Prévia de laboratório em https://192.168.30.10:18444/.
- HTTPS autenticado mantém HTTP 401 para visitante sem credenciais; assets e
  APIs essenciais retornam HTTP 200 com autenticação.
- Captura do Firefox headless na VM existente mostra o novo botão do menu e A+,
  com fonte padrão maior. A revisão manual de interações em tela sensível ao
  toque e no notebook permanece recomendada.

Próxima etapa sugerida: ativar Armazenamento/Compartilhamentos em modo leitura
e depois administração autenticada, ou começar pelo gerenciador Docker/Compose.
