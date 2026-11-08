# Registration And Validation

Use after skill edits.

## Repository checks

Run checks repository defines (README, justfile or Makefile, CI workflow). Do not invent commands. In dot-agents repository, skill changes normally require:

```bash
just catalog   # regenerate docs/catalog.md from catalog.json
just check     # validate snapshot checksums/metadata, test installer, verify rendered config
```

New or retired skill there also needs its `catalog.json` entry (id, source, license, path) added or removed so `./install.sh` renders it.

Use stricter or specialized checks when changed skill includes risky commands, external references, generated artifacts, or package/runtime behavior.

## Artifact checks

Confirm:

- `SKILL.md` frontmatter parses.
- Referenced files exist.
- Generated registry files synced when repository owns them on `main`.
- Credits and provenance present when external sources used.
- Final response reports validation honestly.

## Reject conditions

Do not mark work complete if:

- Required references are missing.
- Skill cannot be followed without hidden context.
- Risky instruction lacks prerequisites.
- Validation failed and user has not explicitly accepted the failure.
