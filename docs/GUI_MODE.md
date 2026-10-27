# StorOS GUI Mode — versão experimental
O StorOS inicia no modo servidor/headless por padrão e expõe apenas um painel local em `127.0.0.1:8765`, ainda sem autenticação para acesso de rede. Assim ele não abre o painel externamente.
A imagem de prévia GUI inicia diretamente na interface gráfica; o modo servidor padrão é mantido na imagem v0.1.1. O modo gráfico é **opcional** e exibe o mesmo painel no monitor/VNC da máquina com **Xorg + LightDM + Openbox + Firefox em modo kiosk**, usando a conta local sem privilégios `storos-gui`.

## Preparação
- Compilar o Containerfile GUI em uma VM Fedora de laboratório; jamais fazer `dnf/rpm-ostree` no host Unraid.
- Gerar disco QCOW2/RAW a partir da imagem OCI GUI, configurar acesso admin via blueprint e testar na VM com vídeo VNC/QXL ou virtio.
- Inicializando pela imagem GUI, o VNC deverá abrir diretamente a sessão de navegador; a imagem de servidor permanece em `multi-user.target`.
- Para voltar ao modo servidor: `sudo storos-gui-mode disable` e reiniciar.

**Atenção:** a conta do modo gráfico utiliza autologin LOCAL e abre apenas o protótipo de painel read-only. Não deve ser usada para tarefas administrativas privilegiadas. Exige console físico/VNC protegido; não expõe a API na rede. **A nova imagem com GUI automático precisa ser recompilada e testada na VM; o primeiro QCOW2 confirmou boot e pacotes instalados, mas não conseguiu habilitar GUI pela ferramenta remota de testes devido ao confinamento SELinux.**

## Status separado por build
O StorOS v0.1.1 headless teve boot UEFI, SSH e HTTP 200 confirmados em VM de laboratório. Isso não confirma a build GUI; a imagem GUI e o boot gráfico precisam de homologação própria.

## Teste realmente concluído em 27/10/2026
A segunda build `StorOS-gui-default.qcow2` foi verificada pelo QEMU, inicializada em VM UEFI separada com vídeo VirtIO/VNC. A sessão `graphical.target` carregou LightDM + Xorg, fez login automático local na conta restrita `storos-gui` e iniciou Firefox em modo kiosk apontando para `http://127.0.0.1:8765/`. A captura VNC mostrou o dashboard com dados da VM. Os endpoints `/` e `/api/status` responderam HTTP 200.

**Como testar no AEROCOOL:** painel Unraid > VMs > `StorOS-BootTest-GUI-Default` > VNC Remote. Não é necessário usar `storos-gui-mode enable` nesta build, pois já inicia em modo gráfico.

**Nota:** ainda não é release para pendrive físico; imagens GUI do laboratório foram construídas com chave pública SSH de teste.

## Correção noVNC e acesso HTTPS no laboratório
O noVNC do Unraid utiliza `/wsproxy/<websocket-port>/`, portanto a VM precisa de atributo `websocket` além de `port`. A VM `StorOS-BootTest-GUI-Default` foi configurada para WebSocket `5717`, VNC `5917`, ambos limitados ao loopback `127.0.0.1` do AEROCOOL. A VM de laboratório foi desligada graciosamente e reiniciada. O handshake QEMU em 5717 retornou HTTP 101, e o Unraid encaminha essa porta somente mediante a sessão autenticada do painel. O script `tools/test-boot-gui.sh` agora inclui a mesma configuração.

A API StorOS continua atendendo **apenas em `127.0.0.1:8765` dentro da VM** e ainda é read-only, sem autenticação própria. Para testes na LAN, criou-se o gateway `tools/lan_gateway.py`, acessível em `https://192.168.30.10:18443/`, protegido por senha e certificado TLS autoassinado (30 dias). O gateway aceita apenas GET/HEAD numa lista fechada de recursos, somente da LAN `192.168.30.0/24`. Encaminha as requisições por túnel SSH de `127.0.0.1:18766` no host até `127.0.0.1:8765` dentro da VM.

O serviço HTTPS e o túnel são **temporários e não são iniciados automaticamente após reboot do Unraid**. O certificado, a senha e a chave SSH permanecem na pasta `lab/` ignorada pelo Git, sem publicação externa. Não expor o painel sem autenticação fora da LAN nem usá-lo em produção; o certificado autoassinado requer confirmação no navegador.
