---
title: "SkillProof MVP Requirements"
aliases:
  - "MVP Requirements"
  - "Phase 1 Requirements"
type: requirements
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - requirements
  - product
---

# SkillProof MVP Requirements

| Field | Value |
| --- | --- |
| Status | Approved Phase 1 baseline |
| Requirement set | `1.0` |
| Evidence contract | `0.1` |
| Product model | Greenfield, single-user public-repository MVP |

## Requirement conventions

- **Must** statements are release-blocking unless explicitly deferred through the decision process.
- Acceptance criteria use stable IDs so backlog stories and tests can reference them directly.
- A **supported skill** is one backed by at least one valid high- or medium-confidence evidence item. README-only evidence is low confidence and never qualifies.
- A deterministic comparison excludes database IDs and timestamps but includes canonical skills, paths, line ranges, hashes, rule IDs, confidence, coverage, matches, score components, and claim-to-evidence links.

## Business requirements

### `BR-01` — Evidence for every supported skill

Every supported skill must expose repository evidence.

- `BR-01-AC1`: For every supported skill returned by a scan or report, at least one qualifying evidence item exposes the pinned commit SHA, file path, start and end lines, detector rule ID/version, content hash, evidence kind, confidence, and redacted excerpt.
- `BR-01-AC2`: A README-only mention may be displayed as low-confidence context but must not set the skill state to supported or contribute score.
- `BR-01-AC3`: Golden-fixture tests fail if expected evidence is absent or forbidden evidence is produced.

### `BR-02` — Evidence for every generated claim

Every generated claim must reference qualifying evidence.

- `BR-02-AC1`: Creating a claim with zero evidence links, only low-confidence links, invalid evidence, or evidence from another scan is rejected.
- `BR-02-AC2`: Every returned valid claim includes at least one link to a high- or medium-confidence evidence item.
- `BR-02-AC3`: Invalidating the final qualifying evidence link makes the claim invalid and prevents it from appearing as a usable output.

### `BR-03` — Reproducible repository analysis

Repository analysis must be reproducible at an immutable commit.

- `BR-03-AC1`: Before file discovery, a scan stores the resolved 40-character hexadecimal commit SHA for the repository's default branch.
- `BR-03-AC2`: Every file and evidence item in the scan references content retrieved at that stored commit, never a mutable branch name.
- `BR-03-AC3`: Repeating the same repository, commit, detector version, and scan configuration produces an identical deterministic result.

### `BR-04` — Honest incomplete coverage

Incomplete analysis must be reported as partial.

- `BR-04-AC1`: A scan affected by truncation, a configured limit, an eligible-file fetch failure, or rate limiting has `partial` coverage and at least one machine-readable reason.
- `BR-04-AC2`: A partial scan never turns an uninspected location into proof that a skill is missing; the affected result is reported as unverified.
- `BR-04-AC3`: The API and UI expose coverage and its reasons wherever scan findings or report results are shown.

### `BR-05` — Independent product scores

Job Fit and Portfolio Quality must remain separate.

- `BR-05-AC1`: Every report returns separately labeled Job Fit and Portfolio Quality values and component explanations.
- `BR-05-AC2`: Changing only job requirements can change Job Fit but cannot change Portfolio Quality.
- `BR-05-AC3`: Changing only repository-quality inputs can change Portfolio Quality but cannot change Job Fit for the same evidence-backed job-skill matches.

## Functional requirements

### `FR-01` — Submit a public GitHub repository

**Traces to:** `BR-03`, `BR-04`

The user must be able to start a scan by submitting one public GitHub repository URL.

- `FR-01-AC1`: `https://github.com/{owner}/{repository}`, with an optional trailing slash or `.git` suffix, is normalized to owner and repository when both path segments are present.
- `FR-01-AC2`: A non-HTTPS URL, a host other than `github.com`, credentials, query parameters, fragments, or a path other than exactly owner/repository is rejected before an outbound request.
- `FR-01-AC3`: An accepted submission returns `202 Accepted` with a scan ID, normalized repository identity, and initial status of `queued`.
- `FR-01-AC4`: A nonexistent, private, or inaccessible repository returns a safe stable error and creates no completed scan or evidence.

### `FR-02` — Run a commit-pinned repository scan

**Traces to:** `BR-03`, `BR-04`

The system must inspect repository content at one immutable commit through approved GitHub API endpoints.

- `FR-02-AC1`: The scan resolves the default branch head once, stores its commit SHA, and uses that SHA for tree and blob retrieval.
- `FR-02-AC2`: The scan status follows `queued` → `running` → `completed` or `failed`; a completed scan additionally exposes `complete` or `partial` coverage.
- `FR-02-AC3`: Repository source is neither cloned nor executed, and binary, dependency, generated, and minified files are skipped according to the versioned scan policy.
- `FR-02-AC4`: The scan records detector version, scan-policy version, start/end timestamps, and every coverage reason needed to reproduce or explain the result.

### `FR-03` — Extract and inspect skill evidence

**Traces to:** `BR-01`, `BR-03`

The system must produce inspectable evidence for Python, FastAPI, Pytest, TypeScript, React, Vite, and Vitest.

- `FR-03-AC1`: Each evidence item conforms to evidence contract `0.1`: canonical skill ID, rule ID/version, repository identity, commit SHA, path, content hash, one-based inclusive start/end lines, redacted excerpt, evidence kind, confidence, coverage, and creation timestamp.
- `FR-03-AC2`: `start_line` is at least 1, `end_line` is not less than `start_line`, and both identify the excerpt's source lines in the hashed file content.
- `FR-03-AC3`: Structured manifests are parsed structurally; implementation imports, routes, components, hooks, tests, or configuration may produce high/medium evidence, while documentation-only mentions produce at most low confidence.
- `FR-03-AC4`: Evidence can be retrieved for a scan and filtered by canonical skill and confidence without changing its stored provenance.
- `FR-03-AC5`: No skill outside the seven-skill initial detector scope is reported as supported in v1.

### `FR-04` — Report complete or partial coverage

**Traces to:** `BR-04`

The system must distinguish a complete scan from one that could not inspect all eligible content.

- `FR-04-AC1`: Coverage has exactly two values: `complete` and `partial`.
- `FR-04-AC2`: Hitting a request, tree-entry, file, file-size, aggregate-byte, or timeout limit; receiving a truncated tree; an eligible-file fetch failure; or GitHub rate limiting sets coverage to `partial`.
- `FR-04-AC3`: Every partial scan includes one or more stable reason codes and the observed limit or external condition; no partial scan has an empty reason list.
- `FR-04-AC4`: Matching uses `unverified` rather than `missing` when incomplete coverage could contain evidence for the job skill.

### `FR-05` — Parse and correct a job description

**Traces to:** `BR-05`

The user must be able to submit a job description, review extracted skills, and confirm a corrected set before reporting.

- `FR-05-AC1`: A job description between 50 and 20,000 Unicode characters is accepted; blank, shorter, or longer input is rejected with a field error.
- `FR-05-AC2`: Every extracted item contains a canonical skill ID, `required` or `preferred` classification, source sentence, and parser version.
- `FR-05-AC3`: Before report creation, the user can add a canonical skill, remove an extracted skill, and change its required/preferred classification.
- `FR-05-AC4`: Corrections create a confirmed revision; report generation uses exactly that immutable revision and does not silently rerun or override it.
- `FR-05-AC5`: A report request with no confirmed job skills is rejected.

### `FR-06` — Produce explainable skill matches

**Traces to:** `BR-01`, `BR-04`, `BR-05`

The system must explain the relationship between every confirmed job skill and repository evidence.

- `FR-06-AC1`: Each confirmed job skill receives exactly one result: `exact`, `equivalent`, `related`, `missing`, or `unverified`.
- `FR-06-AC2`: `exact` and approved `equivalent` results require linked qualifying evidence; `related` is explanatory only and contributes no Job Fit points.
- `FR-06-AC3`: Each result exposes its normalized terms, taxonomy/matcher version, reason, score contribution, and evidence links when evidence is required.
- `FR-06-AC4`: `missing` is permitted only for complete coverage; the relevant result is `unverified` when partial coverage could conceal evidence.

### `FR-07` — Calculate separate, versioned scores

**Traces to:** `BR-05`

The system must calculate Job Fit and Portfolio Quality independently and explain every awarded point.

- `FR-07-AC1`: When required and preferred skills both exist, Job Fit is `80% × required coverage + 20% × preferred coverage`; when only one class exists, that class supplies 100% of Job Fit.
- `FR-07-AC2`: Coverage counts only exact or approved-equivalent matches backed by qualifying evidence. Related, missing, unverified, and low-confidence results contribute zero.
- `FR-07-AC3`: Both scores are in the inclusive range `0.0`–`100.0`, use a recorded scoring version, and expose their component inputs and weights.
- `FR-07-AC4`: Job Fit reads only the confirmed job-skill revision and evidence-backed match results. Portfolio Quality reads only repository-quality signals and never reads job-description content or classifications.
- `FR-07-AC5`: Recalculation with identical inputs and scoring version produces identical score values and component explanations.

### `FR-08` — Enforce evidence-backed career claims

**Traces to:** `BR-02`, `BR-03`

The system must permit resume and interview claims only when qualifying scan evidence supports them.

- `FR-08-AC1`: A claim records its type, text, scan, generation-rule version, validity state, and one or more evidence links.
- `FR-08-AC2`: The service rejects creation when the evidence list is empty, evidence is low confidence, evidence belongs to another scan, or evidence has been invalidated.
- `FR-08-AC3`: Every claim returned as valid exposes the supporting evidence so a user can navigate to commit, path, lines, and excerpt.
- `FR-08-AC4`: Removing or invalidating the final qualifying evidence link invalidates the claim before the next read or export; an invalid claim is never presented as usable.

## Non-functional requirements

### `NFR-01` — Treat repository code as untrusted data

- `NFR-01-AC1`: Scan code contains no repository clone, checkout, build, import, evaluation, shell, or subprocess execution path.
- `NFR-01-AC2`: Repository retrieval permits HTTPS requests only to approved GitHub API/content hosts and does not follow redirects to an unapproved host.
- `NFR-01-AC3`: Automated boundary tests prove that submitted repository content is read as bytes/text only and cannot invoke local processes.

### `NFR-02` — Enforce bounded scanning

Default per-scan limits are 50 GitHub requests, 10,000 tree entries evaluated, 40 file blobs fetched, 256 KiB per file, 5 MiB aggregate downloaded file content, concurrency 5, and a 10-second timeout per outbound request.

- `NFR-02-AC1`: Reaching any limit stops further work governed by that limit and records partial coverage with the corresponding reason code.
- `NFR-02-AC2`: A file larger than 256 KiB is not downloaded or persisted as evidence content.
- `NFR-02-AC3`: At no point are more than five GitHub requests in flight for one scan.
- `NFR-02-AC4`: Limits are configuration values recorded with the scan-policy version; changing a default requires a version change and regression tests.

### `NFR-03` — Redact secret-like values

- `NFR-03-AC1`: Redaction runs before excerpts or external response bodies reach persistence, structured logs, API responses, or UI state.
- `NFR-03-AC2`: The redaction suite covers private-key blocks, GitHub tokens, AWS access-key patterns, and values assigned to names containing `password`, `passwd`, `token`, `api_key`, or `client_secret`.
- `NFR-03-AC3`: A detected value is replaced with the deterministic typed placeholder `[REDACTED:<TYPE>]` defined by evidence contract `0.1` (for example, `[REDACTED:GITHUB_TOKEN]` or `[REDACTED:PASSWORD]`) while path and line provenance remain available.
- `NFR-03-AC4`: The secret-redaction golden fixture produces no original secret value in database, log-capture, or API assertions.

### `NFR-04` — Keep detection and scoring deterministic and versioned

- `NFR-04-AC1`: Every scan records detector, taxonomy, scan-policy, and redaction-rule versions; every report records matcher and scoring versions.
- `NFR-04-AC2`: Two executions with identical pinned content, configuration, and versions produce byte-equivalent canonical result documents after IDs and timestamps are removed.
- `NFR-04-AC3`: A behavior-changing detector, matcher, redaction, or scoring rule change requires a version change and updated golden expectations.

### `NFR-05` — Return a consistent safe API error contract

- `NFR-05-AC1`: Every non-2xx API response uses `{ "code": string, "message": string, "details"?: object, "request_id": string }`.
- `NFR-05-AC2`: Validation details identify fields without echoing secret-like input; unexpected errors return a safe generic message and never a stack trace.
- `NFR-05-AC3`: Stable error codes, rather than message text, distinguish invalid input, inaccessible repository, rate limit, external timeout, invariant violation, not found, and internal failure.
- `NFR-05-AC4`: The same request ID is present in the response and corresponding sanitized structured log.

### `NFR-06` — Manage schema through versioned migrations

- `NFR-06-AC1`: Every persistent schema change is represented by an ordered Alembic migration committed with the consuming change; application startup performs no ad hoc schema creation in production.
- `NFR-06-AC2`: CI creates an empty PostgreSQL database and applies all migrations through `head` successfully.
- `NFR-06-AC3`: CI fails when model metadata introduces an unrepresented schema difference.

### `NFR-07` — Automate critical domain verification

- `NFR-07-AC1`: CI runs unit tests for detector rules, scoring, coverage, redaction, and claim validation; integration tests for GitHub failure handling and PostgreSQL invariants; API contract tests; frontend component tests; and one repository-to-evidence end-to-end flow.
- `NFR-07-AC2`: The release pipeline fails on any expected-evidence, forbidden-evidence, unsupported-claim, deterministic-repeat, score-independence, partial-coverage, or secret-redaction test failure.
- `NFR-07-AC3`: New detector behavior is not accepted without a positive fixture, a confusable negative fixture, exact expected paths/lines, and forbidden-evidence assertions.

## Traceability summary

| Business requirement | Functional requirements | Primary quality controls |
| --- | --- | --- |
| `BR-01` | `FR-03`, `FR-06` | `NFR-03`, `NFR-04`, `NFR-07` |
| `BR-02` | `FR-08` | `NFR-04`, `NFR-06`, `NFR-07` |
| `BR-03` | `FR-01`, `FR-02`, `FR-03` | `NFR-01`, `NFR-02`, `NFR-04` |
| `BR-04` | `FR-02`, `FR-04`, `FR-06` | `NFR-02`, `NFR-05`, `NFR-07` |
| `BR-05` | `FR-05`, `FR-06`, `FR-07` | `NFR-04`, `NFR-07` |

## Related notes

- [[Home]]
- [[MOCs/Product MOC]]
- [[inception/PRODUCT_CHARTER]]
- [[inception/TRACEABILITY_MATRIX]]
