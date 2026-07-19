"""PostgreSQL-only persistence checks.

These tests are intentionally skipped unless ``TEST_DATABASE_URL`` is supplied.
The session migrates an isolated ``*_test`` database through Alembic. Each test
runs in a transaction that is rolled back, so no application data is retained.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, async_sessionmaker, create_async_engine

from app.db.ledger import SqlAlchemyEvidenceLedgerStore
from app.db.models import EvidenceItem, RepoFile, Repository, Scan
from app.db.repositories import SqlAlchemyScanRepository
from app.domain.ledger import CompletedScanLedger, EvidenceCandidate, FileInventoryRecord
from app.services.evidence_ledger import EvidenceLedgerService
from app.services.scan_service import ScanService

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="Set TEST_DATABASE_URL to run PostgreSQL integration tests.",
    ),
]

NOW = datetime(2026, 7, 15, 10, 30, 4, tzinfo=UTC)
COMMIT_SHA = "0123456789abcdef0123456789abcdef01234567"
CONTENT_HASH = "ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c"
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _async_url(value: str) -> URL:
    url = make_url(value)
    if url.get_backend_name() == "postgresql" and url.drivername != "postgresql+psycopg":
        return url.set(drivername="postgresql+psycopg")
    return url


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    assert TEST_DATABASE_URL is not None  # guarded by the module skip marker
    url = make_url(TEST_DATABASE_URL)
    if not url.database or not url.database.endswith("_test"):
        pytest.fail("PostgreSQL integration tests require a database ending in '_test'.")

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("%", "%%"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.check(config)
    yield
    command.downgrade(config, "base")


@pytest_asyncio.fixture
async def postgres_connection(
    migrated_database: None,
) -> AsyncIterator[AsyncConnection]:
    assert TEST_DATABASE_URL is not None  # guarded by the module skip marker
    engine = create_async_engine(_async_url(TEST_DATABASE_URL))

    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()
    await engine.dispose()


async def _insert_repository_and_scan(
    connection: AsyncConnection,
) -> tuple[UUID, UUID]:
    repository_id = uuid4()
    scan_id = uuid4()
    await connection.execute(
        Repository.__table__.insert().values(
            id=repository_id,
            provider="github",
            provider_repository_id=123456,
            normalized_owner="octocat",
            normalized_name="example",
            display_owner="OctoCat",
            display_name="Example",
            canonical_url="https://github.com/OctoCat/Example",
            default_branch="main",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    await connection.execute(
        Scan.__table__.insert().values(
            id=scan_id,
            repository_id=repository_id,
            repository_snapshot={
                "provider": "github",
                "identity": "github:octocat/example",
                "owner": "OctoCat",
                "name": "Example",
                "url": "https://github.com/OctoCat/Example",
            },
            status="completed",
            phase="complete",
            commit_sha=COMMIT_SHA,
            detector_version="0.1.0",
            taxonomy_version="0.1.0",
            redaction_version="0.1.0",
            evidence_contract_version="0.1",
            scan_policy_version="0.1",
            scan_policy_snapshot={"file_blobs": 40, "total_file_bytes": 5_242_880},
            scan_policy_observations={"file_blobs": 1, "total_file_bytes": 512},
            coverage_state="complete",
            coverage_reasons=[],
            files_discovered=2,
            files_inspected=1,
            files_skipped_by_policy=1,
            bytes_inspected=512,
            failure_code=None,
            failure_message=None,
            created_at=NOW,
            started_at=NOW,
            completed_at=NOW,
        )
    )
    return repository_id, scan_id


async def _insert_file_and_evidence(
    connection: AsyncConnection, scan_id: UUID
) -> tuple[UUID, UUID]:
    repo_file_id = uuid4()
    evidence_id = uuid4()
    await connection.execute(
        RepoFile.__table__.insert().values(
            id=repo_file_id,
            scan_id=scan_id,
            path="backend/app/main.py",
            git_blob_sha="a" * 40,
            size_bytes=512,
            purpose="source",
            inspected=True,
            skip_reason=None,
            content_hash=CONTENT_HASH,
            created_at=NOW,
        )
    )
    await connection.execute(
        EvidenceItem.__table__.insert().values(
            id=evidence_id,
            scan_id=scan_id,
            repo_file_id=repo_file_id,
            canonical_skill_id="fastapi",
            rule_id="python.fastapi.route_decorator",
            detector_version="0.1.0",
            evidence_kind="route",
            confidence="high",
            start_line=12,
            end_line=14,
            source_content_hash=CONTENT_HASH,
            redacted_excerpt='@app.get("/health")',
            created_at=NOW,
        )
    )
    return repo_file_id, evidence_id


async def _insert_repository_and_running_scan(connection: AsyncConnection) -> UUID:
    repository_id = uuid4()
    scan_id = uuid4()
    await connection.execute(
        Repository.__table__.insert().values(
            id=repository_id,
            provider="github",
            normalized_owner="octocat",
            normalized_name="atomic-ledger",
            display_owner="OctoCat",
            display_name="Atomic-Ledger",
            canonical_url="https://github.com/OctoCat/Atomic-Ledger",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    await connection.execute(
        Scan.__table__.insert().values(
            id=scan_id,
            repository_id=repository_id,
            repository_snapshot={
                "provider": "github",
                "identity": "github:octocat/atomic-ledger",
                "owner": "OctoCat",
                "name": "Atomic-Ledger",
                "url": "https://github.com/OctoCat/Atomic-Ledger",
            },
            status="running",
            phase="detecting",
            detector_version="0.1.0",
            taxonomy_version="0.1.0",
            redaction_version="0.1.0",
            evidence_contract_version="0.1",
            scan_policy_version="0.1",
            scan_policy_snapshot={"file_blobs": 40},
            scan_policy_observations={},
            coverage_reasons=[],
            started_at=NOW,
            created_at=NOW,
        )
    )
    return scan_id


@pytest.mark.asyncio
async def test_evidence_graph_round_trips_with_exact_provenance(
    postgres_connection: AsyncConnection,
) -> None:
    _, scan_id = await _insert_repository_and_scan(postgres_connection)
    _, evidence_id = await _insert_file_and_evidence(postgres_connection, scan_id)

    row = (
        await postgres_connection.execute(
            select(
                EvidenceItem.id,
                EvidenceItem.canonical_skill_id,
                EvidenceItem.source_content_hash,
                RepoFile.path,
                Scan.commit_sha,
                Scan.repository_snapshot,
            )
            .join(RepoFile, EvidenceItem.repo_file_id == RepoFile.id)
            .join(Scan, EvidenceItem.scan_id == Scan.id)
            .where(EvidenceItem.id == evidence_id)
        )
    ).one()

    assert row.id == evidence_id
    assert row.canonical_skill_id == "fastapi"
    assert row.source_content_hash == CONTENT_HASH
    assert row.path == "backend/app/main.py"
    assert row.commit_sha == COMMIT_SHA
    assert row.repository_snapshot["identity"] == "github:octocat/example"


@pytest.mark.asyncio
async def test_validated_ledger_completes_atomically(
    postgres_connection: AsyncConnection,
) -> None:
    scan_id = await _insert_repository_and_running_scan(postgres_connection)
    session_factory = async_sessionmaker(
        bind=postgres_connection,
        expire_on_commit=False,
    )
    service = EvidenceLedgerService(SqlAlchemyEvidenceLedgerStore(session_factory))

    await service.complete_scan(
        scan_id,
        CompletedScanLedger(
            commit_sha=COMMIT_SHA,
            coverage_state="complete",
            coverage_reasons=[],
            scan_policy_observations={"file_blobs": 1, "total_file_bytes": 512},
            files=[
                FileInventoryRecord(
                    path="backend/app/main.py",
                    git_blob_sha="a" * 40,
                    size_bytes=512,
                    purpose="source",
                    inspected=True,
                    skip_reason=None,
                    content_hash=CONTENT_HASH,
                )
            ],
            evidence=[
                EvidenceCandidate(
                    file_path="backend/app/main.py",
                    canonical_skill_id="fastapi",
                    rule_id="python.fastapi.route_decorator",
                    detector_version="0.1.0",
                    evidence_kind="route",
                    confidence="high",
                    start_line=12,
                    end_line=14,
                    source_content_hash=CONTENT_HASH,
                    redacted_excerpt='@app.get("/health")',
                )
            ],
        ),
    )

    scan = (
        await postgres_connection.execute(
            select(Scan.status, Scan.commit_sha, Scan.files_inspected).where(Scan.id == scan_id)
        )
    ).one()
    assert scan.status == "completed"
    assert scan.commit_sha == COMMIT_SHA
    assert scan.files_inspected == 1
    assert (
        await postgres_connection.scalar(
            select(EvidenceItem.id).where(EvidenceItem.scan_id == scan_id)
        )
        is not None
    )

    async with session_factory() as read_session:
        page = await ScanService(SqlAlchemyScanRepository(read_session)).list_evidence(
            scan_id,
            limit=50,
            cursor=None,
            canonical_skill_id="fastapi",
            confidence=["high"],
            claim_eligible=True,
        )
    assert page.page.next_cursor is None
    assert len(page.data) == 1
    assert page.data[0].path == "backend/app/main.py"
    assert page.data[0].claim_eligible is True


@pytest.mark.asyncio
async def test_database_rejects_inconsistent_inspection_state(
    postgres_connection: AsyncConnection,
) -> None:
    _, scan_id = await _insert_repository_and_scan(postgres_connection)

    with pytest.raises(IntegrityError):
        await postgres_connection.execute(
            RepoFile.__table__.insert().values(
                id=uuid4(),
                scan_id=scan_id,
                path="backend/app/broken.py",
                git_blob_sha=None,
                size_bytes=10,
                purpose="source",
                inspected=True,
                skip_reason="fetch_failed",
                content_hash=None,
                created_at=NOW,
            )
        )


@pytest.mark.asyncio
async def test_database_rejects_duplicate_semantic_evidence(
    postgres_connection: AsyncConnection,
) -> None:
    _, scan_id = await _insert_repository_and_scan(postgres_connection)
    repo_file_id, _ = await _insert_file_and_evidence(postgres_connection, scan_id)

    with pytest.raises(IntegrityError):
        await postgres_connection.execute(
            EvidenceItem.__table__.insert().values(
                id=uuid4(),
                scan_id=scan_id,
                repo_file_id=repo_file_id,
                canonical_skill_id="fastapi",
                rule_id="python.fastapi.route_decorator",
                detector_version="0.1.0",
                evidence_kind="route",
                confidence="high",
                start_line=12,
                end_line=14,
                source_content_hash=CONTENT_HASH,
                redacted_excerpt='@app.get("/health")',
                created_at=NOW,
            )
        )


@pytest.mark.asyncio
async def test_database_rejects_completed_scan_without_provenance(
    postgres_connection: AsyncConnection,
) -> None:
    repository_id = uuid4()
    await postgres_connection.execute(
        Repository.__table__.insert().values(
            id=repository_id,
            provider="github",
            provider_repository_id=None,
            normalized_owner="octocat",
            normalized_name="missing-commit",
            display_owner="octocat",
            display_name="missing-commit",
            canonical_url="https://github.com/octocat/missing-commit",
            default_branch=None,
            created_at=NOW,
            updated_at=NOW,
        )
    )

    with pytest.raises(IntegrityError):
        await postgres_connection.execute(
            Scan.__table__.insert().values(
                id=uuid4(),
                repository_id=repository_id,
                repository_snapshot={
                    "provider": "github",
                    "identity": "github:octocat/missing-commit",
                    "owner": "octocat",
                    "name": "missing-commit",
                    "url": "https://github.com/octocat/missing-commit",
                },
                status="completed",
                phase="complete",
                commit_sha=None,
                detector_version="0.1.0",
                taxonomy_version="0.1.0",
                redaction_version="0.1.0",
                evidence_contract_version="0.1",
                scan_policy_version="0.1",
                scan_policy_snapshot={},
                scan_policy_observations={},
                coverage_state="complete",
                coverage_reasons=[],
                files_discovered=0,
                files_inspected=0,
                files_skipped_by_policy=0,
                bytes_inspected=0,
                failure_code=None,
                failure_message=None,
                created_at=NOW,
                started_at=NOW,
                completed_at=NOW,
            )
        )
