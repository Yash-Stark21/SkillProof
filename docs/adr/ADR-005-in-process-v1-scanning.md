---
title: "ADR-005: Run v1 scans in process and defer a durable worker"
aliases:
  - "ADR-005"
  - "In-process v1 scanning"
type: adr
status: accepted
adr_id: ADR-005
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags: [skillproof, architecture, adr]
---

# ADR-005: Run v1 scans in process and defer a durable worker

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision owners:** Technical lead
- **Related requirements:** FR-02, FR-04, NFR-01, NFR-02, NFR-05

## Context

Repository scans require multiple bounded GitHub requests and should not hold an HTTP request open. A durable queue would improve retry and deployment resilience but introduces a broker, worker deployment, serialization boundary, monitoring, and additional failure modes before v1 load is known.

## Decision

`POST /api/v1/scans` persists a queued scan, commits it, schedules a FastAPI in-process background task, and returns `202 Accepted`. The task opens its own database session and advances `queued -> running -> completed|failed`. The client polls the scan resource.

Concurrency, request count, tree-entry count, file count, file size, total bytes, and timeouts are bounded by a versioned scan policy. Network retrieval completes outside write transactions. One SQLAlchemy `AsyncSession` is never shared across requests or concurrent task work.

In-process tasks are explicitly non-durable. On startup, stale queued/running scans are marked failed with `SCAN_INTERRUPTED`; the user can request a new scan. The API does not claim automatic retries or exactly-once execution.

A durable queue and separate worker become mandatory when any agreed threshold is exceeded for two consecutive review periods: deployment interruptions cause material user failures, scan p95 duration exceeds the request process's operational budget, concurrency harms API latency, automatic retry becomes a product requirement, or scan workloads need independent scaling. Threshold values will be set from staging/production baselines before launch.

## Consequences

### Positive

- v1 has one backend runtime, no broker, and a smaller operational surface.
- The asynchronous API experience exists without committing to a queue technology.
- Service boundaries and persisted scan states provide a later worker seam.

### Costs and risks

- Process restart or deployment loses active task execution.
- Multi-process scheduling has no global queue fairness.
- Retries are user-initiated and create a new attempt.
- Scan concurrency must be conservatively configured per process.

## Alternatives considered

- **Synchronous scan request:** rejected because GitHub latency and limits make response time unpredictable.
- **Celery/Redis immediately:** rejected as premature operational complexity.
- **Database polling worker immediately:** more durable but still adds a second runtime and ownership burden without measured need.

## Validation

- API tests verify `202`, persisted state, `Location`, and pollable transitions.
- An integration test proves the task uses a session distinct from the request session.
- Startup reconciliation tests prove abandoned tasks become explicit failures.
- Load testing records API latency and scan duration for the worker decision review.

## Related notes

- [[Home]]
- [[MOCs/Engineering MOC]]
- [[inception/DECISION_LOG]]
- [[inception/ARCHITECTURE]]
- [[inception/API_CONTRACT]]
- [[inception/BACKLOG]]
