"""Validated inputs for the bounded repository-to-evidence ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FileInventoryRecord:
    path: str
    git_blob_sha: str | None
    size_bytes: int
    purpose: str
    inspected: bool
    skip_reason: str | None
    content_hash: str | None


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    file_path: str
    canonical_skill_id: str
    rule_id: str
    detector_version: str
    evidence_kind: str
    confidence: str
    start_line: int
    end_line: int
    source_content_hash: str
    redacted_excerpt: str


@dataclass(frozen=True, slots=True)
class CompletedScanLedger:
    commit_sha: str
    coverage_state: str
    coverage_reasons: list[str]
    scan_policy_observations: dict[str, Any]
    files: list[FileInventoryRecord]
    evidence: list[EvidenceCandidate]
