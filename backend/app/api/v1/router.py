"""Top-level v1 router."""

from fastapi import APIRouter

from app.api.v1.routes import health, scans

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
