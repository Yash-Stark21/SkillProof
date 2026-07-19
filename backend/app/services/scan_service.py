"""Repository-scan use cases and API serialization."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from uuid import UUID

from app.api.errors import ApiError
from app.domain.policy import (
    DETECTOR_VERSION,
    EMPTY_SCAN_OBSERVATIONS,
    EVIDENCE_CONTRACT_VERSION,
    REDACTION_VERSION,
    SCAN_POLICY_LIMITS,
    SCAN_POLICY_VERSION,
    TAXONOMY_VERSION,
)
from app.domain.ports import InvalidCursorError, ScanStore
from app.domain.records import ScanAttempt, ScanRecord, StoredEvidenceRecord
from app.domain.scan import CLAIM_ELIGIBLE_CONFIDENCE, ScanStatus
from app.schemas.scan import (
    CoverageResponse,
    EvidencePageResponse,
    EvidenceResponse,
    EvidenceScanSummary,
    PageResponse,
    RepositoryResponse,
    ScanErrorResponse,
    ScanResponse,
)
from app.services.repository_url import RepositoryUrlError, normalize_github_repository_url


class ScanService:
    def __init__(self, store: ScanStore) -> None:
        self.store = store

    async def create_scan(self, repository_url: str) -> ScanResponse:
        try:
            normalized = normalize_github_repository_url(repository_url)
        except RepositoryUrlError as error:
            raise ApiError(
                status_code=422,
                code="UNSUPPORTED_REPOSITORY_HOST"
                if error.code == "unsupported_host"
                else "VALIDATION_ERROR",
                message=error.message,
                details={
                    "fields": [
                        {
                            "field": "repository_url",
                            "code": error.code,
                            "message": error.message,
                        }
                    ]
                },
            ) from error

        scan = await self.store.create_attempt(
            normalized,
            ScanAttempt(
                repository_snapshot=normalized.api_snapshot(),
                detector_version=DETECTOR_VERSION,
                taxonomy_version=TAXONOMY_VERSION,
                redaction_version=REDACTION_VERSION,
                evidence_contract_version=EVIDENCE_CONTRACT_VERSION,
                scan_policy_version=SCAN_POLICY_VERSION,
                scan_policy_snapshot=deepcopy(SCAN_POLICY_LIMITS),
                scan_policy_observations=deepcopy(EMPTY_SCAN_OBSERVATIONS),
            ),
        )
        return serialize_scan(scan)

    async def get_scan(self, scan_id: UUID) -> ScanResponse:
        scan = await self.store.get_scan(scan_id)
        if scan is None:
            raise ApiError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="The requested scan could not be found.",
            )
        return serialize_scan(scan)

    async def list_evidence(
        self,
        scan_id: UUID,
        *,
        limit: int,
        cursor: str | None,
        canonical_skill_id: str | None,
        confidence: Sequence[str],
        claim_eligible: bool | None,
    ) -> EvidencePageResponse:
        scan = await self.store.get_scan(scan_id)
        if scan is None:
            raise ApiError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="The requested scan could not be found.",
            )
        if scan.status != ScanStatus.COMPLETED.value:
            details = None
            if scan.status == ScanStatus.FAILED.value and scan.failure_code:
                details = {
                    "scan_error": {
                        "code": scan.failure_code,
                        "message": scan.failure_message,
                    }
                }
            raise ApiError(
                status_code=409,
                code="SCAN_NOT_COMPLETE",
                message="The scan is not complete.",
                details=details,
                headers={"Retry-After": "2"}
                if scan.status in {ScanStatus.QUEUED.value, ScanStatus.RUNNING.value}
                else None,
            )

        try:
            page = await self.store.list_evidence(
                scan_id=scan.id,
                limit=limit,
                cursor=cursor,
                canonical_skill_id=canonical_skill_id,
                confidence=confidence,
                claim_eligible=claim_eligible,
            )
        except InvalidCursorError as error:
            raise ApiError(
                status_code=422,
                code="VALIDATION_ERROR",
                message=str(error),
                details={
                    "fields": [
                        {
                            "field": "cursor",
                            "code": "invalid_cursor",
                            "message": str(error),
                        }
                    ]
                },
            ) from error

        data = [serialize_evidence(scan, evidence) for evidence in page.data]
        coverage = None
        if scan.coverage_state:
            coverage = {"state": scan.coverage_state, "reasons": list(scan.coverage_reasons)}
        return EvidencePageResponse(
            data=data,
            page=PageResponse(next_cursor=page.next_cursor, limit=limit),
            scan=EvidenceScanSummary(id=scan.id, status=scan.status, coverage=coverage),
        )


def serialize_scan(scan: ScanRecord) -> ScanResponse:
    snapshot = scan.repository_snapshot
    coverage = None
    if scan.coverage_state is not None:
        coverage = CoverageResponse(
            state=scan.coverage_state,
            reasons=list(scan.coverage_reasons),
            files_discovered=scan.files_discovered,
            files_inspected=scan.files_inspected,
            files_skipped_by_policy=scan.files_skipped_by_policy,
            bytes_inspected=scan.bytes_inspected,
            limits=dict(scan.scan_policy_snapshot),
            observed=dict(scan.scan_policy_observations),
        )
    error = None
    if scan.failure_code is not None:
        error = ScanErrorResponse(
            code=scan.failure_code, message=scan.failure_message or "Scan failed."
        )
    return ScanResponse(
        id=scan.id,
        repository=RepositoryResponse.model_validate(snapshot),
        status=scan.status,
        phase=scan.phase,
        commit_sha=scan.commit_sha,
        detector_version=scan.detector_version,
        taxonomy_version=scan.taxonomy_version,
        redaction_version=scan.redaction_version,
        evidence_contract_version=scan.evidence_contract_version,
        scan_policy_version=scan.scan_policy_version,
        coverage=coverage,
        error=error,
        created_at=scan.created_at,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
    )


def serialize_evidence(scan: ScanRecord, evidence: StoredEvidenceRecord) -> EvidenceResponse:
    confidence = evidence.confidence
    claim_eligible = (
        scan.status == ScanStatus.COMPLETED.value
        and confidence in {item.value for item in CLAIM_ELIGIBLE_CONFIDENCE}
        and evidence.evidence_kind != "documentation_reference"
    )
    return EvidenceResponse(
        id=evidence.id,
        contract_version=scan.evidence_contract_version,
        canonical_skill_id=evidence.canonical_skill_id,
        rule_id=evidence.rule_id,
        detector_version=evidence.detector_version,
        repository=str(scan.repository_snapshot["identity"]),
        commit_sha=scan.commit_sha or "",
        path=evidence.path,
        content_hash=evidence.source_content_hash,
        start_line=evidence.start_line,
        end_line=evidence.end_line,
        redacted_excerpt=evidence.redacted_excerpt,
        evidence_kind=evidence.evidence_kind,
        confidence=confidence,
        coverage_state=scan.coverage_state or "complete",
        created_at=evidence.created_at,
        claim_eligible=claim_eligible,
    )
