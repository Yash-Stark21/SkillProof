---
title: "SkillProof Product Charter"
aliases:
  - "Product Charter"
  - "Phase 1 Product Charter"
type: charter
status: approved
phase: inception
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - inception
  - product
  - strategy
---

# SkillProof Product Charter

| Field | Value |
| --- | --- |
| Status | Approved baseline for Phase 1 |
| Product stage | Greenfield MVP |
| Delivery model | Solo developer using an Agile iterative-incremental lifecycle |
| Primary stack | Python/FastAPI API, React/TypeScript/Vite UI, PostgreSQL |
| Governing rule | **No evidence, no claim.** |

## Product vision

SkillProof helps junior developers turn public source code into defensible proof of their technical skills. It analyzes a public GitHub repository without executing it, records what was inspected at an immutable commit, shows the exact evidence behind each supported skill, compares that evidence with a user-corrected job description, and permits career claims only when qualifying evidence exists.

### Problem

Junior developers commonly list skills that recruiters and interviewers cannot quickly verify. Repository keyword searches are not trustworthy: documentation can mention tools that are not implemented, repositories change over time, and an incomplete scan can look like proof that a skill is absent.

### Value proposition

For applicants, SkillProof creates an explainable chain from repository code to an interview-defensible claim. For reviewers, it provides a faster and more transparent way to inspect why a skill was detected, matched, or reported missing.

## Users and outcomes

### Primary persona: junior developer or job applicant

The primary user has one public GitHub repository and a target job description. They need to know which skills the repository genuinely demonstrates, where each proof item occurs, how well that proof covers the job, and which claims they can safely use in a resume or interview.

The primary user succeeds when they can:

- Submit a supported public GitHub URL.
- Inspect skill evidence at an exact commit, file, and line range.
- Correct skills extracted from a job description before matching.
- Understand each match and both independent scores.
- Use only claims backed by qualifying evidence.

### Secondary persona: recruiter, mentor, or interviewer

The secondary user reviews a report supplied by the applicant. They need concise, reproducible evidence and an explanation of how each conclusion was reached; they do not administer or edit the applicant's repository.

## Primary workflow

1. The user submits one public GitHub repository URL.
2. SkillProof resolves and pins the default branch to a commit SHA.
3. SkillProof inspects eligible text files within explicit safety and resource limits.
4. Versioned detector rules produce evidence with confidence and provenance.
5. The user inspects the evidence and the scan's `complete` or `partial` coverage state.
6. The user submits a job description and reviews or corrects extracted required and preferred skills.
7. SkillProof creates an explainable report with separate Job Fit and Portfolio Quality scores.
8. SkillProof generates or displays a career claim only when at least one qualifying evidence item is linked to it.

## MVP boundary

### Included

- One public GitHub repository per scan.
- Commit-pinned, read-only analysis through approved GitHub API endpoints.
- Initial detection for Python, FastAPI, Pytest, TypeScript, React, Vite, and Vitest.
- High-, medium-, and low-confidence evidence with exact provenance.
- Explicit complete or partial scan coverage, including the reason for partial coverage.
- Job-description parsing, required/preferred classification, and user correction.
- Explainable matching and separate Job Fit and Portfolio Quality scores.
- Evidence-backed resume or interview claims.
- A React/TypeScript/Vite interface, FastAPI API, and PostgreSQL persistence in one modular monolith.
- Automated tests, versioned database migrations, local Docker Compose, and CI as delivery infrastructure.

### Excluded from v1

- User accounts, JWT authentication, GitHub OAuth, and private repositories.
- Java, Spring Boot, Docker, CI/CD, and any other detector packs not listed as included.
- LLM-generated content, RAG, embeddings, and vector databases.
- Redis, Celery, durable distributed workers, and microservices.
- Multi-repository portfolios, recruiter share links, and resume document export.
- Cloning, building, importing, or executing repository code.

Docker Compose and CI are permitted for building and operating SkillProof; detecting Docker or CI/CD in a submitted repository is deferred.

## Success measures

The MVP is releasable only when all of the following are true:

- **Evidence integrity:** 100% of supported skills in acceptance tests expose at least one qualifying evidence item with commit SHA, path, line range, rule ID, detector version, content hash, and redacted excerpt.
- **Claim integrity:** 0 claims can be created without at least one linked high- or medium-confidence evidence item; deleting or invalidating the last qualifying link prevents the claim from being returned as valid.
- **Detector correctness:** 100% of expected-evidence and forbidden-evidence assertions pass across the frozen golden corpus.
- **Reproducibility:** Repeating a scan for the same repository, commit SHA, detector version, and configuration produces the same normalized evidence and scoring result, excluding generated IDs and timestamps.
- **Coverage honesty:** 100% of limit, truncation, and recoverable external-failure acceptance cases produce `partial` coverage with a machine-readable reason and never present a missing skill as proven absent.
- **User control:** A user can add, remove, or change required/preferred extracted skills before report generation, and the report uses exactly the confirmed set.
- **Score separation:** Every report exposes Job Fit and Portfolio Quality as separate values with separate component explanations.
- **Safety:** Repository code is never cloned or executed, and the secret-redaction fixture persists and returns no unredacted secret-like value.

## Business requirements

| ID | Requirement | Product-level acceptance |
| --- | --- | --- |
| `BR-01` | Every supported skill must expose repository evidence. | A supported skill is absent from report results unless at least one qualifying evidence item identifies the pinned commit, source file, line range, detector rule, and redacted excerpt. |
| `BR-02` | Every generated claim must reference qualifying evidence. | Claim creation is rejected when no high- or medium-confidence evidence is supplied, and every returned valid claim exposes at least one evidence link. |
| `BR-03` | Repository analysis must be reproducible at a commit SHA. | A scan stores an immutable 40-character Git commit SHA and all file retrieval and evidence provenance for that scan reference that commit. |
| `BR-04` | Incomplete analysis must be reported as partial. | Any configured limit, truncated tree, skipped required content, or recoverable GitHub failure sets coverage to `partial`, records a reason, and prevents absence assertions for uninspected content. |
| `BR-05` | Job Fit and Portfolio Quality must remain separate. | A report returns two independently calculated, labeled scores; changing a portfolio-quality input cannot change Job Fit, and changing job requirements cannot change Portfolio Quality. |

## Glossary

| Term | Definition |
| --- | --- |
| Skill | A canonical technical capability identified by a stable skill ID, such as `python`, `fastapi`, or `react`. |
| Evidence item | A detector result tied to a pinned commit, file content hash, exact line range, redacted excerpt, rule/version, evidence kind, confidence, and coverage state. |
| Qualifying evidence | High- or medium-confidence evidence that is valid for the scan and is not based only on README or other documentation text. |
| Claim | A human-readable resume bullet or interview statement asserting a capability or contribution. A claim is valid only while linked to qualifying evidence. |
| Scan | One bounded analysis of one public repository at one immutable commit using a recorded detector version and configuration. |
| Match | A versioned, explained relationship between a confirmed job skill and qualifying repository evidence: exact, approved equivalent, related, or missing. |
| Coverage | `complete` when every eligible item within the declared scan policy was inspected; `partial` when a limit, truncation, skip, or recoverable failure prevented that guarantee. |
| Job Fit | A job-specific score based only on coverage of the user's confirmed required and preferred skills. |
| Portfolio Quality | A repository-quality score based on product-defined quality signals and independent of a job description. |
| Detector rule | A versioned, deterministic rule that turns repository structure or content into a typed evidence candidate. |

## Phase 1 exit gate

Phase 1 may enter Sprint 1 only when the charter and MVP boundary are accepted, numbered requirements have testable acceptance criteria, high risks have treatments, evidence contract `0.1` and golden expectations are frozen, architecture and API boundaries are recorded, and the Sprint 1 vertical slice satisfies the Definition of Ready. Any unresolved decision affecting evidence validity, safety, or the Sprint 1 interface is blocking.

## Related notes

- [[Home]]
- [[MOCs/Product MOC]]
- [[inception/REQUIREMENTS]]
- [[inception/DECISION_LOG]]
