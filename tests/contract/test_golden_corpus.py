"""Dependency-free executable checks for the frozen evidence contract."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "golden"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evidence-contract-v0.1.schema.json"

FIXTURE_IDS = (
    "positive_fastapi",
    "negative_readme_only",
    "positive_react_typescript",
    "negative_typescript_no_react",
    "mixed_fullstack",
    "partial_scan",
    "secret_redaction",
)

TOP_REQUIRED = {
    "contract_version",
    "fixture_id",
    "description",
    "repository",
    "detector_version",
    "coverage",
    "files",
    "expected_evidence",
    "forbidden_evidence",
}
EVIDENCE_REQUIRED = {
    "canonical_skill_id",
    "rule_id",
    "detector_version",
    "repository",
    "commit_sha",
    "path",
    "content_hash",
    "start_line",
    "end_line",
    "redacted_excerpt",
    "evidence_kind",
    "confidence",
    "coverage_state",
    "created_at",
    "claim_eligible",
}
FORBIDDEN_REQUIRED = {
    "canonical_skill_id",
    "rule_id",
    "path",
    "start_line",
    "end_line",
    "excerpt",
    "reason",
}
REDACTION_REQUIRED = {
    "path",
    "start_line",
    "end_line",
    "redacted_excerpt",
    "secret_types",
}
EVIDENCE_KINDS = {
    "manifest_dependency",
    "import",
    "route",
    "test",
    "component",
    "hook",
    "configuration",
    "language_syntax",
    "documentation_reference",
}
CONFIDENCES = {"high", "medium", "low"}
COVERAGE_STATES = {"complete", "partial"}
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
SKILL_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
RULE_RE = re.compile(r"[a-z][a-z0-9_.-]*\Z")
REPOSITORY_ID_RE = re.compile(
    r"github:[A-Za-z0-9-]+/[A-Za-z0-9._-]+\Z"
)
GITHUB_TOKEN_RE = re.compile(r"\bghp_[A-Za-z0-9]{36,}\b")
POSTGRES_PASSWORD_RE = re.compile(
    r"(postgresql://[^:\s\"/]+:)([^@\s\"]+)(@)"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_range(path: Path, start_line: int, end_line: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not 1 <= start_line <= end_line <= len(lines):
        raise AssertionError(
            f"invalid range {start_line}-{end_line} for {path} ({len(lines)} lines)"
        )
    return "\n".join(lines[start_line - 1 : end_line])


def _redact(text: str) -> str:
    text = GITHUB_TOKEN_RE.sub("[REDACTED:GITHUB_TOKEN]", text)
    return POSTGRES_PASSWORD_RE.sub(
        r"\1[REDACTED:PASSWORD]\3",
        text,
    )


def _semantic_digest(manifest: dict[str, Any]) -> str:
    evidence = []
    for item in manifest["expected_evidence"]:
        semantic_item = {key: value for key, value in item.items() if key != "created_at"}
        evidence.append(semantic_item)
    evidence.sort(
        key=lambda item: (
            item["canonical_skill_id"],
            item["path"],
            item["start_line"],
            item["rule_id"],
        )
    )
    payload = {
        "contract_version": manifest["contract_version"],
        "repository": (
            f"github:{manifest['repository']['owner']}/{manifest['repository']['name']}"
        ),
        "commit_sha": manifest["repository"]["commit_sha"],
        "detector_version": manifest["detector_version"],
        "coverage": manifest["coverage"],
        "evidence": evidence,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _canonical_domain_output(
    items: list[dict[str, Any]], ignored_fields: set[str]
) -> str:
    semantic_items = [
        {key: value for key, value in item.items() if key not in ignored_fields}
        for item in items
    ]
    semantic_items.sort(
        key=lambda item: (
            item["canonical_skill_id"],
            item["path"],
            item["start_line"],
            item["rule_id"],
        )
    )
    return json.dumps(
        semantic_items,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _claim_is_valid(
    claim: dict[str, Any], available_evidence: list[dict[str, Any]]
) -> bool:
    qualifying_ids = {
        evidence["id"]
        for evidence in available_evidence
        if evidence["claim_eligible"]
        and evidence["confidence"] in {"high", "medium"}
    }
    return bool(set(claim["evidence_ids"]) & qualifying_ids)


class GoldenCorpusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _load_json(SCHEMA_PATH)
        cls.manifests = {
            fixture_id: _load_json(GOLDEN_ROOT / fixture_id / "manifest.json")
            for fixture_id in FIXTURE_IDS
        }

    def test_schema_declares_frozen_v01_contract(self) -> None:
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(self.schema["properties"]["contract_version"]["const"], "0.1")
        self.assertEqual(self.schema["properties"]["detector_version"]["const"], "0.1.0")
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.schema["required"]), TOP_REQUIRED)
        self.assertEqual(
            set(self.schema["$defs"]["evidence"]["required"]),
            EVIDENCE_REQUIRED,
        )
        self.assertEqual(
            set(self.schema["$defs"]["evidence"]["properties"]["confidence"]["enum"]),
            CONFIDENCES,
        )
        self.assertEqual(
            set(
                self.schema["$defs"]["evidence"]["properties"]["coverage_state"][
                    "enum"
                ]
            ),
            COVERAGE_STATES,
        )

    def test_fixture_set_and_manifest_structure(self) -> None:
        actual_fixture_ids = {
            path.parent.name for path in GOLDEN_ROOT.glob("*/manifest.json")
        }
        self.assertEqual(actual_fixture_ids, set(FIXTURE_IDS))

        seen_commits: set[str] = set()
        for fixture_id, manifest in self.manifests.items():
            with self.subTest(fixture=fixture_id):
                allowed_top = TOP_REQUIRED | {"redaction_cases"}
                self.assertTrue(TOP_REQUIRED <= set(manifest))
                self.assertTrue(set(manifest) <= allowed_top)
                self.assertEqual(manifest["fixture_id"], fixture_id)
                self.assertEqual(manifest["contract_version"], "0.1")
                self.assertEqual(manifest["detector_version"], "0.1.0")
                self.assertIsInstance(manifest["description"], str)
                self.assertTrue(manifest["description"].strip())

                repository = manifest["repository"]
                self.assertEqual(
                    set(repository),
                    {"provider", "owner", "name", "url", "commit_sha"},
                )
                self.assertEqual(repository["provider"], "github")
                self.assertEqual(
                    repository["url"],
                    f"https://github.com/{repository['owner']}/{repository['name']}",
                )
                self.assertRegex(repository["commit_sha"], COMMIT_RE)
                self.assertNotIn(repository["commit_sha"], seen_commits)
                seen_commits.add(repository["commit_sha"])

                coverage = manifest["coverage"]
                self.assertEqual(set(coverage), {"state", "reason"})
                self.assertIn(coverage["state"], COVERAGE_STATES)
                if coverage["state"] == "complete":
                    self.assertIsNone(coverage["reason"])
                else:
                    self.assertIsInstance(coverage["reason"], str)
                    self.assertTrue(coverage["reason"].strip())

                self.assertTrue(manifest["files"])
                self.assertTrue(manifest["expected_evidence"])
                self.assertTrue(manifest["forbidden_evidence"])
                self._assert_file_records(manifest)
                self._assert_evidence_records(manifest)
                self._assert_forbidden_records(manifest)
                self._assert_redaction_records(manifest)

    def _assert_file_records(self, manifest: dict[str, Any]) -> None:
        paths: list[str] = []
        for file_record in manifest["files"]:
            self.assertEqual(set(file_record), {"path", "sha256"})
            self.assertRegex(file_record["sha256"], HASH_RE)
            self._assert_safe_path(file_record["path"])
            paths.append(file_record["path"])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths, sorted(paths))

    def _assert_evidence_records(self, manifest: dict[str, Any]) -> None:
        repository = manifest["repository"]
        repository_id = f"github:{repository['owner']}/{repository['name']}"
        inventory = {item["path"]: item["sha256"] for item in manifest["files"]}
        semantic_keys: set[tuple[Any, ...]] = set()

        for evidence in manifest["expected_evidence"]:
            self.assertEqual(set(evidence), EVIDENCE_REQUIRED)
            self.assertRegex(evidence["canonical_skill_id"], SKILL_RE)
            self.assertRegex(evidence["rule_id"], RULE_RE)
            self.assertRegex(evidence["repository"], REPOSITORY_ID_RE)
            self.assertEqual(evidence["repository"], repository_id)
            self.assertEqual(evidence["commit_sha"], repository["commit_sha"])
            self.assertEqual(evidence["detector_version"], manifest["detector_version"])
            self._assert_safe_path(evidence["path"])
            self.assertIn(evidence["path"], inventory)
            self.assertRegex(evidence["content_hash"], HASH_RE)
            self.assertEqual(evidence["content_hash"], inventory[evidence["path"]])
            self.assertIs(type(evidence["start_line"]), int)
            self.assertIs(type(evidence["end_line"]), int)
            self.assertGreaterEqual(evidence["start_line"], 1)
            self.assertGreaterEqual(evidence["end_line"], evidence["start_line"])
            self.assertTrue(evidence["redacted_excerpt"])
            self.assertIn(evidence["evidence_kind"], EVIDENCE_KINDS)
            self.assertIn(evidence["confidence"], CONFIDENCES)
            self.assertEqual(evidence["coverage_state"], manifest["coverage"]["state"])
            created_at = datetime.fromisoformat(
                evidence["created_at"].replace("Z", "+00:00")
            )
            self.assertEqual(created_at.utcoffset(), timezone.utc.utcoffset(created_at))
            self.assertIs(type(evidence["claim_eligible"]), bool)

            key = (
                evidence["canonical_skill_id"],
                evidence["rule_id"],
                evidence["path"],
                evidence["start_line"],
                evidence["end_line"],
            )
            self.assertNotIn(key, semantic_keys)
            semantic_keys.add(key)

    def _assert_forbidden_records(self, manifest: dict[str, Any]) -> None:
        inventory = {item["path"] for item in manifest["files"]}
        for forbidden in manifest["forbidden_evidence"]:
            self.assertEqual(set(forbidden), FORBIDDEN_REQUIRED)
            self.assertRegex(forbidden["canonical_skill_id"], SKILL_RE)
            self.assertRegex(forbidden["rule_id"], RULE_RE)
            self._assert_safe_path(forbidden["path"])
            self.assertIn(forbidden["path"], inventory)
            self.assertIs(type(forbidden["start_line"]), int)
            self.assertIs(type(forbidden["end_line"]), int)
            self.assertGreaterEqual(forbidden["start_line"], 1)
            self.assertGreaterEqual(forbidden["end_line"], forbidden["start_line"])
            self.assertTrue(forbidden["excerpt"])
            self.assertTrue(forbidden["reason"].strip())

    def _assert_redaction_records(self, manifest: dict[str, Any]) -> None:
        inventory = {item["path"] for item in manifest["files"]}
        for redaction in manifest.get("redaction_cases", []):
            self.assertEqual(set(redaction), REDACTION_REQUIRED)
            self._assert_safe_path(redaction["path"])
            self.assertIn(redaction["path"], inventory)
            self.assertIs(type(redaction["start_line"]), int)
            self.assertIs(type(redaction["end_line"]), int)
            self.assertGreaterEqual(redaction["start_line"], 1)
            self.assertGreaterEqual(redaction["end_line"], redaction["start_line"])
            self.assertTrue(redaction["redacted_excerpt"])
            self.assertTrue(redaction["secret_types"])
            self.assertEqual(
                len(redaction["secret_types"]),
                len(set(redaction["secret_types"])),
            )
            self.assertTrue(
                set(redaction["secret_types"])
                <= {"github_token", "database_password"}
            )

    def _assert_safe_path(self, relative_path: str) -> None:
        self.assertIsInstance(relative_path, str)
        self.assertTrue(relative_path)
        self.assertNotIn("\\", relative_path)
        path = PurePosixPath(relative_path)
        self.assertFalse(path.is_absolute())
        self.assertNotIn("..", path.parts)

    def test_inventory_hashes_and_exact_source_ranges(self) -> None:
        for fixture_id, manifest in self.manifests.items():
            fixture_root = GOLDEN_ROOT / fixture_id
            repo_root = fixture_root / "repo"
            inventory = {item["path"]: item["sha256"] for item in manifest["files"]}
            actual_paths = {
                path.relative_to(repo_root).as_posix()
                for path in repo_root.rglob("*")
                if path.is_file()
            }
            with self.subTest(fixture=fixture_id, check="inventory"):
                self.assertEqual(set(inventory), actual_paths)

            for relative_path, expected_hash in inventory.items():
                with self.subTest(fixture=fixture_id, path=relative_path, check="hash"):
                    self.assertEqual(_sha256(repo_root / relative_path), expected_hash)

            for evidence in manifest["expected_evidence"]:
                source = _source_range(
                    repo_root / evidence["path"],
                    evidence["start_line"],
                    evidence["end_line"],
                )
                with self.subTest(
                    fixture=fixture_id,
                    rule=evidence["rule_id"],
                    check="expected_excerpt",
                ):
                    self.assertEqual(_redact(source), evidence["redacted_excerpt"])

            for forbidden in manifest["forbidden_evidence"]:
                source = _source_range(
                    repo_root / forbidden["path"],
                    forbidden["start_line"],
                    forbidden["end_line"],
                )
                with self.subTest(
                    fixture=fixture_id,
                    rule=forbidden["rule_id"],
                    check="forbidden_excerpt",
                ):
                    self.assertEqual(source, forbidden["excerpt"])

    def test_confidence_and_claim_eligibility(self) -> None:
        for fixture_id, manifest in self.manifests.items():
            for evidence in manifest["expected_evidence"]:
                with self.subTest(fixture=fixture_id, rule=evidence["rule_id"]):
                    expected_eligibility = evidence["confidence"] in {"high", "medium"}
                    self.assertEqual(evidence["claim_eligible"], expected_eligibility)
                    if evidence["evidence_kind"] == "documentation_reference":
                        self.assertEqual(PurePosixPath(evidence["path"]).name.lower(), "readme.md")
                        self.assertEqual(evidence["confidence"], "low")
                        self.assertFalse(evidence["claim_eligible"])

    def test_readme_only_and_negative_fixtures_forbid_implementation_claims(self) -> None:
        cases = {
            "negative_readme_only": "fastapi",
            "negative_typescript_no_react": "react",
        }
        for fixture_id, skill_id in cases.items():
            manifest = self.manifests[fixture_id]
            skill_evidence = [
                item
                for item in manifest["expected_evidence"]
                if item["canonical_skill_id"] == skill_id
            ]
            with self.subTest(fixture=fixture_id, skill=skill_id):
                self.assertTrue(skill_evidence)
                self.assertTrue(
                    all(
                        item["evidence_kind"] == "documentation_reference"
                        and item["confidence"] == "low"
                        and not item["claim_eligible"]
                        for item in skill_evidence
                    )
                )
                forbidden_rules = {
                    item["rule_id"]
                    for item in manifest["forbidden_evidence"]
                    if item["canonical_skill_id"] == skill_id
                }
                self.assertTrue(any(rule.endswith(".import") for rule in forbidden_rules))
                self.assertTrue(
                    any(rule.endswith(".manifest_dependency") for rule in forbidden_rules)
                )

    def test_partial_coverage_has_reason_and_never_asserts_absence(self) -> None:
        partial_ids = [
            fixture_id
            for fixture_id, manifest in self.manifests.items()
            if manifest["coverage"]["state"] == "partial"
        ]
        self.assertEqual(partial_ids, ["partial_scan"])
        manifest = self.manifests["partial_scan"]
        self.assertTrue(manifest["coverage"]["reason"].strip())
        self.assertTrue(
            all(
                item["coverage_state"] == "partial"
                for item in manifest["expected_evidence"]
            )
        )
        absence_guards = [
            item
            for item in manifest["forbidden_evidence"]
            if "absence_from_partial_scan" in item["rule_id"]
        ]
        self.assertTrue(absence_guards)

    def test_secret_redaction_is_typed_and_raw_values_never_enter_manifest(self) -> None:
        fixture_id = "secret_redaction"
        manifest_path = GOLDEN_ROOT / fixture_id / "manifest.json"
        manifest = self.manifests[fixture_id]
        cases = manifest.get("redaction_cases", [])
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(
            set(case["secret_types"]),
            {"github_token", "database_password"},
        )
        source = _source_range(
            GOLDEN_ROOT / fixture_id / "repo" / case["path"],
            case["start_line"],
            case["end_line"],
        )
        github_tokens = GITHUB_TOKEN_RE.findall(source)
        database_passwords = [
            match.group(2) for match in POSTGRES_PASSWORD_RE.finditer(source)
        ]
        self.assertTrue(github_tokens)
        self.assertTrue(database_passwords)
        self.assertEqual(_redact(source), case["redacted_excerpt"])
        self.assertEqual(
            source.count("\n"),
            case["redacted_excerpt"].count("\n"),
        )
        self.assertIn("[REDACTED:GITHUB_TOKEN]", case["redacted_excerpt"])
        self.assertIn("[REDACTED:PASSWORD]", case["redacted_excerpt"])

        serialized_manifest = manifest_path.read_text(encoding="utf-8")
        for raw_secret in github_tokens + database_passwords:
            self.assertNotIn(raw_secret, serialized_manifest)
        self.assertIsNone(GITHUB_TOKEN_RE.search(serialized_manifest))

        redacted_evidence = [
            item
            for item in manifest["expected_evidence"]
            if "[REDACTED:" in item["redacted_excerpt"]
        ]
        self.assertEqual(len(redacted_evidence), 1)
        self.assertEqual(
            redacted_evidence[0]["redacted_excerpt"],
            case["redacted_excerpt"],
        )

    def test_semantic_result_is_deterministic_for_identical_input(self) -> None:
        for fixture_id in FIXTURE_IDS:
            manifest_path = GOLDEN_ROOT / fixture_id / "manifest.json"
            first = _load_json(manifest_path)
            second = json.loads(json.dumps(first))
            second["expected_evidence"].reverse()
            for item in second["expected_evidence"]:
                item["created_at"] = "2030-01-01T00:00:00Z"
            with self.subTest(fixture=fixture_id):
                first_digest = _semantic_digest(first)
                second_digest = _semantic_digest(second)
                self.assertRegex(first_digest, HASH_RE)
                self.assertEqual(first_digest, second_digest)

                changed = json.loads(json.dumps(first))
                changed["expected_evidence"][0]["confidence"] = "changed"
                self.assertNotEqual(first_digest, _semantic_digest(changed))

    def test_domain_scenario_structure(self) -> None:
        document = _load_json(GOLDEN_ROOT / "domain_scenarios.json")
        self.assertEqual(set(document), {"contract_version", "scenarios"})
        self.assertEqual(document["contract_version"], "0.1")
        expected_ids = {
            "unsupported_claim_rejection",
            "final_evidence_deletion",
            "deterministic_rerun",
            "independent_scores",
        }
        self.assertEqual(set(document["scenarios"]), expected_ids)
        for scenario_id, scenario in document["scenarios"].items():
            self.assertEqual(scenario["id"], scenario_id)

    def test_unsupported_claim_is_rejected(self) -> None:
        scenario = _load_json(GOLDEN_ROOT / "domain_scenarios.json")["scenarios"][
            "unsupported_claim_rejection"
        ]
        accepted = _claim_is_valid(
            scenario["claim"],
            scenario["available_evidence"],
        )
        self.assertEqual(accepted, scenario["expected"]["accepted"])
        self.assertFalse(accepted)
        self.assertEqual(
            scenario["expected"]["error_code"],
            "CLAIM_QUALIFYING_EVIDENCE_REQUIRED",
        )

    def test_deleting_final_qualifying_evidence_invalidates_claim(self) -> None:
        scenario = _load_json(GOLDEN_ROOT / "domain_scenarios.json")["scenarios"][
            "final_evidence_deletion"
        ]
        valid_before = _claim_is_valid(
            scenario["claim"],
            scenario["available_evidence"],
        )
        remaining = [
            evidence
            for evidence in scenario["available_evidence"]
            if evidence["id"] != scenario["mutation"]["delete_evidence_id"]
        ]
        valid_after = _claim_is_valid(scenario["claim"], remaining)
        self.assertEqual(valid_before, scenario["expected"]["valid_before"])
        self.assertEqual(valid_after, scenario["expected"]["valid_after"])
        self.assertTrue(valid_before)
        self.assertFalse(valid_after)

    def test_domain_rerun_semantics_are_identical(self) -> None:
        scenario = _load_json(GOLDEN_ROOT / "domain_scenarios.json")["scenarios"][
            "deterministic_rerun"
        ]
        semantic_input = scenario["semantic_input"]
        self.assertRegex(semantic_input["commit_sha"], COMMIT_RE)
        self.assertRegex(semantic_input["repository"], REPOSITORY_ID_RE)
        self.assertEqual(semantic_input["contract_version"], "0.1")
        self.assertEqual(semantic_input["detector_version"], "0.1.0")
        raw_run_a = json.dumps(scenario["run_a"], sort_keys=True)
        raw_run_b = json.dumps(scenario["run_b"], sort_keys=True)
        self.assertNotEqual(raw_run_a, raw_run_b)
        ignored_fields = set(scenario["ignored_runtime_fields"])
        run_a = _canonical_domain_output(scenario["run_a"], ignored_fields)
        run_b = _canonical_domain_output(scenario["run_b"], ignored_fields)
        outputs_equal = run_a == run_b
        self.assertEqual(
            outputs_equal,
            scenario["expected"]["semantic_outputs_equal"],
        )
        self.assertTrue(outputs_equal)

    def test_job_fit_and_portfolio_quality_are_independent(self) -> None:
        scenario = _load_json(GOLDEN_ROOT / "domain_scenarios.json")["scenarios"][
            "independent_scores"
        ]
        baseline = scenario["baseline"]
        portfolio_changed = scenario["portfolio_only_change"]
        job_changed = scenario["job_only_change"]
        for value in (
            baseline["job_fit"],
            baseline["portfolio_quality"],
            portfolio_changed["job_fit"],
            portfolio_changed["portfolio_quality"],
            job_changed["job_fit"],
            job_changed["portfolio_quality"],
        ):
            self.assertIs(type(value), int)
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
        job_fit_unchanged = baseline["job_fit"] == portfolio_changed["job_fit"]
        portfolio_quality_changed = (
            baseline["portfolio_quality"] != portfolio_changed["portfolio_quality"]
        )
        job_fit_changed = baseline["job_fit"] != job_changed["job_fit"]
        portfolio_quality_unchanged = (
            baseline["portfolio_quality"] == job_changed["portfolio_quality"]
        )
        self.assertEqual(
            job_fit_unchanged,
            scenario["expected"]["job_fit_unchanged"],
        )
        self.assertEqual(
            portfolio_quality_changed,
            scenario["expected"]["portfolio_quality_changed"],
        )
        self.assertEqual(
            job_fit_changed,
            scenario["expected"]["job_fit_changed"],
        )
        self.assertEqual(
            portfolio_quality_unchanged,
            scenario["expected"]["portfolio_quality_unchanged"],
        )
        self.assertTrue(portfolio_changed["changed_inputs"])
        self.assertTrue(job_changed["changed_inputs"])


if __name__ == "__main__":
    unittest.main()
