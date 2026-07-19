"""Versioned scan and evidence API representations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RepositoryResponse(BaseModel):
    provider: str
    identity: str
    owner: str
    name: str
    url: str


class CoverageResponse(BaseModel):
    state: str
    reasons: list[str]
    files_discovered: int
    files_inspected: int
    files_skipped_by_policy: int
    bytes_inspected: int
    limits: dict[str, int | float]
    observed: dict[str, int]


class ScanErrorResponse(BaseModel):
    code: str
    message: str


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository: RepositoryResponse
    status: str
    phase: str
    commit_sha: str | None
    detector_version: str
    taxonomy_version: str
    redaction_version: str
    evidence_contract_version: str
    scan_policy_version: str
    coverage: CoverageResponse | None
    error: ScanErrorResponse | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ScanCreateRequest(BaseModel):
    repository_url: str = Field(min_length=1, max_length=2048)


class EvidenceResponse(BaseModel):
    id: UUID
    contract_version: str
    canonical_skill_id: str
    rule_id: str
    detector_version: str
    repository: str
    commit_sha: str
    path: str
    content_hash: str
    start_line: int
    end_line: int
    redacted_excerpt: str
    evidence_kind: str
    confidence: str
    coverage_state: str
    created_at: datetime
    claim_eligible: bool


class PageResponse(BaseModel):
    next_cursor: str | None
    limit: int


class EvidenceScanSummary(BaseModel):
    id: UUID
    status: str
    coverage: dict[str, Any] | None


class EvidencePageResponse(BaseModel):
    data: list[EvidenceResponse]
    page: PageResponse
    scan: EvidenceScanSummary
