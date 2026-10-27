# StorOS GUI Mode — versão experimental
O StorOS inicia no modo servidor/headless por padrão e expõe apenas um painel local em `127.0.0.1:8765`, ainda sem autenticação para acesso de rede. Assim ele não abre o painel externamente.
O modo gráfico é **opcional** e exibe o mesmo painel no monitor/VNC da máquina com **Xorg + LightDM + Openbox + Firefox em modo kiosk**, usando a conta local sem privilégios `storos-gui`.

## Preparação
- Compilar o Containerfile GUI em uma VM Fedora de laboratório; jamais fazer `dnf/rpm-ostree` no host Unraid.
- Gerar disco QCOW2/RAW a partir da imagem OCI GUI, configurar acesso admin via blueprint e testar na VM com vídeo VNC/QXL ou virtio.
- Após iniciar pelo disco GUI, entrar via SSH como `storadmin` com chave de laboratório e executar `sudo storos-gui-mode enable`; reiniciar a VM para abrir o painel automaticamente no console VNC.
- Para voltar ao modo servidor: `sudo storos-gui-mode disable` e reiniciar.

**Atenção:** a conta do modo gráfico utiliza autologin LOCAL e abre apenas o protótipo de painel read-only. Não deve ser usada para tarefas administrativas privilegiadas. Exige console físico/VNC protegido; não expõe a API na rede. **Ainda requer teste de hardware/VM e liberação formal da imagem com GUI antes de uso em produção.**

## Status separado por build
O StorOS v0.1.1 headless teve boot UEFI, SSH e HTTP 200 confirmados em VM de laboratório. Isso não confirma a build GUI; a imagem GUI e o boot gráfico precisam de homologação própria.
