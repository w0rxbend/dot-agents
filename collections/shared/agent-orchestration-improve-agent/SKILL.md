---
name: agent-orchestration-improve-agent
description: "Improve an existing LLM agent or multi-agent workflow with a measured loop: baseline from traces, failure taxonomy, a frozen eval set, one change at a time, paired A/B comparison, staged rollout and rollback. Use when an agent that already runs is failing, too slow or too expensive and you can collect examples; use agent-observability to add tracing first and context-engineering for session context hygiene."
source: community
date_added: "2026-02-27"
---

# Improve an Existing Agent

Change an agent's prompt, tools, model or orchestration only against evidence, and only one variable per experiment. Every change must be comparable against a frozen baseline and reversible.

**Do not use** for designing a brand-new agent (no baseline exists yet), or when there are no traces, logs, user reports or example tasks to evaluate against. Collect those first.

## Procedure

### 1. Fix the target and gather evidence

Write down, before touching anything:
- the agent version under test (prompt file + commit, model id, tool set, parameters such as temperature);
- the outcome that matters (task success as judged how, by whom) and the guardrails (safety rules, latency, cost per task);
- the evidence sources: traces or logs (agent-observability), user corrections/retries/abandonments, bug reports, past eval results.

Pull 30-100 recent real tasks, deliberately including failures. If there is no tracing, add it first; without per-step inputs, tool calls, outputs, tokens and latency you cannot localize failures.

### 2. Classify failures

Read the failing traces and tag each with one primary cause:

| Cause | Typical signal | First fix to try |
|---|---|---|
| Instruction misunderstanding | Right tools, wrong goal | Restate the task contract and success criteria in the prompt |
| Missing or wrong context | Invented APIs/facts, ignores conventions | Load the right files/docs; trim irrelevant context |
| Tool misuse | Wrong tool, bad arguments, loops of retries | Sharpen tool names/descriptions/schemas; return actionable tool errors |
| Output format errors | Parser failures, missing fields | Structured output / schema validation with a repair step |
| Context loss in long runs | Quality drops late in the session | Summarize and hand off by reference (context-engineering) |
| Constraint violation | Unsafe or out-of-policy action | Hard check in code, not only prompt text |
| Capability limit | Fails even with perfect context | Decompose the task, add a tool, or use a stronger model for that step |

Rank causes by frequency x impact. Fix the top one first.

### 3. Build a frozen eval set

- 30-100 tasks for a first pass: common golden-path cases, every previously failed task (regressions), edge cases, and a few adversarial inputs.
- For each task, store the input, any fixtures/tool stubs, and a checkable expectation: exact answer, assertion script, rubric for an LLM or human grader, or "must not call tool X".
- Freeze it in version control next to the agent. Do not edit the set while comparing two versions; add new cases only between experiments.
- Prefer programmatic checks. When using an LLM judge, give it a rubric, have it judge one criterion at a time, and spot-check its verdicts against human labels before trusting it.

### 4. Measure the baseline

Run the current version on the full set. Because agents are nondeterministic, run each task several times (3-5) or at the production temperature and record per task: pass/fail, number of steps/tool calls, input and output tokens, wall-clock latency, cost, and any guardrail violation. Report the pass rate with its run-to-run spread; a difference smaller than that spread is noise.

### 5. Make one change

Typical changes, in rough order of cost:
1. Clarify the task contract: purpose, inputs, success criteria, what not to do.
2. Fix tool definitions: names, descriptions, argument schemas, error messages that tell the agent what to do next.
3. Add 1-3 worked examples drawn from real successes, plus the failure they prevent.
4. Add a verification step: the agent checks its output against the criteria (tests, schema, citation check) before returning.
5. Restructure the workflow: split a step, add a deterministic pre/post-processing step, or route a hard sub-step to a stronger model.

Keep the change in its own commit with a version bump (for example `support-agent v2.3.0 -> v2.4.0`) and a changelog line naming the failure class it targets.

### 6. Compare A vs B on the same tasks

Run the candidate on the identical frozen set with the same settings and repetitions.
- Compare per task (paired): count tasks B fixes, tasks B breaks, and unchanged. A change that fixes 8 and breaks 5 is not a clean win; read the 5.
- Check guardrails separately: no new safety or policy violations, latency and cost per task within the budget you set in step 1.
- For human review, blind the graders to which version produced which output.
- Accept B only if it improves the target metric beyond run-to-run noise, breaks no previously passing critical case, and stays within guardrails. Otherwise revert and try the next hypothesis.

### 7. Roll out and keep a rollback

- Ship behind a version switch (config flag, prompt version id, model routing rule) so the previous version can be restored without a redeploy.
- Stage it: internal users or a small traffic share first, then widen. Watch the same metrics as the eval, from production traces.
- Define rollback triggers up front, for example: success proxy (completion, user acceptance) below baseline beyond normal variation, any new safety violation, cost or latency over budget. On a trigger, switch back first, then investigate.
- Add every production failure that slipped through to the eval set.

## Multi-agent cost and latency

When the agent is a pipeline or a coordinator with subagents, profile the trace before restructuring:

| Symptom in traces | Change to test |
|---|---|
| Wall-clock dominated by sequential steps that do not depend on each other | Run independent subtasks in parallel; cap fan-out to stay within rate limits |
| Subagents re-read or re-derive the same material | Pass a shared artifact by path plus a short digest instead of full transcripts |
| Coordinator context grows with every subagent report | Keep full reports in files; coordinator holds digests only (see context-engineering) |
| Expensive model used for routine steps (classification, extraction, formatting) | Route those steps to a smaller model; keep the strong model for planning and hard reasoning; re-run the eval to confirm |
| Identical prompts or tool calls repeated across runs | Cache deterministic tool results; use the provider's prompt caching for long stable prefixes |
| Many agents for a task one agent handles well | Collapse the pipeline; extra hand-offs add latency, cost and information loss |

Measure end-to-end cost and latency per task, plus per-agent token share, before and after each change. A multi-agent change is accepted by the same A/B rule as any other change.

## Done when

- The baseline, the change, and the A/B results (fixed, broken, unchanged, guardrails, cost, latency) are recorded with the version ids
- The eval set includes every failure that motivated the change
- The new version is behind a switch with written rollback triggers, and the previous version can be restored in one step
