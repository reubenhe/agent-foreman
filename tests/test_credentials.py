import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def load_monitor_server():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("monitor_server", root / "monitor_server.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


monitor_server = load_monitor_server()


class CredentialVaultTests(unittest.TestCase):
    def test_encrypt_decrypt_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "credentials.enc.json"
            vault = monitor_server.CredentialVault(vault_path, iterations=1000)
            vault.create("master-pass")
            vault.unlock("master-pass")
            vault.upsert("gpu-a", "hanting", "sge98@56")

            reopened = monitor_server.CredentialVault(vault_path, iterations=1000)
            reopened.unlock("master-pass")
            creds = reopened.get("gpu-a")

            self.assertEqual(creds["username"], "hanting")
            self.assertEqual(creds["password"], "sge98@56")

    def test_unlock_rejects_wrong_password(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "credentials.enc.json"
            vault = monitor_server.CredentialVault(vault_path, iterations=1000)
            vault.create("correct-pass")

            reopened = monitor_server.CredentialVault(vault_path, iterations=1000)
            with self.assertRaises(ValueError):
                reopened.unlock("wrong-pass")

    def test_delete_host_removes_stored_credentials(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "credentials.enc.json"
            vault = monitor_server.CredentialVault(vault_path, iterations=1000)
            vault.create("master-pass")
            vault.unlock("master-pass")
            vault.upsert("gpu-a", "hanting", "sge98@56")
            vault.delete("gpu-a")

            reopened = monitor_server.CredentialVault(vault_path, iterations=1000)
            reopened.unlock("master-pass")

            self.assertIsNone(reopened.get("gpu-a"))


class ManagedHostStoreTests(unittest.TestCase):
    def _make_store(self, tmpdir: str):
        config_path = Path(tmpdir) / "config.json"
        vault_path = Path(tmpdir) / "credentials.enc.json"
        config = monitor_server.load_config(str(config_path))
        config["credentials_file"] = str(vault_path)
        config["_credentials_path"] = str(vault_path)
        config["_config_path"] = str(config_path)
        vault = monitor_server.CredentialVault(vault_path, iterations=1000)
        vault.create("master-pass")
        vault.unlock("master-pass")
        store = monitor_server.ManagedHostStore(config, vault)
        return store, vault, config_path

    def test_save_host_keeps_existing_password_when_blank(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store, vault, _ = self._make_store(tmpdir)
            saved = store.save_host(
                {
                    "name": "gpu-a",
                    "ssh_target": "192.168.53.210",
                    "port": 22,
                    "username": "hanting",
                    "password": "first-pass",
                    "enabled": True,
                    "send_mode": "stdin",
                }
            )

            store.save_host(
                {
                    "id": saved["id"],
                    "name": "gpu-a-renamed",
                    "ssh_target": "192.168.53.210",
                    "port": 22,
                    "username": "hanting",
                    "password": "",
                    "enabled": False,
                    "send_mode": "stdin",
                }
            )

            creds = vault.get(saved["id"])
            host = store.get_host(saved["id"])
            self.assertEqual(creds["password"], "first-pass")
            self.assertEqual(host["name"], "gpu-a-renamed")
            self.assertFalse(host["enabled"])

    def test_config_persistence_omits_password_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store, _, config_path = self._make_store(tmpdir)
            store.save_host(
                {
                    "name": "gpu-a",
                    "ssh_target": "192.168.53.210",
                    "port": 22,
                    "username": "hanting",
                    "password": "secret-pass",
                    "enabled": True,
                    "send_mode": "stdin",
                }
            )

            raw = config_path.read_text(encoding="utf-8")
            data = json.loads(raw)

            self.assertNotIn("secret-pass", raw)
            self.assertTrue(all("password" not in host for host in data["managed_hosts"]))

    def test_list_hosts_does_not_return_password(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store, _, _ = self._make_store(tmpdir)
            saved = store.save_host(
                {
                    "name": "gpu-a",
                    "ssh_target": "192.168.53.210",
                    "port": 22,
                    "username": "hanting",
                    "password": "secret-pass",
                    "enabled": True,
                    "send_mode": "stdin",
                }
            )

            listed = store.list_hosts()
            self.assertEqual(listed[0]["id"], saved["id"])
            self.assertEqual(listed[0]["username"], "hanting")
            self.assertNotIn("password", listed[0])
