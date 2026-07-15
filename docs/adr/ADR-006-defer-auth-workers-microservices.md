---
title: "ADR-006: Defer authentication, durable workers, and microservices"
aliases:
  - "ADR-006"
  - "Deferred authentication workers and microservices"
type: adr
status: accepted
adr_id: ADR-006
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-006: Defer authentication, durable workers, and microservices

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Product and technical lead
- **Related requirements:** All MVP business and functional requirements

## Context

The MVP analyzes public repositories for a single unauthenticated workflow. Authentication/private repository access, durable job processing, and distributed services are common production patterns, but none proves the core product assumption: trustworthy evidence can support a career claim. Adding them now would consume design, security, deployment, and testing capacity without improving detector validity.

## Decision

The v1 boundary is:

- public repositories only;
- no user accounts, sessions, GitHub OAuth, or private repository tokens;
- one FastAPI modular monolith and one PostgreSQL database;
- in-process scan tasks as defined by ADR-005;
- no Redis, Celery, message broker, service mesh, or independently deployed domain service.

Domain modules and persisted state transitions must remain explicit so later extraction is possible, but code must not introduce speculative network interfaces or generic abstraction layers solely for a hypothetical split.

Reconsider authentication when saved private/user-owned data, private repositories, or controlled sharing becomes an accepted requirement. Reconsider durable workers under ADR-005's measured triggers. Reconsider a microservice only when a module has a demonstrated independent scaling, reliability, security, or team-ownership boundary that cannot be met cleanly inside the modular monolith.

## Consequences

### Positive

- Phase 1 and early sprints focus on evidence integrity and user value.
- Local, CI, staging, and production topology remain understandable to one developer.
- Cross-service consistency, distributed tracing, token flows, and broker operation are avoided.

### Costs and risks

- The public workflow must avoid storing user-specific sensitive data and apply reasonable abuse controls.
- Private repositories and saved user work are unavailable.
- Active scans can be interrupted as documented in ADR-005.
- A later boundary change will require migration and rollout planning.

## Alternatives considered

- **JWT accounts and GitHub OAuth in Sprint 1:** rejected because they do not validate the evidence engine and materially expand the threat model.
- **Event-driven microservices:** rejected because there is one owner, one data store, and no measured scaling split.
- **Redis/Celery as an architectural default:** rejected until durable retries or independent scaling are required.

## Validation

- MVP scope and backlog contain no private-repository or account-dependent acceptance criterion.
- Architecture review confirms all core modules can run in one API deployment.
- Any proposal to add one of the deferred capabilities includes a new requirement, threat/operations assessment, and superseding ADR.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/BACKLOG]]
- [[inception/PRODUCT_CHARTER]]
