# Durable & Background Systems

Four systems run beside main conversation loop.
Developer notes: `AGENTS.md`. User docs: `website/docs/user-guide/features/`.

### Delegation (`delegate_task`)

Spawn subagent with isolated context + terminal session.

- **Single:** `delegate_task(goal, context)`.
- **Batch:** `delegate_task(tasks=[{goal, ...}, ...])` runs children in
  parallel, capped by `delegation.max_concurrent_children` (default 3).
- **Background:** `delegate_task(background=true)` returns handle
  immediately; parent loop continues. Child result re-enters conversation
  as new turn when done.
- **Roles:** `leaf` (default; cannot re-delegate) vs `orchestrator`
  (spawns own workers, bounded by `delegation.max_spawn_depth`).
- **Not durable.** Backgrounded child is process-local; lost if parent
  process exits. Work that must outlive process: use `cronjob` or
  `terminal(background=True, notify_on_complete=True)`.

Config: `delegation.*` in `config.yaml`.

### Cron (scheduled jobs)

Durable scheduler: `cron/jobs.py` + `cron/scheduler.py`. Drive via
`cronjob` tool, `hermes cron` CLI (`list`, `add`, `edit`, `pause`,
`resume`, `run`, `remove`), or `/cron` slash command.

- **Schedules:** duration (`"30m"`, `"2h"`), "every" phrase
  (`"every monday 9am"`), 5-field cron (`"0 9 * * *"`), or ISO timestamp.
- **Per-job knobs:** `skills`, `model`/`provider` override, `script`
  (pre-run data collection; `no_agent=True` makes script whole job),
  `context_from` (chain job A output into job B), `workdir` (run in dir
  with its `AGENTS.md` / `CLAUDE.md` loaded), multi-platform delivery.
- **Invariants:** 3-minute hard interrupt per run. `.tick.lock` file
  stops duplicate ticks across processes. Cron sessions pass
  `skip_memory=True` by default. Deliveries framed with header/footer,
  not mirrored into target gateway session (keeps role alternation intact).

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (skill lifecycle)

Background maintenance for agent-created skills: tracks usage, marks idle
skills stale, archives stale ones. Pre-run tar.gz backup, so nothing lost.

- **CLI:** `hermes curator <verb>`: `status`, `usage`, `run`, `pause`,
  `resume`, `pin`, `unpin`, `archive`, `restore`, `list-archived`, `prune`,
  `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` mirrors CLI.
- **Scope:** only skills with `created_by: "agent"` provenance. Bundled +
  hub-installed skills off-limits. **Never deletes**; most destructive
  action is archive. Pinned skills exempt from every auto-transition and
  every LLM review pass.
- **Cost:** deterministic inactivity/prune sweep is free. Aux-model
  "consolidate overlapping skills into umbrellas" pass **off by default**;
  opt in with `curator.consolidate: true` or
  `hermes curator run --consolidate`. Routine background curation: zero
  tokens.
- **Telemetry:** sidecar `~/.hermes/skills/.usage.json` holds per-skill
  `use_count`, `view_count`, `patch_count`, `last_activity_at`, `state`,
  `pinned`.

Config: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (multi-agent work queue)

Durable SQLite board for multi-profile / multi-worker collaboration. Users
drive via `hermes kanban <verb>`. Dispatcher-spawned workers get focused
`kanban_*` toolset gated by `HERMES_KANBAN_TASK`. Orchestrator profiles can
opt into broader `kanban` toolset. Normal sessions: zero `kanban_*` schema
footprint unless configured.

- **CLI verbs (common):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Less common: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Worker/orchestrator toolset:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`. Profiles explicitly enabling `kanban` toolset outside a
  dispatcher-spawned task also get `kanban_list` and `kanban_unblock` for
  board routing.
- **Dispatcher** runs inside gateway by default
  (`kanban.dispatch_in_gateway: true`). Reclaims stale claims, promotes
  ready tasks, claims atomically, spawns assigned profiles. Auto-blocks
  task after `failure_limit` consecutive spawn failures (default 2; set via
  `kanban.failure_limit` or per-task `max_retries`).
- **Isolation:** board is hard boundary (workers get `HERMES_KANBAN_BOARD`
  pinned in env). Tenant is soft namespace inside board, isolating
  workspace path + memory keys.

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
