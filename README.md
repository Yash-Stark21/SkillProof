# SkillProof

SkillProof is a greenfield Python/FastAPI and React/TypeScript product for turning public repository implementation evidence into defensible skill matches and evidence-backed career claims.

> No evidence, no claim.

## Documentation

The project documentation is an Obsidian-compatible vault rooted at [`docs/`](docs/README.md).

- Open the `docs` directory as a vault in Obsidian.
- Start at [`Home.md`](docs/Home.md).
- Read the [`Obsidian guide`](docs/OBSIDIAN_GUIDE.md) for conventions and workflows.
- Review the [`Phase 1 exit report`](docs/inception/PHASE_1_EXIT_REPORT.md) and [`Sprint 1 backlog`](docs/inception/BACKLOG.md).
- Follow the [`GitHub repository setup guide`](docs/guides/GitHub%20Repository%20Setup.md) to publish and govern the project.

The vault remains ordinary UTF-8 Markdown and works without community plugins.

## Current status

Phase 1 inception is complete with a controlled **GO to Sprint 1**. Production application code has not started. The next approved activity is the bounded GitHub inventory spike followed by `US-01`.

## Validate the documentation baseline

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

This command verifies the evidence corpus, documentation contracts, links, metadata, and decision consistency.
