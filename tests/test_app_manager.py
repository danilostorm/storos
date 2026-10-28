import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "backend"))
import app_manager
from auth_socket import create_server
from security_core import AccountStore, IdentityError


class AppPlanTests(unittest.TestCase):
    def test_all_catalog_templates_are_bounded_named_volumes(self):
        for slug in app_manager.apps.CATALOG:
            plan = app_manager.plan(slug)
            payload = json.loads(plan["compose"])
            self.assertEqual(plan["project"], "storos-" + slug)
            self.assertEqual(len(plan["sha256"]), 64)
            service = next(iter(payload["services"].values()))
            self.assertNotIn("privileged", service)
            self.assertNotIn("devices", service)
            self.assertNotIn("network_mode", service)
            for mount in service.get("volumes", []):
                self.assertNotIn("/var/run/docker.sock", mount)
                self.assertFalse(mount.startswith("/"))
            self.assertTrue(plan["install_supported"])

    def test_invalid_app_fails_without_docker(self):
        for slug in ("../../passwd", "foo;rm", "missing", "", "https://invalid"):
            with self.assertRaises(app_manager.AppActionError):
                app_manager.plan(slug)

    def test_host_mounts_are_rejected(self):
        with mock.patch.object(app_manager.apps, "compose_preview", return_value={
                "compose": json.dumps({"name":"storos-nginx","services":{"nginx":{
                    "image":"nginx:stable", "volumes":["/etc:/host/etc"]}}})}):
            with self.assertRaises(app_manager.AppActionError):
                app_manager.plan("nginx")


class AppManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/"app-root"
        self.root.mkdir(mode=0o700)
        self.commands = []
        def runner(argv, **kwargs):
            self.commands.append(argv)
            return subprocess.CompletedProcess(argv, 0, "", "")
        self.manager = app_manager.AppManager(self.root, runner=runner)

    def test_approved_install_builds_fixed_argv_and_private_compose(self):
        accepted = app_manager.plan("nginx")
        with mock.patch.object(app_manager.shutil,"which",return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["systemd-detect-virt"],0)):
                result = self.manager.install("nginx", accepted["sha256"])
        self.assertEqual(result["state"],"deployed")
        self.assertEqual(len(self.commands),2)
        self.assertEqual(self.commands[0][-2:],["config","--quiet"])
        self.assertEqual(self.commands[1][-3:],["-d","--pull","always"])
        content = (self.root/"storos-nginx"/"compose.json")
        self.assertEqual(stat.S_IMODE(content.stat().st_mode),0o600)
        self.assertEqual(json.loads(content.read_text())["name"],"storos-nginx")
        self.assertEqual(self.manager.list_installed()[0]["state"], "deployed")
        self.assertEqual(self.manager.list_installed()[0]["running"],None)
        with self.assertRaises(app_manager.AppActionError):
            self.manager.install("nginx",accepted["sha256"])

    def test_bad_confirmation_never_invokes_docker(self):
        with self.assertRaises(app_manager.AppActionError):
            self.manager.install("nginx", "bad")
        self.assertEqual(self.commands,[])
        self.assertEqual(list(self.root.iterdir()),[])

    def test_vm_guard_blocks_host(self):
        accepted = app_manager.plan("nginx")
        with mock.patch.object(app_manager.subprocess,"run",
                  return_value=subprocess.CompletedProcess(["virt"],1)):
            with self.assertRaises(app_manager.AppActionError):
                self.manager.install("nginx",accepted["sha256"])
        self.assertEqual(self.commands,[])
        self.assertEqual(list(self.root.iterdir()),[])

    def test_failed_docker_does_not_claim_deployed(self):
        def failing_runner(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 1, "", "fail")
        self.manager.runner = failing_runner
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["vm"],0)):
                with self.assertRaises(app_manager.AppActionError):
                    self.manager.install("nginx", app_manager.plan("nginx")["sha256"])
        state = self.manager.list_installed()[0]
        self.assertEqual(state["state"], "failed")
        self.assertIsNone(state["running"])
        self.assertTrue((self.root/"storos-nginx"/"compose.json").exists())

    def test_private_state_required(self):
        self.root.chmod(0o755)
        with self.assertRaises(app_manager.AppActionError):
            self.manager.list_installed()

    def test_disabled_by_default_even_in_vm(self):
        with tempfile.TemporaryDirectory() as t:
            directory=Path(t)/"auth"
            directory.mkdir(mode=0o700)
            AccountStore(directory/"accounts.json").bootstrap_admin(
                "storadmin","demo-only password for test")
            server=create_server(directory)
            try:
                self.assertIsNone(server.app_manager)
            finally:
                server.server_close()
                (directory/"auth.sock").unlink()

    def test_explicit_opt_in_refuses_non_vm(self):
        with tempfile.TemporaryDirectory() as t:
            directory=Path(t)/"auth"
            directory.mkdir(mode=0o700)
            AccountStore(directory/"accounts.json").bootstrap_admin(
                "storadmin","demo-only password for test")
            with mock.patch("subprocess.run",return_value=subprocess.CompletedProcess(["virt"],1)):
                with self.assertRaises(IdentityError):
                    create_server(directory,enable_apps=True)
            self.assertFalse((directory/"auth.sock").exists())


if __name__=="__main__":
    unittest.main()
