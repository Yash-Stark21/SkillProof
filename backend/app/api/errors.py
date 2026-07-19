"""Safe API error types and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _body(error: ApiError, request: Request) -> dict[str, Any]:
    body: dict[str, Any] = {
        "code": error.code,
        "message": error.message,
        "request_id": _request_id(request),
    }
    if error.details is not None:
        body["details"] = error.details
    return body


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=_body(error, request),
            headers=error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        if any(item.get("type") == "json_invalid" for item in error.errors()):
            malformed = ApiError(
                status_code=400,
                code="MALFORMED_JSON",
                message="The request body is not valid JSON.",
            )
            return JSONResponse(status_code=400, content=_body(malformed, request))

        fields: list[dict[str, str]] = []
        for item in error.errors():
            location = [
                str(part) for part in item.get("loc", ()) if part not in {"body", "query", "path"}
            ]
            fields.append(
                {
                    "field": ".".join(location) or "request",
                    "code": str(item.get("type", "invalid")),
                    "message": str(item.get("msg", "Invalid value.")),
                }
            )
        api_error = ApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="The request contains invalid fields.",
            details={"fields": fields},
        )
        return JSONResponse(status_code=422, content=_body(api_error, request))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _error: Exception) -> JSONResponse:
        api_error = ApiError(
            status_code=500,
            code="INTERNAL_ERROR",
            message="SkillProof could not complete the request.",
        )
        return JSONResponse(status_code=500, content=_body(api_error, request))
