---
title: SkillProof Engineering MOC
aliases:
  - Engineering MOC
type: moc
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-22
tags:
  - skillproof
  - engineering
  - moc
---

# SkillProof Engineering MOC

Use this map when designing or reviewing implementation behavior.

## System design

- [[guides/PostgreSQL Implementation Walkthrough|PostgreSQL Implementation Walkthrough]] — native PostgreSQL 18 setup, migrations, tests, optional Compose fallback, and operational boundaries
- [[inception/ARCHITECTURE|Architecture]] — boundaries, flows, security, runtime, and observability
- [[inception/API_CONTRACT|API Contract]] — requests, responses, errors, states, and compatibility
- [[inception/DATA_MODEL|Data Model]] — entities, constraints, transactions, and provenance
- [[adr/README|ADR Index]] — accepted tradeoffs and their consequences

## Evidence engine

- [[inception/EVIDENCE_CONTRACT|Evidence Contract 0.1]]
- [[inception/REQUIREMENTS#FR-03 — Extract and inspect skill evidence|Evidence Requirements]]
- [[inception/TRACEABILITY_MATRIX#5. Phase 1 test catalog|Evidence Test Catalog]]
- [[inception/FEASIBILITY_REPORT#4. Bounded Sprint 1 spikes|Technical Spikes]]

## Engineering gates

- [[guides/PostgreSQL Implementation Walkthrough#7. Operational checks|PostgreSQL Operational Checks]]
- [[guides/Vue Frontend Walkthrough|Vue Frontend Implementation Walkthrough]]
- [[adr/ADR-007-adopt-vue-javascript-client|Vue and JavaScript Client Decision]]
- [[inception/BACKLOG#3. Definition of Done|Definition of Done]]
- [[inception/BACKLOG|Sprint 1 Engineering Slice]]
- [[inception/RISK_REGISTER|Security and Reliability Risks]]

## Local validation

The default local database is the installed Windows PostgreSQL 18 service `postgresql-x64-18`, using tools from `C:\Program Files\PostgreSQL\18\bin` or `PATH` on `localhost:5432`. From the project root, `backend/scripts/setup_local_postgres.ps1` securely prompts for the PostgreSQL administrator password, creates the `skillproof` and `skillproof_test` databases with application-owned `public` schemas, writes the ignored `backend/.env` only when absent, and migrates development to `0001_evidence_ledger (head)`:

```powershell
powershell -ExecutionPolicy Bypass -File .\backend\scripts\setup_local_postgres.ps1
```

Run the documentation contract from the project root:

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

For backend checks, use the repository-local virtual environment and target the native test database explicitly:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:TEST_DATABASE_URL = "postgresql+psycopg://skillproof_test:skillproof_test@localhost:5432/skillproof_test"
.\.venv\Scripts\python.exe -m pytest
Remove-Item Env:TEST_DATABASE_URL
```

`compose.yaml` remains an optional fallback; its `postgres` service cannot bind port `5432` while the native Windows service is using it, and its disposable `postgres-test` profile uses port `5433`. Full verification and destructive-reset cautions are documented in [[guides/PostgreSQL Implementation Walkthrough#7. Operational checks|the PostgreSQL walkthrough]]. The contract test source is outside this vault under `tests/contract`; the traceability matrix is the vault-facing index for those checks.

## Related notes

- [[Home]]
- [[MOCs/Project MOC]]
- [[MOCs/Product MOC]]
- [[MOCs/Delivery MOC]]
