---
title: SkillProof Engineering MOC
aliases:
  - Engineering MOC
type: moc
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-16
tags:
  - skillproof
  - engineering
  - moc
---

# SkillProof Engineering MOC

Use this map when designing or reviewing implementation behavior.

## System design

- [[inception/ARCHITECTURE|Architecture]] — boundaries, flows, security, runtime, and observability
- [[inception/API_CONTRACT|API Contract]] — requests, responses, errors, states, and compatibility
- [[inception/DATA_MODEL|Data Model]] — entities, constraints, transactions, and provenance
- [[adr/README|ADR Index]] — accepted tradeoffs and their consequences

## Evidence engine

- [[inception/EVIDENCE_CONTRACT|Evidence Contract 0.1]]
- [[inception/REQUIREMENTS#FR-03 — Extract and inspect skill evidence|Evidence Requirements]]
- [[inception/TRACEABILITY_MATRIX#5. Phase 1 test catalog|Evidence Test Catalog]]
- [[inception/FEASIBILITY_REPORT#4. Bounded Sprint 1 spikes|Technical Spikes]]

## Engineering gates

- [[guides/Vue Frontend Walkthrough|Vue Frontend Implementation Walkthrough]]
- [[adr/ADR-007-adopt-vue-javascript-client|Vue and JavaScript Client Decision]]
- [[inception/BACKLOG#3. Definition of Done|Definition of Done]]
- [[inception/BACKLOG|Sprint 1 Engineering Slice]]
- [[inception/RISK_REGISTER|Security and Reliability Risks]]

## Local validation

Run from the project root:

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

The test source is outside this vault under `tests/contract`; the traceability matrix is the vault-facing index for those checks.

## Related notes

- [[Home]]
- [[MOCs/Project MOC]]
- [[MOCs/Product MOC]]
- [[MOCs/Delivery MOC]]
