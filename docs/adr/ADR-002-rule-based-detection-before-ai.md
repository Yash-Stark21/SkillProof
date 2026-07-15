---
title: "ADR-002: Use deterministic rule-based detection before AI"
aliases:
  - "ADR-002"
  - "Rule-based detection before AI"
type: adr
status: accepted
adr_id: ADR-002
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-002: Use deterministic rule-based detection before AI

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Product and technical lead
- **Related requirements:** BR-01, BR-02, FR-03, FR-06, FR-08, NFR-04, NFR-07

## Context

SkillProof must show exactly why a skill is supported and must reject unsupported career claims. AI inference can be nondeterministic, difficult to regression-test, expensive, and capable of inventing evidence. The initial detector set has strong structural signals in manifests, imports, route declarations, components, hooks, and tests.

## Decision

Implement versioned deterministic detector packs first. Rules consume bounded, normalized repository files and emit evidence candidates containing a canonical skill ID, rule ID/version, evidence kind, confidence, path, line range, content hash, and redacted excerpt.

High and medium evidence may support a skill or claim. README-only references are low confidence and cannot. Golden fixtures define both expected and forbidden evidence for every detector pack.

LLMs, embeddings, and RAG are outside v1. A future AI capability may summarize already-qualified evidence, but it may not create, upgrade, or detach a claim from evidence without a new accepted ADR and evaluation suite.

## Consequences

### Positive

- Results are reproducible for a commit and detector version.
- False positives and regressions can be expressed as executable fixtures.
- Users and interviewers can inspect the exact rule and source location.
- The central claim invariant does not depend on probabilistic output.

### Costs and risks

- Rule coverage grows incrementally and can miss unfamiliar patterns.
- Framework syntax changes require explicit detector maintenance and versioning.
- Canonical taxonomy and equivalence rules must be curated.

## Alternatives considered

- **LLM-first repository analysis:** rejected for provenance, repeatability, privacy, and cost reasons.
- **Keyword search only:** rejected because documentation mentions and broad strings create false proof.
- **AST-only detection:** useful for some languages, but insufficient for manifests, config, and mixed-language projects; rules may use structural parsers where appropriate.

## Validation

- The golden corpus passes expected and forbidden evidence assertions.
- Running a detector twice against identical normalized input produces equivalent ordered evidence.
- Tests prove low-confidence README evidence cannot satisfy a claim or awarded match.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/EVIDENCE_CONTRACT]]
- [[inception/REQUIREMENTS]]
