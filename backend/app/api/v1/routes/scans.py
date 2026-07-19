"""Repository scan and evidence endpoints."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status

from app.api.dependencies import get_scan_coordinator, get_scan_service
from app.schemas.scan import EvidencePageResponse, ScanCreateRequest, ScanResponse
from app.services.scan_coordinator import ScanCoordinator
from app.services.scan_service import ScanService

router = APIRouter()


@router.post("", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    payload: ScanCreateRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    service: Annotated[ScanService, Depends(get_scan_service)],
    coordinator: Annotated[ScanCoordinator, Depends(get_scan_coordinator)],
) -> ScanResponse:
    scan = await service.create_scan(payload.repository_url)
    response.headers["Location"] = f"/api/v1/scans/{scan.id}"
    response.headers["Retry-After"] = "2"
    coordinator.schedule(background_tasks, scan.id)
    return scan


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    response: Response,
    service: Annotated[ScanService, Depends(get_scan_service)],
) -> ScanResponse:
    scan = await service.get_scan(scan_id)
    if scan.status in {"queued", "running"}:
        response.headers["Retry-After"] = "2"
    return scan


@router.get("/{scan_id}/evidence", response_model=EvidencePageResponse)
async def list_scan_evidence(
    scan_id: UUID,
    service: Annotated[ScanService, Depends(get_scan_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
    canonical_skill_id: str | None = None,
    confidence: Annotated[list[Literal["high", "medium", "low"]] | None, Query()] = None,
    claim_eligible: bool | None = None,
) -> EvidencePageResponse:
    return await service.list_evidence(
        scan_id,
        limit=limit,
        cursor=cursor,
        canonical_skill_id=canonical_skill_id,
        confidence=confidence or [],
        claim_eligible=claim_eligible,
    )
