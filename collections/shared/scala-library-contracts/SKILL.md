---
name: scala-library-contracts
description: Maintain Scala library APIs, derivation macros, redaction, native resource ownership, and consumer compatibility in worxbend libraries. Use for library changes rather than ordinary application scaffolding.
license: MIT
---

# Scala library contracts

Before editing, find changed artifact and its consumers. Read build, local instructions, compatibility checks, relevant tests. Keep chosen effect model; reviewed repositories include ZIO, Cats Effect/FS2, Future and Ox. Prefer Mill for new builds when task leaves choice open. Established Mill or sbt project: use existing wrapper.

Library's public contract includes error types, laziness, cancellation, resource ownership, JSON/wire behavior, source/binary compatibility, published dependency scope. Cleaner implementation must preserve these unless requested change deliberately alters them.

Read [derivation-redaction.md](references/derivation-redaction.md) for quoted macros, renderer delegation, recursion, secret handling. Read [native-publication.md](references/native-publication.md) for OpenCV ownership, portable artifacts, Scala TASTy compatibility, consumer validation. Load only relevant reference.

Locate authoritative version and compatibility baseline. Do not update snapshot merely to silence failing check; decide whether changed public surface is intended. Change generated API/model sources through generator or documented override.

Run changed module's tests and relevant contract gate. Published API: inspect resulting POM, verify representative consumer on advertised compiler/JDK floor. Report native, live-service or hardware coverage separately from pure tests.
