import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import storage
import modules


class MainParityTests(unittest.TestCase):
    def setUp(self):
        storage._cache = (0.0, None)
        modules._CACHE = (0.0, None)

    def test_one_boot_device_without_fake_array(self):
        devices = {"blockdevices": [
          {"name": "zram0", "type": "disk", "size": 1048576},
          {"name": "vda", "type": "disk", "size": 10737418240,
           "tran": "virtio", "children": [
              {"name": "vda1", "type": "part", "size": 10000, "fstype": "ext4",
               "mountpoints": ["/boot"]}]}
        ]}
        with mock.patch.object(storage, "_command", return_value=json.dumps(devices)):
            with mock.patch.object(storage, "_smb_shares", return_value={"available": True, "items": []}):
                with mock.patch.object(storage, "_nfs_shares", return_value={"available": True, "items": []}):
                    with mock.patch.object(storage, "mount_usage", return_value={"percent": 20}):
                        inv = storage.inventory()
        self.assertEqual(inv["sections"]["boot"]["items"], ["vda"])
        self.assertFalse(inv["sections"]["array"]["configured"])
        self.assertFalse(inv["sections"]["pools"]["configured"])
        self.assertEqual(inv["sections"]["array"]["items"], [])
        self.assertTrue(inv["read_only"])

    def test_other_disk_not_called_unassigned(self):
        devices = {"blockdevices": [
          {"name": "sdb", "type": "disk", "size": 10000, "tran": "virtio", "children": []}
        ]}
        with mock.patch.object(storage, "_command", return_value=json.dumps(devices)):
            with mock.patch.object(storage, "_smb_shares", return_value={"available": True, "items": []}):
                with mock.patch.object(storage, "_nfs_shares", return_value={"available": True, "items": []}):
                    inv = storage.inventory()
        self.assertEqual(inv["sections"]["other"]["items"], ["sdb"])
        self.assertIn("não são automaticamente discos livres", inv["sections"]["other"]["reason"])

    def test_io_initial_sample_is_not_invented(self):
        from unittest.mock import MagicMock
        storage._io_samples.clear()
        fake = MagicMock()
        fake.read_text.return_value = "1 2 10 4 3 2 30 5 0 0"
        with mock.patch.object(storage, "Path", return_value=fake):
            rate = storage._disk_io("vda")
        self.assertIsNone(rate["reads_bps"])
        self.assertIsNone(rate["writes_bps"])
        self.assertIsNone(rate["errors"])

    def test_io_negative_counters_are_not_rates(self):
        from unittest.mock import MagicMock
        storage._io_samples.clear()
        fake = MagicMock()
        fake.read_text.side_effect = ["1 0 90 0 1 0 90 0 0 0", "1 0 20 0 1 0 20 0 0 0"]
        with mock.patch.object(storage, "Path", return_value=fake):
            with mock.patch.object(storage.time, "monotonic", side_effect=[100.0, 101.0]):
                storage._disk_io("vda")
                rate = storage._disk_io("vda")
        self.assertIsNone(rate["reads_bps"])
        self.assertIsNone(rate["writes_bps"])

    def test_module_command_fails_safely(self):
        with mock.patch.object(modules.shutil, "which", return_value=None):
            inv = modules._json_lines(["docker", "volume", "ls"], ("Name",))
        self.assertFalse(inv["available"])
        self.assertEqual(inv["items"], [])

    def test_unknown_records_do_not_break_inventory(self):
        with mock.patch.object(modules, "_run", return_value={"available": True, "lines": ["bad-json", '{"Name":"Volume1"}']}):
            result = modules._json_lines(["docker", "volume", "ls"], ("Name", "Driver"))
        self.assertEqual(result["items"], [{"Name": "Volume1", "Driver": None}])

    def test_no_control_plane_enabled(self):
        with mock.patch.object(modules, "_users", return_value={"available": True, "items": []}):
            with mock.patch.object(modules, "_docker", return_value={}):
                with mock.patch.object(modules, "_vm_networks", return_value={"available": False, "items": []}):
                    with mock.patch.object(modules, "_system", return_value={}):
                        state = modules.collect()
        self.assertEqual(state["capabilities"]["admin_writes"], "desativadas")
        self.assertTrue(state["read_only"])

    def test_ui_has_real_disk_navigation(self):
        html = (ROOT / "web/index.html").read_text()
        js = (ROOT / "web/storage.js").read_text()
        self.assertIn('data-target="storage"><i data-icon="hard-drive"></i>Discos', html)
        for name in ("Dispositivos do Array", "Dispositivos dos Pools", "Dispositivo de Boot",
                     "Outros Dispositivos Detectados", "Operações do Array"):
            self.assertIn(name, js)
        self.assertIn("Array StorOS ainda não configurado", (ROOT / "backend/storage.py").read_text())

    def test_modules_are_not_fake_admin(self):
        frontend = (ROOT / "web/modules.js").read_text()
        for forbidden in ("fetch(", "innerHTML", "docker.sock", "mkfs", "virsh destroy"):
            self.assertNotIn(forbidden, frontend)
        self.assertIn("Somente leitura", frontend)

if __name__ == "__main__":
    unittest.main()
