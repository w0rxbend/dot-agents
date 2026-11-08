# Design Principles

## Write for agent behavior

- Use imperative instructions telling agent what to do.
- Put trigger language in frontmatter description, not only in body.
- Keep SKILL.md a navigation layer when skill has many modes.
- Put optional depth, examples, rubrics, and tool-specific details in references.

## Keep the context budget healthy

- Prefer checklists, tables, and short decision rules over long essays.
- Do not duplicate a rule in SKILL.md and references unless it is a safety-critical reminder.
- Include only files agent may load during work.

## Balance depth and concision

- Add detail where mistakes are costly, repeated, or hard to detect.
- Compress detail where model already has general knowledge.
- Make every required artifact explicit: files, commands, reports, comments, commits, or validation outputs.

## Safety and provenance

- Clearly label risky, destructive, credential-handling, financial, medical, legal, or security guidance.
- Keep source provenance when adapting external content.
- Prefer safe commands and explicit prerequisites over remote execution shortcuts.
