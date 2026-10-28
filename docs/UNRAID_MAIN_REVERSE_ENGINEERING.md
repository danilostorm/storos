# StorOS: engenharia reversa estrutural da tela Main do Unraid

Verificado no AEROCOOL em outubro de 2026 mediante leitura das páginas de uma instalação Unraid do proprietário. O script tools/study_unraid_main.py inspeciona somente seis páginas de interface, registra SHA-256, tamanho e alguns símbolos específicos em docs/UNRAID_MAIN_STATIC_MAP.json. Não executa o Unraid, não lê chaves/licenças e não copia código de terceiros para StorOS.

## Mapeamento real dos módulos

| Área | Página encontrada | Comportamento visível | Módulo StorOS |
|---|---|---|---|
| Array Devices | dynamix/ArrayDevices.page | Lista de discos do array com main_filter | Seção isolada, sem array fictício |
| Pool Devices | dynamix/CacheDevices.page | Gerencia pools usando cache_filter | Seção isolada, sem pools fictícios |
| Boot Device | dynamix/BootDevice.page | Separa flash do boot | Detecta dispositivo pela montagem /boot |
| Array Operation | dynamix/ArrayOperation.page | Ações condicionadas a fsState, referências a paridade | Ações desabilitadas, proteção de dados |
| Disk List | dynamix/DiskList.page | Lista dinâmica de discos | lsblk, partições e estatísticas reais |
| Unassigned Devices | unassigned.devices/UnassignedDevices.page | Plugin próprio para discos e montagens externas | Outros dispositivos detectados; nunca presume que estão livres |

Conclusão: o Unraid separa array, pools, dispositivo de boot e dispositivos adicionais em fontes e estados distintos. O StorOS agora oferece seções correspondentes, porém a sua implementação é independente, com leituras reais de lsblk, statvfs, sysfs e SMART. Não carrega arquivos ou bibliotecas proprietárias do Unraid.

A análise de páginas PHP é engenharia reversa estática verdadeira, mas não equivale a engenharia reversa de todo o kernel, paridade, array, Docker Manager ou licenciamento do Unraid. Ghidra não foi executado nesta etapa, porque o código relevante da interface está disponível como texto PHP e arquivos de página.

## Segurança e recursos ainda ausentes

O endpoint /api/storage acessa apenas os discos da instância StorOS onde roda, jamais os discos físicos do AEROCOOL através da VM. Um grupo não configurado não significa proteção ativa; nenhum disco extra pode ser mostrado automaticamente como formatável.

Ações reais de array, pools, montagem, RAID, usuários, Docker Compose, loja com instalação, VMs e rede dependem de um daemon administrativo isolado com autenticação nativa, RBAC, auditoria, proteção CSRF, confirmação de discos e testes de rollback no laboratório. Não é seguro habilitar botões que operem com privilégios do host sem isso.

A prévia web de laboratório permanece em modo de leitura, com gateway HTTPS autenticado, backend em 127.0.0.1 e requisições POST rejeitadas.
