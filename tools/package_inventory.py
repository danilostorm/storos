#!/usr/bin/env python3
"""Read archive directory metadata only; never unpack or execute target files."""
import argparse
import zipfile
from pathlib import Path

def report(path):
    with zipfile.ZipFile(path) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        total = sum(i.file_size for i in infos)
        lines = [
            "# Inventário estrutural do pacote Unraid (somente metadados)",
            "",
            "Este documento registra nomes/tamanhos do arquivo ZIP oficial disponibilizado",
            "para análise de formato. Nenhum binário foi executado ou extraído.",
            "",
            f"- Arquivo: `{path.name}`",
            f"- Arquivos internos: **{len(infos)}**",
            f"- Total descomprimido: **{total/1048576:.1f} MiB**",
            "",
            "| Item de maior tamanho | Tamanho (MiB) |",
            "|---|---:|",
        ]
        for item in sorted(infos, key=lambda x: x.file_size, reverse=True)[:12]:
            safe_name = item.filename.replace("|", "\\|")
            lines.append(f"| `{safe_name}` | {item.file_size/1048576:.2f} |")
        lines.extend([
            "",
            "## Observações",
            "- A distribuição inclui imagens de inicialização (como `bzimage`, `bzroot`, `bzmodules` e `bzfirmware`).",
            "- O pacote não é código-fonte livre do Unraid e não será incorporado ao StorOS.",
            "- Estudo futuro: requisitos de boot e fluxos observáveis; comparação com componentes Fedora equivalentes.",
            "- Material sobre adulteração de GUID ou licença foi excluído desta investigação.",
            "",
        ])
        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zipfile", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    contents = report(args.zipfile)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(contents, encoding="utf-8")
        print("Saved metadata report:", args.output)
    else:
        print(contents)

if __name__ == "__main__":
    main()
