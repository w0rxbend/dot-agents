# Profile evidence and refresh

Profile maps observed repository structure and conditional skills. Not command allowlist, not fixed architecture. Each public record holds pinned default-branch commit, observed toolchain/configuration paths, applicable instruction paths, evidence file hashes. Domain references add deeper invariants from actual source and tests. Recheck current checkout before editing; multiple builds in one tree may belong to different components.

Companion `dot-agents/scripts/review_repositories.py` refreshes read-only evidence via bounded parallel HTTP/API calls. Uses GitHub CLI authentication, pins each commit before requesting files, caps file size/count, caches unchanged commits. Never executes project code. Keeps archived repositories and forks. Exits nonzero on failed downloads or truncated API trees. File cap gives bounded baseline; unread candidates are recorded explicitly. Cap does not mean every source line was audited. Use `--max-files 100` for broader baseline collection. Caches must match current visibility/metadata, commit and file budget; all cached evidence must pass integrity checks.

```sh
python3 scripts/review_repositories.py --output /tmp/repository-review --owners worxbend w0rxbend
```

Default collects only public repositories. `--include-private` suits authorized local review; evidence destination must be outside public checkout. Raw private evidence must not be copied into profile or release. Public profile generator rejects private records instead of serializing them.

Before adding behavioral constraints, read each profile's actual instructions/build/CI files and inspect representative source/tests. Missing platform hardware, live services, secrets, or integration runners are verification boundaries; record them without inventing results. Confirm tool versions from repository's lock/header/configuration. Cite immutable public sources for reusable domain rules.

Broad skill audit reads all installed entrypoints, records retain/fix/tailor/provider decisions. Retain is valid when skill already supports task; optimization does not require rewriting stable specialist content. Local forks preserve upstream license/notices and record changed files and reasons. Heavy conditional material may move into correctly linked references; entrypoint keeps decisions needed to route task.
