"""In-process scan lifecycle seam for the later GitHub ingestion worker."""

from __future__ import annotations

from uuid import UUID

from fastapi import BackgroundTasks

from app.domain.ports import ScanLifecycleStore


class ScanCoordinator:
    """Schedule scan work only after the queued row has committed.

    The PostgreSQL slice intentionally does not fetch GitHub content yet. Its default
    runner records an explicit terminal failure rather than leaving scans queued forever.
    A later ingestion increment replaces ``run`` behind this stable boundary.
    """

    def __init__(self, lifecycle: ScanLifecycleStore) -> None:
        self.lifecycle = lifecycle

    def schedule(self, background_tasks: BackgroundTasks, scan_id: UUID) -> None:
        background_tasks.add_task(self.run, scan_id)

    async def run(self, scan_id: UUID) -> None:
        if not await self.lifecycle.mark_running(scan_id):
            return
        await self.lifecycle.mark_failed(
            scan_id,
            code="SCAN_INTERNAL_ERROR",
            message="Repository ingestion is not enabled in this database foundation increment.",
        )


async def reconcile_abandoned_scans(
    lifecycle: ScanLifecycleStore,
) -> int:
    """Mark work owned by a previous single-process runtime as interrupted."""

    return await lifecycle.reconcile_abandoned()
