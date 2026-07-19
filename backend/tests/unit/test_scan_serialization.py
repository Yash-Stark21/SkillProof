"""Tests for server-authoritative scan and evidence serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.scan_service import serialize_evidence, serialize_scan

NOW = datetime(2026, 7, 15, 10, 30, 4, tzinfo=UTC)
COMMIT_SHA = "0123456789abcdef0123456789abcdef01234567"
CONTENT_HASH = "ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c"


def _scan(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "id": uuid4(),
        "repository_snapshot": {
            "provider": "github",
            "identity": "github:historical-owner/historical-name",
            "owner": "Historical-Owner",
            "name": "Historical-Name",
            "url": "https://github.com/Historical-Owner/Historical-Name",
        },
        "status": "completed",
        "phase": "complete",
        "commit_sha": COMMIT_SHA,
        "detector_version": "0.1.0",
        "taxonomy_version": "0.1.0",
        "redaction_version": "0.1.0",
        "evidence_contract_version": "0.1",
        "scan_policy_version": "0.1",
        "scan_policy_snapshot": {"file_blobs": 40},
        "scan_policy_observations": {"file_blobs": 1},
        "coverage_state": "complete",
        "coverage_reasons": [],
        "files_discovered": 2,
        "files_inspected": 1,
        "files_skipped_by_policy": 1,
        "bytes_inspected": 512,
        "failure_code": None,
        "failure_message": None,
        "created_at": NOW,
        "started_at": NOW,
        "completed_at": NOW,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _evidence(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "id": uuid4(),
        "canonical_skill_id": "fastapi",
        "rule_id": "python.fastapi.route_decorator",
        "detector_version": "0.1.0",
        "path": "backend/app/main.py",
        "evidence_kind": "route",
        "confidence": "high",
        "start_line": 12,
        "end_line": 14,
        "source_content_hash": CONTENT_HASH,
        "redacted_excerpt": '@app.get("/health")',
        "created_at": NOW,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_scan_uses_immutable_repository_snapshot_for_api_identity() -> None:
    result = serialize_scan(_scan())

    assert result.repository.identity == "github:historical-owner/historical-name"
    assert result.repository.owner == "Historical-Owner"
    assert result.repository.name == "Historical-Name"
    assert result.repository.url == ("https://github.com/Historical-Owner/Historical-Name")
    assert result.coverage is not None
    assert result.coverage.state == "complete"
    assert result.error is None


@pytest.mark.parametrize(
    ("confidence", "evidence_kind", "expected"),
    [
        ("high", "route", True),
        ("medium", "import", True),
        ("low", "route", False),
        ("high", "documentation_reference", False),
    ],
)
def test_claim_eligibility_is_derived_by_the_server(
    confidence: str, evidence_kind: str, expected: bool
) -> None:
    result = serialize_evidence(
        _scan(),
        _evidence(confidence=confidence, evidence_kind=evidence_kind),
    )

    assert result.claim_eligible is expected
    assert result.repository == "github:historical-owner/historical-name"
    assert result.commit_sha == COMMIT_SHA
    assert result.path == "backend/app/main.py"
    assert result.content_hash == CONTENT_HASH


def test_failed_scan_serializes_only_the_safe_error() -> None:
    result = serialize_scan(
        _scan(
            status="failed",
            phase="failed",
            commit_sha=None,
            coverage_state=None,
            failure_code="REPOSITORY_NOT_FOUND",
            failure_message="The public repository could not be found.",
        )
    )

    assert result.coverage is None
    assert result.error is not None
    assert result.error.model_dump() == {
        "code": "REPOSITORY_NOT_FOUND",
        "message": "The public repository could not be found.",
    }
