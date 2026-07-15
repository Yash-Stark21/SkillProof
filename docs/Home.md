---
title: SkillProof Documentation Home
aliases:
  - SkillProof Home
  - Project Home
type: home
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - navigation
  - moc
---

# SkillProof Documentation Home

> [!abstract] Product promise
> SkillProof turns public repository implementation evidence into explainable skill matches and career claims. **No evidence, no claim.**

> [!success] Current delivery state
> Phase 1 inception is complete with a controlled **GO to Sprint 1**. Start implementation with `SPK-01`, then follow `US-01` through `US-07`.

## Start here

1. Open [[MOCs/Project MOC|Project MOC]] for the complete knowledge map.
2. Read [[inception/PHASE_1_EXIT_REPORT|Phase 1 Exit Report]] for the go/no-go evidence.
3. Use [[inception/BACKLOG|Sprint 1 Backlog]] as the delivery source of truth.
4. Follow [[guides/GitHub Repository Setup|GitHub Repository Setup]] to publish and govern the project safely.
5. Consult [[inception/REQUIREMENTS|MVP Requirements]] and [[inception/EVIDENCE_CONTRACT|Evidence Contract 0.1]] before changing behavior.
6. Read [[OBSIDIAN_GUIDE|Obsidian Guide]] before adding or reorganizing notes.

## Knowledge map

```mermaid
flowchart TD
    H["Home"] --> P["Product MOC"]
    H --> E["Engineering MOC"]
    H --> D["Delivery MOC"]
    P --> R["Requirements"]
    P --> C["Product Charter"]
    E --> A["Architecture and ADRs"]
    E --> V["Evidence Contract"]
    D --> B["Backlog"]
    D --> X["Exit Report"]
    R --> T["Traceability"]
    V --> T
    B --> T
```

## Maps of content

| Area | Open when you need to… |
| --- | --- |
| [[MOCs/Product MOC|Product]] | Understand users, scope, requirements, scoring, risks, or product decisions |
| [[MOCs/Engineering MOC|Engineering]] | Work with architecture, APIs, data, evidence rules, security, or ADRs |
| [[MOCs/Delivery MOC|Delivery]] | Plan and execute spikes, stories, tests, reviews, and releases |
| [[MOCs/Project MOC|Project]] | Navigate across all domains and find the current source of truth |

## Project controls

- Requirements and acceptance criteria: [[inception/REQUIREMENTS]]
- Active risk treatments: [[inception/RISK_REGISTER]]
- Approved decisions: [[inception/DECISION_LOG]]
- Requirement-to-test coverage: [[inception/TRACEABILITY_MATRIX]]
- API boundary: [[inception/API_CONTRACT]]
- Data invariants: [[inception/DATA_MODEL]]
- Architecture decisions: [[adr/README|ADR Index]]
- Repository publication and governance: [[guides/GitHub Repository Setup]]

## Working notes

- Create structured notes from [[templates/General Note|templates]].
- Record daily context in [[journal/README|Journal]].
- Store pasted images and other files in `assets/attachments`.
- Keep unfinished notes discoverable with `status: draft`; do not place decisions only in daily or meeting notes.

## Related notes

- [[OBSIDIAN_GUIDE]]
- [[guides/GitHub Repository Setup]]
- [[inception/README|Inception Baseline]]
- [[adr/README|Architecture Decision Records]]
