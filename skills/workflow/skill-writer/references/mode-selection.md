# Mode Selection

Read this file first. Pick smallest path that satisfies user's request.

## Skill classes

- `workflow-process`: repeatable multi-step work where sequencing, checkpoints, and outputs matter.
- `integration-documentation`: using a specific API, CLI, SDK, file format, or platform.
- `security-review`: finding, validating, or fixing safety and security issues.
- `skill-authoring`: creating or improving skills, generators, templates, or skill documentation.
- `generic`: broad guidance where no specialized pattern fits.

## Operation modes

- `create`: new skill folder or new supporting files.
- `update`: revise existing skill without changing its core purpose.
- `synthesize`: build skill from external docs, local files, examples, or multiple sources.
- `iterate`: improve skill from observed outcomes, user feedback, traces, or examples.

## Required paths

| Mode | Read next |
|------|-----------|
| `create` | `authoring-path.md`, then `description-optimization.md` |
| `update` | `authoring-path.md`, then `registration-validation.md` |
| `synthesize` | `synthesis-path.md`, then `authoring-path.md` |
| `iterate` | `iteration-path.md`, then `authoring-path.md` |

For hybrid work, run paths in this order: `synthesize`, `iterate`, `authoring`, `evaluation`, `registration`.

## Depth decision

- Use lightweight pass for small copy, metadata, or reference repairs.
- Use full synthesis pass when skill depends on external behavior, tools, safety rules, or examples.
- Ask one concise clarification only when target audience, tool surface, or safety boundary is unknown and cannot be inferred.
