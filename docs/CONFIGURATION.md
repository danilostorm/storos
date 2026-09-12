# Configuração persistente e painel web — Fase 1

Este incremento cria a fundação de configuração persistente do StorOS sem habilitar escrita no libvirt.

## Estado persistente

A configuração fica em `/var/lib/storos/config`:

- `current.json`: configuração ativa.
- `revisions/NNNNNN.json`: histórico por geração.
- `.lock`: serializa escritores locais.

Cada alteração exige validação completa, pode usar `--expected-generation` para controle otimista de concorrência e grava primeiro a nova revisão antes de substituir `current.json` atomicamente. Um crash antes da troca mantém a configuração anterior como ativa. Rollback não apaga histórico: ele cria uma nova geração a partir da revisão escolhida.

Comandos:

```bash
sudo storosctl config-init
sudo storosctl config-show
sudo storosctl config-history
sudo storosctl config-apply --config-file /caminho/config.json --expected-generation 1
sudo storosctl config-rollback --target-generation 1 --expected-generation 2
```

A configuração inicial mantém `features.vm_write_enabled=false`. Nesta fase o validador rejeita qualquer tentativa de ativar escrita em VMs.

## Painel web autenticado

`storos-web.service` inicia um painel HTTP mínimo e somente leitura. Por padrão ele escuta apenas em `127.0.0.1:8080`.

Rotas:

- `/healthz`: health check sem autenticação.
- `/`: resumo HTML autenticado.
- `/api/status`: snapshot do agente autenticado.
- `/api/config`: configuração ativa autenticada.

Métodos mutáveis (`POST`, `PUT`, `PATCH`, `DELETE`) são recusados. A autenticação usa HTTP Basic com usuário `admin` e um token aleatório persistido em `/var/lib/storos/auth/admin.token` com modo `0600`.

Para consultar o token localmente:

```bash
sudo storosctl web-token-show
```

A opção de escutar fora do loopback é bloqueada por padrão. `allow_insecure_lan=true` precisa ser explícito porque este primeiro painel ainda não implementa TLS. Exposição em LAN é portanto uma opção de laboratório, não configuração recomendada de produção.

Após alterar host/porta, reinicie o painel para reaplicar o listener:

```bash
sudo systemctl restart storos-web.service
```

## Limites deste marco

- Sem criação, edição, start/stop ou remoção de VMs pelo painel.
- Sem TLS integrado ainda.
- Sem usuários múltiplos/RBAC.
- Sem descoberta mDNS ou configuração automática de rede.
- GPU compartilhada continua fora deste marco e exige validação física separada.
