# Historical Scala library skills

This is a durable research project, not a generated list of generic Scala tips.
The acceptance contract is [CONTRACT.md](CONTRACT.md). The historical window is
2018-01-01 through 2024-12-31 UTC; that date range does not prove human-only
contribution. No current code is silently substituted for historical evidence.

## Deliverable and gates

Target: at least 36 distinct, source-backed skills complementing the existing
Scala portfolio, covering development, review, refactoring and hardening.
Required core: ZIO, zio-kafka, zio-http, Cats, Cats Effect, http4s, FS2 and Play.
Discovery enumerates Li Haoyi's personal and organization repositories, records
aliases/exclusions, and includes the historical Scala library/tooling portfolio.
[scope.json](scope.json) preserves the initial public discovery snapshot, including
uncertain candidates and explicit exclusions; live scheduling uses state/inventory.json.
Every included repository must have an outcome; thin evidence is a blocker, not
permission to pad the catalog.

The pipeline has separate gates:

1. Paginated repository inventory and cached historical source/PR collection.
2. One researcher per repository, inspecting code organization, tests, changed
   code and substantive review exchanges, with version/platform distinctions.
3. Structural citation/schema/skill validation. For a new candidate, discussion
   evidence citing a PR in the cached corpus must also quote the cached body
   (whitespace-normalized, `...` allowed between fragments) and match its
   timestamp, author and historical eligibility. Evidence outside the cached sample
   is checked only by the reviewer. This is not semantic proof.
4. Independent source audit and concrete positive, negative, repair and held-out
   case evaluation for every candidate. Model-based evaluation is labeled as
   such; upstream Scala builds are not executed by this research pipeline.
5. Cross-repository deduplication against both new and existing skills, inventory
   completeness review, and coverage of all required ecosystems/categories.
6. Exclusive deterministic promotion of accepted skills, preserving existing
   catalog entries, with generated catalog/installer refresh and both `make test`
   and `make check`. No commits, pushes, or global installation.

The static catalog review script is not used as a substitute for steps 3–5.
Original skill prose is MIT-licensed. Short source quotations retain attribution;
raw upstream source and conversations are not copied into the public catalog.

## State, budgets, and execution

Run commands from the dot-agents checkout. Default state is outside the checkout:

    ~/.local/share/dot-agents/scala-history-2018-2024

It contains `inventory.json`, `corpus/`, API caches, `candidates/`, `reviews/`,
`reviews/evaluations/`, `feedback/`, `jobs/`, `prompts/`, `logs/`, `events.jsonl`, and final
`portfolio*.json`/`promotion.json`. It is not a temporary directory. Each source
and result is persisted before the next phase. Never commit this raw state.

Start or resume the full batch (identical command):

    python3 -m scripts.scala_research.supervisor run --workers 6 --per-year 6 --attempts 3 --job-seconds 2700 --hours 48 --max-turns 100 --provider openai-codex --model gpt-6-astra-900k --promote

That means six concurrent repository pipelines, at most three corpus collectors
at once, up to three author/reviewer repair rounds per repository, 100 tool turns
and 45 minutes per agent invocation, and a 48-hour supervisor ceiling. Collector
calls have their own bounded retries/timeouts. These are ceilings, not estimated
completion times or cost guarantees. Subscription limits can block work.

`--per-year` controls a transparent sample, not exhaustive PR history. Workers
must supplement dependency-noise samples and document remaining sampling bias.
The collector preserves search totals and truncation/gap indicators. An additive
activity sample checks pre-cutoff-created open and later-closed PRs (six candidates
per stratum, two search pages each). Only actual in-window comments/commits qualify;
current diffs are contextual-only, never adopted historical implementation.
Authors and reviewers inspect both `pulls` and `activity_pulls`.

Provider exhaustion stops
every sibling, marks in-flight jobs `interrupted` without consuming repair
attempts, skips the portfolio review and exits 75 (EX_TEMPFAIL). It is detected
only from structured failure lines in a failed worker's own log segment: the
`scala-research: provider-exhausted` marker printed by `library_worker.py`, or a
Hermes one-shot `hermes -z: agent failed:` line naming a quota/credit failure.
Agent output that merely quotes such text does not pause the run. Verified
evidence-blocked author outcomes are reused; attempt-exhausted jobs rerun.
Resume with the same command, or pin another preflighted `--provider/--model`;
accepted checkpoints record the model that authored and reviewed them.

`--deepen` (requires explicit `--repo` selections) re-researches already accepted
repositories for additional distinct skills using `deepen-addendum.txt`. The
accepted package (candidate, review, evaluation, job) is snapshotted first; any
rejection, author-reported `blocked` outcome, failure, cancellation or provider
pause restores it byte-for-byte and re-verifies acceptance, archiving the attempt
under `deepen-attempts/` for the next pass. An unclean exit is recovered on the
next start before any new work, for every repository with an active deepen record,
not only the scheduled ones. Use a
larger `--per-year` to widen the corpus. A cancelled worker is recorded as
interrupted, never as a spent repair attempt.

Consolidation: `python3 -m scripts.scala_research.supervisor consolidate` (or
`run ... --consolidate`) integrates every verified accepted skill into
`collections/shared/` with a MIT LICENSE, a `collections/hermes/` symlink, a catalog
entry and an owned `docs/skill-review.json` row. It records provenance in
`promoted-skills.json`, regenerates `KNOWLEDGE.md` and the routing table of the
`scala-oss-library-review` hub skill, then runs catalog/test/check gates. Shared
files are re-checked before every gate; a change by anyone else stops the run. On
failure, rollback restores a file or skill directory only if it still holds the
bytes this run wrote. Anything edited concurrently is left as it is and listed
in `rollback_conflicts` in `consolidation.json` (the backup under
`integration-backup/` is kept), and the command fails naming those paths. Gate
commands run in their own process group, and a timeout kills the whole group.
The integration lock lives in the git common directory, so worktrees of one
checkout serialize. A deepening repository contributes its
verified pre-deepen snapshot until the deeper package is accepted. Promoted skills
edited by hand after promotion, and same-ID skills not promoted by this pipeline,
are never overwritten. A newer acceptance of a skill whose ledger row has
`merged_into` is never applied automatically. It is skipped, listed under
`merged_needs_manual_fold` in the result and `consolidation.json`, and every other
skill is still integrated. `consolidate` then exits 2 (`run --consolidate` exits 3)
until someone folds the change into the merged skill by hand and updates that
row's `source_tree_sha256`. Unrelated review rows are left untouched (the global
`refresh_review.py` is not used, here or by `--promote`: it would mark every
changed skill in the catalog, including unrelated in-progress ones, as needing
review). `KNOWLEDGE.md` repository outcomes never include local paths or raw
exception text. This integration is incremental; the 36-skill portfolio gate
still governs `--promote`.
On resume,
authors reuse their existing dossiers and the portfolio reviewer's named gaps
instead of repeating broad research. `research-baseline/` preserves the original
research handoff; reports and claims there are not accepted skill artifacts.

Use an independently managed persistent process (for example a user-authorized
Hermes terminal job with `background=true`, `persist_on_release=true`) to survive
chat cleanup. A foreground shell command alone is not a service. Checkpoints
survive reboot; live processes do not. No system service or scheduled task is
installed, and this CLI does not deliver completion messages to a closed chat.

Status and stop:

    python3 -m scripts.scala_research.supervisor status
    python3 -m scripts.scala_research.supervisor stop

Status counts are computed from persisted job records. `accepted` means both
candidate and peer review passed, not yet catalog promotion. Only
`promotion: passed` means repository integration gates passed. Inspect the
relevant `feedback/`, `reviews/`, and logs when a job is blocked. Resume rechecks
accepted artifact hashes/validation and reruns incomplete jobs. Do not manually
flip statuses to accepted.

A single-repository pilot (never auto-promotes a partial portfolio):

    python3 -m scripts.scala_research.supervisor --state "$HOME/.local/share/dot-agents/scala-history-pilot-run" run --repo com-lihaoyi/geny --workers 1 --per-year 1 --attempts 1 --hours 2

Deterministic source collection without model calls:

    python3 -m scripts.scala_research.collector --state "$HOME/.local/share/dot-agents/scala-history-2018-2024" discover
    python3 -m scripts.scala_research.collector --state "$HOME/.local/share/dot-agents/scala-history-2018-2024" collect zio/zio --per-year 6

## Safety and recovery

Linux cgroup v2, pidfds and a reachable systemd user manager are required (the
offline unit tests skip the Linux-only process backend on other platforms). Each
worker runs in a uniquely named transient user service with independent runtime
and stop deadlines; no persistent service is installed. A launch whose
`systemd-run` died more than 60 seconds ago without its unit ever executing is
treated as never started, instead of blocking `run`, `status` and `stop` forever.

Independent Hermes workers use explicitly pinned model/provider and limited
terminal/file/skills toolsets, not recursive process-local delegation. Authors use
the documented `AIAgent` Python API through `library_worker.py`; read-only reviewers
use one-shot CLI sessions. One-shot mode explicitly prohibits skill creation, so
it is unsuitable for authors even when ordinary file writes succeed. The adapter
refuses an inherited one-shot context and never disables or overrides its guard.
A full run must first produce an independently accepted pilot skill package;
blocked authoring stops fanout. Blocked portfolios/scoped runs exit nonzero.
Approval protections stay on.

Agents read untrusted upstream text (PR bodies, comments, source) and have the
`terminal`, `file` and `skills` toolsets. Each agent unit requests systemd
sandboxing: `ProtectSystem=strict`, `ProtectHome=read-only`, `PrivateTmp=yes` and
`NoNewPrivileges=yes`. It may write only to its own scope: the author's
candidate directory and `receipts/`, the reviewer's `reviews/` tree, or the
portfolio reviewer's state root with every research artifact read-only. It may
also write to `processes/` and the Hermes home, with the Hermes `skills/`,
`config.yaml`, `hermes-agent/`, `plugins/`, `hooks/` and `memories/` read-only,
so `skill_manage` cannot plant global skills that a later reviewer loads. The
checkout and `jobs/` are not writable. `~/.config/gh`, `~/.ssh`, `~/.gnupg`,
`~/.git-credentials` and `~/.netrc` are hidden, and no GitHub token is passed
through the environment.

Residual risk, stated plainly:

- Some user managers silently ignore these properties. This happens when they
  cannot create mount namespaces, for example on Ubuntu with
  `kernel.apparmor_restrict_unprivileged_userns=1`, and the development host
  behaves this way. `run` probes enforcement, records `sandbox_enforced` in
  `supervisor.json` and emits a `sandbox_unenforced` event. Without enforcement,
  the write limits above are prompt policy only. Use `run --require-sandbox` to
  refuse to run in that case.
- Even when enforced, authors and reviewers share one writable Hermes home
  (sessions, state, `auth.json` and its token refreshes). A per-job `HERMES_HOME`
  would need copies of provider credentials, so it is not done. Agents can read
  provider credentials and have network access.
- A reviewer can write any file under `reviews/`, including another repository's
  review. Acceptance re-checks review hashes, so this invalidates that acceptance
  (fails closed) rather than forging one.
- Collector and inventory units are not sandboxed; they run no model.

Don't run research on a host where these limits matter without
`--require-sandbox`.

A file lock rejects concurrent supervisors. Process records bind unique units,
boot identity, invocation ID, cgroup and wrapper PID/start ticks. Durable launch
and cancellation gates prevent a delayed start after cancellation. Resume refuses
live or unverifiable orphan workers. Stop verifies entire cgroups, including
TERM-ignoring descendants that change sessions; inspect status before resuming. An
interrupted worker's partial files remain as research checkpoints, never accepted
results. No polling loop is needed: blocking subprocess waits and completion
futures drive the next phase.

Promotion uses an exclusive integration lock, records backups of the current
shared catalog/generated files, refuses existing destination IDs, writes owned
review rows only, and detects shared file changes before writing the catalog and
before every gate. This lock coordinates this pipeline, not unrelated editors.
Avoid simultaneous manual catalog edits during promotion. `--promote` does not
roll back. If promotion fails or is interrupted after copying files, reconcile
its `promotion.json`, `logs/integration-*.log` and `integration-backup/` before
retrying. It fails closed rather than overwriting someone else's changes.
Consolidation's rollback, described above, likewise never overwrites a
concurrent edit.
Do not delete unrelated skill directories or restore the entire dirty tree.

## Verification

    python3 -m unittest discover -s tests -p 'test_scala_research_*.py' -v
    make test
    make check

Offline unit tests use explicitly synthetic fixtures for failure, date, path,
cache, pagination, lock, identity, timeout, integrity and acceptance behavior.
They are not historical research evidence. Live GitHub collection, an actual
Hermes file-tool preflight, candidate source audits and behavioral evaluation
artifacts must be reported separately.
