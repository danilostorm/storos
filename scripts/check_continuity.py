"""Check published change records and local Markdown links; no runtime validation."""
import pathlib
import re
import subprocess
import sys


def check(base=None):
    if base and set(base) != {'0'}:
        changed = subprocess.check_output(['git', 'diff', '--name-only', base, 'HEAD'], text=True).splitlines()
    else:
        changed = subprocess.check_output(['git', 'show', '--pretty=', '--name-only', 'HEAD'], text=True).splitlines()
    required = {'CHANGELOG.md', 'PROJECT_STATE.md'}
    if not required.issubset(changed):
        raise ValueError('Atualize os registros no mesmo envio: ' + ', '.join(sorted(required - set(changed))))
    for name in subprocess.check_output(['git', 'ls-files', '*.md'], text=True).splitlines():
        path = pathlib.Path(name)
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if link.startswith(('https:', 'http:', 'mailto:', '#')):
                continue
            if not (path.parent / link.split('#')[0]).exists():
                raise ValueError(f'Link local inexistente: {path}: {link}')
    print('Registros de continuidade e links relativos verificados.')


if __name__ == '__main__':
    try:
        check(sys.argv[1] if len(sys.argv) > 1 else None)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
