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
            if "ps" in argv:
                payload = [{"Project": "storos-nginx", "Service": "nginx",
                            "State": "running"}]
                return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")
            return subprocess.CompletedProcess(argv, 0, "", "")
        self.manager = app_manager.AppManager(self.root, runner=runner)

    def test_approved_install_builds_fixed_argv_and_private_compose(self):
        accepted = app_manager.plan("nginx")
        with mock.patch.object(app_manager.shutil,"which",return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["systemd-detect-virt"],0)):
                result = self.manager.install("nginx", accepted["sha256"])
        self.assertEqual(result["state"],"deployed")
        self.assertEqual(len(self.commands),3)
        self.assertEqual(self.commands[0][-2:],["config","--quiet"])
        self.assertEqual(self.commands[1][-3:],["-d","--pull","always"])
        self.assertEqual(self.commands[2][-3:],["--all","--format","json"])
        content = (self.root/"storos-nginx"/"compose.json")
        self.assertEqual(stat.S_IMODE(content.stat().st_mode),0o600)
        self.assertEqual(json.loads(content.read_text())["name"],"storos-nginx")
        self.assertEqual(self.manager.list_installed()[0]["state"], "deployed")
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            self.assertTrue(self.manager.list_installed()[0]["running"])
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

    def test_successful_up_with_stopped_container_is_failed(self):
        def stopped_runner(argv, **kwargs):
            self.commands.append(argv)
            output = json.dumps([{"Project": "storos-nginx", "Service": "nginx",
                                  "State": "exited"}]) if "ps" in argv else ""
            return subprocess.CompletedProcess(argv, 0, output, "")
        self.manager.runner = stopped_runner
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["virt"], 0)):
                with self.assertRaisesRegex(app_manager.AppActionError, "did not stay running"):
                    self.manager.install("nginx", app_manager.plan("nginx")["sha256"])
        row = self.manager.list_installed()[0]
        self.assertEqual(row["state"], "failed")
        self.assertFalse(row["running"])
        self.assertTrue((self.root / "storos-nginx" / "compose.json").exists())

    def test_foreign_or_corrupt_compose_status_is_not_trusted(self):
        def foreign_runner(argv, **kwargs):
            output = json.dumps([{"Project": "someone-else", "Service": "nginx",
                                  "State": "running"}]) if "ps" in argv else ""
            return subprocess.CompletedProcess(argv, 0, output, "")
        self.manager.runner = foreign_runner
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["virt"], 0)):
                with self.assertRaises(app_manager.AppActionError):
                    self.manager.install("nginx", app_manager.plan("nginx")["sha256"])
            self.assertEqual(self.manager.list_installed()[0]["state"], "failed")
            self.assertIsNone(self.manager.list_installed()[0]["running"])

    def test_running_probe_reflects_container_exit_after_install(self):
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["virt"], 0)):
                self.manager.install("nginx", app_manager.plan("nginx")["sha256"])
            self.assertTrue(self.manager.list_installed()[0]["running"])
            def exited_runner(argv, **kwargs):
                payload = [{"Project": "storos-nginx", "Service": "nginx",
                            "State": "exited"}]
                return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")
            self.manager.runner = exited_runner
            item = self.manager.list_installed()[0]
        self.assertEqual(item["state"], "deployed")
        self.assertFalse(item["running"])

    def test_compose_ps_accepts_json_lines(self):
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                   return_value=subprocess.CompletedProcess(["virt"], 0)):
                def lines_runner(argv, **kwargs):
                    if "ps" in argv:
                        return subprocess.CompletedProcess(argv, 0, json.dumps({
                            "Project": "storos-nginx", "Service": "nginx", "State": "running"
                        }) + "\n", "")
                    return subprocess.CompletedProcess(argv, 0, "", "")
                self.manager.runner = lines_runner
                result = self.manager.install("nginx", app_manager.plan("nginx")["sha256"])
                self.assertEqual(result["state"], "deployed")
                self.assertTrue(self.manager.list_installed()[0]["running"])

    def _install_test_nginx(self):
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                 return_value=subprocess.CompletedProcess(["virt"], 0)):
                self.manager.install("nginx", app_manager.plan("nginx")["sha256"])

    def test_start_stop_restart_managed_compose(self):
        self._install_test_nginx()
        status = {"running": True}
        commands = []
        def lifecycle_runner(argv, **kwargs):
            commands.append(argv)
            if argv[-1] == "stop":
                status["running"] = False
            elif argv[-1] in ("start", "restart"):
                status["running"] = True
            if "ps" in argv:
                data = ([{"Project": "storos-nginx", "Service": "nginx",
                          "State": "running"}] if status["running"] else [])
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
            return subprocess.CompletedProcess(argv, 0, "", "")
        self.manager.runner = lifecycle_runner
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            with mock.patch.object(app_manager.subprocess, "run",
                 return_value=subprocess.CompletedProcess(["virt"], 0)):
                for action, expected_running in (
                    ("stop", False), ("start", True), ("restart", True)
                ):
                    result = self.manager.control("nginx", action, app_manager.plan("nginx")["sha256"])
                    self.assertEqual(result["action"], action)
                    self.assertEqual(result["running"], expected_running)
                    self.assertEqual(self.manager.list_installed()[0]["state"],
                                     "stopped" if action == "stop" else "deployed")
        effects = [cmd[-1] for cmd in commands if cmd[-1] in ("stop", "start", "restart")]
        self.assertEqual(effects, ["stop", "start", "restart"])
        self.assertFalse(any("down" in command for command in commands))

    def test_lifecycle_rejects_unregistered_tampered_and_symlinked_compose(self):
        accepted = app_manager.plan("nginx")["sha256"]
        with self.assertRaises(app_manager.AppActionError):
            self.manager.control("nginx", "stop", accepted)
        self._install_test_nginx()
        config = self.root / "storos-nginx" / "compose.json"
        config.write_text('{"name":"dangerous"}')
        with self.assertRaisesRegex(app_manager.AppActionError, "differs"):
            self.manager.control("nginx", "stop", accepted)
        config.unlink()
        outside = Path(self.temp.name) / "other.json"
        outside.write_text('{"name":"foreign"}')
        config.symlink_to(outside)
        with self.assertRaises(app_manager.AppActionError):
            self.manager.control("nginx", "restart", accepted)

    def test_lifecycle_wrong_hash_and_action_never_calls_docker(self):
        self._install_test_nginx()
        count = len(self.commands)
        with self.assertRaises(app_manager.AppActionError):
            self.manager.control("nginx", "start", "wrong")
        with self.assertRaises(app_manager.AppActionError):
            self.manager.control("nginx", "remove", app_manager.plan("nginx")["sha256"])
        self.assertEqual(len(self.commands), count)

    def test_tampered_config_is_never_trusted_for_status(self):
        self._install_test_nginx()
        config = self.root / "storos-nginx" / "compose.json"
        config.write_text('{"name":"unexpected"}')
        call_count = len(self.commands)
        with mock.patch.object(app_manager.shutil, "which", return_value="/usr/bin/docker"):
            result = self.manager.list_installed()[0]
        self.assertIsNone(result["running"])
        self.assertEqual(len(self.commands), call_count)

    def test_lifecycle_vm_guard_blocks_host(self):
        self._install_test_nginx()
        count = len(self.commands)
        with mock.patch.object(app_manager.subprocess, "run",
                 return_value=subprocess.CompletedProcess(["virt"], 1)):
            with self.assertRaises(app_manager.AppActionError):
                self.manager.control("nginx", "stop", app_manager.plan("nginx")["sha256"])
        self.assertEqual(len(self.commands), count)

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
