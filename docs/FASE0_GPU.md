# Fase 0 — investigação inicial de GPU

Data: **11/09/2026**. Estado: pesquisa documental concluída para esta primeira triagem; validação física pendente. A revisão 2 e o início da Fase 0 foram aprovados por Danilo com “Ta aprovado.” na conversa do projeto. [PR #1 integrado](https://github.com/danilostorm/storos/pull/1).

## Resultado inicial

Ainda não é possível escolher uma base definitiva ou homologar as placas atuais. Há dois caminhos distintos para testar: virtualização de GPU oferecida pelo fabricante em hardware compatível e aceleração gráfica virtual via VirGL/Venus para guests Linux. A segunda merece teste antes de concluir que é preciso trocar a placa; não equivale a particionamento físico ou compatibilidade universal.

## Matriz de triagem

“Não listado” significa ausência na matriz oficial consultada, não impossibilidade de todo mecanismo alternativo. Nenhuma linha foi testada em hardware nesta sessão.

| Placa / caminho | Evidência e estado | Próximo passo |
| --- | --- | --- |
| RTX 3080 Ti / NVIDIA vGPU oficial | Não consta da lista oficial de GPUs vGPU; não homologar esse caminho para a GeForce | Não instalar desbloqueios; avaliar a rota gráfica virtual Linux |
| RTX 3080 Ti / Hyper-V GPU-P documentado para Server 2025 | Não consta da lista de GPUs da página Microsoft consultada | Não generalizar relatos sobre Windows cliente para suporte Server |
| RX 550 / AMD GIM SR-IOV | Não consta da matriz da release GIM 9.2.0.K consultada | Não presumir SR-IOV por ser AMD; investigar rota Mesa |
| RX 550 / Hyper-V GPU-P documentado para Server 2025 | Também não consta da lista consultada | Sem homologação neste caminho |
| RTX 3080 Ti / Linux + virtio-gpu/Venus | Protocolo e requisitos de drivers documentados; combinação desta placa não testada pelo StorOS | Conferir driver, extensões, kernel/QEMU e executar dois guests Linux |
| RX 550 / Linux + VirGL/Venus | Aceleração por GPU do host e rota RADV documentadas; modelo exato não homologado | Confirmar driver/render node e testar API gráfica em dois guests |
| NVIDIA A2/A10/L4, exemplos | Listadas em NVIDIA vGPU e Microsoft GPU-P; dependem da combinação completa e termos | Referências de hardware alternativo, não recomendação de compra |
| AMD Radeon PRO V710 | Matriz GIM 9.2.0.K descreve 1–12 VFs e combinação Ubuntu/driver específica | Alternativa a pesquisar com custo, equipamento e guest compatíveis |

Fontes: [NVIDIA GPUs suportadas](https://docs.nvidia.com/vgpu/gpus-supported-by-vgpu.html), [Microsoft GPU partitioning](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/gpu-partitioning), [AMD GIM 9.2.0.K](https://github.com/amd/MxGPU-Virtualization/releases/tag/9.2.0.K), [VirGL](https://docs.mesa3d.org/drivers/virgl.html) e [Venus](https://docs.mesa3d.org/drivers/venus.html). Consultadas em 11/09/2026; as matrizes podem mudar.

## O que cada rota demonstra

### NVIDIA vGPU

A lista oficial contém modelos profissionais/datacenter e informa que o suporte também depende do hipervisor e da versão do software. A ausência da RTX 3080 Ti impede anunciá-la como suportada por essa solução. Ainda falta selecionar edição/licença, driver e guest de qualquer hardware alternativo; preços não foram cotados. [Lista NVIDIA](https://docs.nvidia.com/vgpu/gpus-supported-by-vgpu.html).

### Hyper-V GPU-P

A Microsoft documenta fracionamento da GPU entre VMs no Windows Server 2025, com lista de GPUs e guests. DDA atribui a placa inteira a uma VM e não cumpre simultaneidade. Essa documentação não certifica a GeForce/RX 550 nem todos os cenários de Windows cliente. [GPU-P](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/gpu-partitioning), [DDA e planejamento](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/plan-for-gpu-acceleration-in-windows-server).

### AMD GIM

GIM é o módulo AMD para virtualização SR-IOV. A release consultada publica combinações específicas de placa, kernel, guest e driver; a RX 550 não está nela. O suporte a múltiplas VFs de outro produto não se transfere para Radeon de consumo. [Repositório](https://github.com/amd/MxGPU-Virtualization), [release](https://github.com/amd/MxGPU-Virtualization/releases/tag/9.2.0.K).

### VirGL/Venus: hipótese prioritária para aproveitar as placas existentes

VirGL oferece GPU 3D virtual a guests QEMU usando a GPU do host. A documentação descreve uma pilha Linux; não certifica suporte Windows/Direct3D equivalente. Inferência de engenharia: dois guests com renderizadores usando a mesma GPU são uma hipótese de compartilhamento a testar, não resultado já obtido. [Mesa VirGL](https://docs.mesa3d.org/drivers/virgl.html).

Venus serializa comandos Vulkan e declara requisitos de driver; a página consultada inclui RADV e NVIDIA proprietário 570.86 ou posterior entre os drivers testados. Para dGPU com CPU Intel, descreve requisitos kernel 6.16+, QEMU 11.0+ e uma opção relacionada a guest PAT. Isso orienta o laboratório, sem certificar a RTX 3080 Ti/RX 550. Não basta ter Vulkan para garantir compatibilidade. [Mesa Venus](https://docs.mesa3d.org/drivers/venus.html).

Essa rota precisa validar aceleração real, evitando fallback CPU como llvmpipe/lavapipe, isolamento, travamentos e desempenho simultâneo. Não promete VRAM dedicada, CUDA, NVENC, anti-cheat ou Windows. Também exige avaliar a superfície de ataque do renderer; compartilhamento por API não equivale a isolamento por SR-IOV.

## Comparação inicial das bases — STOR-010 parcial

| Base candidata | O que testar | Limitação da decisão atual |
| --- | --- | --- |
| Linux com KVM/QEMU/libvirt | CPU/RAM e VirGL/Venus; drivers fabricantes quando suportados | Melhor candidato inicial para laboratório Linux, por inferência, não escolha final da distribuição |
| MOS/Devuan | Disponibilidade das versões e render backend; reaproveitamento do Guardian | Ter QEMU não comprova que o pacote inclua todos os recursos gráficos |
| Proxmox | Compatibilidade de pacotes e configuração dos dispositivos virtuais | Interface existente não remove limitações de hardware/driver |
| Windows Server/Hyper-V | GPU-P em hardware listado, guests e orçamento de licenças | Não resolve documentalmente as duas placas atuais; muda a proposta de base aberta |

Não será iniciado fork extenso nem compra de placa antes dos testes. A decisão final incluirá workload principal, guests desejados, custo e manutenção, e será submetida ao go/no-go previsto no roadmap.

## Bloqueio atual

Este ambiente de trabalho não possui /dev/kvm nem /dev/dri. Não há acesso configurado ao servidor do usuário. Portanto, não executamos guests, benchmarks ou homologação. A próxima entrada é o inventário do host de laboratório e a definição dos dois guests/workloads, seguindo [o protocolo](FASE0_LAB.md).
