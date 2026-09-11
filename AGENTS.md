# Regras de trabalho e continuidade do StorOS

Aplicam-se a colaboradores humanos e assistentes de IA em todo o repositório. Criadas por solicitação de Danilo em 11/09/2026.

## Antes de começar

1. Leia PROJECT_STATE.md, CHANGELOG.md, ROADMAP.md e docs/APROVACAO.md.
2. Confira branch, commits recentes, PRs abertos e alterações locais. O trabalho mais recente pode estar em um PR, não em main.
3. Considere instruções novas e explícitas do usuário; registre mudanças de direção. Não trate propostas como implementação ou testes como aprovação de produção.
4. Preserve trabalho de terceiros. Se o estado documental divergir do Git, investigue e registre a divergência antes de continuar.

## Em toda atualização publicada

- Toda publicação de conteúdo no GitHub, inclusive documentação, correções, dependências e CI, deve incluir CHANGELOG.md e PROJECT_STATE.md no mesmo commit ou lote de commits enviado. Não adiar o registro para outro chat.
- No CHANGELOG: data, identificador da atualização, mudança, motivo, verificação, limitações e referência ao PR. Preserve entradas anteriores; não reescreva resultados históricos.
- No PROJECT_STATE: fase, concluído, em andamento, bloqueios, decisões, testes realmente executados, próxima tarefa concreta e local do trabalho (branch/PR).
- Mudança de arquitetura também exige atualizar docs/ARQUITETURA.md ou criar decisão arquitetural referenciada. Mudança de prioridade exige ROADMAP.md.
- Não é necessário fabricar um número de release para documentos. Use identificadores de atualização; releases futuras agrupam entradas e usam tags próprias.
- Para evitar SHA autorreferente impossível, o registro pode apontar o PR/branch e a base anterior. O commit que contém a entrada é identificável pelo histórico do arquivo.
- Alterações apenas em metadados do PR devem ser resumidas na próxima entrada de conteúdo. Merge sem mudança de conteúdo usa o registro já incluído no PR; resoluções de conflito com mudança material exigem novo registro.

## Antes de encerrar a sessão

- Diga precisamente o que foi publicado e o que não foi testado. Não declarar instalação, compatibilidade GPU ou suporte em produção sem evidência.
- Deixe próxima tarefa executável, critérios de conclusão e pré-requisitos de acesso/hardware. Registre tentativas que falharam quando relevantes para evitar repetição.
- Não guardar senhas, tokens, chaves ou dados privados nos registros.
- Se não puder publicar, informe o bloqueio e mantenha os registros junto do trabalho local; não afirmar que outra IA já pode ler pelo GitHub.

## Direção do produto

VMs e compartilhamento simultâneo CPU/RAM/GPU são prioridade. Base aberta a comparação; MOS não é obrigatório. Passthrough exclusivo não cumpre compartilhamento GPU. Não contornar licenciamento ou prometer suporte de hardware não comprovado.

## Verificação automática

O workflow continuity verifica que o intervalo publicado altera CHANGELOG.md e PROJECT_STATE.md e que links relativos Markdown existem. No PR, usa a diferença em relação à base; no push, o intervalo enviado. Não prova qualidade/veracidade dos registros nem impede merges por si só: proteção de branch com check obrigatório depende de configuração administrativa e ainda não está confirmada.
