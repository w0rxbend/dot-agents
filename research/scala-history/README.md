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
3. Structural citation/schema/skill validation. This is not semantic proof.
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

Provider exhaustion (quota/credit failure in a worker's own log segment) stops
every sibling, marks in-flight jobs `interrupted` without consuming repair
attempts, skips the portfolio review and exits 75 (EX_TEMPFAIL). Verified
evidence-blocked author outcomes are reused; attempt-exhausted jobs rerun.
Resume with the same command, or pin another preflighted `--provider/--model`;
accepted checkpoints record the model that authored and reviewed them.

`--deepen` (requires explicit `--repo` selections) re-researches already accepted
repositories for additional distinct skills using `deepen-addendum.txt`. The
accepted package (candidate, review, evaluation, job) is snapshotted first; any
rejection, failure, cancellation or provider pause restores it byte-for-byte and
re-verifies acceptance, archiving the attempt under `deepen-attempts/` for the next
pass. An unclean exit is recovered on the next start before any new work. Use a
larger `--per-year` to widen the corpus. A cancelled worker is recorded as
interrupted, never as a spent repair attempt.

Consolidation: `python3 -m scripts.scala_research.supervisor consolidate` (or
`run ... --consolidate`) integrates every verified accepted skill into
`collections/shared/` with a MIT LICENSE, a `collections/hermes/` symlink, a catalog
entry and an owned `docs/skill-review.json` row. It records provenance in
`promoted-skills.json`, regenerates `KNOWLEDGE.md` and the routing table of the
`scala-oss-library-review` hub skill, then runs catalog/test/check gates. Any
gate failure restores every touched file. A deepening repository contributes its
verified pre-deepen snapshot until the deeper package is accepted. Promoted skills
edited by hand after promotion, and same-ID skills not promoted by this pipeline,
are never overwritten. Unrelated review rows are left untouched (the global
`refresh_review.py` is not used because it diffs against git HEAD). This
integration is incremental; the 36-skill portfolio gate still governs `--promote`.
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

Linux cgroup v2, pidfds and a reachable systemd user manager are required. Each
worker runs in a uniquely named transient user service with independent runtime
and stop deadlines; no persistent service is installed.

Independent Hermes workers use explicitly pinned model/provider and limited
terminal/file/skills toolsets, not recursive process-local delegation. Authors use
the documented `AIAgent` Python API through `library_worker.py`; read-only reviewers
use one-shot CLI sessions. One-shot mode explicitly prohibits skill creation, so
it is unsuitable for authors even when ordinary file writes succeed. The adapter
refuses an inherited one-shot context and never disables or overrides its guard.
A full run must first produce an independently accepted pilot skill package;
blocked authoring stops fanout. Blocked portfolios/scoped runs exit nonzero. Their
prompts restrict writes to owned candidate/review areas, and source trees are
read-only research inputs. This is an orchestration ownership policy, not an OS
sandbox; don't run untrusted source instructions. Approval protections stay on.

A file lock rejects concurrent supervisors. Process records bind unique units,
boot identity, invocation ID, cgroup and wrapper PID/start ticks. Durable launch
and cancellation gates prevent a delayed start after cancellation. Resume refuses
live or unverifiable orphan workers. Stop verifies entire cgroups, including
TERM-ignoring descendants that change sessions; inspect status before resuming. An
interrupted worker's partial files remain as research checkpoints, never accepted
results. No polling loop is needed: blocking subprocess waits and completion
futures drive the next phase.

Promotion uses an exclusive integration lock, records backups of the current
shared catalog/generated files, refuses existing destination IDs, and detects
shared file changes before writing the catalog. This lock coordinates this
pipeline, not unrelated editors. Avoid simultaneous manual catalog edits during
promotion. If promotion is interrupted after copying files, reconcile its
`promotion.json`, `logs/integration-*.log` and `integration-backup/` before retrying; it
fails closed rather than overwriting or rolling back someone else's changes.
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
