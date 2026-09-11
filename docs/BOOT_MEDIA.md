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
| Imagem de disco/mídia inicializável | Próxima entrega de empacotamento e teste |
| Pacote ZIP extraível | Possibilidade a avaliar; não existe no StorOS hoje |
| ISO de instalação/recuperação | Opcional, sem obrigação no roadmap |
| Sistema em RAM e persistência reduzida no USB | Não comprovado pelo build uCore; exigiria decisão e testes próprios |

Um sistema imutável não implica que a raiz inteira rode em RAM. Antes de recomendar pendrive comum, medir gravações e definir onde ficam logs, configuração persistente e dados. As VMs devem ter armazenamento persistente separado da mídia de boot quando configurado para esse fim.

## Próximo teste

Gerar um disco virtual descartável a partir da base validada e confirmar boot, rede, identidade StorOS e persistência após reinício. Depois validar a gravação e o boot em mídia física. Isso testa o sistema sem depender de uma ISO nem modificar o MOS atual.

## Referências verificadas

- [MOS: Create Bootable Media](https://github.com/mos-nas/mos-docs/blob/master/docs/Installation/Create-Bootable-Media.md): orienta preparar FAT32, baixar ZIP, extrair os arquivos e iniciar pela mídia; configuração inicial via WebUI.
- [Unraid: downloads](https://unraid.net/download): recomenda USB Creator para a maioria dos usuários, com boot e configuração pelo assistente; também apresenta caminhos para boot interno.
- [Unraid: instalador opcional](https://docs.unraid.net/unraid-os/getting-started/set-up-unraid/use-the-unraid-installer/): a documentação atual inclui ISO e IMG para preparar dispositivos de boot. Portanto, não afirmar que o Unraid nunca oferece ISO.

Essa correção muda a descrição da entrega e o plano de empacotamento, não o resultado dos testes já feitos. Nenhuma mídia StorOS foi gerada ou inicializada nesta atualização.
