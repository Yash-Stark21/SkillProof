---
title: "ADR-004: Keep Job Fit and Portfolio Quality as separate scores"
aliases:
  - "ADR-004"
  - "Separate product scores"
type: adr
status: accepted
adr_id: ADR-004
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-004: Keep Job Fit and Portfolio Quality as separate scores

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Product and technical lead
- **Related requirements:** BR-05, FR-06, FR-07, NFR-04

## Context

Job Fit answers whether a repository proves skills requested by a particular job. Portfolio Quality evaluates qualities of the repository itself. A polished repository can be irrelevant to a job, and a relevant repository can have weak documentation or engineering hygiene. Combining them would hide both meanings and make an awarded point hard to explain.

## Decision

Every match report exposes two independent values and two independent version identifiers:

- **Job Fit Score:** evidence-backed coverage of the confirmed required and preferred job skills.
- **Portfolio Quality Score:** evidence-backed assessment of the quality dimensions supported by the active audit version.

There is no combined, overall, star, or ranking score. The UI labels and explains each score independently. A missing or unavailable Portfolio Quality dimension is represented by the scoring contract; it never changes Job Fit.

Job Fit v0.1 weights required coverage at 80% and preferred coverage at 20% when both classes exist. If only required or only preferred skills exist, the present class supplies 100%. Exact and approved equivalent matches with high/medium evidence count; related, missing, unverified, and low-confidence matches do not. Each awarded component stores reasoning and evidence associations.

Portfolio Quality has its own versioned rules and cannot award points from unsupported dimensions. Detailed dimensions and weights are frozen in the scoring specification before its implementation story enters a sprint.

## Consequences

### Positive

- Users can distinguish role relevance from repository polish.
- Every score can evolve under its own version without changing the other's semantics.
- Partial scan warnings and evidence can be presented in the relevant context.

### Costs and risks

- The UI must explain two values instead of offering a simplistic headline score.
- Cross-report comparisons require matching score versions and coverage context.
- Portfolio Quality implementation needs a separate evidence-backed specification.

## Alternatives considered

- **Single weighted score:** rejected because weights would conflate unrelated questions.
- **Job Fit only:** rejected because repository-quality feedback remains a stated product capability.
- **Unversioned heuristic scores:** rejected because historical reports could silently change meaning.

## Validation

- Tests vary portfolio inputs while holding job evidence constant and prove Job Fit does not change, and vice versa.
- Every awarded Job Fit component resolves to qualifying evidence.
- API and UI contract tests prove no combined-score field is exposed.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/REQUIREMENTS]]
