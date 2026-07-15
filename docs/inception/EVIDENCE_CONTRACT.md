---
title: "SkillProof Evidence Contract 0.1"
aliases:
  - "Evidence Contract"
  - "Evidence Contract 0.1"
type: contract
status: frozen
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - evidence
  - contract
---

# Evidence Contract 0.1

Status: **frozen for Sprint 1**  
Detector version used by the golden corpus: `0.1.0`  
Governing invariant: **No evidence, no claim.**

## Purpose

This contract is the boundary between repository ingestion, detector rules, matching, and generated career claims. It makes a detector result reproducible and reviewable without executing repository code. The machine-readable representation is defined by `schemas/evidence-contract-v0.1.schema.json`; the fixtures in `tests/fixtures/golden` are the executable examples.

Contract `0.1` is intentionally small. It covers the initial Python, FastAPI, Pytest, TypeScript, React, Vite, and Vitest detector families. New skills or evidence kinds may be added without changing the invariant, but a breaking field or semantic change requires a new contract version and a new golden corpus.

## Evidence item

An expected evidence item contains all fields below. It is self-contained so it can be audited after the scan that created it.

| Field | Meaning |
| --- | --- |
| `canonical_skill_id` | Stable lowercase skill identifier, such as `fastapi` or `react`. |
| `rule_id` | Stable detector rule identifier. Rule behavior is versioned with the detector. |
| `detector_version` | Semantic version of the detector implementation. |
| `repository` | Canonical identity in `github:<owner>/<repository>` form. |
| `commit_sha` | Forty-character lowercase Git commit SHA pinned before files were read. |
| `path` | Repository-relative POSIX path. Absolute paths and traversal are forbidden. |
| `content_hash` | SHA-256 of the exact file bytes inspected by the detector. |
| `start_line`, `end_line` | Inclusive, one-based source range. |
| `redacted_excerpt` | Source range after deterministic secret redaction. |
| `evidence_kind` | The structural signal: dependency, import, route, test, component, hook, configuration, syntax, or documentation reference. |
| `confidence` | `high`, `medium`, or `low`. |
| `coverage_state` | `complete` or `partial`, copied from the owning scan. |
| `created_at` | UTC RFC 3339 timestamp. This is metadata and is excluded from semantic result comparison. |
| `claim_eligible` | Whether the item may support a claim under this contract. |

File hashes are hashes of the original bytes, not of the redacted excerpt. Line endings therefore affect the hash and are part of the frozen fixture input.

## Confidence and claim eligibility

- `high` is direct parsed implementation evidence: a dependency, import, route, typed declaration, test, component, hook, or executable configuration construct.
- `medium` is strong project-structure evidence that is not by itself a direct implementation construct.
- `low` is an unverified text reference, including every README-only mention.
- High- and medium-confidence evidence is claim-eligible unless a future evidence kind is explicitly classified otherwise.
- Low-confidence evidence is always `claim_eligible: false`. It may be displayed for review but cannot award a match point or support a generated claim.
- A README reference remains low confidence even if its wording says the technology is in use.
- A generated claim must reference at least one extant, claim-eligible evidence item. Creating a claim with no such item is rejected. Removing its final qualifying evidence invalidates the claim.

`forbidden_evidence` records a candidate signal that a correct detector must not promote to the named rule. It includes an exact source location so false-positive regressions are reproducible. A forbidden item is an assertion about detector output; it is never evidence and never claim-eligible.

## Repository and scan rules

1. Resolve and record the immutable commit before reading the tree.
2. Use only repository-relative paths from that commit.
3. Never clone, import, build, or execute submitted code.
4. Hash the exact bytes used for detection and retain the hash with every evidence item.
5. Apply configured file-count, individual-file-size, and total-byte limits.
6. Set coverage to `partial` when the tree is truncated, a limit is reached, a readable candidate file is skipped, or retrieval otherwise ends early.
7. A partial scan may report found evidence, but an omitted skill must be described as **not observed in scanned files**, never as absent from the repository.
8. Preserve deterministic ordering: canonical skill ID, path, start line, rule ID.

The semantic detector input key is:

```text
repository identity + commit SHA + detector version + contract version
```

For the same key and the same file bytes, the ordered semantic evidence fields must be identical. Runtime IDs and `created_at` are not semantic fields.

## Redaction

Redaction happens before an excerpt is persisted, logged, returned, or displayed. The original fixture file is hashed, then only the redacted excerpt enters the manifest.

Contract `0.1` requires deterministic handling for at least:

- GitHub-style tokens (`ghp_...`) → `[REDACTED:GITHUB_TOKEN]`
- Passwords embedded in PostgreSQL URLs → `postgresql://<user>:[REDACTED:PASSWORD]@...`

Redaction must preserve line count so line references remain valid. Secret fixtures contain inert synthetic values solely to prove this behavior. Raw values must not occur in manifest evidence, application output, snapshots, or logs.

## Coverage states

| State | Meaning | Required reporting behavior |
| --- | --- | --- |
| `complete` | All eligible files within the pinned tree were inspected or deterministically excluded by policy. | Missing evidence can be reported as not detected. |
| `partial` | At least one eligible file may not have been inspected. | Include a non-empty reason; do not convert non-observation into an absence claim. |

Coverage is scan-wide. Every evidence item repeats the owning state to prevent an item from being detached from this limitation.

## Golden-corpus conventions

Each fixture directory contains a `repo/` tree and `manifest.json`. A manifest contains repository provenance, coverage, an inventory of every source file and SHA-256 hash, expected evidence, and forbidden evidence. Paths in manifests are relative to `repo/`.

The seven frozen fixture IDs are:

- `positive_fastapi`
- `negative_readme_only`
- `positive_react_typescript`
- `negative_typescript_no_react`
- `mixed_fullstack`
- `partial_scan`
- `secret_redaction`

`domain_scenarios.json` complements detector fixtures with machine-readable examples of unsupported-claim rejection, evidence deletion, deterministic reruns, and independent product scores.

## Change control

Corrections that change an expected skill, confidence, line range, excerpt, rule, hash, eligibility result, or coverage state require review as a contract change. A breaking semantic change creates contract `0.2` or later and keeps the `0.1` schema and corpus available for compatibility tests. Detector-only refactoring must continue to satisfy the frozen corpus unchanged.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/REQUIREMENTS]]
- [[inception/TRACEABILITY_MATRIX]]
