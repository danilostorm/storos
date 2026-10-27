"""StorOS cost accounting, adapted from the user's Tower Command Center concepts.

Estimates are not meter readings. Input prices and hardware Watts must be configured.
No state is persisted or mutated by this module.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os

CENT = Decimal("0.01")

def number(value, name, minimum=0, maximum=100000000):
    try:
        n = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation) as e:
        raise ValueError(name + " inválido") from e
    if not n.is_finite() or n < minimum or n > maximum:
        raise ValueError(name + " fora do intervalo permitido")
    return n

def cash(value):
    return number(value, "preço").quantize(CENT, rounding=ROUND_HALF_UP)

def configured_model():
    """Default input template, not a claim about actual hardware consumption."""
    return {
        "currency": "BRL",
        "threads": os.cpu_count() or 1,
        "host_ram_gib": round(_memtotal() / (1024 ** 3), 2),
        "hardware": [
            {"id": "cpu", "name": "CPU (TDP informado pelo usuário)", "watts": 0, "allocation": "cores"},
            {"id": "board", "name": "Placa-mãe e ventoinhas", "watts": 0, "allocation": "cores"},
            {"id": "ram", "name": "Memória RAM total", "watts": 0, "allocation": "memory"},
            {"id": "gpu", "name": "GPU dedicada (se houver passthrough)", "watts": 0, "allocation": "dedicated"}
        ],
        "prices": {"electricity_kwh": 0, "uptime_hour": 0},
        "internet": {"plan_price": 0, "total_cycle_gb": 0},
        "note": "Preencha os watts e tarifas reais. Os valores são estimativas, não medições por VM."
    }

def _memtotal():
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0

def estimated_item(cpu_watts, board_watts, ram_watts, threads, host_ram_gib,
                   vcpus, ram_gib, gpu_watts, hours, electricity_kwh,
                   uptime_hour, plan_price, total_cycle_gb, item_cycle_gb):
    """Tower cost rules: CPU+board per thread, RAM per GiB, GPU dedicated.
    Energy kWh = allotted watts * active hours / 1000. Internet = plan price * item GB / total GB.
    """
    cpu, board, ram, gpu = [number(v, key, maximum=10000) for v, key in [
        (cpu_watts, "CPU"), (board_watts, "placa-mãe"), (ram_watts, "RAM"), (gpu_watts, "GPU")]]
    threads = number(threads, "threads", minimum=1, maximum=8192)
    host_ram = number(host_ram_gib, "RAM host", minimum=1, maximum=131072)
    cores = number(vcpus, "vCPUs", maximum=8192)
    guest_ram = number(ram_gib, "RAM item", maximum=131072)
    hours = number(hours, "horas", maximum=24 * 366)
    electricity = number(electricity_kwh, "tarifa de energia", maximum=10000)
    hour_price = number(uptime_hour, "preço da hora", maximum=10000)
    plan_price = number(plan_price, "preço internet", maximum=10000000)
    total_gb = number(total_cycle_gb, "GB total", maximum=10**12)
    item_gb = number(item_cycle_gb, "GB item", maximum=10**12)
    if item_gb > total_gb:
        raise ValueError("GB do item não pode exceder o GB total do plano")
    w_cpu = cpu * cores / threads
    w_board = board * cores / threads
    w_ram = ram * guest_ram / host_ram
    watts = w_cpu + w_board + w_ram + gpu
    kwh = watts * hours / 1000
    energy = cash(kwh * electricity)
    uptime = cash(hours * hour_price)
    internet = cash(plan_price * item_gb / total_gb) if total_gb else Decimal(0)
    total = energy + uptime + internet
    def rounded(v, places="0.000"):
        return float(v.quantize(Decimal(places), rounding=ROUND_HALF_UP))
    return {
        "currency": "BRL",
        "watts_total": rounded(watts),
        "watts_cpu": rounded(w_cpu),
        "watts_platform": rounded(w_board),
        "watts_ram": rounded(w_ram),
        "watts_gpu": rounded(gpu),
        "kwh": rounded(kwh),
        "hours": rounded(hours, "0.00"),
        "cost_energy": float(energy),
        "cost_uptime": float(uptime),
        "cost_internet": float(internet),
        "cost_total": float(total),
        "estimated": True
    }

def split_plan(price, traffic):
    """Exact cent allocation analogous to Tower's largest-user correction.
    Traffic: list of (identifier, GB used). No real consumption is inferred.
    """
    price = cash(price)
    rows = []
    for key, gb in traffic:
        if not isinstance(key, str) or not key or len(key) > 100:
            raise ValueError("identificador inválido")
        rows.append({"id": key, "gb": number(gb, "uso em GB", maximum=10**12)})
    total = sum((r["gb"] for r in rows), Decimal(0))
    if total == 0:
        return [{"id": r["id"], "gb": float(r["gb"]), "cost": 0.0} for r in rows]
    for r in rows:
        r["cost"] = cash(price * r["gb"] / total)
    remainder = price - sum((r["cost"] for r in rows), Decimal(0))
    if remainder:
        max(rows, key=lambda x: x["gb"])["cost"] += remainder
    return [{"id": r["id"], "gb": float(r["gb"]), "cost": float(r["cost"])} for r in rows]
