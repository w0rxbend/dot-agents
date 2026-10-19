# Profile evidence and refresh

The profile is a map of observed repository structure and conditional skills, not a command allowlist or a fixed architecture. Each public record contains the pinned default-branch commit, observed toolchain/configuration paths, applicable instruction paths, and evidence file hashes. Domain references add deeper invariants from actual source and tests. Recheck the current checkout before editing; multiple builds in one tree may belong to different components.

The companion `dot-agents/scripts/review_repositories.py` refreshes read-only evidence with bounded parallel HTTP/API calls. It uses GitHub CLI authentication, pins each commit before requesting files, caps file size/count, caches unchanged commits, and never executes project code. It includes archived repositories and forks rather than silently dropping them. It exits unsuccessfully on failed downloads or truncated API trees. A configured file cap is a bounded baseline, with unread candidates recorded explicitly; it does not mean every source line was audited. Use `--max-files 100` for broader baseline collection. Caches must match current visibility/metadata, commit and file budget, and all cached evidence must pass integrity checks.

```sh
python3 scripts/review_repositories.py --output /tmp/repository-review --owners worxbend w0rxbend
```

The default collects only public repositories. `--include-private` is appropriate for an authorized local review; the evidence destination must be outside the public checkout. Raw private evidence must not be copied into a profile or a release. The public profile generator rejects private records rather than serializing them.

Read each profile's actual instructions/build/CI files and inspect representative source/tests before adding behavioral constraints. Treat missing platform hardware, live services, secrets, or integration runners as verification boundaries; record them without inventing results. Confirm tool versions from the repository's lock/header/configuration, and cite immutable public sources for reusable domain rules.

The broad skill audit reads all installed entrypoints and records retain/fix/tailor/provider decisions. A retain decision is valid when a skill already supports the task; optimization does not require rewriting stable specialist content. Local forks preserve upstream license/notices and record changed files and reasons. Heavy conditional material may move into correctly linked references, while the entrypoint keeps the decisions needed to route the task.
