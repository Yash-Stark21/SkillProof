---
title: "SkillProof Phase 1 Traceability Matrix"
aliases:
  - "Traceability Matrix"
  - "Phase 1 Traceability"
type: traceability-matrix
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - traceability
  - quality
---

# SkillProof Phase 1 Traceability Matrix

**Baseline:** Requirements `1.0`, evidence contract `0.1`, detector `0.1.0`  
**Purpose:** Prove that each business requirement reaches an acceptance scenario, implementation story, fixture, and automated verification.

## 1. Traceability rule

Every release-blocking change must preserve this chain:

```text
business requirement
→ functional/non-functional requirement
→ backlog story
→ acceptance criteria
→ fixture or controlled test input
→ automated test
→ release evidence
```

A requirement is not covered merely because a document mentions it. Coverage requires an identified test input and an observable expected outcome. Phase 1 contract tests validate the frozen inputs; Sprint tests will validate production behavior against those inputs.

## 2. Business requirement chains

| Business requirement and acceptance | Detailed requirements | Delivery stories | Frozen input | Verification |
| --- | --- | --- | --- | --- |
| `BR-01-AC1` qualifying provenance; `BR-01-AC2` README never supports; `BR-01-AC3` expected/forbidden gate | `FR-03`, `FR-06`; `NFR-03`, `NFR-04`, `NFR-07` | `US-03`, `US-04`, `US-08`, `US-09`, `US-11` | `positive_fastapi`, `negative_readme_only`, `positive_react_typescript`, `negative_typescript_no_react`, `mixed_fullstack` | `TC-GC-03` hashes, `TC-GC-04` ranges, `TC-GC-05` eligibility, `TC-GC-06` forbidden output; Sprint detector and API contract suites |
| `BR-02-AC1` reject unsupported claim; `BR-02-AC2` return evidence link; `BR-02-AC3` final-link invalidation | `FR-08`; `NFR-04`, `NFR-06`, `NFR-07` | `US-13` | `domain_scenarios.json`: unsupported claim and final qualifying evidence removal | `TC-DC-01`, `TC-DC-02`; Sprint service transaction and PostgreSQL invariant tests |
| `BR-03-AC1` pin commit; `BR-03-AC2` retrieve same snapshot; `BR-03-AC3` deterministic repeat | `FR-01`, `FR-02`, `FR-03`; `NFR-01`, `NFR-02`, `NFR-04` | `US-01`, `US-02`, `US-03`, `US-04` | Repository metadata in all seven manifests; deterministic rerun domain scenario | `TC-GC-02`, `TC-GC-03`, `TC-GC-09`; `SPK-01`; Sprint GitHub gateway integration tests |
| `BR-04-AC1` partial with reason; `BR-04-AC2` no false absence; `BR-04-AC3` API/UI visibility | `FR-02`, `FR-04`, `FR-06`; `NFR-02`, `NFR-05`, `NFR-07` | `US-02`, `US-05`, `US-06`, `US-11` | `partial_scan` | `TC-GC-07`; Sprint limit, truncated-tree, eligible-fetch-failure, API serialization, and UI state tests |
| `BR-05-AC1` two scores; `BR-05-AC2` job-only change isolation; `BR-05-AC3` quality-only change isolation | `FR-05`, `FR-06`, `FR-07`; `NFR-04`, `NFR-07` | `US-10`, `US-11`, `US-12` | `domain_scenarios.json`: independent product scores | `TC-DC-03`; Sprint scoring unit/property tests and report contract tests |

## 3. Functional delivery coverage

| Requirement | Primary story | Acceptance test family | Planned observable result |
| --- | --- | --- | --- |
| `FR-01` public GitHub submission | `US-01` | API validation/contract | Accepted URL returns `202` and queued scan; unsafe/malformed URLs make no outbound call. |
| `FR-02` commit-pinned scan | `US-02` | GitHub gateway integration | Tree/blob reads use one stored commit and explicit state transitions. |
| `FR-03` evidence extraction | `US-03`, `US-04`, `US-08`, `US-09` | Golden detector regression | Expected evidence is exact and forbidden evidence is absent across all supported skills. |
| `FR-04` honest coverage | `US-06` | Limit/failure matrix | Every incomplete path is partial with a stable reason and cannot create a missing conclusion. |
| `FR-05` job parsing/correction | `US-10` | Parser/API revision tests | Report input equals the explicitly confirmed immutable revision. |
| `FR-06` explainable matching | `US-11` | Matcher table tests | Each confirmed skill has one versioned result and reasoning; awarded results have evidence. |
| `FR-07` independent scores | `US-12` | Scoring examples/property tests | Only qualifying exact/equivalent matches score; changing one score's inputs cannot alter the other. |
| `FR-08` supported claims | `US-13` | Domain service/database tests | Unsupported creation rolls back; valid output exposes evidence; final-link invalidation removes usable status. |

## 4. Non-functional control coverage

| Requirement | Design control | Story/test gate |
| --- | --- | --- |
| `NFR-01` untrusted code | Approved-host GitHub gateway; no clone/build/import/shell path | `US-02`; outbound-host and subprocess-boundary tests; `SPK-01` |
| `NFR-02` bounded scanning | Versioned request/tree/blob/byte/concurrency/timeout policy | `US-02`, `US-06`; one test per limit and `partial_scan` |
| `NFR-03` redaction | Redact before persistence/log/API; preserve provenance | `US-06`; `secret_redaction`, `TC-GC-08`, sanitized-log/API tests |
| `NFR-04` determinism/versioning | Record detector, policy, taxonomy, matcher, redaction, and scoring versions | All domain stories; `TC-GC-09`, deterministic scan/report tests |
| `NFR-05` safe API errors | One error envelope and stable codes with sanitized request ID correlation | `US-01`, `US-04`, `US-06`; endpoint error matrix |
| `NFR-06` migrations | Alembic-only production schema change; empty-database upgrade in CI | `US-01`, `US-04`, `US-07`; model/migration drift tests |
| `NFR-07` automated controls | Blocking golden, unit, integration, contract, frontend, and E2E suites | `US-07`; CI pipeline and Sprint/release evidence |

## 5. Phase 1 test catalog

The dependency-free contract suite under `tests/contract` owns these Phase 1 checks:

| Test ID | Input | Assertion |
| --- | --- | --- |
| `TC-GC-01` | Golden-corpus root | Exactly the seven frozen fixture IDs are present and each has one manifest. |
| `TC-GC-02` | Every manifest | Contract/detector versions, repository identity, commit SHA, coverage, required fields, enums, and path safety are valid. |
| `TC-GC-03` | Manifest file inventory | Every listed file exists and its SHA-256 equals the frozen value; no unlisted source file exists. |
| `TC-GC-04` | Expected and forbidden ranges | Inclusive one-based ranges exist and reproduce the declared excerpt. |
| `TC-GC-05` | Expected evidence | High/medium is claim-eligible; low/documentation-only evidence is not. |
| `TC-GC-06` | Forbidden evidence | Every forbidden assertion has an exact source location and is absent from expected evidence. |
| `TC-GC-07` | Coverage metadata | Complete coverage has no reason; partial coverage has a non-empty reason and propagates to every evidence item. |
| `TC-GC-08` | Secret fixture | Persistable redacted excerpts contain typed placeholders and no raw synthetic secret. |
| `TC-GC-09` | Deterministic rerun scenario | Removing runtime IDs/timestamps produces identical canonical semantic output. |
| `TC-DC-01` | Unsupported-claim scenario | No claim with zero or non-qualifying evidence is accepted. |
| `TC-DC-02` | Evidence-removal scenario | Removing the final qualifying evidence invalidates the dependent claim. |
| `TC-DC-03` | Independent-score scenarios | Changing only job inputs changes only Job Fit; changing only quality inputs changes only Portfolio Quality. |

## 6. Release evidence

Sprint 1 must attach test output for `US-01` through `US-07`, the migration check, and the repository-to-evidence demonstration to its review record. Later MVP stories must attach their mapped automated results before release. A failed mapped test reopens its requirement and blocks release; it cannot be waived by changing only this matrix.

## Related notes

- [[Home]]
- [[MOCs/Delivery MOC]]
- [[inception/REQUIREMENTS]]
- [[inception/EVIDENCE_CONTRACT]]
