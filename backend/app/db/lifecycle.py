"""PostgreSQL adapter for in-process scan lifecycle transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Scan
from app.domain.scan import ScanPhase, ScanStatus


class SqlAlchemyScanLifecycleStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def mark_running(self, scan_id: UUID) -> bool:
        async with self.session_factory() as session:
            async with session.begin():
                scan = await session.get(Scan, scan_id, with_for_update=True)
                if scan is None or scan.status != ScanStatus.QUEUED.value:
                    return False
                scan.status = ScanStatus.RUNNING.value
                scan.phase = ScanPhase.RESOLVING_REPOSITORY.value
                scan.started_at = datetime.now(UTC)
                return True

    async def mark_failed(self, scan_id: UUID, *, code: str, message: str) -> bool:
        async with self.session_factory() as session:
            async with session.begin():
                scan = await session.get(Scan, scan_id, with_for_update=True)
                if scan is None or scan.status != ScanStatus.RUNNING.value:
                    return False
                scan.status = ScanStatus.FAILED.value
                scan.phase = ScanPhase.FAILED.value
                scan.coverage_state = None
                scan.coverage_reasons = []
                scan.failure_code = code
                scan.failure_message = message
                scan.completed_at = datetime.now(UTC)
                return True

    async def reconcile_abandoned(self) -> int:
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    update(Scan)
                    .where(Scan.status.in_([ScanStatus.QUEUED.value, ScanStatus.RUNNING.value]))
                    .values(
                        status=ScanStatus.FAILED.value,
                        phase=ScanPhase.FAILED.value,
                        coverage_state=None,
                        coverage_reasons=[],
                        failure_code="SCAN_INTERRUPTED",
                        failure_message="The scan was interrupted before it completed.",
                        completed_at=now,
                    )
                )
                return int(getattr(result, "rowcount", 0) or 0)
