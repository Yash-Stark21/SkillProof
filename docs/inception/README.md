---
title: "SkillProof Inception Baseline"
aliases:
  - "Inception Baseline"
  - "Inception Index"
type: index
status: active
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - index
  - documentation
---

# SkillProof Inception Baseline

**Status:** Phase 1 complete — GO to Sprint 1  
**Baseline date:** 2026-07-15

This directory is the implementation source of truth for SkillProof v1. Start with the [Phase 1 exit report](PHASE_1_EXIT_REPORT.md), then use the artifacts below for delivery decisions.

| Artifact | Purpose |
| --- | --- |
| [PRODUCT_CHARTER.md](PRODUCT_CHARTER.md) | Product problem, users, workflow, scope, success measures, and glossary |
| [REQUIREMENTS.md](REQUIREMENTS.md) | `BR`, `FR`, `NFR`, and acceptance-criteria baseline |
| [FEASIBILITY_REPORT.md](FEASIBILITY_REPORT.md) | External constraints, feasibility findings, and bounded technical spikes |
| [RISK_REGISTER.md](RISK_REGISTER.md) | Active risks, controls, signals, responses, and owners |
| [DECISION_LOG.md](DECISION_LOG.md) | Approved business and technical decisions |
| [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) | Evidence semantics, confidence, provenance, redaction, coverage, and change control |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System boundaries, data flow, trust boundaries, runtime, and operations |
| [API_CONTRACT.md](API_CONTRACT.md) | Versioned HTTP resources, endpoints, states, errors, and examples |
| [DATA_MODEL.md](DATA_MODEL.md) | Entities, constraints, transactions, and persistence invariants |
| [BACKLOG.md](BACKLOG.md) | Prioritized epics, Definition of Ready/Done, and Sprint 1 stories |
| [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md) | Requirement-to-story-to-fixture-to-test coverage |
| [PHASE_1_EXIT_REPORT.md](PHASE_1_EXIT_REPORT.md) | Verification evidence, residual risks, GO decision, and Sprint 1 handoff |

Related sources:

- The approved execution plan remains at project-root path `PHASE_1_INCEPTION_PLAN.md`; its completed outcome is recorded in this vault's Phase 1 exit report.
- Accepted architecture decisions are under [`docs/adr`](../adr/ADR-001-fastapi-react-separation.md).
- The machine-readable schema remains at project-root path `schemas/evidence-contract-v0.1.schema.json`; its human-readable contract is indexed above.
- Golden inputs are under `tests/fixtures/golden`.
- Contract checks are under `tests/contract`.

Run the Phase 1 quality gate from the repository root:

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

## Related notes

- [[Home]]
- [[MOCs/Product MOC]]
- [[inception/PRODUCT_CHARTER]]
- [[inception/PHASE_1_EXIT_REPORT]]
