# Registration And Validation

Use this path after skill edits.

## Repository checks

Run the checks the repository defines (README, Makefile, CI workflow). Do not invent commands. In the dot-agents repository, skill changes normally require:

```bash
python3 scripts/catalog.py   # regenerate docs/catalog.md from catalog.json
make check                   # validate snapshot checksums/metadata, test installer, verify rendered config
```

A new or retired skill there also needs its `catalog.json` entry (id, source, license, path) added or removed so `./install.sh` renders it.

Use stricter or specialized checks when the changed skill includes risky commands, external references, generated artifacts, or package/runtime behavior.

## Artifact checks

Confirm:

- `SKILL.md` frontmatter parses.
- Referenced files exist.
- Generated registry files are synced when the repository owns them on `main`.
- Credits and provenance are present when external sources are used.
- The final response reports validation honestly.

## Reject conditions

Do not mark the work complete if:

- Required references are missing.
- The skill cannot be followed without hidden context.
- A risky instruction lacks prerequisites.
- Validation failed and the failure is not explicitly accepted by the user.
