# SkillProof

SkillProof is a greenfield Python/FastAPI API with a Vue 3 and plain-JavaScript client for turning public repository implementation evidence into defensible skill matches and evidence-backed career claims.

> No evidence, no claim.

## Documentation

The project documentation is an Obsidian-compatible vault rooted at [`docs/`](docs/README.md).

- Open the `docs` directory as a vault in Obsidian.
- Start at [`Home.md`](docs/Home.md).
- Read the [`Obsidian guide`](docs/OBSIDIAN_GUIDE.md) for conventions and workflows.
- Review the [`Phase 1 exit report`](docs/inception/PHASE_1_EXIT_REPORT.md) and [`Sprint 1 backlog`](docs/inception/BACKLOG.md).
- Read [`ADR-007`](docs/adr/ADR-007-adopt-vue-javascript-client.md) for the Vue/JavaScript frontend decision.
- Follow the [`PostgreSQL implementation walkthrough`](docs/guides/PostgreSQL%20Implementation%20Walkthrough.md) to start the database, apply migrations, and run integration tests.
- Follow the [`GitHub repository setup guide`](docs/guides/GitHub%20Repository%20Setup.md) to publish and govern the project.

The vault remains ordinary UTF-8 Markdown and works without community plugins.

## Current status

Phase 1 inception is complete with a controlled **GO to Sprint 1**. The Sprint 1 Vue client is implemented against the versioned `/api/v1` contract, and the backend now has a PostgreSQL-backed repository-to-evidence foundation with migration-managed persistence.

## Frontend

The browser client lives in [`frontend/`](frontend/README.md) and uses Vue single-file components with plain JavaScript only.

```powershell
cd frontend
npm install
npm run dev
```

Use `npm run lint`, `npm run test`, and `npm run build` for the frontend quality gates. The client calls `/api/v1` by default and includes an explicitly labeled sample result so its evidence workflow can be reviewed before the API is available.

## PostgreSQL

The primary local database is the installed Windows PostgreSQL 18 instance. It runs as service `postgresql-x64-18`, uses the tools in `C:\Program Files\PostgreSQL\18\bin` (or the same tools on `PATH`), and listens on `localhost:5432`.

Prepare the existing backend virtual environment, then run the idempotent setup from the repository root:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location ..
powershell -ExecutionPolicy Bypass -File .\backend\scripts\setup_local_postgres.ps1
```

`backend/scripts/setup_local_postgres.ps1` securely prompts for the PostgreSQL administrator password; do not place that password in a command, environment file, or repository. It provisions the `skillproof` development database and `skillproof_test` integration-test database on port `5432`, assigns each application role ownership of its `public` schema, creates the ignored `backend/.env` when absent, and advances the development schema to Alembic head `0001_evidence_ledger`.

[`compose.yaml`](compose.yaml) remains an optional fallback for machines without the native service. Do not start its `postgres` service on port `5432` while `postgresql-x64-18` is running. The [PostgreSQL walkthrough](docs/guides/PostgreSQL%20Implementation%20Walkthrough.md) contains verification, migrations, integration testing, the optional Compose path, and reset cautions.

## Validate the documentation baseline

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

This command verifies the evidence corpus, documentation contracts, links, metadata, and decision consistency.
