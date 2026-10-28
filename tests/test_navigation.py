import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NavigationTests(unittest.TestCase):
    def test_both_navigation_assets_are_referenced(self):
        html = (ROOT / "web/index.html").read_text()
        gateway = (ROOT / "tools/lan_gateway.py").read_text()
        for asset in ("navigation.js", "navigation.css"):
            self.assertIn(f'/{asset}', html)
            self.assertIn(f'"/{asset}"', gateway)

    def test_sidebar_and_readability_controls(self):
        js = (ROOT / "web/navigation.js").read_text()
        self.assertIn("sidebar-toggle", js)
        self.assertIn("font-size-toggle", js)
        self.assertIn("sidebar-backdrop", js)
        self.assertIn("aria-expanded", js)
        self.assertIn("Escape", js)
        self.assertIn("localStorage", js)
        self.assertIn("storos-sidebar-mode", js)
        self.assertIn("storos-text-size", js)

    def test_collapsed_and_mobile_are_not_same_layout(self):
        css = (ROOT / "web/navigation.css").read_text()
        self.assertIn("body.sidebar-collapsed .sidebar", css)
        self.assertIn("body.sidebar-open .sidebar", css)
        self.assertIn("body.sidebar-open .sidebar-backdrop", css)
        self.assertIn("min-width: 721px", css)
        self.assertIn("max-width: 720px", css)

    def test_text_is_larger_than_prior_11px_menu(self):
        css = (ROOT / "web/navigation.css").read_text()
        self.assertRegex(css, r'\.nav-link\s*\{[^}]+font-size:\s*calc\(14px')
        self.assertRegex(css, r'\.subnav\s+a\s*\{[^}]+font-size:\s*calc\(13px')

    def test_no_privileged_browser_actions(self):
        js = (ROOT / "web/navigation.js").read_text()
        for disallowed in ("docker.sock", "fetch(", "XMLHttpRequest", "sudo ", "exec("):
            self.assertNotIn(disallowed, js)

if __name__ == "__main__":
    unittest.main()
