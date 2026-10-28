import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import check_usb_image as g

class USBImageGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.image=Path(self.temp.name)/"usb.img"
        with open(self.image,"wb") as f:
            f.truncate(3*1024**3)
            f.seek(510);f.write(b"\x55\xaa")

    def _json(self, types=None):
        types=types or [g.BIOS, g.EFI, "bc13c2ff-59e6-4262-a352-b275fd6f7172",next(iter(g.ROOTS))]
        return json.dumps({"partitiontable":{"label":"gpt","sectorsize":512,"partitions":[
            {"start":2048+i*10240,"size":10240,"type":t} for i,t in enumerate(types)
        ]}})

    def test_accepts_structural_gpt_bios_efi_root(self):
        with patch.object(g.subprocess,"run",return_value=CompletedProcess([],0,self._json(),"")):
            data=g.read_structure(self.image)
        self.assertTrue(data["bios_partition"])
        self.assertTrue(data["efi_partition"])
        self.assertFalse(data["boot_tested"])

    def test_rejects_missing_legacy_boot_partition(self):
        with patch.object(g.subprocess,"run",return_value=CompletedProcess([],0,self._json([g.EFI,next(iter(g.ROOTS))]),"")):
            with self.assertRaises(g.ImageCheckError):
                g.read_structure(self.image)

    def test_rejects_non_image_files_and_symlink(self):
        link=Path(self.temp.name)/"link.img"
        link.symlink_to(self.image)
        with self.assertRaises(g.ImageCheckError):
            g.read_structure(link)
        with self.image.open("r+b") as f:
            f.seek(510); f.write(b"\x00\x00")
        with self.assertRaises(g.ImageCheckError):
            g.read_structure(self.image)

    def test_overlapping_partitions_rejected(self):
        data=json.loads(self._json())
        data["partitiontable"]["partitions"][1]["start"]=4096
        with patch.object(g.subprocess,"run",return_value=CompletedProcess([],0,json.dumps(data),"")):
            with self.assertRaises(g.ImageCheckError):
                g.read_structure(self.image)

    def test_no_raw_device_operations(self):
        source=(ROOT/"tools/check_usb_image.py").read_text()
        for forbidden in ("losetup", "mount ", "mkfs", "dd if=", "of=/dev/"):
            self.assertNotIn(forbidden,source)

if __name__=="__main__":unittest.main()
