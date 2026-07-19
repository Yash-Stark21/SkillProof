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

Local development uses PostgreSQL 18 through [`compose.yaml`](compose.yaml). Start the persistent development database from the repository root:

```powershell
docker compose up -d postgres
Set-Location backend
$env:DATABASE_URL = "postgresql+psycopg://skillproof:skillproof@localhost:5432/skillproof"
python -m alembic upgrade head
```

The isolated test database is available as the `postgres-test` Compose profile on port `5433`. The [PostgreSQL walkthrough](docs/guides/PostgreSQL%20Implementation%20Walkthrough.md) contains the full setup, migration, testing, reset, and transaction-boundary guidance.

## Validate the documentation baseline

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

This command verifies the evidence corpus, documentation contracts, links, metadata, and decision consistency.
