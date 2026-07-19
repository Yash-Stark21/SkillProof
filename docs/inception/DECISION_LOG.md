---
title: "SkillProof Phase 1 Decision Log"
aliases:
  - "Decision Log"
  - "Phase 1 Decisions"
type: decision-log
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-19
tags:
  - skillproof
  - inception
  - governance
  - decisions
---

# SkillProof Phase 1 Decision Log

| Field | Value |
| --- | --- |
| Baseline status | Approved for Sprint 1 entry; frontend and PostgreSQL implementation foundations recorded |
| Decision date | 2026-07-15; latest amendment 2026-07-19 |
| Decision owner | Solo developer acting as product owner and technical lead |
| Change policy | Preserve an existing ID; record a dated superseding decision and, for architecture changes, an accepted superseding ADR |

These decisions turn the Phase 1 plan into implementation constraints. `D-*` entries govern product and delivery choices; linked ADRs contain the full architectural context, alternatives, consequences, and validation.

## Approved decision register

| ID | Decision | Rationale and consequence | Authoritative detail |
| --- | --- | --- | --- |
| `D-001` | **Adopt “No evidence, no claim” as the governing invariant.** A supported skill and every valid career claim require at least one valid high- or medium-confidence evidence item. | Trustworthy provenance is the product, not an optional explanation. README-only/low-confidence evidence can be shown but cannot support a skill, score, or claim. | [Product charter](PRODUCT_CHARTER.md), [evidence contract `0.1`](EVIDENCE_CONTRACT.md) |
| `D-002` | **Use an Agile iterative-incremental SDLC with lightweight Scrum/Scrumban, shift-left testing, risk spikes, and vertical increments.** | Detector accuracy, GitHub behavior, and scoring need evidence-driven refinement; each sprint must end in a testable demonstration rather than isolated technical layers. | `SkillProof1.md`, [backlog](BACKLOG.md) |
| `D-003` | **Treat SkillProof as a greenfield product delivered by one developer wearing all product, architecture, engineering, QA, security, and DevOps roles.** | There is no legacy runtime, data, or compatibility contract to preserve. Operational complexity must remain manageable by one owner, while all database changes still use versioned migrations from the first schema. | [Product charter](PRODUCT_CHARTER.md), [architecture](ARCHITECTURE.md) |
| `D-004` | **Serve a junior developer/job applicant first and a recruiter, mentor, or interviewer second through one public-repository workflow.** | The MVP optimizes repository submission → evidence inspection → corrected job comparison → supported career output. Secondary reviewers inspect proof; accounts and collaboration are not required. | [Product charter](PRODUCT_CHARTER.md) |
| `D-005` | **Build one modular monolith with a separate FastAPI/Pydantic JSON API and React/TypeScript/Vite SPA in one repository.** PostgreSQL is the system of record; HTTPX is the async GitHub client; SQLAlchemy async sessions and Alembic provide persistence; Docker Compose and CI support delivery. | Historical Phase 1 choice. The separate SPA/API boundary remains, while `D-019` supersedes the client framework and language. | [Superseded ADR-001](../adr/ADR-001-fastapi-react-separation.md), [architecture](ARCHITECTURE.md) |
| `D-006` | **Implement deterministic, versioned rule-based detectors before any AI capability.** | Structural manifests and source patterns are explainable and regression-testable. LLMs, embeddings, and RAG cannot create, upgrade, or detach claims from evidence in v1. | [ADR-002](../adr/ADR-002-rule-based-detection-before-ai.md) |
| `D-007` | **Pin every scan to one immutable full commit SHA and retrieve all tree/blob content at that SHA.** | Branches move and cannot be a reproducible provenance root. Reports reference completed scans; a later branch state requires a new scan. | [ADR-003](../adr/ADR-003-commit-pinned-evidence.md) |
| `D-008` | **Freeze evidence contract `0.1`.** Evidence includes canonical skill, detector rule/version, repository and commit, path/hash/lines, redacted excerpt, kind, confidence, coverage, and timestamp. | High/medium evidence qualifies; README-only evidence is low. Redaction uses deterministic typed placeholders such as `[REDACTED:GITHUB_TOKEN]` and occurs before persistence, logs, API, or UI. | [Evidence contract](EVIDENCE_CONTRACT.md), `BR-01`, `NFR-03` in [requirements](REQUIREMENTS.md) |
| `D-009` | **Limit the first detector release to Python, FastAPI, Pytest, TypeScript, React, Vite, and Vitest.** | These two complementary stack families are sufficient to prove the detector/evidence model within solo capacity. No other skill may be reported as supported by a v1 detector. | [Product charter](PRODUCT_CHARTER.md), `FR-03` in [requirements](REQUIREMENTS.md) |
| `D-010` | **Keep Job Fit and Portfolio Quality separate and versioned, with no combined overall score.** Job Fit v0.1 uses the locked formula below. | Job relevance and repository polish answer different questions. Each awarded Job Fit point requires qualifying evidence; Portfolio Quality cannot depend on a job description. | [ADR-004](../adr/ADR-004-separate-product-scores.md), `FR-07` in [requirements](REQUIREMENTS.md) |
| `D-011` | **Run bounded v1 scans as FastAPI in-process background tasks after persisting a queued scan and returning `202 Accepted`.** | This avoids a broker/worker before measured need. Tasks use their own database session; stale queued/running work becomes `failed/SCAN_INTERRUPTED`; retries are new user-initiated attempts. | [ADR-005](../adr/ADR-005-in-process-v1-scanning.md), [`SPK-03`](FEASIBILITY_REPORT.md) |
| `D-012` | **Defer authentication, private repositories, durable workers, Redis/Celery, microservices, AI/RAG, multi-repository portfolios, recruiter sharing, document export, and additional detector packs.** | None is required to validate evidence integrity, and each expands security or operations beyond the solo MVP. Reintroduction requires a new requirement, risk assessment, estimate, and accepted decision/ADR. | [ADR-006](../adr/ADR-006-defer-auth-workers-microservices.md), [product charter](PRODUCT_CHARTER.md) |
| `D-013` | **Treat submitted repositories as untrusted read-only data.** Never clone, check out, build, import, evaluate, or execute them; use only approved HTTPS GitHub hosts and reject redirects to other hosts. | This limits the attack surface and makes deterministic bounded inspection possible. Hitting a safety or eligibility boundary is explicit, never silently ignored. | `NFR-01` in [requirements](REQUIREMENTS.md), [architecture](ARCHITECTURE.md) |
| `D-014` | **Adopt the versioned default scan bounds recorded below.** Any reached limit produces partial coverage with a stable reason; behavior changes require a scan-policy version change. | Public GitHub capacity and untrusted repository size are finite. Conservative defaults favor honest partial results over unbounded work. | `NFR-02` in [requirements](REQUIREMENTS.md), [`SPK-01`/`SPK-02`](FEASIBILITY_REPORT.md) |
| `D-015` | **Use the versioned `/api/v1` boundary and one flat safe error envelope.** Stable error codes, not message strings, drive client behavior. | A consistent machine-readable contract supports the separate SPA, hides stack traces/secrets, and correlates sanitized logs. | [API contract](API_CONTRACT.md), `NFR-05` in [requirements](REQUIREMENTS.md) |
| `D-016` | **Use PostgreSQL with SQLAlchemy 2.x asynchronous sessions and Alembic migrations.** Pin development and CI to PostgreSQL 18; deliver the schema through vertical-slice migrations, beginning with the four-table `0001_evidence_ledger` revision. One mutable `AsyncSession` belongs to one request/task and is never shared across concurrent work; network retrieval occurs outside database write transactions. | This preserves transaction ownership, avoids dialect drift and unsafe concurrent session use, and proves repository-to-evidence persistence without deploying unused job/report/claim tables. A fresh database must migrate through `head` in CI; production startup does not create schema ad hoc. | [Architecture](ARCHITECTURE.md), [data model](DATA_MODEL.md), [[guides/PostgreSQL Implementation Walkthrough|PostgreSQL walkthrough]], `NFR-06` in [requirements](REQUIREMENTS.md) |
| `D-017` | **Require human confirmation of parsed job skills and make matching explainable.** The user may add, remove, or reclassify skills; a report binds to that immutable confirmed revision. | Rule-based parsing can be wrong. Exact/approved-equivalent matches with qualifying evidence count; related is explanatory only; partial coverage uses `unverified` instead of asserting `missing`. | `FR-05` through `FR-07` in [requirements](REQUIREMENTS.md) |
| `D-018` | **Apply the locked Definition of Ready below to every sprint story and deliver Sprint 1 as a repository-to-evidence vertical slice.** | A story cannot enter implementation while outcomes, contracts, risks, tests, dependencies, or demonstrations remain undecided. Infrastructure work is integrated into the demonstrable slice. | [Backlog and Sprint 1 plan](BACKLOG.md) |
| `D-019` | **Implement SkillProof's own SPA with Vue 3, plain JavaScript, and Vite.** Keep FastAPI authoritative and keep the versioned `/api/v1` boundary; exclude TypeScript and React from the product client toolchain. | This supersedes only the client-technology portion of `D-005` before UI implementation. Runtime API fixtures, component tests, linting, and end-to-end coverage replace frontend compile-time type checks. React and TypeScript remain detector targets under `D-009`. | [ADR-007](../adr/ADR-007-adopt-vue-javascript-client.md), [architecture](ARCHITECTURE.md), [backlog](BACKLOG.md) |

## Locked decision details

### `D-010` — Job Fit formula

Let required coverage and preferred coverage be the proportion of confirmed skills in that class that have an `exact` or approved `equivalent` match backed by high- or medium-confidence evidence.

```text
If required and preferred skills exist:
  Job Fit = 80% × required coverage + 20% × preferred coverage

If only one class exists:
  Job Fit = 100% × coverage of that class

If neither class exists:
  report creation is rejected
```

`related`, `missing`, `unverified`, and low-confidence evidence contribute zero. Scores and component explanations are deterministic for the recorded scoring version. Portfolio Quality is a separate evidence-backed contract; its dimensions and weights must be frozen before its implementation story becomes Ready and cannot alter Job Fit.

### `D-014` — Default scan-limit policy

| Limit | Default |
| --- | ---: |
| GitHub requests per scan | 50 |
| Tree entries evaluated | 10,000 |
| File blobs fetched | 40 |
| Individual file size | 256 KiB |
| Aggregate downloaded file content | 5 MiB |
| Concurrent GitHub requests per scan | 5 |
| Timeout per outbound request | 10 seconds |

Reaching a limit stops the governed work, records the observed condition and a stable partial-coverage reason, and prevents an absence assertion for uninspected content. The limit values are configuration, but changing a default changes the scan-policy version and golden expectations.

### `D-015` — Error envelope

Every non-2xx API response uses exactly this top-level shape:

```json
{
  "code": "STABLE_MACHINE_CODE",
  "message": "Safe user-facing message",
  "details": {},
  "request_id": "correlation-id"
}
```

`details` is optional; `code`, `message`, and `request_id` are required. Validation details identify fields without echoing secret-like content. The same request ID appears in sanitized structured logs. The [API contract](API_CONTRACT.md) is authoritative for endpoint schemas and status/code mappings.

### `D-018` — Definition of Ready

A story may enter a sprint only when all of these are true:

- The user/business outcome and priority are stated.
- Mapped `BR-*`, `FR-*`, and applicable `NFR-*` IDs are listed.
- Acceptance criteria are observable and written as Given/When/Then.
- API, data, evidence, UI, security, and migration impacts are identified or explicitly `none`.
- Golden fixtures, planned automated test levels, and failure cases are named.
- Dependencies are complete or committed earlier in the same sprint with an explicit order.
- The story is no larger than two ideal solo-developer days; otherwise it is split.
- The demonstration result is stated.
- No product or architecture decision remains unresolved.
- Any linked High or Critical risk has a preventive control plus an automated test or a named time-boxed spike.

Sprint 1 is the end-to-end public repository → commit-pinned inventory → deterministic evidence → evidence API → basic Vue evidence view. All Sprint 1 stories in the approved backlog are Ready; the frontend stack amendment is governed by `D-019` and ADR-007.

## Supersession and review

- Product-scope, evidence-validity, score, safety, or API-envelope changes require a new `D-*` entry that names the superseded decision.
- Architecture changes also require a new or superseding ADR with alternatives, consequences, migration/compatibility impact, and validation.
- Decision review occurs at sprint review and whenever a risk trigger, feasibility-spike failure, or deferred-feature proposal changes an assumption.
- Historical scans and reports retain the decision-bearing detector, policy, matcher, scoring, and evidence-contract versions under which they were created.

## Related notes

- [[Home]]
- [[MOCs/Delivery MOC]]
- [[guides/PostgreSQL Implementation Walkthrough]]
- [[inception/ARCHITECTURE]]
- [[inception/PHASE_1_EXIT_REPORT]]
