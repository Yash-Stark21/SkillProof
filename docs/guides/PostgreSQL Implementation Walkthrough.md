---
title: "PostgreSQL Implementation Walkthrough"
aliases:
  - "PostgreSQL Walkthrough"
  - "Database Implementation Guide"
type: guide
status: active
phase: implementation
owner: solo-developer
created: 2026-07-19
updated: 2026-07-19
tags:
  - skillproof
  - backend
  - postgresql
  - sqlalchemy
  - alembic
  - walkthrough
---

# PostgreSQL Implementation Walkthrough

**Change date:** 2026-07-19<br>
**Outcome:** PostgreSQL 18 now fits behind SkillProof's FastAPI service as the migration-managed system of record for the first repository-to-evidence vertical slice.

This guide explains the database boundary, the initial schema, local operations, migration workflow, transaction ownership, and the limits of this increment.

## 1. Where PostgreSQL fits

```mermaid
flowchart LR
    Vue["Vue 3 + JavaScript SPA"] -->|"JSON over /api/v1"| API["FastAPI routers"]
    API --> Services["Application services"]
    Services --> Ports["Repository and unit-of-work interfaces"]
    Ports --> Adapter["SQLAlchemy 2 async adapters"]
    Adapter -->|"psycopg 3"| PG["PostgreSQL 18"]
    API -->|"after queued scan commits"| Runner["In-process scan coordinator"]
    Runner --> Services
    Runner -.->|"later ingestion increment"| GitHub["GitHub gateway and detectors"]
```

PostgreSQL is an internal adapter, not a public integration point. The Vue client uses only `/api/v1`; application services depend on persistence interfaces; domain and detector modules do not import SQLAlchemy. This keeps evidence rules testable without a database and leaves the adapter replaceable without changing the HTTP contract.

| Boundary | Ownership rule |
| --- | --- |
| HTTP request | Receives one `AsyncSession` lifecycle through the FastAPI dependency |
| Scan task | Opens a fresh session after the queued scan has committed |
| GitHub retrieval | Runs outside database write transactions |
| Domain/detector code | Produces validated values and never operates on ORM objects |
| SQLAlchemy adapter | Translates domain values, executes queries, and owns commit/rollback through a unit of work |
| PostgreSQL | Enforces local constraints, foreign keys, uniqueness, and durable provenance |

The detailed system boundary remains in [[inception/ARCHITECTURE]], and column-level rules remain in [[inception/DATA_MODEL]].

## 2. Initial evidence-ledger schema

Alembic revision `0001_evidence_ledger` creates only the first demonstrable slice:

| Table | Purpose |
| --- | --- |
| `repositories` | Stable normalized GitHub identity and last-observed display metadata |
| `scans` | One auditable attempt, immutable repository snapshot, lifecycle, versions, policy, coverage, counters, and safe failure data |
| `repo_files` | Bounded per-scan inventory and exact hashes for inspected bytes; never raw file content |
| `evidence_items` | Skill evidence with file provenance, exact lines, rule/version, confidence, and a bounded redacted excerpt |

The migration uses UUID keys, UTC `TIMESTAMPTZ`, JSONB policy/snapshot fields, `VARCHAR + CHECK` workflow values, `ON DELETE RESTRICT`, semantic uniqueness, and query indexes. `claim_eligible` is server-derived from scan and evidence state; it is neither stored nor accepted from callers.

Job descriptions, matches, reports, and claims remain part of the approved target model but are intentionally deferred to additive migrations. Revision `0001` must not create placeholder tables for those later capabilities.

## 3. Start PostgreSQL locally

### Prerequisites

- Docker Desktop with Docker Compose v2;
- a supported Python environment for `backend/`; and
- port `5432` available for development and `5433` available when integration tests run.

From the repository root, start the persistent development service:

```powershell
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U skillproof -d skillproof
```

The development connection URL is:

```text
postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof
```

The username, password, and database in `compose.yaml` are explicit local-development defaults, not production credentials. Override the host port with `SKILLPROOF_POSTGRES_PORT` and the local password with `SKILLPROOF_POSTGRES_PASSWORD` when needed. Staging and production must inject `DATABASE_URL` from their secret/configuration system.

PostgreSQL 18 stores its versioned `PGDATA` below `/var/lib/postgresql`, so the named development volume is mounted at that parent path. This follows the [PostgreSQL Docker Official Image guidance](https://hub.docker.com/_/postgres) and prevents a container recreation from silently bypassing the intended volume.

## 4. Install and migrate the backend

From the repository root:

```powershell
Set-Location backend
python -m pip install -e ".[dev]"
$env:DATABASE_URL = "postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof"
python -m alembic upgrade head
python -m alembic current
```

Run the API from the same directory after migration:

```powershell
python -m uvicorn app.main:app --reload
```

The application never calls `create_all` and never runs migrations during startup. Migration is an explicit development, CI, and deployment step. `/health/live` checks the process only; `/health/ready` performs a bounded database connectivity check and returns the safe `NOT_READY` response when PostgreSQL is unavailable.

### Migration authoring workflow

For a future schema change:

```powershell
Set-Location backend
python -m alembic revision --autogenerate -m "describe the additive change"
python -m alembic upgrade head
```

Review generated SQL, constraint names, downgrade order, and data-compatibility requirements before accepting a revision. Use downgrades only against disposable local/test data; production rollback should normally use a reviewed forward repair migration.

## 5. Run database integration tests

The `postgres-test` Compose profile is isolated from development: it publishes port `5433`, uses a different database and role, and keeps its cluster on a disposable `tmpfs` mount.

From the repository root:

```powershell
docker compose --profile test up -d postgres-test
$env:TEST_DATABASE_URL = "postgresql+psycopg://skillproof_test:skillproof_test@localhost:5433/skillproof_test"
Set-Location backend
python -m pytest
```

The database suite must use real PostgreSQL; SQLite is not an accepted substitute for JSONB, constraints, async transaction behavior, or PostgreSQL query semantics. Tests should build an empty database through Alembic, not ORM metadata.

Stop services from the repository root:

```powershell
docker compose --profile test stop postgres-test
docker compose stop postgres
```

`docker compose down` removes containers and the network but retains the named development volume. `docker compose down --volumes` also deletes the development database and should be used only for an intentional local reset.

## 6. Transaction boundaries

The queued/running/failure ownership is implemented in the coordinator seam. When the GitHub ingestion runner is connected, it must preserve the complete transaction contract below:

1. **Accept a scan:** normalize/upsert the repository and insert the queued scan in one unit of work; commit before scheduling background work.
2. **Begin work:** the scan task opens its own session and commits the `running` transition in a short transaction.
3. **Retrieve and detect:** perform bounded GitHub requests and detector work without holding a database write transaction or sharing a session across concurrent requests.
4. **Finalize:** persist the bounded file inventory, validated evidence, and `completed` state atomically in one final unit of work.
5. **Recover from persistence failure:** roll back the final unit, then mark the scan `failed` through a fresh session/transaction with a safe failure code.
6. **Recover after process interruption:** startup reconciliation marks abandoned `queued` or `running` attempts `failed/SCAN_INTERRUPTED`; a retry creates a new auditable scan row.

These boundaries prevent accepted work from disappearing, prevent partially persisted evidence from appearing complete, and keep mutable `AsyncSession` instances out of concurrent code.

## 7. Operational checks

Run these checks before considering the database slice healthy:

```powershell
docker compose config
docker compose --profile test config
docker compose ps
```

Then verify:

- `python -m alembic upgrade head` succeeds against a fresh development or test database;
- `python -m alembic current` reports `0001_evidence_ledger` at head;
- backend unit, repository, migration, and API tests pass against `postgres-test`;
- API state survives an API-process restart while the `postgres` container and named volume remain;
- readiness becomes unavailable when PostgreSQL is stopped while liveness remains process-only; and
- raw source files, tokens, secrets, and unredacted excerpts do not appear in database rows or logs.

## 8. Current limitations

- The PostgreSQL/API foundation does not yet retrieve GitHub content or execute detector rules. Its coordinator seam records an explicit safe terminal failure rather than fabricating evidence; live ingestion remains a later Sprint 1 increment.
- The v1 scan coordinator is in-process and not durable across API restarts; reconciliation records interruption rather than resuming work.
- This increment persists the repository-to-evidence slice only. Job parsing, matching, reports, scores, and claims require later migrations.
- Authentication, private repositories, row-level security, replicas, backups, point-in-time recovery, connection proxies, and production pool sizing are not configured by local Compose.
- The Compose passwords are intentionally low-value local examples. Never reuse them outside a developer workstation or CI sandbox.
- Major PostgreSQL upgrades require an explicit backup/restore or `pg_upgrade` procedure; changing the image major is not an ordinary Compose restart.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/ARCHITECTURE]]
- [[inception/DATA_MODEL]]
- [[inception/DECISION_LOG]]
- [[guides/Vue Frontend Walkthrough]]
