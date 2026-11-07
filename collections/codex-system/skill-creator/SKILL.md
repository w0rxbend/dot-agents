---
name: skill-creator
description: Create or update a Codex skill with appropriately scoped instructions and any needed supporting resources.
metadata:
  short-description: Create or update a skill
---

# Skill Creator

## Core Principles

**Assume Codex is already capable.** Include only what changes its decisions or improves its work. Cut generic advice, repetition, speculative edge cases, and examples that do not materially clarify task.

**Preserve user intent and scope.** Support requested task. Do not replace user's chosen product, expand assignment, modify unrelated configuration, or imply permission for extra external actions. Do not turn one example, past failure, or personal preference into universal requirement.

Task approval does not expand scope or execution permissions. Retrying or externally mutating workflows need stopping condition proportional to risk.

**Match specificity to the risk.** Several reasonable approaches: let model choose. Use detailed steps, deterministic scripts, or absolute language only when correctness, safety, permissions, or truly fragile workflow requires them.

Open-ended work: describe outcome and decision criteria. Workflows with preferred shape: offer examples or configurable scripts. Fixed sequences and narrow parameters only where deviation causes concrete problem. Keep non-obvious operational invariants. Separate requirements from optional recommendations or local conventions. Avoid restating policies enforced elsewhere.

**Keep discovery cheap and precise.** Names and descriptions are visible before skill loads. Describe capability and when it applies. Add exclusions only to prevent likely misrouting. Avoid exhaustive capability lists and catchalls attracting unrelated requests.

Keep skills self-contained. Reference another skill or tool only when workflow requires it and target environment has it. Specialized review, hardening, or audit workflows apply when requested or needed, not merely because ordinary work touches same subject.

**Disclose detail progressively.** `SKILL.md` holds shared purpose, essential constraints, and routing. Substantial mode-specific guidance, schemas, examples, or procedures go in references; read only those relevant to current task. Simple self-contained skill needs no router or extra files.

## Anatomy of a Skill

Every skill is folder with required `SKILL.md` plus optional resources its workflow needs:

```text
skill-name/
|-- SKILL.md                 Required skill instructions
|   |-- YAML frontmatter     Required name and description
|   `-- Markdown body        Instructions loaded when the skill is used
|-- agents/                  Optional UI metadata and invocation policy
|   `-- openai.yaml
|-- scripts/                 Optional executable helpers
|-- references/              Optional documentation loaded as needed
`-- assets/                  Optional files used in generated output
```

Fit structure to task. Some skills are short and self-contained; others route among operating modes or delegate complex mechanics to scripts. Do not create directories, placeholders, examples, or ancillary documentation without clear use.

### SKILL.md

YAML frontmatter identifies skill and decides when it is considered. Include required `name` and `description`. Keep supported optional fields like existing `metadata` when appropriate.

Three disclosure stages:

1. **Name and description:** Seen during skill selection. Keep concise and discriminating.
2. **SKILL.md body:** Loaded when skill applies. Keep instructions relevant to that task.
3. **Supporting resources:** Read or run only when current task needs them.

Keep entrypoint as short as task permits without losing important constraints. Large upper bound is not a target. Move conditional detail into references when it improves clarity or context use; do not wait until file is unwieldy.

### Scripts

Use `scripts/` for code otherwise rewritten repeatedly, or where deterministic execution materially improves reliability.

- **Example:** `scripts/rotate_pdf.py` for PDF operation that would otherwise need same code recreated.
- **Useful for:** Repeated transformations, reliable API operations, data processing, other concrete automation.
- **Validation:** Run new or changed scripts to verify behavior. Scripts usually run without loading full implementation into context. Inspection may be needed when patching or adapting.

### References

Use `references/` for documentation needed only in particular contexts.

- **Examples:** `references/schema.md` for database tables, `references/policies.md` for domain rules, `references/api_docs.md` for an API, or separate writing guides for different deliverables.
- **Useful for:** Schemas, API documentation, company policies, format-specific procedures, detailed workflows, substantial examples.
- **Routing:** Link each reference from `SKILL.md` or other relevant resource, saying when to read it. Keep information in one place, not duplicated across entrypoint and references.

References hold maintained, task-specific information that changes agent decisions. Avoid copied manuals, exhaustive catalogs, and generic tutorials available from authoritative sources. Before removing existing resources, inspect their callers and purpose.

Large references: add search terms or short contents section if that helps find material.

### Assets

Use `assets/` for files belonging in generated output, not model instructions.

- **Examples:** `assets/logo.png`, `assets/slides.pptx`, `assets/font.ttf`, or `assets/frontend-template/`.
- **Useful for:** Templates, images, fonts, icons, boilerplate projects, other files copied or adapted into result.
- **Context:** Do not load assets as instructions unless task requires inspecting them.

### UI Metadata and Invocation Policy

`agents/openai.yaml` can hold UI-facing metadata (`display_name`, `short_description`, `default_prompt`) and invocation policy. When creating or updating these settings, read [references/openai_yaml.md](references/openai_yaml.md); keep values consistent with skill.

Automatic skill selection is allowed by default. Change that only when user explicitly requests explicit-only skill:

```yaml
policy:
  allow_implicit_invocation: false
```

Skill then works when explicitly invoked as `$skill-name` but is not added to model context automatically. When updating `agents/openai.yaml`, keep unrelated existing UI, policy, and dependency fields.

For new or interface-only metadata, generate it with:

```bash
scripts/generate_openai_yaml.py <path/to/skill-folder> --interface key=value
```

Generator replaces whole file. If existing file has `policy` or `dependencies`, edit only intended fields in place; do not regenerate.

Add optional interface fields only when user provides or requests them.

### What Not to Include

Avoid `README.md`, installation guide, changelog, duplicated quick reference, or other auxiliary documentation unless specific task or packaging requirement calls for it.

## Progressive Disclosure in Practice

Skill with multiple substantial modes: keep shared guidance and mode-selection criteria in `SKILL.md`, and link each reference where it becomes relevant.

Example: deployment skill keeps provider selection in `SKILL.md` and splits out provider details:

```text
cloud-deploy/
|-- SKILL.md
`-- references/
    |-- aws.md
    |-- gcp.md
    `-- azure.md
```

User picks AWS: read `references/aws.md`, do not also load GCP and Azure guides. Same pattern works for business domains, deliverable types, or other distinct operating modes.

Short skill can instead route to details only when advanced operation needs them:

```markdown
## Documents

Handle ordinary edits directly.

- For tracked changes, read [references/redlining.md](references/redlining.md).
- For document internals, read [references/ooxml.md](references/ooxml.md).
```

These examples show options, not required structure. Pick organization that keeps skill easy to use without loading irrelevant material.

## Create or Update a Skill

Adapt work to request. Complex new skill may mean understanding realistic use cases, choosing resources, initializing files, writing instructions, and validating result. Narrow update may need only focused edit and validation.

Ask clarifying questions only when missing information matters and cannot be reasonably inferred. Respect user-specified location; otherwise create discoverable skills in `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is unset.

If invocation mode is unclear and matters to workflow, ask: automatic discovery or explicit-only? Otherwise keep default. Do not infer explicit-only invocation from sensitive operations or required approvals. Keep skill discoverable; require authorization immediately before the mutation. Keep existing skill's invocation policy unless user asks to change it.

New or substantially revised skill: consider requests it should handle and which reusable resources would help; create them only when concrete benefit justifies them. If user already explained task clearly, proceed without asking for more examples.

### Naming

- Use lowercase letters, digits, and hyphens.
- Keep under 64 characters; prefer short action-oriented names.
- Namespace by tool or domain when that improves discovery.
- Name skill folder after skill.

### Initialize a New Skill

New skill: use bundled initializer when it helps create required files consistently:

```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

Example:

```bash
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills"
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills" --resources references
```

Request only needed resource directories. Use `--examples` only when concrete placeholders help; replace or remove them before finishing. Do not initialize existing skill again.

Initializer creates skill directory, concise `SKILL.md` starter, and `agents/openai.yaml`. It creates resource directories and example files only on request. Pass generated UI values as `--interface key=value` when needed.

### Write the Instructions

Frontmatter `description`: briefly state what skill does and when it applies. Add meaningful boundary when similar requests should not activate it.

Example:

```yaml
description: Create or edit Word documents when formatting, tracked changes, or comments require document-specific handling.
```

Detailed workflows, tool choices, examples, and operating modes go in body or references, not description.

Write only instructions another Codex instance needs to do task well: desired outcome, non-obvious context, real constraints, relevant references or tools. Keep user's explicit choices and existing authorization boundaries. Do not prescribe fixed structure, process, or number of steps unless task requires one.

### Validate and Iterate

Validate completed skill with:

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

Validator checks frontmatter, naming, and unfinished scaffold placeholders; it does not prove skill makes good decisions. Also check descriptions stay discriminating, instructions preserve user intent, references are discoverable, and added scripts work.

When testing is warranted, verify observable behavior or meaningful invariants. Avoid tests that merely match generated wording, headings, or regex patterns.

Improve skill from real usage or demonstrated failures. Prefer narrow correction over accumulating universal rules for every observed example.

## Independent Forward-Testing

Use independent subagent pass when skill is complex or risky enough for realistic behavioral validation to add real confidence, and delegation is available and authorized. Ordinary creation or small edits do not automatically need subagents.

Give evaluating agent realistic user request, skill, and minimum raw artifacts for task. Do not provide intended answer, suspected bug, proposed fix, or prior conclusions unless evaluation requires them.

Example:

```text
Use $skill-name at /path/to/skill-name to complete this realistic request.
```

Scope evaluation to permitted resources and side effects. Use isolated temporary workspace for generated artifacts so they do not enter working tree or contaminate later evaluations. Ask for approval when evaluation would need extra authorization, affect live production system, or impose substantial time or cost. Review actual outcome and artifacts; change only what observed behavior supports.
