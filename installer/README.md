# StorOS – Boot pelo pendrive (requisito principal)

## Especificação

StorOS **deve ser um sistema operacional inicializável e independente do Unraid**.

- Base proposta: Universal Blue uCore, baseado em Fedora CoreOS.
- Imagem OCI do sistema: `installer/Containerfile`.
- **Sistema de arquivos inicial:** XFS, conforme a definição de disco do uCore (`disk.yaml`), sujeito a validação.
- **Imagem RAW**: disco inteiro com tabela de partições e bootloader, destinado a ser gravado em um pendrive **de testes**. Não é só o painel.
- **Imagem QCOW2**: o mesmo sistema para validação primeiro em QEMU.
- Modo de operação na primeira versão: sistema e configuração persistem no próprio USB, sem modificar discos de dados.
- Atualizações atômicas / recuperação testada, com atenção ao desgaste do USB.
- A API v0.1 continua **somente leitura e local** por falta de autenticação. Para acesso remoto inicial, usar SSH com port-forward.

### Pré-requisitos de compilação

VM Fedora, com Podman, `image-builder` (osbuild) e chaves SSH públicas. Os builds envolvem acesso privilegiado a loop/mount dentro da VM; nunca rodar no host AEROCOOL.

1. Provisionar VM Fedora de build isolada, sem repassar discos físicos do host.
2. Obter/fixar dependências de versões confiáveis, imagem uCore com digest verificado e ferramentas.
3. Na VM, `cd /path/to/StorOS && bash installer/build-usb-image.sh ~/.ssh/id_ed25519.pub`.
4. Validar o QCOW2 em VM **sem nenhum volume de produção conectado**.
5. Após testes de BIOS e UEFI, verificar imagem RAW, tamanho de pendrive e integridade SHA256.
6. Gravar o `raw` no pendrive de teste usando ferramenta dedicada de gravação em um computador separado, conferindo o dispositivo duas vezes. **Gravar RAW apaga o pendrive inteiro**.
7. Verificar inicialização, rede, SSH, persistência entre reboots e ausência de escrita em qualquer outro disco.

### Correções encontradas no teste inicial

O primeiro QCOW2 confirmou boot UEFI, acesso SSH com chave e instalação do painel no filesystem. Porém, identificamos que a unidade systemd não foi habilitada no deployment e que os arquivos do painel ficaram com permissão 0600. O `Containerfile` foi corrigido para habilitar a unidade em `/usr/lib/systemd/system/multi-user.target.wants/` e dar permissão de leitura aos arquivos. **Exige nova compilação e reteste.**

### O que ainda NÃO está pronto

- Imagem ISO/RAW compilada e testada: **não**.
- Instalação gráfica, recuperação de senha e fluxo de configuração inicial: **não**.
- Login inicial por senha no console: **não** (o build requer chave SSH).
- Painel autenticado na LAN: **não**.
- Proteção de dados por paridade e gestão de arrays: **não**.
- Secure Boot e BIOS legacy: **não validados** (testar ambos antes de afirmar suporte).
- Firmware e boot em hardware real: **não validados**.
- Release distribuível ao usuário: **não**.

### Justificativa

É possível construir RAW/QCOW2 a partir de bootable containers com `image-builder`. O `ucore-minimal` é uma base já voltada a servidores, com bootc e recursos de host; nossa imagem e os serviços StorOS serão próprios. Precisamos auditar licenças de dependências e não copiar código do Unraid.

Fontes técnicas:
- https://unraid.net/blog/unraid-8-announced
- https://github.com/ublue-os/ucore
- https://osbuild.org/docs/developer-guide/projects/image-builder/usage/
- https://osbuild.org/docs/user-guide/image-descriptions/bootc/raw/
