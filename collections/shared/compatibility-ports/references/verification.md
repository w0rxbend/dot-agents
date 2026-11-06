# Verification and release evidence

Pick smallest independent checks that distinguish changed behavior:

| Contract | Useful evidence |
|---|---|
| Persistent codec | Exact oracle-produced bytes, cross-decoding, signed/unsigned and truncation boundaries |
| Chess legality | Published perft positions/depths by variant, edge-rule fixtures, replay comparisons |
| Public facade | Real downstream compile/run, overload/import signatures, artifact class inventory |
| Wire client/server | Shared raw vectors, partial transport segments, version mismatch, unknown/absent fields |
| Authorization migration | Provider response fixtures, grant/identity distinctions, rotated-token persistence, outage vs rejection |
| Performance | Same semantic corpus before/after plus representative throughput, allocations, initialization cost |

Self-round-trip can pass when encoder and decoder share same bug. Reference port can copy that bug too if expected values were generated from it. Record which implementation produced each golden, including commit, toolchain, fixture derivation. Fixed seeds make randomized differential failures repeatable. Minimize mismatches; keep triggering input.

Exercise numeric and representation boundaries the format supports: empty/minimum data, maximum unsigned bytes, high-bit masks, overflow, optional field omission, odd packing counts, invalid enum/variant values, early EOF, legacy versions. Keep deliberately unsupported behavior explicit. Test accepted stricter rejection as documented divergence; do not call it byte/semantic parity outside supported domain.

For asynchronous clients, also compare observable semantics: one reply completion, late/duplicate reply handling, bounded queues, idempotent teardown, stale-session exclusion. State which retryable operations have idempotency evidence; request timeout alone does not supply it. Avoid coupling externally compatible patch with unrelated API cleanup, build migration or effect-system replacement.

Check delivered artifact with consuming toolchain, not merely implementation's test runner. Existing [codec CI](https://github.com/w0rxbend/compression-flix/blob/920b0514bb1c34fe3bb5f25c4dbaad78e0c2a1ee/.github/workflows/test.yml) separately runs Flix tests, Scala facade compilation, consumer smoke program and release-jar inspection. Where current contract says so, keep generated test classes/fixtures out of release. Preserve required notices for derived AGPL or other upstream material. These original instructions grant no new license to implementation being ported.

State result as “compatible for these versions/fixtures/features” plus any known exclusions. Reserve “drop-in replacement” for verified supported consumer/API, artifact, numeric/error semantics and data formats. For narrow ordinary edit, do not demand exhaustive port verification from this skill; run gates relevant to changed contract plus repository-required checks.
