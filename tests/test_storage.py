import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import storage


class StorageInventoryTests(unittest.TestCase):
    def setUp(self):
        storage._cache = (0.0, None)

    def test_partition_usage_only_on_mount(self):
        root = {"name":"vda","type":"disk","size":10737418240, "tran":"virtio",
                "children":[
                    {"name":"vda1","type":"part","size":1024,"fstype":None,"mountpoints":[]},
                    {"name":"vda2","type":"part","size":4096,"fstype":"ext4","mountpoints":["/var"]}]}
        payload=json.dumps({"blockdevices":[
            {"name":"zram0","type":"disk","size":2048},
            root,
        ]})
        with mock.patch.object(storage, "_command", return_value=payload):
            with mock.patch.object(storage, "_smb_shares", return_value={"available":True,"items":[]}):
                with mock.patch.object(storage, "_nfs_shares", return_value={"available":True,"items":[]}):
                    with mock.patch.object(storage, "mount_usage", return_value={"percent":33}):
                        d=storage.inventory()
        self.assertTrue(d["available"])
        self.assertEqual(len(d["disks"]),1)
        self.assertEqual(d["disks"][0]["name"],"vda")
        self.assertIsNone(d["disks"][0]["partitions"][0]["usage"])
        self.assertEqual(d["disks"][0]["partitions"][1]["usage"]["percent"],33)
        self.assertFalse(d["disks"][0]["smart"]["available"])
        self.assertTrue(d["read_only"])

    def test_no_lsblk_returns_unavailable_not_fictitious_disks(self):
        with mock.patch.object(storage, "_command", return_value=None):
            with mock.patch.object(storage, "_smb_shares", return_value={"available":False,"items":[]}):
                with mock.patch.object(storage, "_nfs_shares", return_value={"available":False,"items":[]}):
                    d=storage.inventory()
        self.assertFalse(d["available"])
        self.assertEqual(d["disks"],[])

    def test_smb_reads_sections_but_not_users_or_secrets(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"smb.conf"
            p.write_text("[global]\nsecurity=user\n[homes]\npath=/home/%S\n[Filmes]\npath=/srv/media\nread only=yes\n")
            d=storage._smb_shares(p)
        self.assertEqual(d["items"],[{"name":"Filmes","path":"/srv/media","read_only":"yes"}])

    def test_nfs_skips_comments(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"exports"
            p.write_text("# example\n/srv/media 192.168.0.0/24(ro)\ninvalid foo\n")
            d=storage._nfs_shares(p)
        self.assertEqual(len(d["items"]),1)
        self.assertEqual(d["items"][0]["path"],"/srv/media")

    def test_missing_share_files_do_not_claim_empty_configuration(self):
        d=storage._smb_shares(Path("/nonexistent/random_smb_config.conf"))
        self.assertFalse(d["available"])

    def test_smart_virtual_never_queries_physical_device(self):
        with mock.patch.object(storage.subprocess,"run",side_effect=AssertionError("smartctl must not run")):
            d=storage._smart("vda","QEMU Virtual disk","virtio")
        self.assertFalse(d["available"])
        self.assertIsNone(d["health"])

    def test_smart_invalid_device_name_rejected(self):
        with mock.patch.object(storage.shutil,"which",return_value="/usr/sbin/smartctl"):
            d=storage._smart("sda;rm","",None)
        self.assertFalse(d["available"])


if __name__=="__main__":
    unittest.main()
