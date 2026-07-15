---
title: SkillProof Obsidian Documentation Guide
type: guide
status: active
phase: project
owner: solo-developer
created: 2026-07-15
updated: 2026-07-15
tags:
  - documentation
  - obsidian
  - guide
aliases:
  - Obsidian guide
---

# SkillProof Obsidian documentation guide

The docs directory is a self-contained Obsidian vault and remains readable in GitHub, editors, and ordinary Markdown tooling. The shared setup uses only Obsidian core plugins; no community plugin is required.

## Open the vault

1. Install and start Obsidian.
2. Select **Open folder as vault**.
3. Choose the repository's docs directory, not the repository root.
4. If prompted, trust the vault and enable its configured core plugins.
5. Open this guide, the [inception index](inception/README.md), or the [journal](journal/README.md).

Obsidian reads the committed settings from .obsidian. Personal workspace state, such as open panes and recent files, is not part of the documentation contract.

## Vault layout

| Path | Purpose |
| --- | --- |
| .obsidian | Portable vault settings and core-plugin configuration |
| templates | Reusable project note templates |
| assets/attachments | Images and other note attachments |
| journal | Daily engineering notes |
| guides | Operational and project setup runbooks |
| inception | Product, requirements, risk, and delivery baselines |
| adr | Architecture decision records |

Keep production source code outside this vault. Documentation may link to source files, but the docs directory remains the documentation root.

## Note conventions

- Give each durable topic its own note and use a single level-one heading that matches its title.
- Preserve canonical IDs such as ADR-001, FR-001, RSK-001, and SPK-001 in filenames and headings when an artifact has an identifier.
- Use YAML properties at the beginning of structured notes.
- Use the plural properties tags and aliases. Both properties are YAML lists, even when they contain one value.
- Use lowercase, hyphenated tags such as technical-spike.
- Use ISO dates in YYYY-MM-DD format. Template timestamps use YYYY-MM-DD HH:mm in local time.
- Keep status values concise and consistent, for example proposed, planned, active, accepted, superseded, completed, or closed.
- Replace all template placeholders, sample IDs, owners, links, and acceptance criteria before treating a note as approved.
- Link to source evidence and related decisions instead of copying information into multiple notes.

Example properties:

~~~yaml
---
title: Example note
status: draft
tags:
  - requirement
aliases:
  - Example requirement
---
~~~

## Links

Use standard Markdown links by default so durable notes remain portable in GitHub, editors, and documentation tooling. Paths are relative to the note containing the link.

~~~markdown
[Evidence contract](inception/EVIDENCE_CONTRACT.md)
[Architecture decision](adr/ADR-001-fastapi-react-separation.md)
~~~

Curated navigation notes—`Home`, maps of content, indexes, and `Related notes` sections—may use Obsidian wikilinks because Obsidian supports both formats and uses wikilinks naturally for backlinks and graph navigation:

~~~markdown
[[MOCs/Engineering MOC|Engineering map]]
[[inception/EVIDENCE_CONTRACT|Evidence contract]]
~~~

Do not rely on block references, transclusion, or other Obsidian-only behavior for an authoritative requirement, decision, or contract. The note body must still make sense in a standard Markdown reader.

The vault is configured to create relative Markdown links and update links when files are renamed or moved inside Obsidian. A move performed outside Obsidian may require manual link repair. Encode spaces as %20 when writing a link manually.

Use descriptive link labels. Avoid bare filenames when the reader benefits from knowing why the target matters.

## Properties

Templates provide a small common property set and add artifact-specific fields.

| Property | Meaning |
| --- | --- |
| title | Human-readable note title |
| type | Stable artifact category such as `requirement`, `adr`, `risk`, or `moc` |
| phase | Project phase that owns the note, or `project` for cross-phase material |
| created | Local creation date and time |
| updated | Local date and time of the latest material update |
| status | Current lifecycle state |
| owner | Person accountable for the artifact |
| tags | Search and graph categories |
| aliases | Alternative names used to find the note |
| artifact-specific ID | Stable `adr_id`, `decision_id`, `requirement_id`, `risk_id`, `spike_id`, or `sprint_id` |

Properties support navigation and filtering, but the note body remains the authoritative, portable content.

## Attachments

New attachments are stored in assets/attachments. Use meaningful, lowercase filenames and add context in the note that embeds or links them.

~~~markdown
![Architecture diagram](assets/attachments/architecture-diagram.png)
[Feasibility data](assets/attachments/github-api-results.csv)
~~~

From a nested note, let Obsidian generate the correct relative path. Do not place secrets, credentials, private repository content, or personal data in attachments.

## Templates

Create or open the destination note, give it the intended filename, then run **Templates: Insert template** from the command palette. The core Templates plugin expands:

- {{title}} from the destination note title.
- {{date}} using YYYY-MM-DD.
- {{time}} using HH:mm.

The available templates are:

| Template | Use |
| --- | --- |
| General Note | Research, explanations, and durable project context |
| ADR | Architecture decisions and their consequences |
| Decision | Product, process, or implementation decisions that are not ADRs |
| Requirement | Testable functional and non-functional requirements |
| Risk | Risk assessment, mitigation, detection, and response |
| Technical Spike | Time-boxed feasibility investigation |
| Sprint | Sprint goal, commitments, review, and retrospective |
| Meeting Note | Objectives, discussion, decisions, and actions |
| Daily Note | Daily priorities, progress, blockers, and review |

Template links use explicit placeholder paths. Replace them with valid relative links before the note is complete.

## Daily notes

Run **Daily notes: Open today's daily note** to create or open journal/YYYY-MM-DD.md from the Daily Note template. Use the journal for short-lived work context. Promote durable requirements, decisions, risks, and findings into dedicated notes and link them from the daily entry.

The daily-note configuration deliberately uses one note per calendar day and does not depend on locale-specific filenames.

## Enabled core plugins

The vault enables the core capabilities needed for project documentation:

- File Explorer, Quick Switcher, Search, Command Palette, and Bookmarks for navigation.
- Backlinks, Outgoing Links, Graph View, Tags, Properties, Page Preview, and Outline for discovery.
- Templates and Daily Notes for consistent note creation.
- Note Composer for extracting or merging durable material.
- Word Count and File Recovery for basic editing safety.

No community plugin is required. If a community plugin is evaluated later, record the need and portability impact in an ADR, and keep the Markdown useful when that plugin is absent.

## Maintenance checks

- Run the automated vault and contract gate from the project root:

  ```powershell
  python -B -m unittest discover -s tests\contract -p "test_*.py" -v
  ```

- Open moved or renamed notes and confirm their outgoing links.
- Keep templates aligned with approved artifact contracts.
- Store attachments only in assets/attachments.
- Keep daily-only context out of authoritative project artifacts.
- Review generated Obsidian settings before committing them; the root `.gitignore` excludes personal workspace state, caches, and community-plugin installations.

## Related notes

- [Inception artifacts](inception/README.md)
- [Evidence contract](inception/EVIDENCE_CONTRACT.md)
- [Daily journal](journal/README.md)
