"""Read-only, dependency-free Linux inventory for the StorOS Phase 0 lab."""
import json
import os
from pathlib import Path
import platform


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def inventory():
    cpu = read('/proc/cpuinfo') or ''
    models = sorted({line.split(':', 1)[1].strip() for line in cpu.splitlines() if line.startswith('model name') and ':' in line})
    memory = next((line.split(':', 1)[1].strip() for line in (read('/proc/meminfo') or '').splitlines() if line.startswith('MemTotal:')), None)
    devices = []
    for path in sorted(Path('/sys/bus/pci/devices').glob('*')):
        device_class = read(path/'class')
        if not device_class or not device_class.startswith('0x03'):
            continue
        driver = path/'driver'
        devices.append(dict(pci_address=path.name, vendor=read(path/'vendor'), device=read(path/'device'),
                            driver=driver.resolve().name if driver.is_symlink() else None,
                            iommu_group=(path/'iommu_group').resolve().name if (path/'iommu_group').is_symlink() else None,
                            sriov_totalvfs=read(path/'sriov_totalvfs'),
                            mdev_types=sorted(p.name for p in (path/'mdev_supported_types').glob('*'))))
    distro = {}
    for line in (read('/etc/os-release') or '').splitlines():
        key, sep, value = line.partition('=')
        if sep and key in ('ID', 'VERSION_ID', 'PRETTY_NAME'):
            distro[key] = value.strip('"')
    return dict(schema_version=1, kernel=platform.release(), architecture=platform.machine(),
                distribution=distro, cpu_models=models, logical_cpus=os.cpu_count(), total_memory=memory,
                kvm_present=Path('/dev/kvm').exists(), gpu_devices=devices,
                render_nodes=sorted(p.name for p in Path('/dev/dri').glob('renderD*')),
                warning='Inventory only; no GPU sharing or virtualization support certified.')


if __name__ == '__main__':
    print(json.dumps(inventory(), indent=2, ensure_ascii=False))
