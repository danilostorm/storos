import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from security_core import (AccountStore, AuditLog, IdentityError, LoginThrottle,
                           SessionRegistry, password_hash, policy_allows,
                           verify_password)


class PasswordTests(unittest.TestCase):
    def test_scrypt_round_trip_uses_salted_digest(self):
        first = password_hash("Correct Horse Battery 123!")
        second = password_hash("Correct Horse Battery 123!")
        self.assertNotEqual(first, second)
        self.assertNotIn("Correct Horse Battery 123!", first)
        self.assertTrue(verify_password("Correct Horse Battery 123!", first))
        self.assertFalse(verify_password("wrong password!", first))

    def test_rejects_bad_and_expensive_stored_parameters(self):
        hashed = password_hash("a sufficiently long phrase")
        self.assertFalse(verify_password("a sufficiently long phrase",
                         hashed.replace("16384", "1048576")))
        self.assertFalse(verify_password("a sufficiently long phrase", "not a hash"))
        self.assertFalse(verify_password("short", hashed))

    def test_never_allows_weak_passwords(self):
        with self.assertRaises(IdentityError):
            password_hash("12345")
        with self.assertRaises(IdentityError):
            password_hash("x" * 257)


class AccountStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "private"
        self.folder.mkdir(mode=0o700)
        self.path = self.folder / "accounts.json"
        self.store = AccountStore(self.path)

    def test_provision_once_with_private_permissions(self):
        self.store.bootstrap_admin("storadmin", "unique long passphrase for demo")
        self.assertEqual(self.store.check_login("storadmin", "unique long passphrase for demo"), "admin")
        self.assertIsNone(self.store.check_login("storadmin", "wrong passphrase long enough"))
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        record = self.path.read_text()
        self.assertNotIn("unique long passphrase for demo", record)
        self.assertEqual(json.loads(record)["version"], 1)
        with self.assertRaises(IdentityError):
            self.store.bootstrap_admin("storadmin", "another unique passphrase")

    def test_refuses_world_readable_directory(self):
        self.folder.chmod(0o755)
        with self.assertRaises(IdentityError):
            self.store.bootstrap_admin("storadmin", "unique long passphrase")

    def test_refuses_world_readable_accounts(self):
        self.store.bootstrap_admin("storadmin", "unique long passphrase")
        self.path.chmod(0o644)
        with self.assertRaises(IdentityError):
            self.store.read()

    def test_dangling_symlink_is_never_overwritten(self):
        self.path.symlink_to(self.folder / "does-not-exist")
        with self.assertRaises(IdentityError):
            self.store.bootstrap_admin("storadmin", "unique long passphrase")
        self.assertTrue(self.path.is_symlink())


class LockoutAndSessionTests(unittest.TestCase):
    def test_rate_limiter_blocks_after_five_failures(self):
        limit = LoginThrottle()
        for number in range(5):
            self.assertTrue(limit.allowed("storadmin", now=number))
            limit.fail("storadmin", now=number)
        self.assertFalse(limit.allowed("storadmin", now=6))
        self.assertTrue(limit.allowed("storadmin", now=306))
        limit.succeed("storadmin")
        self.assertTrue(limit.allowed("storadmin", now=307))

    def test_sessions_require_csrf_for_mutating_requests(self):
        sessions = SessionRegistry()
        token, csrf = sessions.issue("storadmin", "admin", now=1)
        self.assertEqual(sessions.validate(token, "admin", now=2), "storadmin")
        self.assertIsNone(sessions.validate(token, "admin", mutate=True, now=3))
        self.assertIsNone(sessions.validate(token, "admin", mutate=True, csrf="invalid", now=3))
        self.assertEqual(sessions.validate(token, "admin", mutate=True, csrf=csrf, now=4), "storadmin")
        sessions.revoke(token)
        self.assertIsNone(sessions.validate(token, "admin", now=5))

    def test_idle_and_absolute_expiry(self):
        sessions = SessionRegistry(idle_seconds=10, lifetime_seconds=15)
        token, _ = sessions.issue("storadmin", "admin", now=100)
        self.assertEqual(sessions.validate(token, now=105), "storadmin")
        self.assertIsNone(sessions.validate(token, now=115))
        other, _ = sessions.issue("storadmin", "admin", now=100)
        self.assertIsNone(sessions.validate(other, now=116))

    def test_viewer_cannot_act_as_admin(self):
        sessions = SessionRegistry()
        token, csrf = sessions.issue("viewer1", "viewer", now=1)
        self.assertIsNone(sessions.validate(token, "admin", csrf=csrf, mutate=True, now=2))
        self.assertEqual(sessions.validate(token, "viewer", now=2), "viewer1")

    def test_cookie_is_host_only_secure_and_httponly(self):
        sessions = SessionRegistry()
        token, _ = sessions.issue("storadmin", "admin")
        cookie = sessions.secure_cookie(token)
        for feature in ("__Host-", "Path=/", "HttpOnly", "Secure", "SameSite=Strict"):
            self.assertIn(feature, cookie)
        self.assertNotIn("Domain=", cookie)


class PolicyAndAuditTests(unittest.TestCase):
    def test_default_deny_all_mutations_even_admin(self):
        for action in ("storage.format", "storage.pool.create",
                       "docker.compose.deploy", "vm.destroy", "shares.create",
                       "user.create", "system.shutdown"):
            self.assertFalse(policy_allows("admin", action))
            self.assertFalse(policy_allows("viewer", action))
        self.assertTrue(policy_allows("viewer", "storage.inventory.read"))
        self.assertFalse(policy_allows("nobody", "storage.inventory.read"))
        self.assertFalse(policy_allows("admin", "custom.unrecognized.action"))

    def test_audit_log_only_accepts_known_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.jsonl"
            log = AuditLog(path)
            log.record("storadmin", "storage.format", "denied")
            event = json.loads(path.read_text().strip())
            self.assertEqual(event["actor"], "storadmin")
            self.assertEqual(event["result"], "denied")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(IdentityError):
                log.record("storadmin", "password=secret!", "failed")
            self.assertNotIn("secret", path.read_text())


if __name__ == "__main__":
    unittest.main()
