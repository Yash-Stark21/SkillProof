"""Application-facing persistence ports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.domain.ledger import CompletedScanLedger
from app.domain.records import EvidenceRecordPage, ScanAttempt, ScanRecord
from app.domain.repository import NormalizedRepository


class InvalidCursorError(ValueError):
    """An opaque collection cursor cannot be decoded safely."""


class ScanStore(Protocol):
    async def create_attempt(
        self, repository: NormalizedRepository, attempt: ScanAttempt
    ) -> ScanRecord: ...

    async def get_scan(self, scan_id: UUID) -> ScanRecord | None: ...

    async def list_evidence(
        self,
        *,
        scan_id: UUID,
        limit: int,
        cursor: str | None,
        canonical_skill_id: str | None,
        confidence: Sequence[str],
        claim_eligible: bool | None,
    ) -> EvidenceRecordPage: ...


class ScanLifecycleStore(Protocol):
    async def mark_running(self, scan_id: UUID) -> bool: ...

    async def mark_failed(self, scan_id: UUID, *, code: str, message: str) -> bool: ...

    async def reconcile_abandoned(self) -> int: ...


class EvidenceLedgerStore(Protocol):
    async def complete_scan(self, scan_id: UUID, ledger: CompletedScanLedger) -> None: ...
