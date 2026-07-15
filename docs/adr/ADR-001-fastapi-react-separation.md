---
title: "ADR-001: Separate the FastAPI API from the React client"
aliases:
  - "ADR-001"
  - "FastAPI and React separation"
type: adr
status: accepted
adr_id: ADR-001
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-001: Separate the FastAPI API from the React client

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Product and technical lead
- **Related requirements:** BR-01, BR-02, FR-01 through FR-08, NFR-05

## Context

SkillProof needs an interactive repository submission, evidence explorer, job-skill correction workflow, and explainable report. It also needs a typed HTTP boundary for repository scanning and matching. Server-rendered templates would couple product interaction to backend rendering, while separate microservices would add operational cost without an ownership or scaling need.

## Decision

Build a React/TypeScript/Vite single-page client and a FastAPI/Pydantic JSON API as separate application artifacts in one repository. They communicate only through the versioned `/api/v1` contract.

FastAPI owns authoritative validation, workflow state, evidence rules, scores, and persistence. React owns interaction and presentation and may derive display-only state, but it must not independently decide whether evidence qualifies or calculate authoritative scores.

The backend remains a modular monolith. The static frontend and API can be deployed independently, but are tested and released from the same codebase. Cross-origin policy is explicit per environment.

## Consequences

### Positive

- The evidence and scoring contract is testable independently of presentation.
- React can support polling, correction, filtering, and evidence navigation without server-template complexity.
- OpenAPI can drive client types and API contract tests.
- Backend domain modules remain reusable if another trusted client is added later.

### Costs and risks

- Two build toolchains and deployment artifacts must be maintained.
- API compatibility, CORS, loading/error states, and frontend contract tests are required.
- UI and API releases must retain compatible `/api/v1` behavior.

## Alternatives considered

- **FastAPI with server-rendered templates:** fewer artifacts, but a weaker fit for the interactive correction and evidence-exploration workflow.
- **Next.js full-stack application:** capable, but moves the chosen Python evidence engine behind a second server runtime or duplicates backend responsibilities.
- **Multiple backend services:** rejected because v1 has one owner, one database, and no demonstrated independent scaling boundary.

## Validation

- An API contract test verifies every documented route and error shape.
- A single end-to-end flow submits a repository, polls a scan, and displays evidence.
- Frontend tests prove scores and evidence qualification are rendered from API values, not recalculated in the browser.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/BACKLOG]]
