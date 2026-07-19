"""Persistence-neutral records exchanged through application ports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ScanAttempt:
    repository_snapshot: dict[str, str]
    detector_version: str
    taxonomy_version: str
    redaction_version: str
    evidence_contract_version: str
    scan_policy_version: str
    scan_policy_snapshot: dict[str, int]
    scan_policy_observations: dict[str, int]


@dataclass(frozen=True, slots=True)
class ScanRecord:
    id: UUID
    repository_snapshot: dict[str, str]
    status: str
    phase: str
    commit_sha: str | None
    detector_version: str
    taxonomy_version: str
    redaction_version: str
    evidence_contract_version: str
    scan_policy_version: str
    scan_policy_snapshot: dict[str, int | float]
    scan_policy_observations: dict[str, int]
    coverage_state: str | None
    coverage_reasons: list[str]
    files_discovered: int
    files_inspected: int
    files_skipped_by_policy: int
    bytes_inspected: int
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class StoredEvidenceRecord:
    id: UUID
    canonical_skill_id: str
    rule_id: str
    detector_version: str
    path: str
    source_content_hash: str
    start_line: int
    end_line: int
    redacted_excerpt: str
    evidence_kind: str
    confidence: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class EvidenceRecordPage:
    data: list[StoredEvidenceRecord]
    next_cursor: str | None


JsonObject = dict[str, Any]
