# StorOS — Etapa 2: Armazenamento real (somente leitura)

## Implementado

- API /api/storage: inventário local obtido via lsblk, exclusivo do sistema onde o StorOS executa, não do Unraid hospedeiro.
- Discos e partições: nome, tamanho, filesystem, rótulo, montagens, transporte, flag de somente leitura e ocupação dos volumes montados via statvfs.
- SMART: consulta limitada a smartctl -H -j -n standby, somente se acessível; sem sudo, sem acordar discos em standby. QEMU/VirtIO não anuncia saúde física inexistente.
- Samba: consulta às seções da configuração /etc/samba/smb.conf, sem contar [homes], [global], [printers] e [print$] como shares comuns.
- NFS: leitura das exportações /etc/exports, sem acessar ou alterar os dados compartilhados.
- Frontend: cartões e tabelas reais, com preenchimento seguro via textContent, sem operações mutáveis.
- Cache de 75 segundos, evitando varreduras SMART excessivas.
- Gateway HTTPS autenticado, API em loopback da VM, HTTP POST bloqueado.

## Verificação na VM StorOS-BootTest-v030

- Um disco virtual VirtIO vda de 10 GiB com quatro partições e montagens /boot e /var.
- SMART: indisponível porque o disco físico não é exposto ao sistema convidado.
- Nenhum compartilhamento SMB efetivo e nenhuma exportação NFS no StorOS convidado.
- HTTP 200 para /, /storage.js, /storage.css, /api/storage e /api/overview.
- HTTP 401 para /api/storage sem autenticação.
- 47 testes automatizados aprovados.
- Nenhum disco de produção conectado, nenhuma VM nova, nenhuma alteração em discos existentes.

## Próximos passos

Habilitar alterações de armazenamento apenas após desenvolver um daemon administrativo separado, com login, permissões granulares, autenticação CSRF, autorização por recurso, auditoria, confirmação de dispositivo e ensaios em discos virtuais descartáveis.

Este painel consulta apenas a VM StorOS. A imagem USB v0.4 compilada anteriormente não recebe automaticamente esta atualização.
