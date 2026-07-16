---
title: "SkillProof Product Backlog and Sprint 1 Plan"
aliases:
  - "Product Backlog"
  - "Sprint 1 Plan"
type: backlog
status: ready
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-16
tags:
  - skillproof
  - inception
  - planning
  - sprint-1
---

# SkillProof Product Backlog and Sprint 1 Plan

**Status:** Accepted for implementation  
**Backlog baseline:** `0.2`<br>
**Delivery model:** Solo developer, Agile iterative-incremental  
**Initial sprint length:** 10 working days

## 1. Prioritization model

Priority follows business risk and dependency:

1. Evidence integrity and provenance.
2. Safe repository ingestion.
3. Initial Python/FastAPI/Pytest and React/TypeScript/Vite/Vitest detection.
4. Job-description correction.
5. Explainable matching and separate scores.
6. Evidence-backed claims.
7. Production hardening and release presentation.

`P0` is required for the MVP release; `P1` improves the MVP after the core evidence journey works; `Deferred` requires a new scope decision. Story estimates are ideal solo-developer days, not elapsed promises. Sprint 1 reserves two of ten days for review, integration, defects, and unexpected GitHub behavior; planned story work totals eight ideal days.

## 2. Definition of Ready

A story may enter a sprint only when all of these are true:

- The user/business outcome and priority are stated.
- Mapped `BR-*`, `FR-*`, and applicable `NFR-*` IDs are listed.
- Acceptance criteria are observable and written as Given/When/Then.
- API, data, evidence, UI, security, and migration impacts are identified or explicitly `none`.
- Golden fixture(s), planned automated test levels, and failure cases are named.
- Dependencies are completed or committed earlier in the same sprint with an explicit order.
- The story is no larger than two ideal days; otherwise it is split.
- The demonstration result is stated.
- There is no unresolved product or architecture decision.

Every Sprint 1 story below satisfies this checklist and is marked **Ready**.

## 3. Definition of Done

A story is done only when:

- all acceptance criteria and mapped critical-rule tests pass;
- backend linting/type checks and frontend linting/runtime-contract checks pass where affected;
- unit tests cover domain behavior and integration/contract tests cover database or GitHub boundaries;
- the golden evidence suite has no unexpected or forbidden evidence;
- OpenAPI and documentation reflect public behavior;
- an Alembic migration exists and upgrades an empty PostgreSQL database when the schema changes;
- errors and structured logs expose safe codes/request IDs without tokens, secrets, raw source, or stack traces;
- the change is reviewed, merged, deployable to staging, and included in the sprint demonstration; and
- no unsupported match or claim can be produced.

## 4. Epic backlog

| Epic | Priority | Outcome | Requirements | Release gate |
| --- | --- | --- | --- | --- |
| `EP-01 Repository-to-evidence` | P0 | A public repository produces safe, commit-pinned, inspectable evidence | BR-01, BR-03, BR-04; FR-01..04; NFR-01..03, NFR-05..07 | Sprint 1 end-to-end demonstration and golden FastAPI pass |
| `EP-02 Initial detector coverage` | P0 | All seven initial skills have deterministic expected/forbidden fixture coverage | BR-01; FR-03..04; NFR-03..04, NFR-07 | Python/FastAPI/Pytest and React/TypeScript/Vite/Vitest fixtures pass |
| `EP-03 Job requirement correction` | P0 | A user can inspect and correct required/preferred parsed skills | FR-05; NFR-04..05, NFR-07 | Corrected revision is explicit and report-ready |
| `EP-04 Explainable matching and scoring` | P0 | Confirmed job skills map transparently to evidence and two independent scores | BR-01, BR-05; FR-06..07; NFR-04, NFR-07 | Every awarded point is explained; independence tests pass |
| `EP-05 Supported career outputs` | P0 | Resume/interview claims exist only with qualifying evidence | BR-02; FR-08; NFR-03..04, NFR-07 | Claim-without-evidence and invalidation tests pass |
| `EP-06 Hardening and release` | P0 | The MVP is bounded, observable, migration-managed, and deployable | BR-04; all NFRs | CI, staging smoke, security checks, rollback notes, and demo pass |
| `EP-07 Post-MVP capabilities` | Deferred | Private/user-owned workflows, AI assistance, and scale-out processing | New requirements required | Accepted scope change and superseding ADRs |

## 5. Sprint 1: Repository-to-evidence vertical slice

### Sprint goal

A user submits a public GitHub URL and receives a pollable scan that is pinned to one commit, safely inspects bounded content, detects Python/FastAPI/Pytest evidence, and displays exact evidence in the Vue UI with honest complete/partial coverage.

The deterministic demonstration uses the `positive_fastapi` golden fixture through the same GitHub gateway interface and application/API/UI path. GitHub gateway contract tests use recorded synthetic HTTP responses; an optional live public-repository smoke validates environment connectivity but is not a CI or acceptance dependency.

### Sequencing

```text
US-01
  -> US-02
      -> US-03 -> US-04 -> US-05
      -> US-06 -----^       |
US-07 spans and gates all ---+
```

Only the minimum migration, runtime, and UI shell needed for this vertical outcome is built. Job parsing, matching, scores, and claim generation remain later increments.

### US-01 — Accept and persist a public repository scan

- **Status / estimate / priority:** Ready / 1.0 ideal day / P0
- **User story:** As a junior developer, I want to submit a public GitHub repository and receive a stable scan ID so I can follow its analysis.
- **Business value:** Establishes the entry point and persisted workflow root for all evidence.
- **Mapped requirements:** BR-03; FR-01, FR-02; NFR-05, NFR-06, NFR-07.
- **Dependencies:** Accepted API contract, data model, ADR-003, ADR-005, and ADR-007; no prior story.
- **Implementation notes:** Create only the walking FastAPI/Vue/PostgreSQL structure needed for `POST /scans`, `GET /scans/{id}`, standard errors/request IDs, and the first Alembic migration. Normalize URLs before repository upsert. Commit the queued scan before scheduling its task.
- **Interface/data impact:** Scan create/read endpoints; `repositories` and `scans`; Vue submission form may initially show the returned ID/status.
- **Security impact:** Reject credentials, query/fragment, arbitrary hosts, IPs, and GitHub subpaths. Do not fetch during synchronous validation.

Acceptance criteria:

1. Given a canonical or normalizable public `github.com/{owner}/{repo}` URL, when it is submitted, then the API returns `202`, `Location`, request ID, and a persisted queued scan.
2. Given that scan ID, when status is read, then the same repository identity, versions, status, and nullable commit/coverage fields follow the API contract.
3. Given an unsupported or malformed URL, when submitted, then the API returns the stable safe error envelope and creates no repository or scan row.
4. Given an unknown scan ID, when read, then the API returns `404 RESOURCE_NOT_FOUND`.

Planned tests:

- URL-normalization unit table including casing, trailing slash, `.git`, credentials, subpaths, fragments, and non-GitHub hosts.
- API contract tests for `202`, `Location`, request ID, invalid `422`, and missing `404`.
- PostgreSQL integration test for canonical repository upsert and queued scan persistence.
- Alembic test upgrading an empty database to head.

Demonstration: submit the golden repository URL representation and open its queued scan status from the UI/API.

### US-02 — Resolve and inventory one immutable GitHub snapshot

- **Status / estimate / priority:** Ready / 1.75 ideal days / P0
- **User story:** As a user, I want analysis tied to one immutable commit so the result remains reproducible after a branch changes.
- **Business value:** Establishes defensible provenance rather than mutable branch claims.
- **Mapped requirements:** BR-03, BR-04; FR-02, FR-04; NFR-01, NFR-02, NFR-05, NFR-07.
- **Dependencies:** US-01; ADR-003 and ADR-005.
- **Implementation notes:** Build the async HTTPX GitHub gateway for approved repository, commit, tree, and blob endpoints. Resolve the default branch SHA once and use it for every later request. Enumerate eligible files without cloning or executing. Run through an in-process task with its own `AsyncSession` and bounded HTTP concurrency.
- **Interface/data impact:** Scan state/phase/failure fields and `repo_files`; no new public route.
- **Security impact:** Enforce API-host and endpoint allowlists, timeouts, redirect policy, safe upstream error translation, and token-free logs.

Acceptance criteria:

1. Given a resolvable public repository, when the task starts, then it records the full commit SHA before fetching the tree or blobs and completes against that SHA only.
2. Given a branch that changes after commit resolution, when remaining calls run, then they still target the originally stored commit.
3. Given an eligible tree, when inventory completes, then each path is normalized, classified, and stored once without raw file content.
4. Given GitHub `404`, rate limit, timeout, malformed tree, or unavailable response before a useful result, when handled, then the scan becomes failed with the documented safe code.
5. Given a process-interrupted stale task, when startup reconciliation runs, then it becomes failed with `SCAN_INTERRUPTED` rather than remaining running forever.

Planned tests:

- HTTPX/respx contract tests for repository/default-branch/commit/tree/blob requests and GitHub error translation.
- Branch-movement integration test asserting all tree/blob request refs equal the stored SHA.
- Unit tests for path normalization/file classification and prohibited endpoint/redirect rejection.
- PostgreSQL state-transition and distinct-request/task-session integration tests.
- Startup reconciliation test.

Demonstration: show a completed inventory and exact commit SHA while the mocked default branch advances independently.

### US-03 — Detect qualifying Python, FastAPI, and Pytest evidence

- **Status / estimate / priority:** Ready / 1.25 ideal days / P0
- **User story:** As a developer, I want implementation signals to prove my initial backend skills without documentation-only false positives.
- **Business value:** Validates the core product assumption on the first detector family.
- **Mapped requirements:** BR-01; FR-03; NFR-03, NFR-04, NFR-07.
- **Dependencies:** US-02; ADR-002; evidence contract `0.1`; `positive_fastapi` and `negative_readme_only` golden manifests.
- **Implementation notes:** Implement versioned detector rules `0.1.0` for structural manifest/import/route/test signals. Rules emit candidates only; the evidence service performs contract validation. Output ordering is canonical and timestamps/IDs are excluded from deterministic comparison.
- **Interface/data impact:** No new route or table beyond US-04; defines initial rule/evidence-kind vocabulary.
- **Security impact:** Detectors operate only on bounded normalized text after redaction; no imports, builds, package installation, or code execution.

Acceptance criteria:

1. Given `positive_fastapi`, when detector `0.1.0` runs, then all expected Python/FastAPI/Pytest items appear at exact paths and line ranges and no forbidden item appears.
2. Given `negative_readme_only`, when it runs, then documentation mentions are low confidence, `claim_eligible=false`, and no implementation proof is awarded.
3. Given identical normalized files and versions, when detection runs twice, then semantic ordered evidence is identical.
4. Given a malformed or unsupported file, when a rule cannot parse it, then the file produces a safe diagnostic/skip without failing unrelated detectors or inventing evidence.

Planned tests:

- Golden expected/forbidden regression tests for `positive_fastapi` and `negative_readme_only`.
- Unit tests per rule for boundary line numbers, confidence, kind, and stable rule ID.
- Determinism/property test with shuffled input file order.
- Tests proving detectors never receive or invoke executable repository modules.

Demonstration: compare implementation evidence with a README-only mention and explain why only the former qualifies.

### US-04 — Persist and inspect evidence contract 0.1

- **Status / estimate / priority:** Ready / 1.0 ideal day / P0
- **User story:** As a user or reviewer, I want every detected skill to reveal exact repository evidence so I can verify it myself.
- **Business value:** Delivers the evidence ledger and establishes the proof half of “no evidence, no claim.”
- **Mapped requirements:** BR-01, BR-03; FR-03, FR-04; NFR-03, NFR-05, NFR-06, NFR-07.
- **Dependencies:** US-02, US-03; accepted data model and API/evidence contracts.
- **Implementation notes:** Persist inspected file hashes and validated evidence in one controlled unit of work, complete scan state last, and serve stable cursor-ordered evidence with filters. Derive self-contained repository, commit, coverage, and claim-eligibility fields without inconsistent duplicate storage.
- **Interface/data impact:** `repo_files`, `evidence_items`; `GET /scans/{id}/evidence` and documented filters.
- **Security impact:** Persist only metadata plus bounded redacted excerpts; render excerpts as plain text.

Acceptance criteria:

1. Given a completed scan, when evidence is requested, then every item contains every contract `0.1` field with exact repository, commit, path, SHA-256 hash, lines, kind, confidence, coverage, and eligibility.
2. Given more than one page, when cursors are followed, then each item appears exactly once in canonical order.
3. Given skill/confidence/eligibility filters, when applied, then only matching items are returned without changing ordering.
4. Given queued, running, failed, empty-completed, and unknown scans, when evidence is requested, then each returns its documented response/error behavior.
5. Given persistence failure before terminal commit, when the transaction rolls back, then no completed scan exposes a partial evidence ledger.

Planned tests:

- Evidence schema/contract serialization tests against the golden manifest.
- PostgreSQL integration tests for uniqueness, hash/version consistency, transaction rollback, and delete restrictions.
- API pagination/filter/state contract tests.
- Redacted-excerpt XSS-safe frontend rendering test shared with US-05.

Demonstration: open a FastAPI skill and trace rule → excerpt/lines → file hash → commit.

### US-05 — Complete the basic Vue evidence journey

- **Status / estimate / priority:** Ready / 0.75 ideal day / P0
- **User story:** As a junior developer, I want to submit, follow, and inspect a repository scan in one understandable screen.
- **Business value:** Converts backend capability into the first demonstrable vertical product increment.
- **Mapped requirements:** BR-01, BR-03, BR-04; FR-01..04; NFR-05, NFR-07.
- **Dependencies:** US-01 and API shapes fixed; integrates completed US-02 through US-04 behavior.
- **Implementation notes:** Build the minimal Vite/Vue/JavaScript page with URL form, status polling using `Retry-After`, safe failure state, coverage banner, and evidence list/detail. Validate representative API fixtures at runtime. Do not calculate eligibility in the browser.
- **Interface/data impact:** No API/data change; UI route `/` is sufficient for Sprint 1.
- **Security impact:** No GitHub token in client state; source excerpts render as text, not HTML; safe API messages only.

Acceptance criteria:

1. Given a valid URL, when submitted, then the UI shows queued/running progress and automatically reaches terminal status without duplicate submissions.
2. Given a completed scan, when evidence loads, then skill, confidence, claim eligibility, commit, path, lines, excerpt, and coverage are visible.
3. Given partial coverage, when results render, then an unmistakable warning and reasons appear and the UI does not label unobserved skills missing.
4. Given validation, scan, network, or readiness failure, when encountered, then the user sees a safe actionable state with request ID where present.
5. Given keyboard-only navigation and narrow viewport, when using the form and evidence list, then controls, focus, labels, and content remain usable.

Planned tests:

- Vitest/Vue Test Utils tests for form, polling, terminal states, partial banner, failure/request ID, and plain-text excerpt.
- Runtime contract tests against representative API fixtures and unknown enum values.
- One Playwright path using the deterministic GitHub gateway: submit → poll → inspect evidence.
- Basic accessibility assertions for form labels, status announcements, focus, and evidence disclosure.

Demonstration: complete the repository-to-evidence flow without using API documentation or database tools.

### US-06 — Enforce scan limits, partial coverage, and secret redaction

- **Status / estimate / priority:** Ready / 1.25 ideal days / P0
- **User story:** As a user, I want large or sensitive repositories analyzed safely and limitations stated honestly.
- **Business value:** Prevents resource abuse, secret disclosure, and false claims of absence.
- **Mapped requirements:** BR-04; FR-02, FR-04; NFR-01, NFR-02, NFR-03, NFR-05, NFR-07.
- **Dependencies:** US-02; integrates with US-04 and US-05. `partial_scan` and `secret_redaction` golden manifests are frozen.
- **Implementation notes:** Centralize a versioned scan policy containing request, tree-entry, file-count, eligible file-size, total-byte, timeout, and concurrency bounds. Redact before excerpt persistence/logging. Policy exclusions are distinct from coverage-limiting skips.
- **Interface/data impact:** Coverage statistics/reasons and scan-policy version already defined; no new route.
- **Security impact:** This story is the primary resource-exhaustion and data-exposure control for scanning.

Acceptance criteria:

1. Given `partial_scan`, when an eligible resource limit is reached, then the scan completes deterministically with `coverage=partial`, the exact reason, and inspected/skipped counters.
2. Given a partial scan and no evidence for a requested skill, when interpreted by UI/API consumers, then absence is not asserted.
3. Given `secret_redaction`, when a detector excerpt or log context contains a secret-like value, then the stored/returned/logged value is replaced while non-secret structural evidence remains useful.
4. Given binary, dependency, generated, or minified files, when skipped by policy, then they are not fetched/detected and do not alone mark coverage partial.
5. Given concurrency and request bounds, when a large synthetic tree is processed, then observed in-flight requests and totals never exceed configured limits.

Planned tests:

- Golden expected/forbidden tests for `partial_scan` and `secret_redaction`.
- Unit tables for eligibility, file-size/byte/count accounting, reason selection, and redaction patterns.
- Async integration test measuring maximum concurrent mocked HTTP calls and timeout behavior.
- Log-capture/API/database assertions that seeded secret values never appear.
- UI test for partial coverage semantics.

Demonstration: scan the partial and secret fixtures, inspect explicit reasons, and search outputs/log capture for the seeded secret.

### US-07 — Gate the vertical slice in CI and migrations

- **Status / estimate / priority:** Ready / 1.0 ideal day / P0
- **User story:** As the solo product team, I want every evidence change automatically verified so regressions cannot silently create unsupported proof.
- **Business value:** Makes the first slice repeatable, reviewable, and safe to extend.
- **Mapped requirements:** BR-01..04; FR-01..04; NFR-03..07.
- **Dependencies:** Starts with US-01 and evolves alongside every Sprint 1 story; final acceptance depends on US-02 through US-06.
- **Implementation notes:** Configure backend lint/types/tests, PostgreSQL integration tests, migration upgrade validation, frontend lint/runtime-contract/tests/build, golden suite, and one deterministic Playwright flow. Live GitHub calls are excluded from required CI.
- **Interface/data impact:** None beyond contract snapshot and migration history.
- **Security impact:** CI secret scanning/dependency checks may be advisory in Sprint 1 but redaction and seeded-secret non-disclosure tests are blocking.

Acceptance criteria:

1. Given a clean checkout and documented supported runtimes, when CI runs, then database migration, backend, frontend, contract, and golden jobs complete without manual state.
2. Given any forbidden evidence or changed public schema, when tests run, then the relevant blocking job fails with a useful diagnostic.
3. Given the seeded fixture secret, when the full suite completes, then no captured log, API artifact, snapshot, or test report contains its raw value.
4. Given an empty PostgreSQL database, when Alembic upgrades to head, then model integration tests pass without `create_all`.
5. Given all jobs pass, when the deterministic E2E runs, then it demonstrates submission through evidence inspection.

Planned tests:

- CI workflow self-validation through the actual configured jobs.
- Alembic empty-database upgrade and schema smoke test.
- OpenAPI snapshot/compatibility test and representative frontend runtime-contract checks.
- Golden manifest runner and Playwright path.
- Artifact/log secret scan for the seeded value.

Demonstration: show one green pipeline tied to the same vertical flow demonstrated in the UI.

## 6. Sprint 1 execution and exit gate

Recommended implementation order by working day:

| Day | Planned focus |
| --- | --- |
| 1 | US-01 API/data walking skeleton and first CI checks |
| 2–3 | US-02 GitHub gateway, snapshot resolution, inventory, scan lifecycle |
| 4 | US-03 initial deterministic detector rules |
| 5 | US-04 evidence persistence and API |
| 6 | US-06 scan policy, partial coverage, redaction |
| 7 | US-05 integrated Vue journey |
| 8 | US-07 full CI/migration/E2E gate |
| 9 | Integration fixes, accessibility/security review, documentation |
| 10 | Regression, staging demonstration, sprint review/retrospective |

Sprint 1 exits only when:

- all seven stories meet the Definition of Done;
- the `positive_fastapi`, `negative_readme_only`, `partial_scan`, and `secret_redaction` fixture assertions pass;
- the Vue journey displays exact commit/file/line evidence;
- process interruption and GitHub failure states are explicit;
- complete and partial coverage are visibly different;
- seeded secrets appear nowhere outside the fixture source; and
- no open P0 defect undermines evidence accuracy, provenance, or safety.

## 7. Ready backlog after Sprint 1

These items are ordered but must undergo story-level refinement against the Definition of Ready before sprint commitment.

| Story | Priority | Estimate | Outcome | Dependencies / acceptance focus |
| --- | --- | --- | --- | --- |
| `US-08` React/TypeScript/Vite/Vitest detector pack | P0 | 2.0 d | Expected and forbidden evidence passes `positive_react_typescript` and `negative_typescript_no_react` | EP-01 engine; exact paths/lines, README exclusion, determinism |
| `US-09` Mixed full-stack detector regression | P0 | 1.0 d | Python and frontend packs coexist without duplicates/cross-language false positives | US-08; `mixed_fullstack` fixture |
| `US-10` Parse and correct job requirements | P0 | 2.0 d | Visible required/preferred extraction can be atomically replaced and confirmed | FR-05; parser/taxonomy versions, revision conflict tests |
| `US-11` Explainable skill matcher | P0 | 2.0 d | Each confirmed skill is exact/equivalent/related/missing/unverified with reasoning and evidence | US-10; partial coverage and equivalence contract |
| `US-12` Independent versioned scoring | P0 | 2.0 d | Job Fit and Portfolio Quality are calculated independently with component explanations | US-11; ADR-004 independence and awarded-point tests |
| `US-13` Evidence-backed career outputs | P0 | 2.0 d | Deterministic resume/interview claims are atomically linked to qualifying evidence | US-11; claim-without-evidence rollback/invalidation tests |
| `US-14` Complete report UI | P0 | 2.0 d | User corrects skills and inspects matches, both scores, claims, and provenance | US-10..13; responsive/accessibility/E2E acceptance |
| `US-15` Operational hardening | P0 | 2.0 d | Metrics, safe logs, abuse controls, readiness, Docker Compose, and staging checks are complete | All MVP flows; failure/runbook tests |
| `US-16` Release and interview package | P1 | 2.0 d | Public demo, README, diagrams, ADR index, limitations, scoring examples, and two-minute script are coherent | Staging acceptance and production rollout plan |

## 8. Explicitly deferred backlog

Do not refine or implement these without a new accepted requirement and architecture review:

- user registration, JWT, sessions, GitHub OAuth, and private repositories;
- LLM-generated claims, RAG, embeddings, and vector databases;
- Redis, Celery, durable queues, independently deployed workers, or microservices;
- Java/Spring, Docker/CI detector packs, multi-repository portfolios, share links, and document export.

Measured task interruption, latency, or scale may trigger the durable-worker review in ADR-005; it does not automatically authorize an implementation.

## Related notes

- [[Home]]
- [[MOCs/Delivery MOC]]
- [[inception/REQUIREMENTS]]
- [[inception/PHASE_1_EXIT_REPORT]]
