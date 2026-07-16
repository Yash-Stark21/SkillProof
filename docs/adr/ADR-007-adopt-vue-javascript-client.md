---
title: "ADR-007: Adopt Vue and JavaScript for the browser client"
aliases:
  - "ADR-007"
  - "Vue JavaScript client"
type: adr
status: accepted
adr_id: ADR-007
phase: implementation
owner: solo-developer
created: 2026-07-16
updated: 2026-07-16
tags: [skillproof, architecture, adr, frontend, vue]
---

# ADR-007: Adopt Vue and JavaScript for the browser client

- **Status:** Accepted
- **Date:** 2026-07-16
- **Decision owners:** Product and technical lead
- **Related requirements:** BR-01, BR-02, FR-01 through FR-08, NFR-05, NFR-07
- **Supersedes:** The React/TypeScript client choice in [[adr/ADR-001-fastapi-react-separation]]

## Context

ADR-001 established the durable architectural boundary: a static single-page client communicates with the FastAPI modular monolith only through the versioned `/api/v1` contract. Before product UI implementation began, the project owner selected Vue and plain JavaScript instead of React and TypeScript for SkillProof's own browser client.

This decision changes the client technology, not the evidence-detector scope. React and TypeScript remain supported repository skills and remain in the frozen golden corpus.

## Decision

Build SkillProof's browser client with Vue 3, plain JavaScript, Vue single-file components, and Vite. Frontend source and configuration use `.js` and `.vue` files without TypeScript language blocks, TypeScript configuration, or TypeScript-only build tools.

Keep the API/client separation established by ADR-001. FastAPI remains authoritative for validation, scan state, evidence qualification, coverage, matching, scores, and persistence. Vue owns interaction and presentation only and must render authoritative API values rather than infer proof or recalculate scores.

Enforce API compatibility through the versioned contract, representative runtime fixtures, component tests, and the repository-to-evidence end-to-end flow. Preserve API `snake_case` field names in the client to avoid a second translation model.

## Consequences

### Positive

- The chosen client stack matches the owner's implementation direction before legacy UI code exists.
- Vue single-file components provide a compact model for the polling, coverage, and evidence-explorer workflow.
- Plain JavaScript removes a separate frontend type-checking gate and keeps the initial client toolchain small.
- The framework change does not alter the API, evidence contract, backend boundary, or detector fixtures.

### Costs and risks

- Compile-time TypeScript guarantees are unavailable, so API-boundary regressions need stronger runtime fixtures and behavioral tests.
- Client code must use explicit defensive handling for missing fields and unknown enum values.
- The team must avoid accidentally reintroducing `.ts`, `.tsx`, `tsconfig`, `vue-tsc`, or React dependencies.
- Two build artifacts and API compatibility concerns from ADR-001 still apply.

## Alternatives considered

- **Retain React and TypeScript:** technically valid, but no product code depended on it and it no longer matched the selected implementation direction.
- **Use Vue with TypeScript:** retains static checking, but conflicts with the explicit plain-JavaScript requirement.
- **Use server-rendered FastAPI templates:** reduces build tooling but is a weaker fit for scan polling, evidence filtering, correction, and report interactions.

## Validation

- A structural contract test rejects TypeScript files/configuration and React dependencies inside `frontend`.
- Frontend linting, Vue component tests, runtime API-contract fixtures, and a production Vite build pass in CI.
- The end-to-end flow submits a repository, follows `Retry-After` polling, distinguishes complete from partial coverage, and renders source excerpts as text.
- Frontend tests prove evidence eligibility and future score values are displayed from API responses rather than recalculated.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[adr/ADR-001-fastapi-react-separation]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/BACKLOG]]
