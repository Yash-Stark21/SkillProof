"""Contract validation before file and evidence records reach PostgreSQL."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.domain.ledger import CompletedScanLedger, EvidenceCandidate, FileInventoryRecord
from app.services.evidence_ledger import EvidenceContractError, validate_completed_ledger

CONTENT_HASH = "e" * 64


def _ledger() -> CompletedScanLedger:
    return CompletedScanLedger(
        commit_sha="a" * 40,
        coverage_state="complete",
        coverage_reasons=[],
        scan_policy_observations={"file_blobs": 1, "total_file_bytes": 128},
        files=[
            FileInventoryRecord(
                path="backend/app/main.py",
                git_blob_sha="b" * 40,
                size_bytes=128,
                purpose="source",
                inspected=True,
                skip_reason=None,
                content_hash=CONTENT_HASH,
            )
        ],
        evidence=[
            EvidenceCandidate(
                file_path="backend/app/main.py",
                canonical_skill_id="fastapi",
                rule_id="python.fastapi.route_decorator",
                detector_version="0.1.0",
                evidence_kind="route",
                confidence="high",
                start_line=1,
                end_line=2,
                source_content_hash=CONTENT_HASH,
                redacted_excerpt='@app.get("/health")',
            )
        ],
    )


def test_valid_completed_ledger_is_accepted() -> None:
    validate_completed_ledger(_ledger())


def test_partial_coverage_requires_a_reason() -> None:
    ledger = replace(_ledger(), coverage_state="partial")

    with pytest.raises(EvidenceContractError, match="requires at least one reason"):
        validate_completed_ledger(ledger)


def test_evidence_hash_must_match_the_inspected_file() -> None:
    ledger = _ledger()
    ledger = replace(
        ledger,
        evidence=[replace(ledger.evidence[0], source_content_hash="f" * 64)],
    )

    with pytest.raises(EvidenceContractError, match="hashes must match"):
        validate_completed_ledger(ledger)


def test_evidence_cannot_reference_a_skipped_file() -> None:
    ledger = _ledger()
    ledger = replace(
        ledger,
        files=[
            replace(
                ledger.files[0],
                inspected=False,
                skip_reason="file_count_limit_reached",
                content_hash=None,
            )
        ],
    )

    with pytest.raises(EvidenceContractError, match="inspected file"):
        validate_completed_ledger(ledger)
