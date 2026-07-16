---
title: "Vue Frontend Implementation Walkthrough"
aliases:
  - "Frontend Walkthrough"
  - "Vue Walkthrough"
type: guide
status: complete
phase: implementation
owner: solo-developer
created: 2026-07-16
updated: 2026-07-16
tags:
  - skillproof
  - frontend
  - vue
  - javascript
  - walkthrough
---

# Vue Frontend Implementation Walkthrough

**Change date:** 2026-07-16<br>
**Outcome:** SkillProof now has a tested Vue 3 and Vite browser client written entirely in plain JavaScript.

This walkthrough explains what changed, how the live and sample workflows operate, where the implementation lives, and how to verify it.

## 1. What changed today

### Product-client stack

SkillProof's own client changed from the planned React/TypeScript stack to:

- Vue 3 single-file components;
- plain JavaScript only;
- Vite for development and production builds;
- native `fetch` for the `/api/v1` boundary;
- Vitest and Vue Test Utils for component and workflow tests; and
- ESLint with Vue rules for static checks.

The change is recorded as `D-019` in [[inception/DECISION_LOG]] and as [[adr/ADR-007-adopt-vue-javascript-client|ADR-007]]. The original [[adr/ADR-001-fastapi-react-separation|ADR-001]] is retained as superseded history rather than rewritten.

### What did not change

React and TypeScript remain repository-detector targets. The existing golden fixtures verify that SkillProof can recognize React/TypeScript evidence in repositories submitted by users; they do not determine the framework used by SkillProof's own client.

The following boundaries also remain unchanged:

- FastAPI owns validation, scan state, evidence qualification, coverage, matching, and future scores.
- The browser communicates only through the versioned contract in [[inception/API_CONTRACT]].
- Repository content is untrusted, read-only input and is never executed.
- Partial coverage never becomes an assertion that a skill is missing.

## 2. Implementation map

| Path | Responsibility |
| --- | --- |
| `frontend/package.json` | Vue/Vite dependencies and the `dev`, `lint`, `test`, and `build` commands |
| `frontend/package-lock.json` | Reproducible installed dependency graph |
| `frontend/vite.config.js` | Vue plugin, Vitest environment, and local `/api` proxy |
| `frontend/src/main.js` | Mounts the Vue application |
| `frontend/src/App.vue` | Composes the page, workflow states, results, and completion announcement |
| `frontend/src/composables/useRepositoryScan.js` | Owns submission, polling, pagination, selection, cancellation guards, and stage-aware retry |
| `frontend/src/services/scanApi.js` | Sends versioned API requests and normalizes safe errors, request IDs, and `Retry-After` |
| `frontend/src/data/demoScan.js` | Fixed complete and partial sample results for reviewing the UI without a backend |
| `frontend/src/components/RepositoryForm.vue` | Public GitHub URL form and sample-result controls |
| `frontend/src/components/ScanProgress.vue` | Accessible queued/running phase presentation |
| `frontend/src/components/CoverageBanner.vue` | Complete, partial, and unknown coverage semantics |
| `frontend/src/components/EvidenceList.vue` | Evidence selection and honest empty-state language |
| `frontend/src/components/EvidenceDetail.vue` | Exact provenance and text-only redacted excerpt |
| `frontend/src/components/ErrorPanel.vue` | Safe error message, request ID, and retry action |
| `frontend/src/styles.css` | Responsive layout, focus states, contrast, and reduced-motion behavior |
| `frontend/tests/*.spec.js` | Workflow, pagination, retry, partial/unknown coverage, errors, and safe-rendering tests |
| `tests/contract/test_frontend_stack.py` | Repository guard that rejects React, TypeScript, TSX, `tsconfig`, `vue-tsc`, and `v-html` |

No product frontend file uses `.ts`, `.tsx`, `<script lang="ts">`, or TypeScript configuration.

## 3. Walk through the interface

### Step 1 — Open the landing state

The first screen explains the evidence-first promise and presents one labeled input for a public GitHub repository. It also makes three safety properties visible before submission:

1. inspection is read-only;
2. results are pinned to a commit; and
3. repository code is never executed.

### Step 2 — Choose live or sample data

There are two ways to continue:

- **Scan repository** starts the real `/api/v1` workflow.
- **Complete example** or **Partial example** loads fixed in-browser sample data.

Sample results are visibly labeled **Sample data**. They make the completed evidence workspace reviewable while the backend is still being implemented, without pretending that a live repository was scanned.

### Step 3 — Submit a live repository

The live flow sends:

```http
POST /api/v1/scans
Content-Type: application/json

{
  "repository_url": "https://github.com/owner/repository"
}
```

While the request is active, duplicate submission is disabled. The returned scan ID becomes the stable workflow root.

### Step 4 — Follow scan progress

For a queued or running scan, the client reads the response's `Retry-After` header before requesting status again:

```text
queued → resolving repository → inventory → fetch → detect → persist → complete
```

The progress region announces phase changes. Polling stops when the scan is completed, failed, replaced by a sample view, or the Vue scope is disposed.

A transient polling failure does not create a second scan. **Try again** resumes `GET /scans/{id}` for the already accepted attempt. A transient evidence-page failure similarly retries evidence loading for the completed scan.

### Step 5 — Interpret coverage before evidence

Coverage is displayed before the evidence workspace:

- **Complete** means every eligible file within the published scan policy was inspected.
- **Partial** remains usable, but displays every reason code and never labels an unobserved skill missing.
- **Unknown** keeps the new enum value visible and explicitly refuses to infer its meaning.

Empty evidence is definitive only when coverage is explicitly `complete`. Any other state says only that evidence was not observed in inspected files.

### Step 6 — Inspect the evidence ledger

The ledger keeps the server's ordering and shows:

- canonical skill;
- evidence kind;
- confidence;
- server-provided claim eligibility;
- file path; and
- one-based line range.

Selecting an item opens its full provenance: repository identity, immutable commit SHA, content hash, detector rule/version, contract version, and redacted excerpt.

The excerpt uses Vue text rendering inside `<pre><code>`. It never uses `v-html`, so source-like markup is displayed as text instead of being interpreted by the browser.

### Step 7 — Handle failures safely

Endpoint failures show only the API's safe `code`, `message`, and `request_id`. The client deliberately ignores internal details and never displays stack traces, upstream bodies, credentials, or raw repository secrets.

Terminal scan failures start a new scan only when the user retries. Transient polling and evidence-fetch failures resume the existing scan, preserving its accepted ID and commit relationship.

## 4. API mapping

| Client action | API operation | Client behavior |
| --- | --- | --- |
| Submit repository | `POST /api/v1/scans` | Stores the returned scan and disables duplicate submission |
| Follow progress | `GET /api/v1/scans/{scan_id}` | Honors `Retry-After` until `completed` or `failed` |
| Load evidence | `GET /api/v1/scans/{scan_id}/evidence?limit=100` | Follows opaque cursors and concatenates pages in server order |
| Show failure | Error envelope or scan `error` | Displays safe message and request ID |
| Show eligibility | Evidence `claim_eligible` | Renders the API value without recalculation |
| Show coverage | Scan `coverage` | Distinguishes complete, partial, and unknown values |

API fields remain in `snake_case` in the client, avoiding a second translation model.

## 5. Run the walkthrough locally

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. Use **Complete example** first, then **Partial example** to compare coverage semantics. With the FastAPI service running at `http://localhost:8000`, submit a public GitHub URL to exercise the live flow.

Environment defaults are documented in `frontend/.env.example`:

- `VITE_API_BASE_URL=/api/v1`
- `VITE_DEV_API_TARGET=http://localhost:8000`

## 6. Verify the implementation

Frontend gates:

```powershell
cd frontend
npm run lint
npm run test
npm run build
```

Repository contract gates:

```powershell
cd ..
python -B -m unittest tests.contract.test_frontend_stack tests.contract.test_golden_corpus tests.contract.test_phase1_documents -v
```

Results recorded on 2026-07-16:

- ESLint: pass with no warnings;
- Vitest: 3 files and 7 tests passed;
- Vite production build: pass, 19 modules transformed;
- focused repository contract suite: 23 tests passed;
- dependency audit during installation: 0 known vulnerabilities; and
- `git diff --check`: pass.

The full discovery suite runs 31 tests. Thirty pass; the remaining pre-existing failure is caused by the untracked empty `docs/.obsidian/Untitled.md`, which has no YAML frontmatter. That user-owned Obsidian file was left untouched.

## 7. Planning and documentation updates

Today's stack change was propagated through:

- `README.md` and `Implementation.md`;
- the root Phase 1 plan;
- [[inception/PRODUCT_CHARTER]];
- [[inception/ARCHITECTURE]];
- [[inception/BACKLOG]];
- [[inception/DECISION_LOG]];
- the Phase 1 exit and feasibility reports through dated amendment notes;
- the GitHub repository setup guide; and
- the ADR index and documentation maps.

The backlog now calls `US-05` the basic Vue evidence journey. Frontend quality gates use linting, runtime-contract checks, component tests, and a production build instead of TypeScript checks.

## 8. Next implementation steps

1. Implement the FastAPI scan endpoints and persistence defined by `US-01` through `US-04`.
2. Connect the live client flow to those endpoints through the existing Vite proxy.
3. Add the deterministic Playwright repository-to-evidence path once the backend fixture gateway exists.
4. Implement job-description correction and the full report UI later under `US-10` through `US-14`.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[MOCs/Delivery MOC]]
- [[adr/ADR-007-adopt-vue-javascript-client]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/BACKLOG]]
