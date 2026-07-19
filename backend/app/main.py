"""SkillProof FastAPI application factory."""

from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.errors import install_exception_handlers
from app.api.v1.router import api_router
from app.db.lifecycle import SqlAlchemyScanLifecycleStore
from app.db.session import async_session_factory, dispose_engine
from app.services.scan_coordinator import reconcile_abandoned_scans

logger = logging.getLogger(__name__)
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def create_app() -> FastAPI:
    lifecycle_store = SqlAlchemyScanLifecycleStore(async_session_factory)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        try:
            interrupted = await reconcile_abandoned_scans(lifecycle_store)
            if interrupted:
                logger.info("reconciled_interrupted_scans count=%s", interrupted)
        except SQLAlchemyError:
            logger.warning("database_startup_reconciliation_unavailable")
        yield
        await dispose_engine()

    application = FastAPI(
        title="SkillProof API",
        version="0.1.0",
        lifespan=lifespan,
    )
    install_exception_handlers(application)

    @application.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        supplied = request.headers.get("X-Request-ID")
        request_id = (
            supplied
            if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied)
            else f"req_{uuid4().hex}"
        )
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
