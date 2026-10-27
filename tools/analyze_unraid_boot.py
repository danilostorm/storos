#!/usr/bin/env python3
"""Structural inspection of an Unraid boot archive supplied by project owner.

Never extracts or runs proprietary executables. Reads only archive names/sizes
and the boot menu text. Never reads licensing or authentication material.
"""
import argparse
import hashlib
import json
import pathlib
import re
import zipfile

def analyze(path):
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist()
        known={i.filename:i for i in infos}
        menu='syslinux/syslinux.cfg'
        config=archive.read(menu).decode('utf-8','replace').replace('\r\n','\n') if menu in known else ''
        labels=re.findall(r'^label\s+(.+)$',config,flags=re.MULTILINE)
        kernels=re.findall(r'^\s*kernel\s+(.+)$',config,flags=re.MULTILINE)
        args=re.findall(r'^\s*append\s+(.+)$',config,flags=re.MULTILINE)
        return {
            'archive':pathlib.Path(path).name,
            'entries':len(infos),
            'boot_menu_sha256':hashlib.sha256(config.encode()).hexdigest() if config else None,
            'boot_choices':labels,
            'kernel_paths':sorted(set(kernels)),
            'gui_separate_initramfs':any('bzroot-gui' in x for x in args),
            'safe_mode_flag':any('unraidsafemode' in x for x in args),
            'efi_paths':sorted(x for x in known if x.startswith('EFI/') and not x.endswith('/')),
            'images_sizes':{k:known[k].file_size for k in ('bzimage','bzroot','bzroot-gui','bzmodules','bzfirmware') if k in known},
            'proprietary_executables_extracted':False,
            'license_files_inspected':False
        }

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive')
    print(json.dumps(analyze(p.parse_args().archive),ensure_ascii=False,indent=2))
