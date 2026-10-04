# Skills adapted to the repositories

The October 2026 review covered all **100 accessible repositories** across
`worxbend` and `w0rxbend`: **92 public and 8 private**. Every one of the 560
previously installed skills received a recorded decision. The resulting catalog
contains **586 skills: 500 included and 86 external**.

The review updated 92 existing skills and added 25 public skills. Private repository
context is installed locally as one additional external entry. Provider entrypoints
were reviewed locally; their caches and restricted text remain under provider control.
The [per-skill report](skill-review.json) records retained skills as well as changes.
[Local fork records](../sources/local-forks.json) preserve attribution, reasons,
affected files, and before/after entrypoint hashes.

## Find the conventions for a repository

Use `worxbend-repository-context` when working in either account's repositories.
Its helper selects one commit-pinned profile from the current Git origin:

```sh
python3 ~/.agents/skills/worxbend-repository-context/scripts/repo_profile.py --cwd .
# Inspect the structured record when needed:
python3 ~/.agents/skills/worxbend-repository-context/scripts/repo_profile.py --cwd . --json
```

The [public index](../collections/shared/worxbend-repository-context/references/profiles.json)
contains build files, CI paths, observations, source evidence, frontend dependency
versions, and relevant installed skills for every public repository. Load only the
matching record and references needed for the task. Unknown origins require checkout
inspection. Dated profiles cannot override newer instructions or prove a build succeeds.

Prefer **Mill for a new JVM build**, including mixed Scala/Java/Kotlin modules and
monorepos. Preserve existing sbt, Gradle, Maven, and Scala CLI builds unless migration
is requested. Preserve deliberate ZIO, Cats Effect, FS2, Future, and Ox choices.
[The Mill guide](mill-skills.md) covers declarative configuration, single-file scripts,
programmable builds, and 14 specialist skills.

## Added skills

| Skill | Evidence-backed purpose |
| --- | --- |
| `worxbend-repository-context` | Select the repository's build, CI, runtime, and specialist skill conventions. |
| `scala-library-contracts` | API compatibility, compile-time derivation, lazy secret access, JVM/Scala floors, native loading, and effect boundaries. |
| `rust-linux-apps` | GTK/Relm4 requirements, async UI state, DBus/keyring interactions, and desktop packaging. |
| `workstation-installers` | Plans, dry runs, checksums, install ownership, and failure recovery. |
| `airgradient-clients` | API contracts, sensor/config handling, unknown configuration siblings, and local file updates. |
| `streaming-integrations` | OBS/Twitch/browser contracts, event deduplication, reconnects, stale callbacks, and game protocols. |
| `embedded-device-protocols` | Board-specific firmware, flashing gates, binary camera frames, and host/device tests. |
| `homelab-operations` | Inventory/readiness evidence, Ansible/GitOps contracts, deployment locks, and operational gates. |
| `compatibility-ports` | Behavior-preserving ports, independent oracles, and exact protocol vectors. |
| `parametric-cad-validation` | build123d geometry, assembly/preset gates, and real FreeCAD save/reopen evidence. |
| `zig-build-and-memory` | Version-sensitive build graphs, unmanaged containers, buffered output, and fuzz scopes. |
| `cpp-obs-plugin-development` | OBS/Qt references, callback/thread ownership, fork build contracts, and plugin packaging. |
| `crystal-build-and-test` | Shards/spec/benchmark boundaries, editor extension scope, and workstation compiler selection. |
| `elixir-project-workflow` | Mix identity, ExUnit/doctests, runtime floors, and proportionate scaffold repairs. |
| `typescript-project-contracts` | Actual pnpm package filters, Solid/Hono runtime boundaries, and pinned integrations. |
| `rust-systems-contracts` | Cargo package/edition selection, ownership/errors, UTF-8, and conditional unsafe-memory work. |

Nine official MIT-licensed [PixiJS skills](https://github.com/pixijs/pixijs-skills)
were reviewed and installed at commit `83760c6f53462ca9cecd68055041f5a8c94758ce`:
`pixijs-application`, `pixijs-assets`, `pixijs-events`, `pixijs-performance`,
`pixijs-scene-container`, `pixijs-scene-graphics`, `pixijs-scene-text`,
`pixijs-ticker`, and `pixijs-core-concepts`. Read each frontend's installed PixiJS
version before applying examples. Three reviewed entrypoints have local corrections
for ticker rendering and the current renderer call shape.

## Existing skill improvements

Changes repair missing references and remove assumptions about unshipped helpers.
Discovery descriptions distinguish Go, Scala, frontend, review, and architecture
tasks more precisely. Detailed Scala and Lua material moved to linked references
with examples preserved. The 95 modified entrypoints, including three new PixiJS
skills, are approximately 18,000 words shorter in total.

Workflow guidance respects repository test contracts, authorized delegation,
exclusive edit ownership, and permission to publish review comments. It removes
forced model choices, simultaneous autofixes, and blindly timed terminal input.
Explicit-only invocation policies and licenses are retained. Technical corrections
include Effect v3 schema imports, withdrawn Java string templates, and archived Wire.

## Review and verification boundaries

Three parallel workers reviewed the two accounts and global skill inventory.
Repository workers cross-reviewed each other's skills against source scenarios;
an independent worker exercised the profile and evidence tools. Evidence is pinned
to default-branch commits. Every repository has a complete collected baseline of
eligible build files, instructions, CI, and documentation at the selected budget.
Representative source scenarios supplement that baseline; not every source line
was read.

No repository application, device flasher, fleet deployment, or live integration
was executed. Verification covers 41 installer/profile unit tests, 17 independent
profile scenarios, cross-reviewed domain scenarios, isolated Effect date/email
examples, and the six existing Mill fixtures. Linux/macOS CI check hashes, review
coverage, local forks, routing, installation, and distribution boundaries.

## Refresh the evidence

Authenticate GitHub CLI first. Keep evidence outside the public clone. The collector
reads configuration/documentation and never executes repository code. Cache reuse
requires matching commit, visibility, metadata, budget, selection, and file/tree hashes.

```sh
cd ~/.dot-agents
python3 scripts/review_repositories.py \
  --output ~/.local/share/dot-agents/repository-review --max-files 100
python3 scripts/build_repository_profiles.py \
  --evidence ~/.local/share/dot-agents/repository-review
```

Review any remaining candidates and representative source. The exporter accepts
`--analysis FILE ...` but copies only approved public fields with matching commits.
Without analyses, it produces structure-only profiles; preserve or refresh the richer
observations before publishing. Update installed source folders deliberately, then
run `scripts/import_skills.py --replace` and `scripts/catalog.py`. Refresh review and
fork records too: `make check` rejects stale hashes or incomplete coverage. Compare
upstream updates with `sources/local-forks.json` before overwriting personalized forks.

## Private context on another machine

Private names and observations stay outside public Git and release archives.
The generic private skill is external; its directories use `0700` and files `0600`.

```sh
python3 scripts/review_repositories.py \
  --output ~/.local/share/dot-agents/repository-review \
  --include-private --max-files 100
python3 scripts/build_private_profile.py \
  --evidence ~/.local/share/dot-agents/repository-review
./install.sh --agents all --include-local
```

The generator refuses output inside the public checkout. It preserves customized
context; `--replace` creates a backup. For a private origin, select its local index:

```sh
python3 ~/.agents/skills/worxbend-repository-context/scripts/repo_profile.py \
  --cwd . --index ~/.local/share/dot-agents/private-skills/worxbend-private-repository-context/references/profiles.json
```

This machine's changed global folders were backed up under
`~/.local/share/dot-agents/backups/repository-review-TIMESTAMP/`. Existing shared/Claude
bootstrap root links were preserved. Restart agent sessions to refresh discovery.
