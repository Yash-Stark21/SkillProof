"""SQLAlchemy persistence adapter for the repository-to-evidence slice."""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvidenceItem, RepoFile, Repository, Scan
from app.domain.ports import InvalidCursorError
from app.domain.records import (
    EvidenceRecordPage,
    ScanAttempt,
    ScanRecord,
    StoredEvidenceRecord,
)
from app.domain.repository import NormalizedRepository
from app.domain.scan import CLAIM_ELIGIBLE_CONFIDENCE

CursorKey = tuple[str, str, int, str, int]


def encode_evidence_cursor(key: CursorKey) -> str:
    payload = json.dumps(key, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_evidence_cursor(value: str) -> CursorKey:
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = json.loads(base64.b64decode(padded, altchars=b"-_", validate=True))
        if not isinstance(decoded, list) or len(decoded) != 5:
            raise ValueError
        skill, path, start_line, rule_id, end_line = decoded
        if not isinstance(skill, str) or not isinstance(path, str) or not isinstance(rule_id, str):
            raise ValueError
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            raise ValueError
        if start_line < 1 or end_line < start_line:
            raise ValueError
        return skill, path, start_line, rule_id, end_line
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("The evidence cursor is invalid.") from exc


class SqlAlchemyScanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _upsert_repository(self, repository: NormalizedRepository) -> Repository:
        now = datetime.now(UTC)
        statement = (
            insert(Repository)
            .values(
                provider=repository.provider,
                provider_repository_id=None,
                normalized_owner=repository.normalized_owner,
                normalized_name=repository.normalized_name,
                display_owner=repository.display_owner,
                display_name=repository.display_name,
                canonical_url=repository.canonical_url,
                default_branch=None,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[
                    Repository.provider,
                    Repository.normalized_owner,
                    Repository.normalized_name,
                ],
                set_={
                    "display_owner": repository.display_owner,
                    "display_name": repository.display_name,
                    "canonical_url": repository.canonical_url,
                    "updated_at": now,
                },
            )
            .returning(Repository.id)
        )
        repository_id = (await self.session.execute(statement)).scalar_one()
        stored = await self.session.get(Repository, repository_id)
        if stored is None:  # pragma: no cover - protected by RETURNING and the transaction
            raise RuntimeError("Repository upsert did not return a persisted row.")
        return stored

    async def create_attempt(
        self, repository: NormalizedRepository, attempt: ScanAttempt
    ) -> ScanRecord:
        async with self.session.begin():
            stored_repository = await self._upsert_repository(repository)
            scan = Scan(
                repository_id=stored_repository.id,
                repository_snapshot=attempt.repository_snapshot,
                status="queued",
                phase="queued",
                commit_sha=None,
                detector_version=attempt.detector_version,
                taxonomy_version=attempt.taxonomy_version,
                redaction_version=attempt.redaction_version,
                evidence_contract_version=attempt.evidence_contract_version,
                scan_policy_version=attempt.scan_policy_version,
                scan_policy_snapshot=attempt.scan_policy_snapshot,
                scan_policy_observations=attempt.scan_policy_observations,
                coverage_state=None,
                coverage_reasons=[],
                files_discovered=0,
                files_inspected=0,
                files_skipped_by_policy=0,
                bytes_inspected=0,
                failure_code=None,
                failure_message=None,
                started_at=None,
                completed_at=None,
            )
            self.session.add(scan)
            await self.session.flush()
        return _scan_record(scan)

    async def get_scan(self, scan_id: UUID) -> ScanRecord | None:
        scan = await self.session.get(Scan, scan_id)
        return _scan_record(scan) if scan is not None else None

    async def list_evidence(
        self,
        *,
        scan_id: UUID,
        limit: int,
        cursor: str | None,
        canonical_skill_id: str | None,
        confidence: Sequence[str],
        claim_eligible: bool | None,
    ) -> EvidenceRecordPage:
        decoded_cursor = decode_evidence_cursor(cursor) if cursor else None
        order_columns = (
            EvidenceItem.canonical_skill_id,
            RepoFile.path,
            EvidenceItem.start_line,
            EvidenceItem.rule_id,
            EvidenceItem.end_line,
        )
        statement: Select[Any] = (
            select(EvidenceItem, RepoFile)
            .join(RepoFile, EvidenceItem.repo_file_id == RepoFile.id)
            .where(EvidenceItem.scan_id == scan_id)
            .order_by(*order_columns)
        )
        if decoded_cursor is not None:
            statement = statement.where(tuple_(*order_columns) > decoded_cursor)
        if canonical_skill_id is not None:
            statement = statement.where(EvidenceItem.canonical_skill_id == canonical_skill_id)
        if confidence:
            statement = statement.where(EvidenceItem.confidence.in_(confidence))
        if claim_eligible is not None:
            eligible = and_(
                EvidenceItem.confidence.in_([item.value for item in CLAIM_ELIGIBLE_CONFIDENCE]),
                EvidenceItem.evidence_kind != "documentation_reference",
            )
            statement = statement.where(eligible if claim_eligible else ~eligible)

        rows = list((await self.session.execute(statement.limit(limit + 1))).all())
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = None
        if has_more and page_rows:
            evidence, repo_file = page_rows[-1]
            next_cursor = encode_evidence_cursor(
                (
                    evidence.canonical_skill_id,
                    repo_file.path,
                    evidence.start_line,
                    evidence.rule_id,
                    evidence.end_line,
                )
            )
        return EvidenceRecordPage(
            data=[_evidence_record(evidence, repo_file) for evidence, repo_file in page_rows],
            next_cursor=next_cursor,
        )


def _scan_record(scan: Scan) -> ScanRecord:
    return ScanRecord(
        id=scan.id,
        repository_snapshot=dict(scan.repository_snapshot),
        status=scan.status,
        phase=scan.phase,
        commit_sha=scan.commit_sha,
        detector_version=scan.detector_version,
        taxonomy_version=scan.taxonomy_version,
        redaction_version=scan.redaction_version,
        evidence_contract_version=scan.evidence_contract_version,
        scan_policy_version=scan.scan_policy_version,
        scan_policy_snapshot=dict(scan.scan_policy_snapshot),
        scan_policy_observations=dict(scan.scan_policy_observations),
        coverage_state=scan.coverage_state,
        coverage_reasons=list(scan.coverage_reasons),
        files_discovered=scan.files_discovered,
        files_inspected=scan.files_inspected,
        files_skipped_by_policy=scan.files_skipped_by_policy,
        bytes_inspected=scan.bytes_inspected,
        failure_code=scan.failure_code,
        failure_message=scan.failure_message,
        created_at=scan.created_at,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
    )


def _evidence_record(evidence: EvidenceItem, repo_file: RepoFile) -> StoredEvidenceRecord:
    return StoredEvidenceRecord(
        id=evidence.id,
        canonical_skill_id=evidence.canonical_skill_id,
        rule_id=evidence.rule_id,
        detector_version=evidence.detector_version,
        path=repo_file.path,
        source_content_hash=evidence.source_content_hash,
        start_line=evidence.start_line,
        end_line=evidence.end_line,
        redacted_excerpt=evidence.redacted_excerpt,
        evidence_kind=evidence.evidence_kind,
        confidence=evidence.confidence,
        created_at=evidence.created_at,
    )
