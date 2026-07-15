---
title: SkillProof Documentation Vault
aliases:
  - Documentation Vault
type: guide
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - skillproof
  - documentation
  - obsidian
---

# SkillProof Documentation Vault

This folder is both the project documentation tree and an Obsidian vault. It uses ordinary UTF-8 Markdown, standard YAML properties, Markdown links, and Obsidian wikilinks without requiring community plugins.

## Open the vault

1. In Obsidian, choose **Open folder as vault**.
2. Select this `docs` directory, not the project root.
3. Open [[Home]].
4. Read [[OBSIDIAN_GUIDE]] before creating or moving notes.

## Browse without Obsidian

- [Documentation home](Home.md)
- [Project map](MOCs/Project%20MOC.md)
- [Inception baseline](inception/README.md)
- [Architecture decisions](adr/README.md)
- [GitHub repository setup](guides/GitHub%20Repository%20Setup.md)
- [Documentation conventions](OBSIDIAN_GUIDE.md)

## Quality gate

Run from the project root:

```powershell
python -B -m unittest discover -s tests\contract -p "test_*.py" -v
```

## Related notes

- [[Home]]
- [[MOCs/Project MOC]]
- [[inception/PHASE_1_EXIT_REPORT]]
