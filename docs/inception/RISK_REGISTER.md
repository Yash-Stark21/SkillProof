---
title: "SkillProof Phase 1 Risk Register"
aliases:
  - "Risk Register"
  - "Phase 1 Risks"
type: risk-register
status: active
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - risk
  - governance
---

# SkillProof Phase 1 Risk Register

| Field | Value |
| --- | --- |
| Status | Active baseline; reviewed at sprint planning and review |
| Assessment date | 2026-07-15 |
| Accountable owner | Solo developer acting in the named product, engineering, QA, security, or operations role |
| Risk appetite | No acceptance of a risk that can silently create unsupported evidence or claims |

## Rating and control rules

Probability is `Unlikely` (less than 25%), `Possible` (25–60%), or `Likely` (greater than 60%) during the MVP. Impact is `Low`, `Medium`, `High`, or `Critical`; Critical means the governing evidence promise or user safety can be violated. A High or Critical risk may enter implementation only when it has a preventive control and an executable test or a named, time-boxed feasibility spike. Discovery of an unsupported claim, unredacted secret, or mixed-commit evidence blocks release regardless of rating.

## `R-001` — False-positive skill evidence

- **Probability:** Likely
- **Impact:** Critical
- **Owner:** Engineering and QA
- **Status:** Open — treated; release-blocking tests required
- **Linked requirements:** [`BR-01`, `FR-03`, `FR-06`, `NFR-04`, `NFR-07`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-04` detector rule harness](FEASIBILITY_REPORT.md)
- **Mitigation:** Use deterministic versioned rules, parse manifests structurally, cap documentation-only references at low confidence, and require positive plus confusable-negative golden cases with forbidden-evidence assertions for every rule.
- **Detection signal:** A forbidden-evidence assertion fails; a skill lacks qualifying implementation evidence; repeat runs disagree; or a user reports that a documentation mention was treated as proof.
- **Response:** Block the release, disable or revert the offending rule, add the smallest reproducing fixture, correct the rule, increment the detector version, and regenerate affected non-released results. Never hand-edit evidence to conceal the defect.
- **Residual risk:** Novel syntax can still be misclassified; detector feedback remains a monitored backlog source.

## `R-002` — GitHub request or rate-limit exhaustion

- **Probability:** Likely
- **Impact:** High
- **Owner:** Backend and operations
- **Status:** Open — spike assigned and runtime controls required
- **Linked requirements:** [`FR-02`, `FR-04`, `NFR-02`, `NFR-05`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-01` commit-pinned GitHub inventory](FEASIBILITY_REPORT.md)
- **Mitigation:** Enforce the 50-request scan budget, bounded concurrency and timeouts; record rate-limit headers; cache by immutable semantic key; and keep optional server-side GitHub credentials separate from end-user authentication.
- **Detection signal:** Remaining-request headers approach the configured reserve, GitHub returns `403`/`429`, the request budget is reached, or rate-limit failures increase in telemetry.
- **Response:** Stop further GitHub calls, preserve completed safe work, mark the scan partial or failed with the stable rate-limit reason and reset/retry context, and never reinterpret uninspected content as absence. Retry is user-initiated for v1.
- **Residual risk:** Unauthenticated capacity is shared externally and cannot be guaranteed by SkillProof.

## `R-003` — Truncated tree or missing eligible files

- **Probability:** Possible
- **Impact:** Critical
- **Owner:** Backend and product
- **Status:** Open — spike assigned; absence protection is mandatory
- **Linked requirements:** [`BR-04`, `FR-02`, `FR-04`, `FR-06`, `NFR-02`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-01` commit-pinned GitHub inventory](FEASIBILITY_REPORT.md)
- **Mitigation:** Inspect GitHub's `truncated` indicator and every fetch outcome; maintain stable partial-reason codes; track eligible versus inspected content; and apply the versioned request, entry, file, size, and byte budgets.
- **Detection signal:** `truncated=true`, eligible/file counts exceed policy, an eligible blob cannot be fetched, aggregate limits are reached, or inventory and retrieval counts disagree.
- **Response:** Mark coverage `partial`, record all observed reasons, render potentially affected skill outcomes as `unverified` rather than `missing`, and offer a new scan only after the limiting condition changes. Do not silently expand limits within the same policy version.
- **Residual risk:** Very large repositories may remain partial by design in v1.

## `R-004` — Repository changes during or after analysis

- **Probability:** Likely
- **Impact:** Critical
- **Owner:** Backend and data
- **Status:** Controlled — invariant and integration tests required
- **Linked requirements:** [`BR-03`, `FR-02`, `FR-03`, `NFR-04`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-01` commit-pinned GitHub inventory](FEASIBILITY_REPORT.md)
- **Mitigation:** Resolve the default branch once, pin the full commit SHA, address every tree/blob request by that commit, persist file hashes, and key cached results by repository, commit, detector/evidence versions, and limit-policy version as defined by [ADR-003](../adr/ADR-003-commit-pinned-evidence.md).
- **Detection signal:** A request targets a branch after SHA resolution, returned object identity does not belong to the pinned tree, a content hash changes for the same semantic key, or a repeat scan differs.
- **Response:** Stop the scan and record a safe provenance failure. Continue only against the originally pinned SHA; never switch to a newer branch head. If the object is unavailable, fail explicitly and require a new scan attempt.
- **Residual risk:** Upstream force-push or object deletion can make later refetch impossible, so stored redacted provenance remains necessary.

## `R-005` — Secret-like content is exposed

- **Probability:** Possible
- **Impact:** Critical
- **Owner:** Security and backend
- **Status:** Open — spike assigned; zero known-secret tolerance
- **Linked requirements:** [`FR-03`, `NFR-03`, `NFR-07`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-02` resource and redaction policy](FEASIBILITY_REPORT.md)
- **Mitigation:** Treat source as untrusted; exclude known sensitive/generated paths where policy requires; redact before persistence, logging, API output, or UI state; use deterministic typed placeholders from evidence contract `0.1`; and test the secret-redaction fixture across database, log, and API boundaries.
- **Detection signal:** A seeded secret appears outside fixture source, a redaction assertion fails, log scanning finds a token/private-key pattern, or a user reports an exposed value.
- **Response:** Stop affected output, block release, purge exposed persisted excerpts and logs where operationally possible, determine the affected scans, correct and version the redaction rule, add a regression fixture, and rescan. Notify the operator/user to rotate a real exposed credential when contact is available.
- **Residual risk:** Pattern redaction cannot recognize every possible secret; excerpts remain deliberately short and never include raw source in logs.

## `R-006` — Unsupported career claim is created or remains usable

- **Probability:** Possible
- **Impact:** Critical
- **Owner:** Domain engineering and QA
- **Status:** Controlled — invariant is a release gate
- **Linked requirements:** [`BR-02`, `FR-08`, `NFR-06`, `NFR-07`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-04` detector rule harness](FEASIBILITY_REPORT.md) validates qualifying evidence semantics; claim persistence is validated in the Sprint 1-following claim story.
- **Mitigation:** Create claims and qualifying `ClaimEvidence` links atomically; accept only valid high/medium evidence from the same scan; reject an empty qualifying set; and invalidate a claim when its final qualifying link is removed or invalidated.
- **Detection signal:** An orphan-claim database query returns rows, a claim API response has no qualifying links, a low-confidence item awards a claim, or an invariant test fails.
- **Response:** Block claim return and release, mark affected claims invalid, repair the invariant rather than synthesizing evidence, add the reproducing test, and audit all claims created under the affected generation-rule version.
- **Residual risk:** Claim wording can still overstate what evidence means; v1 uses deterministic, versioned templates rather than AI generation.

## `R-007` — Job-description parser misclassifies a skill

- **Probability:** Likely
- **Impact:** High
- **Owner:** Product and matching engineering
- **Status:** Open — mitigated by mandatory user confirmation
- **Linked requirements:** [`FR-05`, `FR-06`, `FR-07`, `NFR-04`, `NFR-07`](REQUIREMENTS.md)
- **Linked spike:** No pre-Sprint 1 spike; parser fixture evaluation is required before the job-fit story satisfies Definition of Ready.
- **Mitigation:** Persist parser version and source sentence, expose required/preferred classification, require the user to add/remove/reclassify items, and bind reports to the immutable confirmed revision rather than silently reparsing it.
- **Detection signal:** Parser fixture failure, high correction rate for a canonical skill, repeated required/preferred edits, or a report input differs from the confirmed revision.
- **Response:** Prevent report creation until confirmation, use the corrected set immediately, add the failure to parser fixtures, improve and version the parser, and never retroactively change an existing confirmed report input.
- **Residual risk:** Human confirmation can itself be wrong; the report must continue to show its exact confirmed inputs.

## `R-008` — Scope expansion delays evidence validation

- **Probability:** Likely
- **Impact:** High
- **Owner:** Product owner
- **Status:** Monitoring — explicit change control
- **Linked requirements:** [Approved MVP requirement set](REQUIREMENTS.md) and [product boundary](PRODUCT_CHARTER.md)
- **Linked spike:** None; scope requests are product decisions, not technical uncertainty.
- **Mitigation:** Keep Java/Spring Boot, Docker/CI detector packs, authentication/private repositories, AI/RAG, multi-repository analysis, export, Redis/Celery, and microservices in the deferred backlog. Require a new requirement, risk review, estimate, and superseding decision/ADR before admission.
- **Detection signal:** A sprint candidate introduces a deferred detector, dependency, service, identity flow, or output without a mapped approved requirement; Sprint 1 exceeds the vertical repository-to-evidence goal.
- **Response:** Remove the item from the sprint and record it in the post-MVP backlog. Reprioritize only through an explicit scope decision after the evidence engine meets its release gates.
- **Residual risk:** External portfolio or interview expectations may pressure expansion; measurable product value takes precedence over dependency count.

## `R-009` — Untrusted or oversized repository exhausts resources

- **Probability:** Possible
- **Impact:** High
- **Owner:** Backend and security
- **Status:** Open — spike assigned and bounded by policy
- **Linked requirements:** [`FR-02`, `FR-04`, `NFR-01`, `NFR-02`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-02` resource and redaction policy](FEASIBILITY_REPORT.md)
- **Mitigation:** Never clone or execute content; permit approved hosts only; cap requests, tree entries, blobs, individual bytes, aggregate bytes, concurrency, and request duration; and classify binary/generated/minified/dependency content before inspection.
- **Detection signal:** Any limit is reached, a redirect targets an unapproved host, binary/oversize policy is invoked, scan duration grows near the operational budget, or memory/latency alarms fire.
- **Response:** Cancel affected retrieval, mark coverage partial with the exact reason when safe work remains, otherwise fail safely, release resources, and reject any evidence derived from incomplete or disallowed content.
- **Residual risk:** Pathological text within allowed limits can still be expensive; detector-level time/complexity tests remain required.

## `R-010` — In-process scan is interrupted

- **Probability:** Possible
- **Impact:** High
- **Owner:** Backend and operations
- **Status:** Accepted for v1 with recovery control and promotion triggers
- **Linked requirements:** [`FR-02`, `FR-04`, `NFR-05`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-03` interrupted background task](FEASIBILITY_REPORT.md)
- **Mitigation:** Persist state before scheduling, give the background task its own database-session lifecycle, never promise automatic retry/exactly-once behavior, and reconcile stale `queued`/`running` scans at startup as `failed/SCAN_INTERRUPTED` under [ADR-005](../adr/ADR-005-in-process-v1-scanning.md).
- **Detection signal:** Startup finds stale work, deployment interrupts an active scan, failed/interrupted rate rises, or scan duration/concurrency meets an ADR-005 promotion trigger.
- **Response:** Mark the attempt failed with a stable code, preserve its audit record, let the user create a distinct retry attempt, and adopt a durable queue only when measured promotion criteria are met.
- **Residual risk:** One active attempt can be lost during any process restart; this is visible rather than hidden.

## `R-011` — Version or ordering drift breaks reproducibility

- **Probability:** Possible
- **Impact:** High
- **Owner:** Engineering and QA
- **Status:** Controlled — deterministic regression gate
- **Linked requirements:** [`BR-03`, `FR-07`, `NFR-04`, `NFR-07`](REQUIREMENTS.md)
- **Linked spike:** [`SPK-04` detector rule harness](FEASIBILITY_REPORT.md)
- **Mitigation:** Record every behavior-bearing version, sort canonical outputs explicitly, exclude only IDs/timestamps from semantic comparison, and require a version increment plus updated golden expectations for behavior changes.
- **Detection signal:** Identical-input repeat documents differ, output order varies, a score changes without a version change, or historical cache keys collide across rule behavior.
- **Response:** Block release and cache reuse, identify the nondeterministic component, make ordering and inputs explicit, bump the affected version, and regenerate only under a new semantic key.
- **Residual risk:** Runtime/library upgrades can alter parser behavior; dependency updates run the full corpus before merge.

## Review cadence and escalation

- Review all Open, Monitoring, and Accepted risks during sprint planning and sprint review.
- Reassess probability, impact, and residual risk after each linked spike or production-like test.
- A Critical risk whose control or release test is absent makes the related story Not Ready.
- A triggered Critical incident stops release and creates a P0 defect plus a decision-log entry if policy changes.
- Closing a risk requires evidence that its prevention, detection, and response tests pass; implementation alone is insufficient.

## Related notes

- [[Home]]
- [[MOCs/Delivery MOC]]
- [[inception/FEASIBILITY_REPORT]]
- [[inception/DECISION_LOG]]
