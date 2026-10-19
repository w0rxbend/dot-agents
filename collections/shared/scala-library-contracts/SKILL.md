---
name: scala-library-contracts
description: Maintain Scala library APIs, derivation macros, redaction, native resource ownership, and consumer compatibility in worxbend libraries. Use for library changes rather than ordinary application scaffolding.
license: MIT
---

# Scala library contracts

Find the changed artifact and its consumers before editing. Read the repository build, local instructions, compatibility checks, and relevant tests. Preserve its chosen effect model: the reviewed repositories include ZIO, Cats Effect/FS2, Future, and Ox. Prefer Mill for new builds when the task leaves that choice open; use the existing wrapper for an established Mill or sbt project.

A library's public contract includes error types, laziness, cancellation, resource ownership, JSON/wire behavior, source/binary compatibility, and published dependency scope. A cleaner implementation must preserve these unless the requested change deliberately alters them.

Read [derivation-redaction.md](references/derivation-redaction.md) for quoted macros, renderer delegation, recursion, and secret handling. Read [native-publication.md](references/native-publication.md) for OpenCV ownership, portable artifacts, Scala TASTy compatibility, and consumer validation. Load only the relevant reference.

Locate the authoritative version and compatibility baseline. Do not update a snapshot merely to silence a failing check; determine whether the changed public surface is intended. Generated API/model sources should change through their generator or documented override.

Run the changed module's tests and the repository's relevant contract gate. For a published API, inspect the resulting POM and verify a representative consumer using the advertised compiler/JDK floor. Report native, live-service, or hardware coverage separately from pure tests.
