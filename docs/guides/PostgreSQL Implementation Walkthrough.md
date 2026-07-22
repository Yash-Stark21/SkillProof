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
updated: 2026-07-22
tags:
  - skillproof
  - backend
  - postgresql
  - sqlalchemy
  - alembic
  - walkthrough
---

# PostgreSQL Implementation Walkthrough

**Change date:** 2026-07-22<br>
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

## 3. Set up the installed PostgreSQL 18 service

### Prerequisites

- PostgreSQL 18 installed on Windows and registered as service `postgresql-x64-18`;
- PostgreSQL client tools in `C:\Program Files\PostgreSQL\18\bin` or available on `PATH`;
- the existing backend virtual environment at `backend/.venv`; and
- `localhost:5432` available to the native service.

Confirm that the Windows service and server are reachable:

```powershell
Get-Service -Name postgresql-x64-18
& "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe" -h localhost -p 5432
```

If PostgreSQL was installed in a different directory, use the matching `pg_isready.exe`; `backend/scripts/setup_local_postgres.ps1` also checks the default PostgreSQL 18 tools directory and `PATH`. Start a stopped service through Windows Services or an elevated PowerShell session before continuing.

Prepare the backend dependencies with the repository-local virtual environment:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location ..
```

From the repository root, run the local database setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\backend\scripts\setup_local_postgres.ps1
```

The script securely prompts for the PostgreSQL administrator password. The input is masked and is used only for the setup process; it is not written to `backend/.env`, process output, or the repository. Do not put the administrator password directly on a command line or in an environment file. The script is idempotent and non-destructive by default.

The setup provisions these native resources on the same PostgreSQL 18 instance:

| Purpose | Database | Application role | Local-only password | Schema | SQLAlchemy URL |
| --- | --- | --- | --- | --- | --- |
| Development | `skillproof` | `skillproof` | `skillproof` | `public` | `postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof` |
| Integration test | `skillproof_test` | `skillproof_test` | `skillproof_test` | `public` | `postgresql+psycopg://skillproof_test:skillproof_test@localhost:5432/skillproof_test` |

Each application role owns its database and `public` schema; unrestricted `PUBLIC` schema creation is revoked. The listed passwords are deliberately low-value workstation credentials and must never be reused in staging or production.

When absent, the script creates `backend/.env` with the native development and test URLs. That file is ignored by Git, contains only application-role credentials, and must remain uncommitted. An existing `backend/.env` is preserved for deliberate local configuration. The setup exports the URLs for its own process, runs Alembic `upgrade head`, verifies `current`, and runs the migration drift check. The expected development head is `0001_evidence_ledger` in schema `public`.

## 4. Migrate and run the backend

The setup script applies the current migration. To verify or reapply it explicitly, run from the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

`current` must report `0001_evidence_ledger (head)`. This migration creates `repositories`, `scans`, `repo_files`, and `evidence_items` in the development database's `public` schema. If `backend/.env` is intentionally absent, set `DATABASE_URL` in the current process before running Alembic.

Run the API from the same directory after migration:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The application never calls `create_all` and never runs migrations during startup. Migration is an explicit development, CI, and deployment step. `/api/v1/health/live` checks the process only; `/api/v1/health/ready` performs a bounded database connectivity check and returns the safe `NOT_READY` response when PostgreSQL is unavailable.

### Migration authoring workflow

For a future schema change:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe the additive change"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Review generated SQL, constraint names, downgrade order, and data-compatibility requirements before accepting a revision. Use downgrades only against disposable local/test data; production rollback should normally use a reviewed forward repair migration.

## 5. Run database integration tests

The native `skillproof_test` database is isolated from development by database and role while sharing the local service on port `5432`. The integration fixture refuses the development database, requires a database name ending in `_test`, migrates the test schema from base to head, rolls back each test transaction, and downgrades the schema to base when the session ends.

Export the test URL explicitly because the PostgreSQL integration module reads `TEST_DATABASE_URL` from the process environment:

```powershell
Set-Location backend
$env:TEST_DATABASE_URL = "postgresql+psycopg://skillproof_test:skillproof_test@localhost:5432/skillproof_test"
.\.venv\Scripts\python.exe -m pytest
Remove-Item Env:TEST_DATABASE_URL
```

The database suite must use real PostgreSQL; SQLite is not an accepted substitute for JSONB, constraints, async transaction behavior, or PostgreSQL query semantics. Tests should build an empty database through Alembic, not ORM metadata.

### Optional Docker Compose fallback

`compose.yaml` is retained for contributors who do not have the native Windows service. It is an alternative local runtime, not the default setup. The Compose development service publishes port `5432`, which conflicts with a running `postgresql-x64-18` service; either use a different host port or intentionally stop the native service before starting that container.

This example keeps the Windows service running and publishes the optional development container on `55432`:

```powershell
$env:SKILLPROOF_POSTGRES_PORT = "55432"
docker compose up -d postgres
$env:DATABASE_URL = "postgresql+psycopg://skillproof:skillproof@localhost:55432/skillproof"
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
Set-Location ..
```

The optional `postgres-test` profile still publishes its disposable database on port `5433`:

```powershell
docker compose --profile test up -d postgres-test
$env:TEST_DATABASE_URL = "postgresql+psycopg://skillproof_test:skillproof_test@localhost:5433/skillproof_test"
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
Set-Location ..
```

Run Compose commands from the repository root. `docker compose down` removes containers and the network but retains the named development volume. `docker compose down --volumes` deletes only the Compose development volume; it does not reset the native Windows databases and should be used only for an intentional container-database reset.

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

Run these checks before considering the native database slice healthy:

```powershell
Get-Service -Name postgresql-x64-18
& "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe" -h localhost -p 5432
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U skillproof -d skillproof -W -c "SELECT current_database(), current_schema(), current_user;"
Set-Location backend
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Then verify:

- the service status is `Running` and `pg_isready` accepts connections on `localhost:5432`;
- the SQL identity query reports database `skillproof`, schema `public`, and user `skillproof`;
- `.\.venv\Scripts\python.exe -m alembic upgrade head` succeeds and `current` reports `0001_evidence_ledger (head)`;
- backend unit, repository, migration, and API tests pass against `skillproof_test`, never `skillproof`;
- API state survives an API-process restart while the Windows PostgreSQL service remains available;
- readiness becomes unavailable when PostgreSQL is stopped while liveness remains process-only; and
- raw source files, tokens, secrets, and unredacted excerpts do not appear in database rows or logs.

For the optional Compose fallback, additionally run `docker compose config`, `docker compose --profile test config`, and `docker compose ps` from the repository root.

### Intentional native reset

The setup script's `-Reset` switch force-drops and recreates both `skillproof` and `skillproof_test` before restoring roles, `public` schema ownership, and the migration head:

```powershell
powershell -ExecutionPolicy Bypass -File .\backend\scripts\setup_local_postgres.ps1 -Reset
```

This permanently deletes all local application and test data. Stop the API and test processes first, back up anything needed, confirm that the target is the local PostgreSQL 18 instance, and let the script prompt securely for the administrator password. Never use `-Reset` against staging, production, a shared server, or a database containing work you need. Do not manually drop the whole PostgreSQL cluster or restart `postgresql-x64-18` merely to reset SkillProof; the service can contain unrelated databases. Compose volume deletion and the native `-Reset` path are separate operations.

## 8. Current limitations

- The PostgreSQL/API foundation does not yet retrieve GitHub content or execute detector rules. Its coordinator seam records an explicit safe terminal failure rather than fabricating evidence; live ingestion remains a later Sprint 1 increment.
- The v1 scan coordinator is in-process and not durable across API restarts; reconciliation records interruption rather than resuming work.
- This increment persists the repository-to-evidence slice only. Job parsing, matching, reports, scores, and claims require later migrations.
- Authentication, private repositories, row-level security, replicas, backups, point-in-time recovery, connection proxies, and production pool sizing are not configured by the native local setup or optional Compose fallback.
- Native application-role and Compose passwords are intentionally low-value local examples. Never reuse them outside a developer workstation or CI sandbox, and never store the PostgreSQL administrator password in `backend/.env`.
- Major PostgreSQL upgrades require an explicit backup/restore or `pg_upgrade` procedure; replacing the Windows service or changing a container image major is not an ordinary restart.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/ARCHITECTURE]]
- [[inception/DATA_MODEL]]
- [[inception/DECISION_LOG]]
- [[guides/Vue Frontend Walkthrough]]
