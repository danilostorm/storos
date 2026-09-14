# Mídia de boot do StorOS

Direção registrada em 11/09/2026 após Danilo corrigir o uso de “ISO instalável” como marco do projeto. O requisito é entregar uma forma simples de inicializar e configurar o sistema. ISO não é requisito do StorOS.

## Experiência pretendida

Preparar uma mídia de boot → inicializar o servidor por ela → acessar o painel pelo navegador → configurar conta, armazenamento e VMs.

O objetivo é boot direto do sistema pela mídia preparada. Não exigir que o usuário percorra um instalador tradicional em um segundo disco como único caminho. Provisionamento opcional para SSD/NVMe e instalação remota podem ser avaliados depois.

A primeira hipótese de empacotamento é uma imagem de disco comprimida para gravação em mídia de boot. Um pacote ZIP para extração direta exige outro arranjo de boot e só será anunciado se implementado e testado. O formato final deve seguir as necessidades de bootloader, partições, persistência e atualização da base.

## Distinções técnicas

| Artefato ou comportamento | Situação |
| --- | --- |
| Imagem OCI do Containerfile | Composição do sistema já construída no CI; não é arquivo pronto para copiar ao pendrive |
| Imagem QCOW2 | Pipeline de laboratório adicionada em BOOT-001; precisa de workflow verde para ser considerada comprovada |
| Imagem RAW/mídia física | Próxima etapa após validar QCOW2 e persistência |
| Pacote ZIP extraível | Possibilidade a avaliar; não existe no StorOS hoje |
| ISO de instalação/recuperação | Opcional, sem obrigação no roadmap |
| Sistema em RAM e persistência reduzida no USB | Não comprovado pelo build uCore; exigiria decisão e testes próprios |

Um sistema imutável não implica que a raiz inteira rode em RAM. Antes de recomendar pendrive comum, medir gravações e definir onde ficam logs, configuração persistente e dados. As VMs devem ter armazenamento persistente separado da mídia de boot quando configurado para esse fim.

## Pipeline BOOT-001

O workflow `Bootable media` segue este caminho:

1. reconstrói a imagem StorOS a partir do digest uCore já fixado;
2. executa `bootc container lint` e os checks de conteúdo;
3. publica a imagem intermediária somente em um registro Docker local efêmero do runner;
4. converte a imagem bootc em QCOW2 com a action oficial `osbuild/bootc-image-builder-action`;
5. inicializa o QCOW2 em QEMU/TCG, sem depender de `/dev/kvm`;
6. considera a prova concluída somente quando o console serial mostra o systemd iniciando `storos-agent.service` (`StorOS read-only host and VM observer`);
7. somente depois dessa evidência o CI grava `STOROS_BOOT_OK` em `boot-proof.txt` e preserva QCOW2/checksum/log de console como evidência temporária.

Não existe serviço extra de “prova de boot” dentro do StorOS: o próprio agente já habilitado é o marco observado. Nenhuma credencial padrão ou porta adicional é criada. O QEMU em TCG verifica inicialização funcional, não desempenho.

## Critérios do primeiro boot

O primeiro gate fecha somente quando o workflow remoto comprovar:

- artefato QCOW2 não vazio e reconhecido pelo `qemu-img`;
- kernel e systemd chegam ao StorOS;
- o console serial registra a inicialização de `storos-agent.service` e o CI gera `boot-proof.txt`;
- logs e checksum ficam disponíveis como evidência.

Depois disso, o próximo gate é **reiniciar o mesmo disco e comprovar persistência**. Só então a configuração persistente e o painel web passam a ser o foco principal.

## Referências verificadas

- [MOS: Create Bootable Media](https://github.com/mos-nas/mos-docs/blob/master/docs/Installation/Create-Bootable-Media.md): orienta preparar FAT32, baixar ZIP, extrair os arquivos e iniciar pela mídia; configuração inicial via WebUI.
- [Unraid: downloads](https://unraid.net/download): recomenda USB Creator para a maioria dos usuários, com boot e configuração pelo assistente; também apresenta caminhos para boot interno.
- [Unraid: instalador opcional](https://docs.unraid.net/unraid-os/getting-started/set-up-unraid/use-the-unraid-installer/): a documentação atual inclui ISO e IMG para preparar dispositivos de boot. Portanto, não afirmar que o Unraid nunca oferece ISO.
- [bootc: imagens compatíveis](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootc-images.md): requisitos de imagens bootc e validação com `bootc container lint`.
- [osbuild: bootc/Image Builder](https://osbuild.org/docs/bootc/): geração de discos QCOW2/RAW a partir de contêineres bootáveis.

Nenhuma mídia física StorOS foi gravada nesta atualização. Um workflow criado também não equivale a um boot verde; o resultado do Actions deve ser registrado separadamente.
