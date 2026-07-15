---
title: "SkillProof API Contract"
aliases:
  - "API Contract"
  - "Phase 1 API Contract"
type: contract
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - api
  - contract
---

# SkillProof API Contract

**Status:** Accepted for MVP implementation  
**API version:** `v1`  
**Evidence contract:** `0.1`  
**Base path:** `/api/v1`

## 1. Conventions

- JSON request and response bodies use `application/json` and `snake_case` field names.
- Resource IDs are opaque UUID strings. Clients must not infer ordering or type from them.
- Timestamps are UTC RFC 3339 strings, for example `2026-07-15T10:30:00Z`.
- Scores are JSON numbers from `0` through `100`, rounded to one decimal place for display. Stored calculation precision is not inferred from the response.
- Optional values that are not yet known are `null`; absent fields are reserved for fields not selected or not supported by that API version.
- Every response carries `X-Request-ID`. A caller-supplied valid `X-Request-ID` may be retained; otherwise the API generates one.
- Collection ordering is stable. Cursor pagination is used where a collection can grow.
- The frontend treats unknown enum values as displayable unknown states and does not fail the whole page.

## 2. Shared representations

### 2.1 Repository

```json
{
  "provider": "github",
  "identity": "github:octocat/example",
  "owner": "octocat",
  "name": "example",
  "url": "https://github.com/octocat/example"
}
```

Only `provider=github` is accepted in v1. Owner and repository name preserve GitHub display casing in response; `identity` is normalized for comparison.

### 2.2 Scan

```json
{
  "id": "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd",
  "repository": {
    "provider": "github",
    "identity": "github:octocat/example",
    "owner": "octocat",
    "name": "example",
    "url": "https://github.com/octocat/example"
  },
  "status": "completed",
  "phase": "complete",
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "detector_version": "0.1.0",
  "taxonomy_version": "0.1.0",
  "redaction_version": "0.1.0",
  "evidence_contract_version": "0.1",
  "scan_policy_version": "0.1",
  "coverage": {
    "state": "complete",
    "reasons": [],
    "files_discovered": 24,
    "files_inspected": 12,
    "files_skipped_by_policy": 12,
    "bytes_inspected": 48219,
    "limits": {
      "github_requests": 50,
      "tree_entries": 10000,
      "file_blobs": 40,
      "per_file_bytes": 262144,
      "total_file_bytes": 5242880,
      "concurrency": 5,
      "request_timeout_seconds": 10
    },
    "observed": {
      "github_requests": 15,
      "tree_entries": 24,
      "file_blobs": 12,
      "largest_file_bytes": 9012,
      "total_file_bytes": 48219,
      "maximum_concurrency": 5
    }
  },
  "error": null,
  "created_at": "2026-07-15T10:30:00Z",
  "started_at": "2026-07-15T10:30:01Z",
  "completed_at": "2026-07-15T10:30:04Z"
}
```

`status` is one of `queued`, `running`, `completed`, or `failed`. `phase` is one of `queued`, `resolving_repository`, `enumerating_tree`, `fetching_files`, `detecting`, `persisting`, `complete`, or `failed` and is informational.

`coverage` is `null` until a deterministic completed result exists. Its `state` is `complete` or `partial`. A failed scan has `coverage=null`; a completed partial scan remains usable but must not imply that an unobserved skill is absent.

Coverage reason codes are:

- `github_tree_truncated`
- `request_limit_reached`
- `tree_entry_limit_reached`
- `file_count_limit_reached`
- `total_byte_limit_reached`
- `eligible_file_too_large`
- `eligible_file_fetch_failed`
- `github_rate_limit_reached`
- `upstream_timeout_after_partial_result`

Policy exclusions such as binary, dependency, generated, and minified files increase `files_skipped_by_policy` but do not by themselves make coverage partial. A safety/resource limit that prevents an otherwise eligible file from being inspected does.

A failed scan's embedded safe error uses this smaller representation:

```json
{
  "code": "REPOSITORY_NOT_FOUND",
  "message": "The public repository could not be found."
}
```

### 2.3 Evidence item

```json
{
  "id": "4a47e339-b59b-4b4d-ad58-bfc56b4d47d2",
  "contract_version": "0.1",
  "canonical_skill_id": "fastapi",
  "rule_id": "python.fastapi.route_decorator",
  "detector_version": "0.1.0",
  "repository": "github:octocat/example",
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "path": "backend/app/main.py",
  "content_hash": "ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c",
  "start_line": 12,
  "end_line": 14,
  "redacted_excerpt": "@app.get(\"/health\")\nasync def health():\n    return {\"status\": \"ok\"}",
  "evidence_kind": "route",
  "confidence": "high",
  "coverage_state": "complete",
  "created_at": "2026-07-15T10:30:04Z",
  "claim_eligible": true
}
```

`confidence` is `high`, `medium`, or `low`. `claim_eligible` is derived, never caller-supplied: contract `0.1` returns `true` only for valid high/medium evidence from a completed scan. README-only evidence is low confidence and always returns `false`.

The content hash is the lowercase SHA-256 hex digest of the exact inspected file bytes; it has no algorithm prefix. The evidence item's semantic equality excludes `id` and `created_at`. Evidence collections are ordered by canonical skill ID, path, start line, rule ID, and then end line as a tie-breaker.

### 2.4 Job skill

```json
{
  "id": "d6bb8713-5841-42ae-88a8-606a9b20e60a",
  "canonical_skill_id": "fastapi",
  "display_name": "FastAPI",
  "requirement": "required",
  "source_sentence": "Build production APIs using FastAPI.",
  "origin": "parser",
  "parser_version": "0.1.0"
}
```

`requirement` is `required` or `preferred`. `origin` is `parser` before correction and `user` for a corrected or explicitly confirmed replacement list. `parser_version` is inherited from the job description for parser output and is `null` for user-origin replacement items.

### 2.5 Error envelope

All endpoint-level errors use one shape:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "The request contains invalid fields.",
  "details": {
    "fields": [
      {
        "field": "repository_url",
        "code": "unsupported_host",
        "message": "Only public github.com repository URLs are supported."
      }
    ]
  },
  "request_id": "req_01J2KFH6T0B14N5AS19YFQBC7Z"
}
```

`details` is an optional object and must contain only safe field-level or conflict information. No upstream body, token, stack trace, raw source, or secret-like value is returned.

Stable endpoint error codes are:

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | `MALFORMED_JSON` | Body is not valid JSON |
| 404 | `RESOURCE_NOT_FOUND` | Local resource ID does not exist |
| 409 | `RESOURCE_VERSION_CONFLICT` | Correction used a stale revision |
| 409 | `SCAN_NOT_COMPLETE` | A report was requested before scan completion |
| 409 | `JOB_SKILLS_NOT_CONFIRMED` | A report was requested before user confirmation |
| 409 | `NO_QUALIFYING_EVIDENCE` | A requested supported output has no high/medium evidence |
| 422 | `VALIDATION_ERROR` | Schema or field validation failed |
| 422 | `UNSUPPORTED_REPOSITORY_HOST` | URL is not an accepted public GitHub repository URL |
| 429 | `RATE_LIMITED` | SkillProof request limit was reached; includes `Retry-After` |
| 500 | `INTERNAL_ERROR` | Unexpected safe server error |
| 503 | `NOT_READY` | Required local dependency such as PostgreSQL is unavailable |

GitHub failures discovered after a scan is accepted are represented on the scan resource, not as a later HTTP response to `POST /scans`.

## 3. Scan endpoints

### 3.1 Start a scan

`POST /api/v1/scans`

Request:

```json
{
  "repository_url": "https://github.com/octocat/example"
}
```

Validation accepts the canonical HTTPS GitHub repository URL with an optional trailing slash or `.git` suffix and normalizes it. Query strings, fragments, embedded credentials, non-GitHub hosts, subpaths such as `/tree/...`, and private/inaccessible repositories are not accepted as successful scans.

Response: `202 Accepted`

Headers:

```text
Location: /api/v1/scans/9ec0aa44-ebac-471e-bbeb-82f34ef0fecd
Retry-After: 2
```

Body is a Scan with `status=queued`, `phase=queued`, `commit_sha=null`, and `coverage=null`.

The endpoint always creates a scan attempt. Completed semantic results may be reused internally only after repository and commit resolution; reuse must still return a scan resource with auditable versions.

### 3.2 Read scan status

`GET /api/v1/scans/{scan_id}`

Response: `200 OK` with a Scan.

While queued/running, `Retry-After: 2` is returned. `404 RESOURCE_NOT_FOUND` is returned for an unknown ID. HTTP success does not mean the scan succeeded; clients inspect the resource `status` and embedded `error`.

Scan failure codes are stable values:

- `REPOSITORY_NOT_FOUND`
- `REPOSITORY_NOT_PUBLIC`
- `GITHUB_RATE_LIMITED`
- `GITHUB_TIMEOUT`
- `GITHUB_UNAVAILABLE`
- `GITHUB_TREE_UNREADABLE`
- `SCAN_LIMIT_PREVENTED_RESULT`
- `SCAN_INTERRUPTED`
- `SCAN_INTERNAL_ERROR`

### 3.3 List scan evidence

`GET /api/v1/scans/{scan_id}/evidence`

Query parameters:

| Name | Default | Rules |
| --- | --- | --- |
| `limit` | `50` | Integer `1..100` |
| `cursor` | none | Opaque cursor returned by the prior page |
| `canonical_skill_id` | none | Exact normalized skill filter |
| `confidence` | none | Repeatable `high`, `medium`, or `low` filter |
| `claim_eligible` | none | Boolean filter |

Response: `200 OK`

```json
{
  "data": [],
  "page": {
    "next_cursor": null,
    "limit": 50
  },
  "scan": {
    "id": "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd",
    "status": "completed",
    "coverage": {
      "state": "partial",
      "reasons": ["file_count_limit_reached"]
    }
  }
}
```

Each `data` entry is an Evidence item. For a queued/running scan, return `409 SCAN_NOT_COMPLETE`; for a failed scan return the same code with safe scan-failure context. An empty completed collection is a successful `200`.

## 4. Job-description endpoints

### 4.1 Parse a job description

`POST /api/v1/job-descriptions`

Request:

```json
{
  "title": "Junior Backend Engineer",
  "company": "Example Co",
  "text": "We require Python and FastAPI. React experience is preferred."
}
```

`text` is required and must contain 50 through 20,000 Unicode characters after the blank check. `title` and `company` are optional strings up to 200 characters.

Response: `201 Created`

```json
{
  "id": "d2471f88-2baa-44f9-8e48-3a3f54b66193",
  "title": "Junior Backend Engineer",
  "company": "Example Co",
  "text": "We require Python and FastAPI. React experience is preferred.",
  "parser_version": "0.1.0",
  "revision": 1,
  "skills_confirmed": false,
  "skills": [
    {
      "id": "d6bb8713-5841-42ae-88a8-606a9b20e60a",
      "canonical_skill_id": "python",
      "display_name": "Python",
      "requirement": "required",
      "source_sentence": "We require Python and FastAPI.",
      "origin": "parser",
      "parser_version": "0.1.0"
    },
    {
      "id": "431aeabe-080e-4ae0-b9c0-7bde952bce92",
      "canonical_skill_id": "fastapi",
      "display_name": "FastAPI",
      "requirement": "required",
      "source_sentence": "We require Python and FastAPI.",
      "origin": "parser",
      "parser_version": "0.1.0"
    },
    {
      "id": "4f56cbf4-5c29-4d57-b555-c0adb96b7b07",
      "canonical_skill_id": "react",
      "display_name": "React",
      "requirement": "preferred",
      "source_sentence": "React experience is preferred.",
      "origin": "parser",
      "parser_version": "0.1.0"
    }
  ],
  "created_at": "2026-07-15T11:00:00Z",
  "updated_at": "2026-07-15T11:00:00Z"
}
```

`skills` contains the parser's visible results. A parser result is never silently treated as user-confirmed.

### 4.2 Correct or confirm job skills

`PATCH /api/v1/job-descriptions/{job_description_id}/skills`

The request replaces the entire skill list. To confirm without changes, the client sends back the parsed list. Duplicate canonical skill IDs with the same requirement are invalid.

```json
{
  "expected_revision": 1,
  "confirm": true,
  "skills": [
    {
      "canonical_skill_id": "python",
      "requirement": "required",
      "source_sentence": "We require Python and FastAPI."
    },
    {
      "canonical_skill_id": "fastapi",
      "requirement": "required",
      "source_sentence": "We require Python and FastAPI."
    },
    {
      "canonical_skill_id": "react",
      "requirement": "preferred",
      "source_sentence": "React experience is preferred."
    }
  ]
}
```

At least one skill is required. `canonical_skill_id` must exist in taxonomy version `0.1`; unsupported free-form values return `422 VALIDATION_ERROR`. `confirm` must be `true` in v1.

Response: `200 OK` with the Job Description resource, `revision` incremented by one, `skills_confirmed=true`, and every returned skill `origin=user`.

A stale `expected_revision` returns `409 RESOURCE_VERSION_CONFLICT` without changing the resource.

## 5. Report endpoints

### 5.1 Create a report

`POST /api/v1/reports`

Request:

```json
{
  "scan_id": "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd",
  "job_description_id": "d2471f88-2baa-44f9-8e48-3a3f54b66193"
}
```

Preconditions:

- The scan is `completed` with a pinned commit.
- Partial scans are permitted but produce an explicit warning and never convert unobserved skills into definitive absence.
- Job skills are explicitly confirmed.
- Score input uses only evidence stored for that scan.

Response: `201 Created` with the complete Report resource and `Location: /api/v1/reports/{id}`. Matching is synchronous because all input is already persisted.

### 5.2 Read a report

`GET /api/v1/reports/{report_id}`

Response: `200 OK`

```json
{
  "id": "3f39cd31-acf1-408d-a239-0ef0581c8955",
  "scan_id": "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd",
  "job_description_id": "d2471f88-2baa-44f9-8e48-3a3f54b66193",
  "repository": {
    "identity": "github:octocat/example",
    "commit_sha": "0123456789abcdef0123456789abcdef01234567"
  },
  "coverage": {
    "state": "complete",
    "reasons": []
  },
  "taxonomy_version": "0.1.0",
  "matcher_version": "0.1.0",
  "job_fit": {
    "score": 83.3,
    "version": "0.1",
    "required_coverage": 100.0,
    "preferred_coverage": 16.7,
    "weights": {
      "required": 0.8,
      "preferred": 0.2
    }
  },
  "portfolio_quality": {
    "score": 70.0,
    "version": "0.1",
    "components": [
      {
        "id": "tests",
        "value": 100.0,
        "weight": 0.3,
        "reason": "Qualifying test evidence was detected.",
        "evidence_ids": ["4a47e339-b59b-4b4d-ad58-bfc56b4d47d2"]
      }
    ]
  },
  "skill_matches": [
    {
      "job_skill_id": "d6bb8713-5841-42ae-88a8-606a9b20e60a",
      "canonical_skill_id": "fastapi",
      "normalized_job_skill": "fastapi",
      "normalized_repository_skill": "fastapi",
      "taxonomy_version": "0.1.0",
      "matcher_version": "0.1.0",
      "requirement": "required",
      "match_type": "exact",
      "awarded": true,
      "score_contribution": 40.0,
      "reason": "A qualifying FastAPI route declaration was detected.",
      "evidence_ids": ["4a47e339-b59b-4b4d-ad58-bfc56b4d47d2"]
    }
  ],
  "generated_claims": [
    {
      "id": "fc013568-e5f4-4d1f-8604-d47c42afc37e",
      "type": "interview_talking_point",
      "text": "Implemented FastAPI route handlers in a public project.",
      "scan_id": "9ec0aa44-ebac-471e-bbeb-82f34ef0fecd",
      "generation_rule_version": "0.1.0",
      "validity_state": "active",
      "evidence_ids": ["4a47e339-b59b-4b4d-ad58-bfc56b4d47d2"]
    }
  ],
  "warnings": [],
  "created_at": "2026-07-15T11:05:00Z"
}
```

`match_type` is `exact`, `equivalent`, `related`, `missing`, or `unverified`. Only exact or approved equivalent matches with qualifying evidence can set `awarded=true`. Related, missing, and unverified matches award no score. On a partial scan, an unsupported requirement is `unverified`, not `missing`, unless the matcher can establish that the relevant eligible scope was fully inspected. Each match inherits the report's taxonomy and matcher versions.

Job Fit v0.1 is `80% required coverage + 20% preferred coverage` when both classes exist. If only required skills exist, required coverage supplies 100%; if only preferred skills exist, preferred coverage supplies 100%. Portfolio Quality uses its independent score version. No combined score exists.

Both score objects expose their component inputs and weights. A class that does not exist has coverage `null` and weight `0`; the present class has weight `1`. Portfolio Quality component IDs and weights are frozen by its score version before implementation.

Each generated claim contains at least one evidence ID whose item has `claim_eligible=true`. Claim creation and evidence associations are atomic; an unsupported claim is omitted or causes `409 NO_QUALIFYING_EVIDENCE` when specifically requested by a future endpoint.

## 6. Health endpoints

### 6.1 Liveness

`GET /api/v1/health/live`

Response: `200 OK`

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

This performs no external dependency call.

### 6.2 Readiness

`GET /api/v1/health/ready`

Response `200 OK` when application initialization and PostgreSQL connectivity pass:

```json
{
  "status": "ready",
  "checks": {
    "database": "ok"
  }
}
```

Response `503 NOT_READY` uses the standard error envelope. GitHub availability is not a readiness dependency.

## 7. Compatibility and contract tests

- Additive optional response fields may be introduced inside `v1`; removing or changing existing meaning requires `/api/v2`.
- Enum additions are additive. Clients must provide a safe unknown-state presentation.
- OpenAPI is generated by FastAPI and checked against the committed contract snapshot in CI.
- Contract tests cover every success status, every listed workflow conflict, validation errors, request IDs, partial coverage, and safe serialization of failures.
- Golden-fixture API tests assert exact evidence provenance fields and claim eligibility.
- Logs and error responses are tested to ensure fixture secrets and GitHub tokens never appear.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/ARCHITECTURE]]
- [[inception/REQUIREMENTS]]
