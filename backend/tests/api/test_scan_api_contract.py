"""HTTP contract tests using dependency-injected, side-effect-free services."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_readiness_service,
    get_scan_coordinator,
    get_scan_service,
)
from app.api.errors import ApiError
from app.main import create_app
from app.schemas.scan import EvidencePageResponse, ScanResponse
from app.services.repository_url import (
    RepositoryUrlError,
    normalize_github_repository_url,
)

SCAN_ID = "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd"
COMMIT_SHA = "0123456789abcdef0123456789abcdef01234567"
CONTENT_HASH = "ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c"


def _repository() -> dict[str, str]:
    return {
        "provider": "github",
        "identity": "github:octocat/example",
        "owner": "octocat",
        "name": "example",
        "url": "https://github.com/octocat/example",
    }


def _coverage() -> dict[str, Any]:
    return {
        "state": "complete",
        "reasons": [],
        "files_discovered": 2,
        "files_inspected": 1,
        "files_skipped_by_policy": 1,
        "bytes_inspected": 512,
        "limits": {
            "github_requests": 50,
            "tree_entries": 10_000,
            "file_blobs": 40,
            "per_file_bytes": 262_144,
            "total_file_bytes": 5_242_880,
            "concurrency": 5,
            "request_timeout_seconds": 10,
        },
        "observed": {
            "github_requests": 3,
            "tree_entries": 2,
            "file_blobs": 1,
            "largest_file_bytes": 512,
            "total_file_bytes": 512,
            "maximum_concurrency": 1,
        },
    }


def _scan(*, status: str = "queued") -> dict[str, Any]:
    completed = status == "completed"
    running = status == "running"
    return {
        "id": SCAN_ID,
        "repository": _repository(),
        "status": status,
        "phase": "complete" if completed else ("detecting" if running else "queued"),
        "commit_sha": COMMIT_SHA if completed else None,
        "detector_version": "0.1.0",
        "taxonomy_version": "0.1.0",
        "redaction_version": "0.1.0",
        "evidence_contract_version": "0.1",
        "scan_policy_version": "0.1",
        "coverage": _coverage() if completed else None,
        "error": None,
        "created_at": "2026-07-15T10:30:00Z",
        "started_at": "2026-07-15T10:30:01Z" if completed or running else None,
        "completed_at": "2026-07-15T10:30:04Z" if completed else None,
    }


def _evidence_item() -> dict[str, Any]:
    return {
        "id": "4a47e339-b59b-4b4d-ad58-bfc56b4d47d2",
        "contract_version": "0.1",
        "canonical_skill_id": "fastapi",
        "rule_id": "python.fastapi.route_decorator",
        "detector_version": "0.1.0",
        "repository": "github:octocat/example",
        "commit_sha": COMMIT_SHA,
        "path": "backend/app/main.py",
        "content_hash": CONTENT_HASH,
        "start_line": 12,
        "end_line": 14,
        "redacted_excerpt": '@app.get("/health")\nasync def health():\n    return {"status": "ok"}',
        "evidence_kind": "route",
        "confidence": "high",
        "coverage_state": "complete",
        "created_at": "2026-07-15T10:30:04Z",
        "claim_eligible": True,
    }


@dataclass
class FakeReadinessService:
    ready: bool = True
    calls: int = 0

    async def check(self) -> bool:
        self.calls += 1
        return self.ready


@dataclass
class FakeScanCoordinator:
    scheduled_scan_ids: list[UUID] = field(default_factory=list)

    def schedule(self, _background_tasks: Any, scan_id: UUID) -> None:
        self.scheduled_scan_ids.append(scan_id)


@dataclass
class FakeScanService:
    scan: ScanResponse | None = field(default_factory=lambda: ScanResponse.model_validate(_scan()))
    create_calls: list[Any] = field(default_factory=list)
    get_calls: list[UUID] = field(default_factory=list)
    evidence_calls: list[dict[str, Any]] = field(default_factory=list)

    async def create_scan(self, repository_url: str) -> ScanResponse:
        try:
            normalize_github_repository_url(repository_url)
        except RepositoryUrlError as error:
            raise ApiError(
                status_code=422,
                code=(
                    "UNSUPPORTED_REPOSITORY_HOST"
                    if error.code == "unsupported_host"
                    else "VALIDATION_ERROR"
                ),
                message=error.message,
                details={
                    "fields": [
                        {
                            "field": "repository_url",
                            "code": error.code,
                            "message": error.message,
                        }
                    ]
                },
            ) from error
        self.create_calls.append(repository_url)
        return ScanResponse.model_validate(_scan())

    async def get_scan(self, scan_id: UUID) -> ScanResponse:
        self.get_calls.append(scan_id)
        if self.scan is None:
            raise ApiError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="The requested scan could not be found.",
            )
        return self.scan

    async def list_evidence(
        self,
        scan_id: UUID,
        limit: int,
        cursor: str | None,
        canonical_skill_id: str | None,
        confidence: list[str] | None,
        claim_eligible: bool | None,
    ) -> EvidencePageResponse:
        self.evidence_calls.append(
            {
                "scan_id": scan_id,
                "limit": limit,
                "cursor": cursor,
                "canonical_skill_id": canonical_skill_id,
                "confidence": confidence,
                "claim_eligible": claim_eligible,
            }
        )
        return EvidencePageResponse.model_validate(
            {
                "data": [_evidence_item()],
                "page": {"next_cursor": None, "limit": limit},
                "scan": {
                    "id": SCAN_ID,
                    "status": "completed",
                    "coverage": _coverage(),
                },
            }
        )


@pytest.fixture
def fake_scan_service() -> FakeScanService:
    return FakeScanService()


@pytest.fixture
def fake_readiness_service() -> FakeReadinessService:
    return FakeReadinessService()


@pytest.fixture
def fake_scan_coordinator() -> FakeScanCoordinator:
    return FakeScanCoordinator()


@pytest.fixture
def client(
    fake_scan_service: FakeScanService,
    fake_readiness_service: FakeReadinessService,
    fake_scan_coordinator: FakeScanCoordinator,
) -> Iterator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_scan_service] = lambda: fake_scan_service
    application.dependency_overrides[get_readiness_service] = lambda: fake_readiness_service
    application.dependency_overrides[get_scan_coordinator] = lambda: fake_scan_coordinator
    test_client = TestClient(application, raise_server_exceptions=False)
    yield test_client
    test_client.close()


def test_liveness_does_not_call_dependency_services(
    client: TestClient,
    fake_scan_service: FakeScanService,
    fake_readiness_service: FakeReadinessService,
) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
    assert response.headers["x-request-id"]
    assert fake_readiness_service.calls == 0
    assert fake_scan_service.get_calls == []


def test_readiness_reports_database_health(
    client: TestClient, fake_readiness_service: FakeReadinessService
) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}
    assert response.headers["x-request-id"]
    assert fake_readiness_service.calls == 1


def test_readiness_returns_safe_503_when_database_is_unavailable(
    client: TestClient, fake_readiness_service: FakeReadinessService
) -> None:
    fake_readiness_service.ready = False

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["code"] == "NOT_READY"
    assert response.json()["message"]
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "database" not in response.text.lower() or "unavailable" in response.text.lower()


def test_start_scan_accepts_url_and_returns_polling_headers(
    client: TestClient,
    fake_scan_service: FakeScanService,
    fake_scan_coordinator: FakeScanCoordinator,
) -> None:
    response = client.post(
        "/api/v1/scans",
        json={"repository_url": "https://github.com/OctoCat/Example.git"},
    )

    assert response.status_code == 202
    assert response.headers["location"] == f"/api/v1/scans/{SCAN_ID}"
    assert response.headers["retry-after"] == "2"
    assert response.headers["x-request-id"]
    assert response.json()["status"] == "queued"
    assert response.json()["coverage"] is None
    assert fake_scan_service.create_calls == ["https://github.com/OctoCat/Example.git"]
    assert fake_scan_coordinator.scheduled_scan_ids == [UUID(SCAN_ID)]


def test_start_scan_rejects_unsupported_host_without_calling_service(
    client: TestClient, fake_scan_service: FakeScanService
) -> None:
    response = client.post(
        "/api/v1/scans",
        json={"repository_url": "https://gitlab.com/octocat/example"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "UNSUPPORTED_REPOSITORY_HOST"
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert fake_scan_service.create_calls == []


def test_malformed_json_uses_the_stable_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scans",
        content=b'{"repository_url":',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "MALFORMED_JSON"
    assert response.json()["request_id"] == response.headers["x-request-id"]


@pytest.mark.parametrize("status", ["queued", "running"])
def test_nonterminal_scan_status_includes_retry_after(
    status: str,
    client: TestClient,
    fake_scan_service: FakeScanService,
) -> None:
    fake_scan_service.scan = ScanResponse.model_validate(_scan(status=status))

    response = client.get(f"/api/v1/scans/{SCAN_ID}")

    assert response.status_code == 200
    assert response.json()["status"] == status
    assert response.headers["retry-after"] == "2"
    assert fake_scan_service.get_calls == [UUID(SCAN_ID)]


def test_unknown_scan_returns_safe_not_found(
    client: TestClient, fake_scan_service: FakeScanService
) -> None:
    fake_scan_service.scan = None

    response = client.get(f"/api/v1/scans/{SCAN_ID}")

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_completed_evidence_supports_all_filters(
    client: TestClient, fake_scan_service: FakeScanService
) -> None:
    response = client.get(
        f"/api/v1/scans/{SCAN_ID}/evidence",
        params=[
            ("limit", "25"),
            ("cursor", "opaque-page-2"),
            ("canonical_skill_id", "fastapi"),
            ("confidence", "high"),
            ("confidence", "medium"),
            ("claim_eligible", "true"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == {"next_cursor": None, "limit": 25}
    assert body["data"][0]["claim_eligible"] is True
    assert body["data"][0]["repository"] == "github:octocat/example"
    assert fake_scan_service.evidence_calls == [
        {
            "scan_id": UUID(SCAN_ID),
            "limit": 25,
            "cursor": "opaque-page-2",
            "canonical_skill_id": "fastapi",
            "confidence": ["high", "medium"],
            "claim_eligible": True,
        }
    ]


@pytest.mark.parametrize("limit", [0, 101])
def test_evidence_limit_is_bounded_by_contract(client: TestClient, limit: int) -> None:
    response = client.get(
        f"/api/v1/scans/{SCAN_ID}/evidence",
        params={"limit": limit},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["details"]["fields"][0]["field"] == "limit"


def test_invalid_scan_id_uses_validation_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/scans/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["request_id"] == response.headers["x-request-id"]
