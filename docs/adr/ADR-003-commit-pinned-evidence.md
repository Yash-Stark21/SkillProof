---
title: "ADR-003: Pin every scan and evidence item to an immutable commit"
aliases:
  - "ADR-003"
  - "Commit-pinned evidence"
type: adr
status: accepted
adr_id: ADR-003
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-003: Pin every scan and evidence item to an immutable commit

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Product and technical lead
- **Related requirements:** BR-01, BR-03, FR-02, FR-03, NFR-04

## Context

GitHub branches move. A file path and excerpt without a commit cannot prove what was analyzed or reproduce a report later. Fetching metadata, a tree, and files from different branch moments can also create an internally inconsistent scan.

## Decision

At scan start, resolve the repository's default branch to one full Git commit SHA. All subsequent tree and blob retrieval uses that immutable commit snapshot. Persist the normalized repository identity, commit SHA, detector version, evidence-contract version, and scan-policy version with the scan.

Every evidence representation includes or resolves unambiguously to that repository and commit, plus a file content hash and exact line range. Reports reference a completed scan rather than a mutable branch. A later branch update requires a new scan.

The semantic cache key is repository identity + commit SHA + detector version + evidence-contract version + scan-policy version/configuration. Cache reuse never rewrites the historical input of a report.

## Consequences

### Positive

- Evidence remains reproducible and defensible after a branch changes.
- All files in a scan belong to one coherent snapshot.
- Cached results can be compared safely by versioned input.
- Reports have an immutable provenance root.

### Costs and risks

- The latest branch state is not reflected until a new scan is requested.
- GitHub endpoints must be called with commit-aware references.
- Force-pushed or deleted Git objects may later become unavailable upstream, so stored metadata and redacted excerpts remain necessary for audit.

## Alternatives considered

- **Store only branch name:** rejected because it is mutable.
- **Resolve the branch independently per file:** rejected because a scan could mix revisions.
- **Clone the repository:** rejected because cloning expands the attack surface and is unnecessary for the bounded MVP.

## Validation

- An integration test changes the fixture branch after resolution and verifies every scan fetch still targets the original SHA.
- Evidence API responses always contain the 40-character commit SHA and source content hash.
- A report cannot reference a scan whose commit has not been resolved.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/DATA_MODEL]]
- [[inception/EVIDENCE_CONTRACT]]
