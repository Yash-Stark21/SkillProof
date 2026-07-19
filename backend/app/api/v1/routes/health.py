"""Process liveness and PostgreSQL readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_readiness_service
from app.api.errors import ApiError
from app.services.readiness import DatabaseReadinessService

router = APIRouter()


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@router.get("/ready")
async def ready(
    readiness: Annotated[DatabaseReadinessService, Depends(get_readiness_service)],
) -> dict[str, object]:
    if not await readiness.check():
        raise ApiError(
            status_code=503,
            code="NOT_READY",
            message="SkillProof is not ready because PostgreSQL is unavailable.",
        )
    return {"status": "ready", "checks": {"database": "ok"}}
