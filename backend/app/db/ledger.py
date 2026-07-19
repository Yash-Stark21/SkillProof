"""Atomic PostgreSQL writer for validated file inventory and evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import EvidenceItem, RepoFile, Scan
from app.domain.ledger import CompletedScanLedger
from app.domain.scan import ScanPhase, ScanStatus


class InvalidScanTransitionError(RuntimeError):
    pass


class SqlAlchemyEvidenceLedgerStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def complete_scan(self, scan_id: UUID, ledger: CompletedScanLedger) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                scan = await session.get(Scan, scan_id, with_for_update=True)
                if scan is None or scan.status != ScanStatus.RUNNING.value:
                    raise InvalidScanTransitionError("only a running scan can be completed")

                files_by_path: dict[str, RepoFile] = {}
                for file_record in ledger.files:
                    repo_file = RepoFile(
                        scan_id=scan.id,
                        path=file_record.path,
                        git_blob_sha=file_record.git_blob_sha,
                        size_bytes=file_record.size_bytes,
                        purpose=file_record.purpose,
                        inspected=file_record.inspected,
                        skip_reason=file_record.skip_reason,
                        content_hash=file_record.content_hash,
                    )
                    session.add(repo_file)
                    files_by_path[file_record.path] = repo_file
                await session.flush()

                for evidence_record in ledger.evidence:
                    if evidence_record.detector_version != scan.detector_version:
                        raise InvalidScanTransitionError(
                            "evidence detector version must match the owning scan"
                        )
                    session.add(
                        EvidenceItem(
                            scan_id=scan.id,
                            repo_file_id=files_by_path[evidence_record.file_path].id,
                            canonical_skill_id=evidence_record.canonical_skill_id,
                            rule_id=evidence_record.rule_id,
                            detector_version=evidence_record.detector_version,
                            evidence_kind=evidence_record.evidence_kind,
                            confidence=evidence_record.confidence,
                            start_line=evidence_record.start_line,
                            end_line=evidence_record.end_line,
                            source_content_hash=evidence_record.source_content_hash,
                            redacted_excerpt=evidence_record.redacted_excerpt,
                        )
                    )

                scan.commit_sha = ledger.commit_sha
                scan.scan_policy_observations = dict(ledger.scan_policy_observations)
                scan.coverage_state = ledger.coverage_state
                scan.coverage_reasons = list(ledger.coverage_reasons)
                scan.files_discovered = len(ledger.files)
                scan.files_inspected = sum(item.inspected for item in ledger.files)
                scan.files_skipped_by_policy = sum(not item.inspected for item in ledger.files)
                scan.bytes_inspected = sum(
                    item.size_bytes for item in ledger.files if item.inspected
                )
                scan.failure_code = None
                scan.failure_message = None
                scan.status = ScanStatus.COMPLETED.value
                scan.phase = ScanPhase.COMPLETE.value
                scan.completed_at = datetime.now(UTC)
