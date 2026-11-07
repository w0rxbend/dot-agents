---
name: skill-writer
description: Create, update or evaluate a SKILL.md, including trigger-precise descriptions, focused references, and validation against the repository's checks. Use when asked to write a new skill, fix or extend an existing one, or tune when a skill triggers.
source: community
date_added: "2026-09-04"
---

# Skill Writer

Single canonical workflow for skill creation and improvement.
Primary success condition: maximize high-value input coverage before authoring, so resulting skill has minimal blind spots.

Load only path(s) task requires:

| Task | Read |
|------|------|
| Set skill class, required dimensions, workflow path and required outputs | `references/mode-selection.md` |
| Apply depth vs concision writing constraints | `references/design-principles.md` |
| Select skill structure pattern | `references/skill-patterns.md` |
| Select workflow orchestration pattern for process-heavy skills | `references/workflow-patterns.md` |
| Select output format pattern for deterministic quality | `references/output-patterns.md` |
| Load worked synthesis example (workflow-process skills) | `references/examples/workflow-process.md` |
| Synthesize external/local sources with depth gates | `references/synthesis-path.md` |
| Author or update SKILL.md and supporting files | `references/authoring-path.md` |
| Optimize skill description and trigger precision | `references/description-optimization.md` |
| Iterate using positive/negative/fix examples | `references/iteration-path.md` |
| Evaluate behavior, compare baseline vs with-skill (opt-in quantitative) | `references/evaluation-path.md` |
| Register and validate skill changes | `references/registration-validation.md` |

## Step 1: Resolve target and path

1. Resolve target skill path and intended operation (`create`, `update`, `synthesize`, `iterate`).
2. Read `references/mode-selection.md`; select required path(s).
3. Classify skill (`workflow-process`, `integration-documentation`, `security-review`, `skill-authoring`, `generic`).
4. If class or depth requirements are ambiguous, ask one direct question. Otherwise state explicit assumptions.

## Step 2: Run synthesis when needed

Read `references/synthesis-path.md`.

1. Collect and score relevant sources with provenance.
2. Apply trust and safety rules when ingesting external content.
3. Produce source-backed decisions and coverage/gap status.
4. For `workflow-process` skill, load `references/examples/workflow-process.md` as worked profile. For other classes, use two or three strong existing repository skills of that class as profile.
5. For skill-authoring skills, use Agent Skills specification plus two or three strong existing repository skills as baseline sources.
6. Enforce depth gates in `references/synthesis-path.md` before authoring.

## Step 3: Run iteration first when improving from outcomes/examples

When selected path includes `iteration` (for example operation `iterate`), read `references/iteration-path.md` first.

1. Capture and anonymize examples with provenance.
2. Re-evaluate skill behavior against working and holdout slices.
3. Propose improvements from positive/negative/fix evidence.
4. Carry concrete behavior deltas into authoring.

Skip this step when selected path does not include `iteration`.

## Step 4: Author or update skill artifacts

Read `references/authoring-path.md`.

1. Write or update `SKILL.md` in imperative voice with trigger-rich description.
2. Create focused reference files and scripts only when justified.
3. Follow `references/skill-patterns.md`, `references/workflow-patterns.md`, and
   `references/output-patterns.md` for structure and output determinism.
4. For authoring/generator skills, include transformed examples in references:
   - happy-path
   - secure/robust variant
   - anti-pattern + corrected version

## Step 5: Optimize description quality

Read `references/description-optimization.md`.

1. Validate should-trigger and should-not-trigger query sets.
2. Cut false positives and false negatives with targeted description edits.
3. Keep trigger language generic across Codex and Claude.

## Step 6: Evaluate outcomes

Read `references/evaluation-path.md`.

1. Run lightweight qualitative check by default (recommended).
2. For integration/documentation and skill-authoring skills, include concise depth rubric from `references/evaluation-path.md`.
3. Run deeper eval playbook and quantitative baseline-vs-with-skill only when requested or risk warrants.
4. Record outcomes and unresolved risks.

## Step 7: Register and validate

Read `references/registration-validation.md`.

1. Apply repository registration steps.
2. Run quick validation with strict depth gates.
3. Reject shallow outputs that fail depth gates or required artifact checks.

## Output format

Return:

1. `Summary`
2. `Changes Made`
3. `Validation Results`
4. `Open Gaps`
