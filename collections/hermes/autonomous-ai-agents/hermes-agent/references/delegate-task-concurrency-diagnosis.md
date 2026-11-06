# delegate_task: diagnosing "my batch was capped"

User reports `delegate_task` ran fewer subagents than asked (e.g. "I set
max_concurrent_children: 15 but only 9 ran")? Exactly **three** Hermes
code paths cap a batch. If none fired, **model itself** capped it, not
Hermes.

## The three real caps in Hermes

All resolve through `tools.delegate_tool._get_max_concurrent_children()`.
Reads `delegation.max_concurrent_children` from `config.yaml` (env fallback
`DELEGATION_MAX_CONCURRENT_CHILDREN`, default 3). Floor of 1.
**No hard ceiling.**

1. **Per-call hard reject**: `tools/delegate_tool.py` (~line 1953).
   If `len(tasks) > max_children`, call returns `tool_error` with
   exact message: `"Too many tasks: {N} provided, but
   max_concurrent_children is {M}. ..."` Model sees failed tool call,
   usually retries with fewer tasks.

2. **Per-turn truncator**: `run_agent.py::AIAgent._cap_delegate_task_calls`
   (~line 5708). If model emits *multiple separate* `delegate_task`
   tool_calls in one assistant turn, count of those calls truncated to
   `max_children`. Logs at WARNING:
   `Truncated N excess delegate_task call(s) to enforce
   max_concurrent_children=M limit`.

3. **Cost-warning**: same `_get_max_concurrent_children()`. When resolved
   value is `> 10`, logs once at WARNING:
   `delegation.max_concurrent_children=N: each child consumes API tokens
   independently. High values multiply cost linearly.` **Only a log
   line**; caps nothing. Easy to mis-read as "Hermes is refusing my value."

## Diagnostic recipe

User says "delegate is capped at N":

```bash
# 1. What does the loaded config actually say?
hermes config get delegation.max_concurrent_children

# 2. Did Hermes' truncator or rejector actually fire?
grep -E "Truncated.*delegate_task|Too many tasks" ~/.hermes/logs/agent.log | tail
# If neither line appears, neither cap path executed.

# 3. Confirm the resolver returns what config says (in venv with hermes on path)
python -c "from tools.delegate_tool import _get_max_concurrent_children; \
           print(_get_max_concurrent_children())"
```

Config and `_get_max_concurrent_children()` agree, and neither log line
appears? **The cap is the model**, not Hermes.

## Why models self-limit batches

Reasoning models (Claude Opus/Sonnet, GPT-5, Grok-4) routinely trim 13- or
15-task batch to "rounder" number (5, 8, 9, 10) when they judge
coordination cost outweighs parallelism. Startup cost-warning log line
*reinforces* this: model sees "each child consumes API tokens
independently" in own reasoning trace, decides smaller batch is "more
responsible."

Model then claims "the runtime caps at 9" or "despite the config saying
15, max parallel is 9," which is **not true**: post-hoc rationalisation.
Fine to call out to user.

## How to actually force N parallel children

Tell model explicitly in prompt:

> "Send all 13 tasks in **one** `delegate_task` call with a `tasks` array
> of 13 items. Do not split into multiple calls. The runtime supports
> this; `delegation.max_concurrent_children` is set to 15."

Model still trims? Build `tasks` list deterministically with
`execute_code`, call tool with that exact list. Model becomes courier, far
less likely to second-guess count. Or switch model: smaller /
less-reasoning-heavy models trim less aggressively in practice.

## Pitfalls / gotchas

- **`max_concurrent_children` is a per-parent cap, not a global cap.**
  Confirmed in `ui-tui/src/components/appChrome.tsx`. Two different
  parents can each spawn `max_children` workers concurrently.
- **`subagent_auto_approve: false` does not cap concurrency.** Only
  controls whether children inherit yolo / approval bypass. Not a throttle.
- **The cost-warning log fires on every call** when value > 10. Presence
  is not evidence of capping. Only `Truncated...` and `Too many tasks`
  lines indicate actual capping.
- **Don't suggest reverting `max_concurrent_children` to fix this.** User
  set it deliberately. Push back on model, not config.
