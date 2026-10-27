# Requisitos de produto StorOS (aprovados)

## Requisito obrigatório P0
**StorOS precisa ser instalável e dar boot pelo pendrive como sistema independente**, mesmo quando o Unraid não estiver instalado.

### Critérios de aceitação P0
1. Imagem original do StorOS, não um pendrive de boot do Unraid.
2. Imagem de disco inicializável (RAW para USB); futura ISO instaladora opcional.
3. Boot em VM QEMU/OVMF comprovado, e teste adicional de BIOS legado antes de alegar compatibilidade.
4. Sistema, dashboard e agentes StorOS iniciam com o hardware de teste.
5. Alterações de configuração persistem após reinicialização.
6. Sistema nunca seleciona/formata automaticamente discos de dados.
7. USB de instalação explicitamente escolhido por identificador e capacidade.
8. Possibilidade documentada de atualização e reversão para imagem anterior.
9. Testes de segurança, integridade e recuperação antes de distribuição.
10. Nenhuma dependência de binários proprietários do Unraid.

## Requisito P1: NAS
Inventário, SMART, partições/pools/sistemas de arquivos, SMB, NFS, usuários, ACLs, containers, VMs e backups com interfaces auditáveis.

## Requisito P2: proteção semelhante ao Unraid
Estudar **sem copiar** comportamento observado de paridade e discos de tamanhos diferentes. Implementar somente após especificação original, benchmarks, testes de falha e restauração. SnapRAID não substitui paridade em tempo real; não fazer essa alegação.

## Projeto experimental atual
O StorOS v0.1 só possui API/painel em modo de leitura. O código do builder foi preparado, mas não há imagem bootável gerada ou validada ainda.
