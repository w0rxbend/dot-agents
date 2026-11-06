---
name: compatibility-ports
description: Port or optimize externally compatible codecs, chess engines, protocol clients and JVM facades, using pinned upstream oracles, byte/semantic differential fixtures and explicit supported behavior.
license: MIT
---

Before changing implementation, define what must stay compatible: byte format, decoded meaning, error behavior, public API/ABI, wire protocol, numeric precision, supported variants, deployment artifacts. Port may intentionally support a subset; describe it precisely. Compilation, self-round-trip tests, coverage percentage or faster benchmark cannot prove compatibility with separate implementation.

Read [references/flix-and-chess.md](references/flix-and-chess.md) for Flix codec/chess projects, [references/verification.md](references/verification.md) for oracle, fixture and release checks. Keep upstream attribution/license and repository's selected toolchain/build. Prefer Mill for new JVM build; existing sbt/Gradle facade does not imply migration task.

Pin upstream commit and toolchain used as oracle. Get independently produced expected data where possible. Compare target encoding with oracle encoding; decode oracle bytes with target. If upstream accepts target's supported subset, also decode target bytes with oracle. Test malformed/truncated data and absent/default fields as separate contract. Stricter reader may be documented divergence, not automatic parity.

For optimization, keep small discriminating compatibility corpus beside workload-representative benchmarks. First verify unchanged outputs/error classes and side effects, then measure warmup, allocation and lifecycle costs. Tie performance claim to actual platform/toolchain/input; do not generalize one microbenchmark into deployment guarantees.

Report exact compatible scope, deliberate differences, excluded behavior, validation performed, versioned artifacts. Minimize any mismatch into reproducible fixture before altering algorithm or expected output. Never “fix” golden file solely so new implementation passes.
