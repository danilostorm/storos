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
