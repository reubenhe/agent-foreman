import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MascotOptionsPageTests(unittest.TestCase):
    def test_mascot_options_uses_scene_svg_not_absolute_hat_layout(self):
        html = (ROOT / "static" / "mascot-system-options.html").read_text(encoding="utf-8")
        self.assertIn('class="scene-svg"', html)
        self.assertNotIn('.hardhat.small', html)
        self.assertNotIn('.hardhat.hero', html)

    def test_mascot_options_contains_all_requested_elements(self):
        html = (ROOT / "static" / "mascot-system-options.html").read_text(encoding="utf-8")
        self.assertIn("真实安全帽", html)
        self.assertIn("赶牛鞭", html)
        self.assertIn("黄牌 / 工牌", html)


if __name__ == "__main__":
    unittest.main()
