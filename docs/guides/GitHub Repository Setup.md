---
title: SkillProof GitHub Repository Setup
aliases:
  - GitHub Repository Setup
  - Publish SkillProof to GitHub
type: guide
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-16
tags:
  - skillproof
  - github
  - repository
  - delivery
---

# SkillProof GitHub Repository Setup

This runbook publishes the existing SkillProof project as a professional GitHub repository and configures the minimum governance needed for Sprint 1. It is designed for a solo developer and keeps the local repository, the GitHub remote, and the Obsidian documentation vault aligned.

> [!important] Scope
> This guide describes the setup. Following it creates an external public repository and pushes local files, so perform the security review before running the publish commands.

## 1. Recommended repository profile

Use these values on GitHub:

| Field | Recommended value | Rationale |
| --- | --- | --- |
| Owner | Your GitHub user account or intended organization | The owner controls access, billing, and repository policy. |
| Repository name | `skillproof` | Lowercase keeps the URL and command-line examples consistent; the product name remains **SkillProof**. |
| Visibility | **Public**, after the security review | Appropriate for a portfolio project and for demonstrating the product's own evidence-first standard. Use private visibility temporarily if the review is incomplete. |
| Default branch | `main` | Matches the commands and planned branch rules in this guide. |
| Website | Leave blank initially | Add the production or demonstration URL only after a deployment exists. |
| README | Do not create on GitHub | The project already has a root `README.md`. |
| `.gitignore` | Do not create on GitHub | The project already has a Python, frontend, secret, and Obsidian-aware `.gitignore`. |
| License | Select **No license** during repository creation | Avoid an accidental legal decision and an initial commit conflict. Record a deliberate license decision before presenting the project as open source. |

### Copy-ready description

Use this as the GitHub **Description**:

> Evidence-first developer portfolio analyzer that scans public GitHub repositories, verifies Python/FastAPI and React/TypeScript skills, and generates explainable job-fit reports and evidence-backed career claims.

Short alternative:

> Turn public GitHub repositories into verifiable skills, explainable job-fit reports, and evidence-backed career claims.

### Recommended topics

```text
python
fastapi
pytest
react
typescript
vite
vitest
postgresql
github-api
developer-tools
portfolio
career-tools
skill-verification
evidence-based
```

GitHub topics use lowercase letters, numbers, and hyphens. GitHub currently permits up to 20 topics, each no more than 50 characters, so this list remains within the documented boundary.

### License decision

A public repository is not automatically an open-source project. Without a license, default copyright applies; GitHub users can still view and fork a public repository under GitHub's terms. Keep **No license** for the initial empty remote, then make an explicit decision:

- add a recognized open-source license if reuse, modification, and distribution are intended; or
- keep the repository unlicensed if those permissions are not intended yet.

Do not select a license in the GitHub creation form for this first push. Adding it there creates a remote commit before the existing local history is uploaded.

## 2. Publication readiness gate

Complete this checklist before making the repository public:

- [ ] The product description and MVP boundary are accurate.
- [ ] The root README renders correctly and contains no private information.
- [ ] The legacy top-level concept files (`SkillProof*.md*` and `Implementation.md`) are acceptable for public viewing.
- [ ] `.env`, access tokens, passwords, private keys, personal data, and private-repository content are absent from the files to be committed.
- [ ] Any `.env.example` values are placeholders only.
- [ ] Obsidian attachments contain no private or secret material.
- [ ] The contract test suite passes.
- [ ] The entire staged diff has been reviewed.
- [ ] The repository visibility and license choice are intentional.

> [!warning] Synthetic secret fixture
> `tests/fixtures/golden/secret_redaction/repo/config.py` deliberately contains fake token-shaped and password-shaped values used to test redaction. GitHub push protection may flag them. Confirm that a flagged value is exactly the documented synthetic fixture before using a narrow, documented test-fixture bypass. Never disable secret scanning globally or bypass an unfamiliar value.

The `.gitignore` reduces accidental staging, but it is not a security review and does not remove files that were already staged or committed.

## 3. Validate the local baseline

Open PowerShell and move to the project root:

```powershell
Set-Location C:\Users\yasha\Documents\Projects\SkillProof
```

Run the current contract gate:

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

Do not publish while this command fails. Correct the baseline or record an explicit, reviewed exception first.

## 4. Create the empty GitHub repository

1. Sign in to GitHub.
2. Choose **New repository** from the **+** menu.
3. Select the intended owner.
4. Enter `skillproof` as the repository name.
5. Paste the recommended description from this guide.
6. Select **Public** only after completing the publication readiness gate.
7. Do **not** add a README.
8. Do **not** add a `.gitignore` template.
9. Select **No license**.
10. Choose **Create repository** and keep the Quick Setup page open.

Creating an empty remote is important because the project already contains its initial documentation baseline. GitHub also recommends leaving README, license, and `.gitignore` initialization off when uploading an existing local project.

## 5. Initialize and review the local Git repository

First check whether the folder is already a valid Git repository:

```powershell
git status
```

If Git reports that the folder is not a repository, initialize it with `main`:

```powershell
git init -b main
```

Verify the commit identity that will be public:

```powershell
git config --get user.name
git config --get user.email
```

If either value is missing or inappropriate for a public commit, configure it for this repository:

```powershell
git config user.name "Your Name"
git config user.email "your-public-or-noreply-email@example.com"
```

Confirm that representative private state is ignored:

```powershell
git check-ignore -v -- .env .env.local docs/.obsidian/workspace.json
```

Stage the baseline, then inspect it before committing:

```powershell
git add .
git status --short
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Stop if an unexpected file, credential, personal path, private note, generated artifact, or real secret appears. Remove it from the staged set and fix the source or ignore rule before continuing.

Create the first commit:

```powershell
git commit -m "chore: establish SkillProof inception baseline"
```

The initial commit is expected to contain the project README, `.gitignore`, Phase 1 artifacts, Obsidian vault, evidence schemas, golden fixtures, and contract tests. Production application code is not expected yet.

## 6. Connect and push to GitHub

Copy the HTTPS URL from the GitHub Quick Setup page, replace `<github-username>`, and add it as `origin`:

```powershell
git remote add origin https://github.com/<github-username>/skillproof.git
git remote -v
```

Check both displayed URLs carefully, then push `main` and record the upstream:

```powershell
git push -u origin main
```

GitHub may open a browser or use the system credential manager for authentication. Do not place a personal access token in the remote URL, a command saved in project files, or committed configuration.

### GitHub CLI alternative

Use this only as an alternative to creating the remote in the browser. Run it after the local commit exists, and do not run it if the `skillproof` repository has already been created:

```powershell
gh auth status
gh repo create skillproof --public --source=. --remote=origin --push --description "Evidence-first developer portfolio analyzer that scans public GitHub repositories, verifies Python/FastAPI and React/TypeScript skills, and generates explainable job-fit reports and evidence-backed career claims."
```

## 7. Verify the first publication

On the GitHub repository page, confirm:

- [ ] `main` is the default branch.
- [ ] The first commit has the intended author identity and message.
- [ ] The README renders and links into the `docs/` vault.
- [ ] The description is exact and the recommended topics are present.
- [ ] No `.env`, Obsidian workspace state, credential, or private attachment is visible.
- [ ] The synthetic redaction fixture is clearly test data if GitHub flags it.
- [ ] `git status --short` is clean locally after the push.
- [ ] `git remote -v` points only to the intended repository.

If a real secret was pushed, do not merely delete it in a later commit. Revoke or rotate the credential immediately, stop further publication work, and follow GitHub's sensitive-data removal guidance.

## 8. Configure repository features

Open **Settings → General** and use this initial configuration:

| Setting | Initial choice | Reason |
| --- | --- | --- |
| Issues | Enabled | Sprint 1 spikes, stories, bugs, and decisions need traceable work items. |
| Projects | Optional | Enable if the board described below will be actively maintained. |
| Wiki | Disabled | The committed `docs/` Obsidian vault is the authoritative documentation system. |
| Discussions | Disabled initially | Enable when there is a real community-support or design-discussion need. |
| Allow squash merging | Enabled | Produces one clear change per pull request. |
| Allow merge commits | Disabled | Keeps `main` linear when squash merging is the standard. |
| Allow rebase merging | Disabled initially | One supported merge path is simpler for a solo project. |
| Automatically delete head branches | Enabled | Removes merged working branches. |

Add the website only after a real deployment exists. Add a social preview later when product branding is ready.

## 9. Protect `main` with a ruleset

Create this after the initial push, because `main` must exist first:

1. Open **Settings → Rules → Rulesets**.
2. Choose **New ruleset → New branch ruleset**.
3. Name it `protect-main`.
4. Set enforcement to **Active**.
5. Target the default branch.
6. Enable **Restrict deletions**.
7. Enable **Block force pushes**.
8. Enable **Require linear history**.
9. Enable **Require a pull request before merging**.
10. Require conversation resolution.
11. Keep required approvals at zero while there is only one developer; otherwise the author may be unable to approve their own change.
12. Do not require status checks yet.

Add required status checks only after `US-07` creates stable CI jobs and each check has completed successfully at least once. Planned checks are:

- backend linting, type checking, unit tests, and PostgreSQL integration tests;
- Alembic upgrade validation against an empty database;
- frontend linting, runtime-contract checks, tests, and production build;
- evidence contract and golden-corpus tests; and
- the deterministic repository-to-evidence end-to-end path.

Use unique job names. Requiring a check that does not exist or has never run can block every pull request.

## 10. Configure security and automation boundaries

In **Settings → Security & analysis**, enable the security features available for the repository and account, including dependency alerts, automated security updates, secret scanning, and push protection where offered.

For future GitHub Actions workflows:

- keep default workflow permissions read-only;
- grant additional permissions only to the job that needs them;
- pin or deliberately review third-party actions;
- store GitHub API credentials in repository or environment secrets;
- never expose a server-side GitHub token to the Vue client; and
- keep live GitHub calls out of required CI acceptance tests, as defined by Sprint 1.

## 11. Create Sprint 1 work management

### Milestone

Create one milestone:

```text
Sprint 1 — Repository to Evidence
```

Use the 10-working-day Sprint 1 window from the approved backlog. Set the actual due date when the sprint start date is chosen.

### Labels

Create a small, consistent label taxonomy:

```text
type:spike
type:feature
type:bug
type:docs
type:delivery
priority:p0
priority:p1
area:backend
area:frontend
area:github
area:evidence
area:security
status:blocked
```

### Initial issues

Create the bounded feasibility spikes first:

1. `SPK-01 — Commit-pinned GitHub inventory`
2. `SPK-02 — Resource and redaction policy`
3. `SPK-03 — Interrupted background task`
4. `SPK-04 — Detector rule harness`

Then create the Sprint 1 delivery stories from the approved backlog:

1. `US-01 — Accept and persist a public repository scan`
2. `US-02 — Resolve and inventory one immutable GitHub snapshot`
3. `US-03 — Detect qualifying Python, FastAPI, and Pytest evidence`
4. `US-04 — Persist and inspect evidence contract 0.1`
5. `US-05 — Complete the basic Vue evidence journey`
6. `US-06 — Enforce scan limits, partial coverage, and secret redaction`
7. `US-07 — Gate the vertical slice in CI and migrations`

Copy the authoritative acceptance criteria, dependencies, planned tests, and demonstration from the Sprint 1 backlog into each issue. Link the issue back to the relevant project note instead of inventing a second version of the requirement.

### Issue body

Use this minimum structure:

```markdown
## Outcome

## Requirements

## Acceptance criteria

- [ ]

## Planned tests

## Security and coverage impact

## Dependencies

## Demonstration
```

If a GitHub Project board is used, keep the workflow small:

```text
Backlog → Ready → In progress → In review → Done
```

`SPK-01` is the first implementation issue. Its stop condition remains authoritative: if commit-consistent retrieval cannot be guaranteed, detector integration does not begin.

## 12. Working conventions

### Branch names

Use short branches tied to one issue:

```text
spike/spk-01-github-inventory
feat/us-01-submit-scan
fix/scan-url-validation
docs/github-setup
```

### Commit messages

Use an imperative Conventional Commit-style prefix:

```text
chore: establish SkillProof inception baseline
docs: add GitHub repository setup guide
feat(scan): accept public repository URL
test(evidence): reject documentation-only FastAPI claims
fix(security): redact token-shaped excerpts
```

### Pull requests

Each pull request should contain:

- the linked issue and intended outcome;
- an acceptance-criteria checklist;
- tests run and their result;
- evidence, coverage, and security impact;
- API, migration, and compatibility impact;
- documentation changes; and
- residual risks or follow-up work.

For a solo project, the pull request is still valuable as a review checkpoint. Review the diff, wait for required checks, resolve conversations, and squash merge into `main`.

## 13. Release policy

Do not tag this documentation-only baseline as `v1.0.0`. Create the first pre-release only after the repository-to-evidence vertical slice works through the API and Vue UI and passes the agreed CI gate. A reasonable first product milestone is `v0.1.0`; the final version remains a release decision, not an automatic result of repository creation.

## 14. Troubleshooting

### `remote origin already exists`

Inspect it before changing anything:

```powershell
git remote -v
```

If it is the wrong repository, replace only the URL:

```powershell
git remote set-url origin https://github.com/<github-username>/skillproof.git
```

### The GitHub repository was initialized accidentally

If GitHub already contains a README, license, or `.gitignore` commit, do not force-push or reset blindly. For a brand-new remote with no unique work, the clearest option is usually to recreate it as an empty repository. If it contains work that must be preserved, inspect and merge the histories deliberately.

### Authentication fails

Use GitHub CLI authentication or the system credential manager:

```powershell
gh auth login
gh auth status
```

Do not embed tokens in a remote URL.

### Push protection blocks the fixture

Read the alert and compare the path and value with the known synthetic redaction fixture. Bypass only the verified fake test value with an explanatory reason. If the value is not the known fixture, treat it as a real incident and rotate it before proceeding.

### A secret was staged but not committed

Remove the file from the staged set, fix the source or `.gitignore`, then review the staged diff again. Do not continue merely because the remote is still empty.

## 15. Completion checklist

Repository setup is complete only when:

- [ ] the repository is owned by the intended account and has the exact description;
- [ ] visibility and licensing are deliberate;
- [ ] `main` contains the reviewed local baseline;
- [ ] the README and documentation links render on GitHub;
- [ ] the recommended topics are applied;
- [ ] no real secret or private artifact is published;
- [ ] Issues are enabled and the Sprint 1 milestone exists;
- [ ] the four spikes and `US-01` through `US-07` are represented as traceable issues;
- [ ] the `protect-main` ruleset is active without nonexistent required checks;
- [ ] local `main` tracks `origin/main`; and
- [ ] the contract suite passes from a clean checkout.

## Official references

- [Adding locally hosted code to GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [Classifying a repository with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [Available rules for repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

## Related notes

- [[Home]]
- [[MOCs/Delivery MOC]]
- [[inception/BACKLOG]]
- [[inception/FEASIBILITY_REPORT]]
- [[inception/PHASE_1_EXIT_REPORT]]
