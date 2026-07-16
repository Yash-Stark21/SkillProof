---
title: "Architecture Decision Records"
aliases:
  - "ADR Map"
  - "Architecture Decisions"
type: map
status: active
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-16
tags: [skillproof, architecture, adr]
---

# Architecture Decision Records

This map is the entry point for SkillProof's Architecture Decision Records. ADRs explain why consequential technical choices were made, the alternatives considered, and the conditions that could justify a later change. The authoritative requirement and design context lives in [[inception/REQUIREMENTS]], [[inception/ARCHITECTURE]], and [[inception/DECISION_LOG]].

## Decision map

| ID | Decision | Status | Primary concern |
| --- | --- | --- | --- |
| `ADR-001` | [[adr/ADR-001-fastapi-react-separation]] | Superseded | Original client/API boundary and React/TypeScript choice |
| `ADR-002` | [[adr/ADR-002-rule-based-detection-before-ai]] | Accepted | Deterministic evidence |
| `ADR-003` | [[adr/ADR-003-commit-pinned-evidence]] | Accepted | Reproducible provenance |
| `ADR-004` | [[adr/ADR-004-separate-product-scores]] | Accepted | Score semantics |
| `ADR-005` | [[adr/ADR-005-in-process-v1-scanning]] | Accepted | Background execution |
| `ADR-006` | [[adr/ADR-006-defer-auth-workers-microservices]] | Accepted | MVP architecture boundary |
| `ADR-007` | [[adr/ADR-007-adopt-vue-javascript-client]] | Accepted | Vue/plain-JavaScript client stack |

## Lifecycle and statuses

1. Create a new ADR when a decision affects architecture, security boundaries, public interfaces, durable data, operations, or a material product invariant.
2. Start it as `proposed`, gather the evidence and alternatives needed for review, and link it from [[inception/DECISION_LOG]].
3. Change it to `accepted` when the owner commits to the decision. Update the `status` frontmatter and the visible body status together.
4. Do not rewrite the historical decision after implementation. A changed direction gets a new ADR that links to and supersedes the old one.

Supported statuses:

- `proposed`: under review and not implementation-authorizing.
- `accepted`: approved and governing current work.
- `rejected`: evaluated but not selected.
- `superseded`: replaced by a newer ADR; retain it for history and link both directions.
- `deprecated`: no longer recommended, but not replaced by one specific decision.

## Naming and metadata

- Filename: `ADR-NNN-short-kebab-case-title.md`.
- Decision ID: sequential, zero-padded `ADR-NNN`; never reuse an ID.
- Title: `ADR-NNN: Imperative decision summary`.
- Required frontmatter: `title`, `aliases`, `type`, `status`, `adr_id`, `phase`, `owner`, `created`, `updated`, and `tags`.
- Required body sections: Context, Decision, Consequences, Alternatives considered, Validation, and Related notes.
- Dates use ISO `YYYY-MM-DD`; aliases include both the decision ID and a short human-searchable phrase.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/DATA_MODEL]]
- [[inception/BACKLOG]]
