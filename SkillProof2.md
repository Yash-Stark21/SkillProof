# SkillProof — Phase 1 Inception and Evidence Contract Plan

**Target file:** `PHASE_1_INCEPTION_PLAN.md`  
**Duration:** 5 working days  
**Delivery model:** Solo developer  
**Project type:** Greenfield Python/FastAPI and React/TypeScript application

## Summary

Phase 1 will convert the existing concept into an implementation-ready product baseline. SkillProof’s governing rule is:

> No evidence, no claim.

The phase will establish the product scope, requirements, architecture boundaries, risks, evidence contract, synthetic test corpus, prioritized backlog, and Sprint 1 entry criteria.

Phase 1 does not build production features. Disposable read-only feasibility spikes are allowed when needed to validate GitHub API behavior.

### Product outcome

SkillProof will let junior developers submit a public GitHub repository, inspect evidence-backed skills, compare them with a corrected job description, and generate career outputs that always reference qualifying evidence.

### Initial detector scope

The first release will detect:

- Python
- FastAPI
- Pytest
- TypeScript
- React
- Vite
- Vitest

Java, Spring Boot, Docker, CI/CD, authentication, and additional detector packs are deferred.

## Five-Day Execution Plan

### Day 1 — Product charter and MVP boundary

Create the product charter containing:

- Problem statement and value proposition.
- Primary persona: junior developer or job applicant.
- Secondary persona: recruiter, mentor, or interviewer.
- Primary workflow: repository submission → evidence → job comparison → supported career output.
- Measurable success criteria.
- Explicit MVP inclusions and exclusions.
- Glossary for skill, evidence, claim, scan, match, and coverage.
- Decision log with IDs and rationale.

Define the initial business requirements:

- `BR-01`: Every supported skill must expose repository evidence.
- `BR-02`: Every generated claim must reference qualifying evidence.
- `BR-03`: Repository analysis must be reproducible at a commit SHA.
- `BR-04`: Incomplete analysis must be reported as partial.
- `BR-05`: Job Fit and Portfolio Quality must remain separate.

**Day 1 gate:** The product goal, users, workflow, and MVP boundary contain no unresolved scope decisions.

### Day 2 — Requirements, feasibility, and risks

Produce numbered functional and non-functional requirements with acceptance criteria.

Required functional areas:

- Public GitHub URL submission.
- Commit-pinned repository scanning.
- Evidence extraction and inspection.
- Complete or partial coverage reporting.
- Job-description parsing and user correction.
- Explainable matching.
- Separate Job Fit and Portfolio Quality scores.
- Evidence-backed claims.

Required quality constraints:

- Never clone or execute repository code.
- Apply bounded request, file-count, file-size, and byte limits.
- Redact secret-like values before storage or display.
- Keep scoring deterministic and versioned.
- Return consistent API errors.
- Use versioned database migrations.
- Test critical domain rules automatically.

Create a risk register covering false positives, GitHub limits, truncated trees, changing repositories, secret exposure, unsupported claims, parser errors, and scope expansion. Each risk must have probability, impact, mitigation, detection signal, and response.

**Day 2 gate:** Every high-risk assumption has a mitigation or a bounded feasibility spike assigned.

### Day 3 — Evidence contract and golden corpus

Freeze evidence contract version `0.1`.

Each evidence item must define:

- Canonical skill ID.
- Detector rule ID and detector version.
- Repository identity and immutable commit SHA.
- File path and content hash.
- Start and end line.
- Redacted source excerpt.
- Evidence kind.
- Confidence: `high`, `medium`, or `low`.
- Scan coverage state.
- Creation timestamp.

Rules:

- High and medium evidence can support a skill or claim.
- README-only references are low confidence and cannot support claims.
- Low-confidence evidence may still appear in the report.
- Every claim must link to at least one valid high- or medium-confidence evidence item.
- Identical input, commit, and detector version must produce identical results.

Create synthetic golden fixtures under a dedicated test-fixture directory:

- Positive FastAPI project with routes, dependencies, and Pytest tests.
- Negative Python project mentioning FastAPI only in documentation.
- Positive React/TypeScript/Vite project with components, hooks, and Vitest tests.
- Negative TypeScript project without React implementation.
- Mixed full-stack fixture.
- Partial-scan fixture.
- Secret-redaction fixture.

Each fixture must contain expected evidence, forbidden evidence, exact paths and lines, and the expected coverage state.

**Day 3 gate:** The corpus can unambiguously determine whether a detector implementation is correct.

### Day 4 — Architecture and delivery design

Approve a modular-monolith architecture:

- React, TypeScript, and Vite frontend.
- FastAPI and Pydantic API.
- Async HTTPX GitHub client.
- PostgreSQL with SQLAlchemy async sessions.
- Alembic migrations.
- Background scan execution without Redis or Celery for v1.
- Docker Compose for local development.
- CI for linting, types, tests, migrations, and frontend builds.

Record architecture decisions for:

- FastAPI and React separation.
- Rule-based detection before AI.
- Commit-pinned evidence.
- Separate product scores.
- Background processing strategy.
- Deferred authentication, workers, and microservices.

Define the core entities: Repository, Scan, RepoFile, EvidenceItem, JobDescription, JobSkill, MatchReport, SkillMatch, GeneratedClaim, and ClaimEvidence.

Approve these initial API boundaries:

- `POST /api/v1/scans`
- `GET /api/v1/scans/{id}`
- `GET /api/v1/scans/{id}/evidence`
- `POST /api/v1/job-descriptions`
- `PATCH /api/v1/job-descriptions/{id}/skills`
- `POST /api/v1/reports`
- `GET /api/v1/reports/{id}`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

Every error response will expose a stable error code, safe message, optional field details, and request ID.

Convert requirements into prioritized epics and implementation-ready stories. Sprint 1 must be a vertical repository-to-evidence slice, not isolated infrastructure work.

**Day 4 gate:** Sprint 1 has no unresolved architecture, contract, or dependency decisions.

### Day 5 — Validation and phase exit

Complete the requirement traceability chain:

```text
Business requirement
→ functional requirement
→ user story
→ acceptance criteria
→ golden fixture
→ planned automated test
```

Review the phase against these scenarios:

- FastAPI and React implementation evidence is detected.
- Documentation-only mentions do not become supported skills.
- Every evidence item identifies its file, lines, and commit.
- Partial scans cannot imply that an undetected skill is absent.
- Secret-like content is redacted.
- Repeated analysis remains deterministic.
- Unsupported claim creation is rejected.
- Removing qualifying evidence invalidates dependent claim generation.
- Job Fit and Portfolio Quality remain independent.

Publish a Phase 1 exit report with completed artifacts, accepted risks, deferred work, Sprint 1 backlog, and a go/no-go decision.

## Phase Exit Criteria

Phase 1 is complete only when:

- Product scope and exclusions are explicit.
- Requirements have identifiers and acceptance criteria.
- High risks have recorded mitigations.
- Evidence contract `0.1` is frozen.
- Synthetic golden fixtures contain expected and forbidden results.
- Architecture and API boundaries are approved.
- The central claim-to-evidence invariant is testable.
- Sprint 1 stories meet the Definition of Ready.
- No blocking product or technical decision remains.

## Assumptions and Defaults

- `SkillProof1.md` supplies the lifecycle model; `Implementation.md` supplies the technical baseline.
- `SkillProof.md.txt` is treated as a duplicate of `Implementation.md`.
- This is a fresh project with no dependency on SteadyMind or Library Management.
- One developer performs the product, architecture, engineering, QA, security, and DevOps roles.
- Python/FastAPI and React/TypeScript are the only initial detector families.
- PostgreSQL remains the production database.
- Authentication, private repositories, LLMs, RAG, Redis, Celery, microservices, multi-repository portfolios, and document export are outside v1.
- All new project documentation will use UTF-8 encoding.
- There are no migration or backward-compatibility requirements because the project is greenfield.
