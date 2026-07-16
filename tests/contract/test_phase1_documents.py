"""Executable consistency checks for the Phase 1 planning baseline."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INCEPTION_ROOT = PROJECT_ROOT / "docs" / "inception"
ADR_ROOT = PROJECT_ROOT / "docs" / "adr"

REQUIRED_DOCUMENTS = {
    "README.md",
    "PRODUCT_CHARTER.md",
    "REQUIREMENTS.md",
    "FEASIBILITY_REPORT.md",
    "RISK_REGISTER.md",
    "DECISION_LOG.md",
    "EVIDENCE_CONTRACT.md",
    "ARCHITECTURE.md",
    "API_CONTRACT.md",
    "DATA_MODEL.md",
    "BACKLOG.md",
    "TRACEABILITY_MATRIX.md",
    "PHASE_1_EXIT_REPORT.md",
}
EXPECTED_ADRS = {
    "ADR-001-fastapi-react-separation.md",
    "ADR-002-rule-based-detection-before-ai.md",
    "ADR-003-commit-pinned-evidence.md",
    "ADR-004-separate-product-scores.md",
    "ADR-005-in-process-v1-scanning.md",
    "ADR-006-defer-auth-workers-microservices.md",
    "ADR-007-adopt-vue-javascript-client.md",
}
EXPECTED_ENDPOINTS = {
    "POST /api/v1/scans",
    "GET /api/v1/scans/{scan_id}",
    "GET /api/v1/scans/{scan_id}/evidence",
    "POST /api/v1/job-descriptions",
    "PATCH /api/v1/job-descriptions/{job_description_id}/skills",
    "POST /api/v1/reports",
    "GET /api/v1/reports/{report_id}",
    "GET /api/v1/health/live",
    "GET /api/v1/health/ready",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


class PhaseOneDocumentTests(unittest.TestCase):
    def test_required_artifacts_and_adrs_exist(self) -> None:
        actual_documents = {path.name for path in INCEPTION_ROOT.glob("*.md")}
        self.assertTrue(REQUIRED_DOCUMENTS <= actual_documents)
        self.assertEqual(
            {path.name for path in ADR_ROOT.glob("ADR-*.md")},
            EXPECTED_ADRS,
        )
        self.assertTrue((PROJECT_ROOT / "PHASE_1_INCEPTION_PLAN.md").is_file())

    def test_new_documents_are_clean_utf8(self) -> None:
        paths = [PROJECT_ROOT / "PHASE_1_INCEPTION_PLAN.md"]
        paths.extend(INCEPTION_ROOT.glob("*.md"))
        paths.extend(ADR_ROOT.glob("*.md"))
        for path in paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = _read(path)
                self.assertTrue(text.strip())
                for mojibake_marker in ("â€", "â†", "Ã", "�"):
                    self.assertNotIn(mojibake_marker, text)

    def test_requirement_and_acceptance_id_sets_are_complete(self) -> None:
        text = _read(INCEPTION_ROOT / "REQUIREMENTS.md")
        self.assertEqual(
            set(re.findall(r"^### `BR-(\d{2})`", text, flags=re.MULTILINE)),
            {f"{index:02d}" for index in range(1, 6)},
        )
        self.assertEqual(
            set(re.findall(r"^### `FR-(\d{2})`", text, flags=re.MULTILINE)),
            {f"{index:02d}" for index in range(1, 9)},
        )
        self.assertEqual(
            set(re.findall(r"^### `NFR-(\d{2})`", text, flags=re.MULTILINE)),
            {f"{index:02d}" for index in range(1, 8)},
        )
        requirement_ids = re.findall(r"^### `(B?N?FR-\d{2})`", text, flags=re.MULTILINE)
        for requirement_id in requirement_ids:
            with self.subTest(requirement=requirement_id):
                self.assertRegex(text, rf"`{re.escape(requirement_id)}-AC1`")

    def test_risks_decisions_and_adrs_are_actionable(self) -> None:
        risks = _read(INCEPTION_ROOT / "RISK_REGISTER.md")
        risk_matches = list(
            re.finditer(r"^## `R-(\d{3})`", risks, flags=re.MULTILINE)
        )
        self.assertEqual(
            {match.group(1) for match in risk_matches},
            {f"{index:03d}" for index in range(1, 12)},
        )
        for index, match in enumerate(risk_matches):
            end = risk_matches[index + 1].start() if index + 1 < len(risk_matches) else len(risks)
            section = risks[match.start() : end]
            for field in (
                "Probability",
                "Impact",
                "Owner",
                "Status",
                "Mitigation",
                "Detection signal",
                "Response",
            ):
                with self.subTest(risk=match.group(1), field=field):
                    self.assertIn(f"**{field}:**", section)

        decisions = _read(INCEPTION_ROOT / "DECISION_LOG.md")
        self.assertEqual(
            set(re.findall(r"`D-(\d{3})`", decisions)),
            {f"{index:03d}" for index in range(1, 20)},
        )
        for adr_path in ADR_ROOT.glob("ADR-*.md"):
            with self.subTest(adr=adr_path.name):
                expected_status = (
                    "Superseded"
                    if adr_path.name == "ADR-001-fastapi-react-separation.md"
                    else "Accepted"
                )
                self.assertIn(f"**Status:** {expected_status}", _read(adr_path))

    def test_api_and_data_contracts_use_the_same_locked_values(self) -> None:
        requirements = _read(INCEPTION_ROOT / "REQUIREMENTS.md")
        api = _read(INCEPTION_ROOT / "API_CONTRACT.md")
        data = _read(INCEPTION_ROOT / "DATA_MODEL.md")
        backlog = _read(INCEPTION_ROOT / "BACKLOG.md")
        combined = "\n".join((requirements, api, data, backlog))

        self.assertNotIn("unknown_due_to_partial_coverage", combined)
        locked_match_values = "`exact`, `equivalent`, `related`, `missing`, or `unverified`"
        self.assertIn(locked_match_values, requirements)
        self.assertIn(locked_match_values, api)
        self.assertIn("`exact`, `equivalent`, `related`, `missing`, `unverified`", data)
        self.assertIn("50 through 20,000 Unicode characters", api)
        self.assertIn("between 50 and 20,000 Unicode characters", requirements)
        self.assertIn("only preferred skills exist", api)
        self.assertIn(
            '{ "code": string, "message": string, "details"?: object, "request_id": string }',
            requirements,
        )
        for endpoint in EXPECTED_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.assertIn(f"`{endpoint}`", api)

    def test_sprint_one_and_traceability_are_ready(self) -> None:
        backlog = _read(INCEPTION_ROOT / "BACKLOG.md")
        traceability = _read(INCEPTION_ROOT / "TRACEABILITY_MATRIX.md")
        for story_number in range(1, 8):
            story_id = f"US-{story_number:02d}"
            match = re.search(
                rf"^### {story_id}.*?(?=^### US-|^## )",
                backlog,
                flags=re.MULTILINE | re.DOTALL,
            )
            with self.subTest(story=story_id):
                self.assertIsNotNone(match)
                section = match.group(0)
                self.assertRegex(
                    section,
                    r"\*\*Status / estimate / priority:\*\* Ready / .+ / P0",
                )
                self.assertIn("**Mapped requirements:**", section)
                self.assertIn("Acceptance criteria:", section)
                self.assertIn("Planned tests:", section)

        for business_id in range(1, 6):
            self.assertIn(f"`BR-{business_id:02d}", traceability)
        for test_id in (
            "TC-GC-01",
            "TC-GC-09",
            "TC-DC-01",
            "TC-DC-02",
            "TC-DC-03",
        ):
            self.assertIn(f"`{test_id}`", traceability)

    def test_all_relative_markdown_links_resolve(self) -> None:
        markdown_paths = [PROJECT_ROOT / "PHASE_1_INCEPTION_PLAN.md"]
        markdown_paths.extend(INCEPTION_ROOT.glob("*.md"))
        markdown_paths.extend(ADR_ROOT.glob("*.md"))
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for source in markdown_paths:
            for raw_target in link_pattern.findall(_read(source)):
                target = raw_target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (source.parent / target).resolve()
                with self.subTest(source=source.name, target=target):
                    self.assertTrue(resolved.is_file(), f"broken link: {source} -> {target}")


if __name__ == "__main__":
    unittest.main()
