import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CartoonForemanThemeTests(unittest.TestCase):
    def test_index_contains_foreman_brand_language(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("包工头监工台", html)
        self.assertIn("今天谁在摸鱼", html)

    def test_app_contains_foreman_status_labels(self):
        js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("等回话", js)
        self.assertIn("开工", js)
        self.assertIn("摸鱼", js)
        self.assertIn("const laneGroups", js)
        self.assertNotIn("催办", js)

    def test_styles_switch_to_cartoon_display_font(self):
        css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("Baloo 2", css)
        self.assertIn("--paper", css)
        self.assertIn("repeat(3, minmax(0, 1fr))", css)

    def test_index_uses_friendlier_action_copy(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("继续干活", html)
        self.assertIn("发消息", html)

    def test_app_uses_explicit_bovine_mascot_features(self):
        js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('class="horn left"', js)
        self.assertIn('class="horn right"', js)
        self.assertIn('class="muzzle"', js)


if __name__ == "__main__":
    unittest.main()
