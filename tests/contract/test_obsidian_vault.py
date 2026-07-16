"""Dependency-free checks for the portable Obsidian documentation vault."""

from __future__ import annotations

import json
import re
import unittest
import urllib.parse
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VAULT_ROOT = PROJECT_ROOT / "docs"
CONFIG_ROOT = VAULT_ROOT / ".obsidian"
TEMPLATE_ROOT = VAULT_ROOT / "templates"

COMMON_PROPERTIES = {
    "title",
    "type",
    "status",
    "phase",
    "owner",
    "created",
    "updated",
    "tags",
    "aliases",
}
EXPECTED_TEMPLATES = {
    "ADR.md",
    "Daily Note.md",
    "Decision.md",
    "General Note.md",
    "Meeting Note.md",
    "Requirement.md",
    "Risk.md",
    "Sprint.md",
    "Technical Spike.md",
}
REQUIRED_CORE_PLUGINS = {
    "backlink",
    "command-palette",
    "daily-notes",
    "file-explorer",
    "global-search",
    "graph",
    "outline",
    "outgoing-link",
    "page-preview",
    "properties",
    "switcher",
    "tag-pane",
    "templates",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def _strip_fenced_code(text: str) -> str:
    return re.sub(
        r"(^|\n)(```|~~~).*?\n\2(?:\n|$)",
        "\n",
        text,
        flags=re.DOTALL,
    )


def _parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        return [
            item.strip().strip("\"'")
            for item in value[1:-1].split(",")
            if item.strip()
        ]
    return []


def _frontmatter(path: Path) -> dict[str, Any]:
    lines = _read(path).splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing YAML frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"unterminated YAML frontmatter: {path}") from exc

    properties: dict[str, Any] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line or line.startswith((" ", "\t")):
            index += 1
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?", line)
        if not match:
            raise AssertionError(f"unsupported top-level YAML line in {path}: {line!r}")
        key, raw_value = match.group(1), (match.group(2) or "").strip()
        if key in properties:
            raise AssertionError(f"duplicate YAML property {key!r} in {path}")
        if raw_value.startswith("["):
            value: Any = _parse_inline_list(raw_value)
        elif raw_value:
            value = raw_value.strip("\"'")
        else:
            values: list[str] = []
            cursor = index + 1
            while cursor < end:
                list_match = re.fullmatch(r"\s+-\s+(.+)", lines[cursor])
                if not list_match:
                    break
                values.append(list_match.group(1).strip().strip("\"'"))
                cursor += 1
            value = values
            index = cursor - 1
        properties[key] = value
        index += 1
    return properties


def _normalized_heading(value: str) -> str:
    value = value.strip().rstrip("#").strip()
    value = re.sub(r"[`*_]", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return " ".join(value.split()).casefold()


def _headings(path: Path) -> set[str]:
    return {
        _normalized_heading(match.group(1))
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", _read(path), flags=re.MULTILINE)
    }


def _resolve_wikilink(source: Path, raw_target: str) -> tuple[Path, str | None]:
    target = raw_target.split("|", 1)[0].strip()
    note_part, separator, heading = target.partition("#")
    if not note_part:
        return source, heading or None

    note_part = note_part.removesuffix(".md")
    if "/" in note_part:
        resolved = VAULT_ROOT / f"{note_part}.md"
    else:
        matches = [
            path
            for path in VAULT_ROOT.rglob("*.md")
            if path.stem.casefold() == note_part.casefold()
        ]
        if len(matches) != 1:
            raise AssertionError(
                f"wikilink {raw_target!r} in {source} resolved to {len(matches)} notes"
            )
        resolved = matches[0]
    return resolved, heading if separator else None


class ObsidianVaultTests(unittest.TestCase):
    def test_portable_vault_configuration(self) -> None:
        app = json.loads(_read(CONFIG_ROOT / "app.json"))
        core = json.loads(_read(CONFIG_ROOT / "core-plugins.json"))
        templates = json.loads(_read(CONFIG_ROOT / "templates.json"))
        daily = json.loads(_read(CONFIG_ROOT / "daily-notes.json"))

        self.assertTrue(app["alwaysUpdateLinks"])
        self.assertTrue(app["useMarkdownLinks"])
        self.assertEqual(app["newLinkFormat"], "relative")
        self.assertEqual(app["attachmentFolderPath"], "assets/attachments")
        self.assertTrue(REQUIRED_CORE_PLUGINS <= {key for key, value in core.items() if value})
        self.assertEqual(templates["folder"], "templates")
        self.assertEqual(templates["dateFormat"], "YYYY-MM-DD")
        self.assertEqual(daily["folder"], "journal")
        self.assertEqual(daily["format"], "YYYY-MM-DD")
        self.assertEqual(daily["template"], "templates/Daily Note")
        self.assertFalse((CONFIG_ROOT / "workspace.json").exists())
        self.assertFalse((CONFIG_ROOT / "community-plugins.json").exists())
        self.assertTrue((VAULT_ROOT / "assets" / "attachments" / ".gitkeep").is_file())

    def test_all_vault_notes_have_consistent_properties(self) -> None:
        durable_notes = [
            path for path in VAULT_ROOT.rglob("*.md") if TEMPLATE_ROOT not in path.parents
        ]
        titles: dict[str, Path] = {}
        for path in durable_notes:
            with self.subTest(note=path.relative_to(VAULT_ROOT)):
                properties = _frontmatter(path)
                self.assertTrue(COMMON_PROPERTIES <= set(properties))
                self.assertNotIn("tag", properties)
                self.assertNotIn("alias", properties)
                self.assertIsInstance(properties["tags"], list)
                self.assertTrue(properties["tags"])
                self.assertIsInstance(properties["aliases"], list)
                self.assertTrue(str(properties["title"]).strip())
                self.assertTrue(str(properties["type"]).strip())
                self.assertTrue(str(properties["status"]).strip())
                self.assertTrue(str(properties["phase"]).strip())
                self.assertTrue(str(properties["owner"]).strip())
                self.assertRegex(str(properties["created"]), r"^\d{4}-\d{2}-\d{2}$")
                self.assertRegex(str(properties["updated"]), r"^\d{4}-\d{2}-\d{2}$")
                title_key = str(properties["title"]).casefold()
                self.assertNotIn(title_key, titles, f"duplicate title with {titles.get(title_key)}")
                titles[title_key] = path
                self.assertIn("## Related notes", _read(path))

    def test_templates_have_common_properties_and_sections(self) -> None:
        self.assertEqual(
            {path.name for path in TEMPLATE_ROOT.glob("*.md")},
            EXPECTED_TEMPLATES,
        )
        for path in TEMPLATE_ROOT.glob("*.md"):
            with self.subTest(template=path.name):
                properties = _frontmatter(path)
                self.assertTrue(COMMON_PROPERTIES <= set(properties))
                self.assertIsInstance(properties["tags"], list)
                self.assertIsInstance(properties["aliases"], list)
                self.assertNotIn("tag", properties)
                self.assertNotIn("alias", properties)
                text = _read(path)
                self.assertIn("{{title}}", text)
                self.assertIn("{{date}}", text)
                self.assertIn("{{time}}", text)
                self.assertIn("## Related notes", text)

        self.assertEqual(_frontmatter(TEMPLATE_ROOT / "ADR.md")["adr_id"], "ADR-XXX")
        self.assertEqual(
            _frontmatter(TEMPLATE_ROOT / "Requirement.md")["requirement_type"],
            "functional",
        )

    def test_existing_artifact_metadata_is_typed(self) -> None:
        inception_notes = list((VAULT_ROOT / "inception").glob("*.md"))
        self.assertEqual(len(inception_notes), 13)
        for path in inception_notes:
            with self.subTest(note=path.name):
                properties = _frontmatter(path)
                self.assertEqual(properties["phase"], "inception")
                self.assertIn("skillproof", properties["tags"])

        adr_notes = sorted((VAULT_ROOT / "adr").glob("ADR-*.md"))
        self.assertEqual(len(adr_notes), 7)
        for index, path in enumerate(adr_notes, start=1):
            with self.subTest(adr=path.name):
                properties = _frontmatter(path)
                self.assertEqual(properties["type"], "adr")
                expected_status = "superseded" if index == 1 else "accepted"
                self.assertEqual(properties["status"], expected_status)
                self.assertEqual(properties["adr_id"], f"ADR-{index:03d}")

    def test_all_wikilinks_resolve_inside_the_vault(self) -> None:
        for source in VAULT_ROOT.rglob("*.md"):
            if TEMPLATE_ROOT in source.parents:
                continue
            text = _strip_fenced_code(_read(source))
            for raw_target in re.findall(r"!?(?:\[\[)([^\]]+)(?:\]\])", text):
                with self.subTest(source=source.relative_to(VAULT_ROOT), target=raw_target):
                    resolved, heading = _resolve_wikilink(source, raw_target)
                    self.assertTrue(resolved.is_file(), f"missing wikilink target: {resolved}")
                    self.assertTrue(
                        resolved.resolve().is_relative_to(VAULT_ROOT.resolve()),
                        f"wikilink leaves vault: {resolved}",
                    )
                    if heading:
                        self.assertIn(_normalized_heading(heading), _headings(resolved))

    def test_all_durable_markdown_links_resolve_inside_the_vault(self) -> None:
        link_pattern = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")
        for source in VAULT_ROOT.rglob("*.md"):
            if TEMPLATE_ROOT in source.parents:
                continue
            text = _strip_fenced_code(_read(source))
            for raw_target in link_pattern.findall(text):
                target, _, heading = raw_target.partition("#")
                target = urllib.parse.unquote(target.strip().strip("<>"))
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (source.parent / target).resolve()
                with self.subTest(source=source.relative_to(VAULT_ROOT), target=raw_target):
                    self.assertTrue(
                        resolved.is_relative_to(VAULT_ROOT.resolve()),
                        f"link leaves vault: {resolved}",
                    )
                    self.assertTrue(resolved.is_file(), f"missing link target: {resolved}")
                    if heading and resolved.suffix.lower() == ".md":
                        self.assertIn(_normalized_heading(heading), _headings(resolved))

    def test_navigation_and_guide_cover_the_workflow(self) -> None:
        for relative_path in (
            "Home.md",
            "README.md",
            "OBSIDIAN_GUIDE.md",
            "MOCs/Project MOC.md",
            "MOCs/Product MOC.md",
            "MOCs/Engineering MOC.md",
            "MOCs/Delivery MOC.md",
            "adr/README.md",
            "journal/README.md",
            "guides/GitHub Repository Setup.md",
        ):
            self.assertTrue((VAULT_ROOT / relative_path).is_file())

        guide = _read(VAULT_ROOT / "OBSIDIAN_GUIDE.md")
        self.assertIn("no community plugin is required", guide.lower())
        self.assertIn("standard Markdown links by default", guide)
        self.assertIn("may use Obsidian wikilinks", guide)
        home = _read(VAULT_ROOT / "Home.md")
        for moc in ("Product MOC", "Engineering MOC", "Delivery MOC", "Project MOC"):
            self.assertIn(moc, home)

    def test_github_repository_setup_guide_covers_publication_controls(self) -> None:
        guide = _read(VAULT_ROOT / "guides" / "GitHub Repository Setup.md")
        required_content = (
            "Evidence-first developer portfolio analyzer",
            "Do not create on GitHub",
            "git push -u origin main",
            "protect-main",
            "SPK-01",
            "US-07",
            "Synthetic secret fixture",
            "## Official references",
        )
        for expected in required_content:
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)


if __name__ == "__main__":
    unittest.main()
