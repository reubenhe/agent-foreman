import importlib.util
import sys
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


class ProcessFilterTests(unittest.TestCase):
    def test_infer_agent_type_accepts_real_codex_cli(self):
        args = "node /public/home/user/.nvm/versions/node/v24.14.0/bin/codex --yolo"
        self.assertEqual(monitor_server.infer_agent_type(args), "codex")

    def test_infer_agent_type_rejects_vscode_codex_app_server(self):
        args = "/home/user/.vscode-server/extensions/openai.chatgpt/bin/codex app-server --analytics-default-enabled"
        self.assertEqual(monitor_server.infer_agent_type(args), "")

    def test_infer_agent_type_rejects_stream_json_claude_daemon(self):
        args = "/home/user/.vscode-server/extensions/anthropic/native-binary/claude --output-format stream-json --input-format stream-json --verbose"
        self.assertEqual(monitor_server.infer_agent_type(args), "")


if __name__ == "__main__":
    unittest.main()
