import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_monitor_server():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("monitor_server", root / "monitor_server.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


monitor_server = load_monitor_server()


class PasswordSshTests(unittest.TestCase):
    @mock.patch.object(monitor_server.subprocess, "run")
    def test_password_ssh_command_uses_askpass_env(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

        monitor_server.run_password_ssh_command(
            {
                "ssh_target": "192.168.53.210",
                "port": 22,
            },
            {"username": "hanting", "password": "secret-pass"},
            "echo ok",
        )

        _, kwargs = run_mock.call_args
        self.assertEqual(kwargs["env"]["SSH_ASKPASS_REQUIRE"], "force")
        self.assertEqual(kwargs["env"]["AGENT_FOREMAN_ASKPASS"], "secret-pass")

    @mock.patch.object(monitor_server, "run_password_ssh_command")
    def test_password_host_test_reports_auth_failure(self, run_command_mock):
        run_command_mock.return_value = {
            "returncode": 255,
            "stdout": "",
            "stderr": "Permission denied",
        }
        draft = {
            "name": "gpu-a",
            "ssh_target": "192.168.53.210",
            "port": 22,
            "username": "hanting",
            "password": "secret-pass",
            "enabled": True,
            "send_mode": "stdin",
        }

        result = monitor_server.test_managed_host_connection(draft)

        self.assertFalse(result["ok"])
        self.assertIn("Permission denied", result["error"])


class StartupUnlockTests(unittest.TestCase):
    def test_bootstrap_creates_vault_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = monitor_server.load_config(str(config_path))
            config["credentials_file"] = str(Path(tmpdir) / "credentials.enc.json")
            config["_credentials_path"] = config["credentials_file"]

            prompts = iter(["master-pass", "master-pass"])
            vault = monitor_server.bootstrap_vault(config, prompt_fn=lambda _: next(prompts), require_tty=False)

            self.assertTrue(Path(config["credentials_file"]).exists())
            self.assertTrue(vault.is_unlocked)

    def test_existing_vault_requires_master_password(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "credentials.enc.json"
            vault = monitor_server.CredentialVault(vault_path, iterations=1000)
            vault.create("correct-pass")

            config_path = Path(tmpdir) / "config.json"
            config = monitor_server.load_config(str(config_path))
            config["credentials_file"] = str(vault_path)
            config["_credentials_path"] = str(vault_path)

            with self.assertRaises(ValueError):
                monitor_server.bootstrap_vault(config, prompt_fn=lambda _: "wrong-pass", require_tty=False)
