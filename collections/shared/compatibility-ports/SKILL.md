---
name: compatibility-ports
description: Port or optimize externally compatible codecs, chess engines, protocol clients and JVM facades, using pinned upstream oracles, byte/semantic differential fixtures and explicit supported behavior.
license: MIT
---

Define what must remain compatible before changing implementation: byte format, decoded meaning, error behavior, public API/ABI, wire protocol, numeric precision, supported variants and deployment artifacts. A port can intentionally support a subset, but describe that subset precisely. Compilation, self-round-trip tests, a coverage percentage or a faster benchmark cannot establish compatibility with a separate implementation.

Read [references/flix-and-chess.md](references/flix-and-chess.md) for the Flix codec/chess projects and [references/verification.md](references/verification.md) for oracle, fixture and release checks. Preserve upstream attribution/license and the repository's selected toolchain/build. Mill is preferred for a new JVM build; an existing sbt/Gradle facade is not an implied migration task.

Pin the upstream commit and toolchain used as the oracle. Obtain independently produced expected data where possible. Compare target encoding against oracle encoding and decode oracle bytes with the target; when the upstream accepts the target's supported subset, also decode target bytes with the oracle. Test malformed/truncated data and absent/default fields as a separate contract. A stricter reader may be a documented divergence, not automatic parity.

For an optimization retain a small discriminating compatibility corpus alongside workload-representative benchmarks. Verify unchanged outputs/error classes and side effects first, then measure warmup, allocation and lifecycle costs. Keep a performance claim tied to its actual platform/toolchain/input; do not generalize one microbenchmark into deployment guarantees.

Report exact compatible scope, deliberate differences, excluded behavior, validation performed and versioned artifacts. When a mismatch appears, minimize it into a reproducible fixture before altering the algorithm or expected output. Never “fix” the golden file solely to make the new implementation pass.
