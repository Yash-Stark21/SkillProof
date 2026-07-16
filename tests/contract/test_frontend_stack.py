"""Guard the product frontend's Vue and plain-JavaScript stack decision."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


class FrontendStackTests(unittest.TestCase):
    def test_frontend_uses_vue_and_vite_without_react_or_typescript(self) -> None:
        package_path = FRONTEND_ROOT / "package.json"
        self.assertTrue(package_path.is_file(), "frontend/package.json is required")

        package = json.loads(package_path.read_text(encoding="utf-8"))
        dependencies = {
            **package.get("dependencies", {}),
            **package.get("devDependencies", {}),
        }

        self.assertIn("vue", dependencies)
        self.assertIn("@vitejs/plugin-vue", dependencies)
        self.assertIn("vite", dependencies)

        banned_dependencies = {
            "react",
            "react-dom",
            "@vitejs/plugin-react",
            "typescript",
            "vue-tsc",
        }
        self.assertFalse(
            banned_dependencies & dependencies.keys(),
            f"banned frontend dependencies: {sorted(banned_dependencies & dependencies.keys())}",
        )

    def test_frontend_contains_only_javascript_and_vue_source(self) -> None:
        banned_paths: list[Path] = []
        for path in FRONTEND_ROOT.rglob("*"):
            if not path.is_file() or {"node_modules", "dist", "coverage"} & set(path.parts):
                continue
            if path.suffix.lower() in {".ts", ".tsx"} or re.fullmatch(
                r"tsconfig(?:\..+)?\.json", path.name, flags=re.IGNORECASE
            ):
                banned_paths.append(path.relative_to(PROJECT_ROOT))

        self.assertEqual(banned_paths, [])

        for component in FRONTEND_ROOT.rglob("*.vue"):
            text = component.read_text(encoding="utf-8")
            with self.subTest(component=component.relative_to(PROJECT_ROOT)):
                self.assertNotRegex(text, r"<script\b[^>]*\blang=[\"']ts[\"']")

    def test_untrusted_evidence_is_never_inserted_as_html(self) -> None:
        for component in FRONTEND_ROOT.rglob("*.vue"):
            with self.subTest(component=component.relative_to(PROJECT_ROOT)):
                self.assertNotIn("v-html", component.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
