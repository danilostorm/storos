# Fase 0 — protocolo de laboratório

Estado: preparado, não executado. Não aplicar a comandos de produção sem planejar janela e recuperação.

## 1. Inventário sem alterar o host

O script [collect_host.py](../scripts/collect_host.py) usa somente leitura de informações locais e imprime JSON. Não instala pacotes, reinicia serviços, muda drivers ou escreve em sysfs. Não coleta hostname, IP, serial de disco, credenciais ou configurações de VMs.

Após obter o repositório na branch phase0/gpu-feasibility, executar no host Linux a avaliar:

```sh
python3 scripts/collect_host.py
```

O resultado informa kernel/base, CPU/RAM, dispositivos gráficos PCI, driver, presença de interfaces SR-IOV/mdev e render nodes. Presença dessas interfaces não certifica compartilhamento. Não requer root; indisponibilidade de leitura aparece como null. É uma coleta parcial, não substitui consulta às matrizes ou ferramentas de API gráfica.

## 2. Completar a ficha

Registrar GPU/ID PCI, driver e firmware; CPU/placa-mãe/BIOS/IOMMU; versões QEMU/libvirt/Mesa; API disponível no host; versão dos dois guests; workload e resolução. Conferir se o host continuará acessível sem a GPU testada. Definir armazenamento descartável e backup de configurações antes de mudanças.

Para Linux, registrar resultados de glxinfo/vulkaninfo quando disponíveis, depois de revisar a saída antes de compartilhá-la. Não instalar ou atualizar kernel/driver automaticamente como parte da coleta. Para Windows, preparar coleta específica somente se essa base for escolhida para o laboratório.

## 3. Ensaio em sequência

| Etapa | Procedimento | Evidência / aceite |
| --- | --- | --- |
| Base | Uma VM e workload gráfico por vez | Renderer acelerado; baseline de FPS/latência, CPU, RAM e consumo GPU |
| Simultâneo | Duas VMs no mesmo dispositivo físico | Provar mesma GPU, workload concorrente e métricas em ambas; sem fallback CPU |
| CPU | Carga concorrente com prioridades diferentes | Limites obedecidos, host responsivo e resultado medido |
| RAM | Crescer/reduzir demanda dentro de limites | Memória devolvida confirmada; piso e reserva preservados; sem OOM |
| Métrica ausente | Interromper coleta guest de forma controlada | Nenhuma redução agressiva; diagnóstico visível |
| Recuperação | Reiniciar uma VM durante uso da outra | Registrar impacto; não aceitar travamento do host como resultado normal |
| Duração | 8 horas concorrentes no workload-alvo | Logs de erros e estabilidade, sem chamar isso ainda de homologação v1.0 |

Não executar carga que exceda RAM/VRAM disponível deliberadamente sem limite de parada. Interromper se houver travamento do host, perda de acesso administrativo, erro de memória ou degradação fora do limiar definido antes do teste.

## 4. Relatório a preencher

ID do teste; data; versões completas; GPU física e render backend; duas VMs/guests; método de acesso; configuração CPU/RAM/GPU; workload/configuração; tempo; métricas isoladas e concorrentes; falhas; resultado; limitações; evidência de aceleração; próximo passo. Usar identificadores de teste em vez de segredos/nomes privados.

STOR-009 está em triagem documental. STOR-010 é comparação preliminar. STOR-011 tem protocolo, mas o laboratório físico continua pendente. Fase 0 só termina com prova ou bloqueio formal e decisão de Danilo.
