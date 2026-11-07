---
name: worxbend-repository-context
description: Identify repository-specific stacks and build/test conventions when working in repositories owned by worxbend or w0rxbend. Use the Git origin and current committed instructions to choose the relevant skills.
license: MIT
---

# Work in this user's repositories

Identify repository from Git remotes. Before choosing workflow, read its current applicable `AGENTS.md`, build files, and CI. Skill supplies dated public repository index; current checkout overrides it. Use when remote belongs to `worxbend` or `w0rxbend`; not needed elsewhere.

Run bundled lookup from current checkout:

```sh
python3 <this-skill-directory>/scripts/repo_profile.py --cwd .
```

Without local checkout, pass `--remote https://github.com/worxbend/worxbend`. Helper reads [the profile index](references/profiles.json), prints observed build files and relevant skill candidates. No network access, no project execution. Read only relevant repository record. No record: inspect current repository directly; do not guess stack from name.

Prefer Mill for **new** Scala/JVM builds when free to choose. Keep existing sbt, Gradle, Maven, Scala CLI, Crystal, Cargo, and frontend builds unless migration is requested. Repositories deliberately differ in application model: ZIO, Cats Effect/FS2, plain `Future`, Ox/synchronous Tapir. Match guidance to dependency files and public API. Installed skill does not authorize replacing that stack. Keep version pins, compiler target floors, native packaging boundaries, and test tiers; do not apply newest example globally.

Original domain skills add concrete repository constraints when applicable:

- `scala-library-contracts`: Scala derivation/redaction, stable API/effect boundaries, native/JVM publication contracts.
- `mill-jvm-modules` and `mill-monorepo`: actual Scala/Java/Kotlin graph and shared conventions in Mill builds.
- `rust-linux-apps`: Rust desktop, TUI, async lifecycle, Linux system dependencies.
- `workstation-installers`: package plans, checked downloads, state, atomic replacement, idempotency.
- `airgradient-clients`: LAN device contracts, client/configuration behavior across surfaces.
- `streaming-integrations`: OBS request/event boundaries, Twitch auth/EventSub, browser overlays.
- `embedded-device-protocols`: actual board identity, firmware/wire protocols, host/firmware compatibility.
- `homelab-operations`: repository-owned Ansible/Flux/K3s/SOPS workflows, execution scope.
- `compatibility-ports`: byte-for-byte ports, chess fixtures, observable compatibility boundaries.

These are optional relevant capabilities, not mandatory skill stack to load. Ordinary tasks: use existing language, API, documentation, testing, or CI skills. Avoid loading several overlapping review or orchestration guides for small change. Delegate only when available and authorized, with separate edit ownership.

Archived repositories and forks: before proposing modernization, confirm whether work is maintenance, port, or revival. Documentation-only profiles do not imply application to scaffold. When README and implementation disagree, inspect current source/tests. In reports, distinguish static review, offline tests, service integration, and actual device/fleet execution; local check does not prove deployment.

Private repositories are absent from public index; inspect their checkout normally. If `worxbend-private-repository-context` is installed locally, it supplies local-only profile. Keep private source, names, host inventories, and credentials out of public skill exports and issue/release text.

Index records 2026-10-04 review. Read [review-method.md](references/review-method.md) only to refresh this collection or assess evidence coverage.
