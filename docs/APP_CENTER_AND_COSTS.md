# StorOS v0.3 — App Center e módulo de custos

## Origem autorizada
O usuário é autor do código-fonte Tower Command Center, executado no servidor ZIEL. A lógica de **modelo energético, rateio de internet e custos por tempo ativo** foi adaptada de `tower-control/app/server.js` (conceitos `currentPowerModel`, `itemPower`, `computePlanShares` e `computeCosts`) para `backend/billing.py`, com testes independentes. Não foram copiados dados operacionais, históricos de clientes, usuários, tokens ou configurações privadas do ZIEL.

## Cálculo de custo
- Watts CPU e placa-mãe são rateados pelos threads do host e vCPUs destinadas a cada serviço.
- Watts RAM são rateados pela razão da memória reservada e memória física total.
- GPU dedicada é cobrada integralmente ao serviço que usa passthrough, **quando informado**; isso não representa GPU virtual compartilhada.
- kWh = watts alocados × horas ativas / 1000.
- Internet = valor total de plano × (GB usados pelo serviço / GB usados no ciclo). O módulo de `split_plan` garante soma exata de centavos no rateio em lote.
- Mensalidade estimada = energia + internet + custo opcional por hora ativa.
- **A tela é um simulador**, ainda não um coletor persistente. Os campos exigem entrada manual. Tarifas e Watts padrão 0, propositalmente para não afirmar valores de hardware não medidos.

## App Center
- Docker Engine (Moby) e Docker Compose já estão presentes na base uCore. O Containerfile GUI habilita os serviços, sujeito a teste de inicialização no QCOW2.
- Catálogo local: seis aplicativos com descrição e prévia de Compose; a validação `docker compose config --quiet` passou em todos os exemplos.
- Busca no Docker Hub via endpoint público `https://hub.docker.com/v2/search/repositories/` com HTTPS fixo, query filtrada, cache e limite de resultados.
- O botão **Ver Docker Compose** apresenta somente arquivo de exemplo; não faz pull, não grava arquivos de usuário nem sobe containers.
- **Instalação pelo navegador está desabilitada**. Isso precisa de serviço administrativo separado com autenticação, controle de permissões e auditoria; o frontend nunca deve receber `/var/run/docker.sock`.

## Segurança e próxima versão
1. Um onboarding de administração local, sem credenciais pré-embutidas na imagem distribuível e sem ssh key de laboratório.
2. Coletor persistente de eventos/horas/tráfego com testes de recuperação; configurações de preços e perfil de hardware editáveis e auditáveis.
3. Operações Docker Compose `validate/pull/up/down/logs` somente por daemon privilegiado com RBAC e confirmação, isolamento de volumes e backup; catálogo com revisão de imagens/tags.
4. Instalação física no USB apenas em notebook de teste, sem discos de produção; o RAW do laboratório contém chave SSH do laboratório e **não está pronto para distribuição**.
5. Implantar alertas, SMART, rede, VMs, monitoramento e histórico do Tower de maneira nativa, sem depender do Unraid.

## Qualidade validada
- Testes Python e JavaScript (sintaxe) no host de desenvolvimento.
- Consultas HTTP `200` para endpoints de catálogo, Docker Hub, Compose e custos em servidor temporário local.
- `docker compose config --quiet` aprovou todos os seis exemplos de Compose.
- Boot da imagem nova v0.3 e inicialização dos serviços precisam ser testados na VM separada antes de recomendação para USB.
