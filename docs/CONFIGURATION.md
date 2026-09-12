# Configuração persistente e painel web — Fase 1

Este incremento cria a fundação de configuração persistente do StorOS sem habilitar escrita no libvirt.

## Estado persistente

A configuração fica em `/var/lib/storos/config`:

- `current.json`: configuração ativa.
- `revisions/NNNNNN.json`: histórico por geração.
- `.lock`: serializa escritores locais.

Cada alteração exige validação completa, pode usar `--expected-generation` para controle otimista de concorrência e grava primeiro a nova revisão antes de substituir `current.json` atomicamente. Um crash antes da troca mantém a configuração anterior como ativa. Rollback não apaga histórico: ele cria uma nova geração a partir da revisão escolhida.

As gravações críticas usam `fsync` no arquivo e no diretório após a troca atômica. O mesmo cuidado é aplicado ao token administrativo, para que a prova de persistência entre boots não dependa apenas do cache do host.

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

## Marcador seguro de prontidão

O service executa `storosctl web-marker` depois que o servidor HTTP é iniciado. O comando autentica localmente em `/api/config`, confirma que a resposta é idêntica ao documento persistido e publica no console apenas:

- geração da configuração;
- SHA-256 canônico da configuração;
- SHA-256 do token administrativo.

O token bruto não é impresso pelo marcador. O workflow de boot compara os fingerprints do primeiro e do segundo boot no mesmo QCOW2; igualdade dos hashes, junto com `boot_count=1 → 2`, é a prova automatizada de que configuração e identidade administrativa sobreviveram ao reboot e que o endpoint autenticado respondeu.

O CI espera prontidão real em vez de encerrar cada VM após um tempo fixo. O primeiro boot TCG recebe uma janela maior porque executa trabalho único de inicialização; assim que `STOROS_WEB_READY` aparece, o QEMU é encerrado e o mesmo QCOW2 é usado no segundo boot.

## Limites deste marco

- Sem criação, edição, start/stop ou remoção de VMs pelo painel.
- Sem TLS integrado ainda.
- Sem usuários múltiplos/RBAC.
- Sem descoberta mDNS ou configuração automática de rede.
- O fingerprint do token é evidência de persistência, não substitui política futura de rotação/credenciais.
- GPU compartilhada continua fora deste marco e exige validação física separada.
