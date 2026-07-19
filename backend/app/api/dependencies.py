"""FastAPI dependency wiring for application services."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.lifecycle import SqlAlchemyScanLifecycleStore
from app.db.repositories import SqlAlchemyScanRepository
from app.db.session import async_session_factory, engine, get_db_session
from app.services.readiness import DatabaseReadinessService
from app.services.scan_coordinator import ScanCoordinator
from app.services.scan_service import ScanService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_scan_service(session: DbSession) -> ScanService:
    return ScanService(SqlAlchemyScanRepository(session))


_readiness_service = DatabaseReadinessService(engine)
_scan_lifecycle = SqlAlchemyScanLifecycleStore(async_session_factory)
_scan_coordinator = ScanCoordinator(_scan_lifecycle)


def get_readiness_service() -> DatabaseReadinessService:
    return _readiness_service


def get_scan_coordinator() -> ScanCoordinator:
    return _scan_coordinator
