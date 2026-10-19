---
name: worxbend-repository-context
description: Identify repository-specific stacks and build/test conventions when working in repositories owned by worxbend or w0rxbend. Use the Git origin and current committed instructions to choose the relevant skills.
license: MIT
---

# Work in this user's repositories

Identify the repository from its Git remotes and read its current applicable `AGENTS.md`, build files, and CI before choosing a workflow. This skill supplies a dated public repository index, not instructions that override the current checkout. Use it when the remote belongs to `worxbend` or `w0rxbend`; ordinary work elsewhere does not require it.

Run the bundled lookup from the current checkout:

```sh
python3 <this-skill-directory>/scripts/repo_profile.py --cwd .
```

Or pass `--remote https://github.com/worxbend/worxbend` when inspecting a repository without a local checkout. The helper reads [the profile index](references/profiles.json), prints observed build files and relevant skill candidates, and performs no network or project execution. Read only the relevant repository record. A missing record means inspect the current repository directly; do not guess its stack from its name.

Prefer Mill for **new** Scala/JVM builds when a choice is needed. Preserve existing sbt, Gradle, Maven, Scala CLI, Crystal, Cargo, and frontend build arrangements unless migration is requested. The existing repositories deliberately use different application models: ZIO, Cats Effect/FS2, plain `Future`, and Ox/synchronous Tapir. Select guidance that matches the dependency files and public API; an installed skill does not authorize replacing that stack. Preserve version pins, compiler target floors, native packaging boundaries, and test tiers instead of applying the newest example globally.

The original domain skills add concrete repository constraints when applicable:

- `scala-library-contracts`: Scala derivation/redaction, stable API/effect boundaries, and native/JVM publication contracts.
- `mill-jvm-modules` and `mill-monorepo`: the actual Scala/Java/Kotlin graph and shared conventions in Mill builds.
- `rust-linux-apps`: Rust desktop, TUI, async lifecycle, and Linux system dependencies.
- `workstation-installers`: package plans, checked downloads, state, atomic replacement, and idempotency.
- `airgradient-clients`: LAN device contracts and client/configuration behavior across surfaces.
- `streaming-integrations`: OBS request/event boundaries, Twitch auth/EventSub, and browser overlays.
- `embedded-device-protocols`: actual board identity, firmware/wire protocols, and host/firmware compatibility.
- `homelab-operations`: repository-owned Ansible/Flux/K3s/SOPS workflows and execution scope.
- `compatibility-ports`: byte-for-byte ports, chess fixtures, and observable compatibility boundaries.

These are optional relevant capabilities, not a mandatory stack of skills to load. Use existing language, API, documentation, testing, or CI skills for ordinary tasks. Avoid loading several overlapping review or orchestration guides for a small change; delegate only when available and authorized, with separate edit ownership.

For archived repositories and forks, confirm whether the requested work is maintenance, a port, or revival before proposing modernization. Documentation-only profiles do not imply an application to scaffold. Inspect current source/tests when a README and implementation disagree. Report the distinction between static review, offline tests, service integration, and actual device/fleet execution; a local check does not prove deployment.

Private repositories are absent from the public index. Inspect their checkout normally; if `worxbend-private-repository-context` is installed locally, it supplies a local-only profile. Keep private source, names, host inventories, and credentials out of public skill exports and issue/release text.

The index records the 2026-10-04 review. Read [review-method.md](references/review-method.md) only when refreshing this collection or assessing evidence coverage.
