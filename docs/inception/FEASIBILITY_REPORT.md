---
title: "SkillProof Phase 1 Feasibility Report"
aliases:
  - "Feasibility Report"
  - "Phase 1 Feasibility"
type: report
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-16
tags:
  - skillproof
  - inception
  - feasibility
  - engineering
---

# SkillProof Phase 1 Feasibility Report

**Status:** Feasible with controlled MVP constraints  
**Assessment date:** 2026-07-15  
**Owner:** Solo developer  
**Decision:** Proceed to Sprint 1

> [!note] Post-assessment implementation amendment
> ADR-007 and `D-019` replace the product client's React/TypeScript choice with Vue 3 and plain JavaScript. The feasibility findings and React/TypeScript detector spike remain valid.

## 1. Assessment boundary

This report evaluates whether the approved v1 can deliver a trustworthy repository-to-evidence workflow with a FastAPI/React modular monolith. It does not claim production scale. The governing feasibility question is whether SkillProof can acquire a reproducible public-repository snapshot, inspect it safely within limits, produce deterministic evidence, and prevent unsupported claims.

## 2. Evidence reviewed

- A live, read-only request to the public GitHub REST API returned repository identity and default-branch metadata for `octocat/Hello-World` on 2026-07-15. This confirms that public metadata acquisition works without cloning or executing repository content.
- GitHub documents a primary limit of 60 REST requests per hour for unauthenticated clients. SkillProof must therefore support optional server-side authentication, request budgeting, caching, and explicit rate-limit failures even though end-user authentication is outside v1.
- GitHub documents that a recursive Git tree can be truncated and caps the returned tree at 100,000 entries or 7 MB. The response exposes a `truncated` flag, which must become partial scan coverage rather than a silent omission.
- FastAPI supports work after a `202 Accepted` response, while its documentation recommends a larger queue when background work becomes heavy or needs multi-process execution. The v1 in-process decision is feasible only with explicit interrupted-task recovery and measured promotion thresholds.
- The frozen local evidence contract and synthetic corpus provide deterministic inputs for Python/FastAPI and React/TypeScript detector development without depending on a third-party project.

Authoritative references:

- [GitHub REST API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GitHub Git Trees API](https://docs.github.com/en/rest/git/trees)
- [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## 3. Feasibility findings

| ID | Question | Finding | Constraint or proof | Disposition |
| --- | --- | --- | --- | --- |
| `F-01` | Can v1 resolve an immutable repository snapshot without cloning? | Yes | Resolve repository/default branch, then pin the commit and use approved tree/blob endpoints. | Prove the complete endpoint chain in `SPK-01` before building detector orchestration. |
| `F-02` | Can incomplete GitHub responses be represented honestly? | Yes | Persist `complete` or `partial` coverage plus a machine-readable reason; never infer absence from partial coverage. | Required by `BR-04`, evidence contract `0.1`, and API schemas. |
| `F-03` | Can the initial detector families be evaluated deterministically? | Yes | Frozen synthetic fixtures provide exact paths, hashes, line ranges, expected evidence, and forbidden evidence. | Golden contract tests gate detector changes. |
| `F-04` | Can repository content be handled without executing untrusted code? | Yes | Inspect bounded text as data only; reject arbitrary hosts; skip binary/generated/dependency content. | Security invariant and mandatory negative tests. |
| `F-05` | Can source excerpts avoid leaking obvious secrets? | Yes, with residual risk | Hash original bytes, redact before persistence/output, and validate known token/password patterns. No finite pattern set detects every secret. | Test known cases, log no source text, document residual risk, and expand rules from incidents. |
| `F-06` | Is an in-process scan task sufficient for v1? | Conditionally | Suitable for bounded MVP scans, but work can be lost on process restart and is not a durable queue. | Persist states, reconcile stale work to `SCAN_INTERRUPTED`, and measure promotion triggers. |
| `F-07` | Can the central claim invariant be enforced? | Yes | Create the claim and qualifying evidence association atomically; reject an empty or non-qualifying association set. | Database and service tests are required before claim output ships. |
| `F-08` | Can one developer operate the architecture? | Yes | One API, one SPA, one database, one repository, and no distributed worker/auth subsystem. | Keep deferred features outside Sprint 1 and require an ADR to reintroduce them. |

## 4. Bounded Sprint 1 spikes

### `SPK-01` — Commit-pinned GitHub inventory

**Timebox:** 4 hours  
**Goal:** Demonstrate the real request sequence from a normalized public URL to repository identity, default branch, commit SHA, tree entries, and one bounded text blob.

Acceptance:

- No clone or repository execution occurs.
- Every retrieval is tied to the same commit.
- A recursive-tree `truncated` result becomes partial coverage.
- `403`, `404`, `422`, rate-limit, timeout, and malformed-payload cases map to safe internal outcomes.
- The spike records request count and rate-limit headers.

Stop condition: if commit-consistent retrieval cannot be guaranteed, do not start detector integration; revise the ingestion design first.

### `SPK-02` — Resource and redaction policy

**Timebox:** 3 hours  
**Goal:** Run representative text, binary, oversize, generated, minified, and synthetic-secret inputs through the proposed eligibility/redaction policy.

Acceptance:

- Excluded content produces an explicit policy decision.
- Any skipped eligible content changes coverage to partial.
- Persistable excerpts contain no raw corpus secret.
- Redaction preserves line count and is deterministic.

### `SPK-03` — Interrupted background task

**Timebox:** 2 hours  
**Goal:** Validate the v1 task-state design without implementing a durable worker.

Acceptance:

- Request and task use separate database-session lifecycles.
- Restart simulation leaves no scan indefinitely `running`.
- Startup reconciliation produces `failed/SCAN_INTERRUPTED`.
- Retrying creates a separately auditable scan attempt.

### `SPK-04` — Detector rule harness

**Timebox:** 4 hours  
**Goal:** Prove that one FastAPI rule and one React rule can consume the frozen fixtures and emit contract-valid evidence.

Acceptance:

- Positive expected items match exact paths, lines, excerpts, and hashes.
- Documentation-only and TypeScript-without-React forbidden assertions do not become qualifying evidence.
- Two executions have identical semantic output after timestamps and runtime IDs are excluded.

## 5. Promotion triggers

Replace in-process tasks with a durable queue only after one or more triggers are measured:

- production/deployment interruption causes unacceptable scan loss;
- scan duration regularly exceeds the deployment platform's safe task window;
- automatic retries or scheduled work become a product requirement;
- multiple API processes must coordinate work; or
- scan throughput requires independent worker scaling.

Authentication remains deferred until private repositories, user-owned history, saved personal data, or share permissions become approved requirements.

## 6. Conclusion

The MVP is technically feasible within the approved boundary. No distributed architecture, AI system, repository execution, or private-repository access is needed to prove the product promise. Sprint 1 may begin with `SPK-01`, followed by the repository-to-evidence vertical slice. The residual risks—external rate limits, incomplete trees, imperfect secret detection, and in-process task loss—are explicit, testable, and have bounded responses rather than hidden assumptions.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/RISK_REGISTER]]
- [[inception/ARCHITECTURE]]
