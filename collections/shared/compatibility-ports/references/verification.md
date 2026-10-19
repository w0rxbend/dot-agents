# Verification and release evidence

Select the smallest independent checks that distinguish the changed behavior:

| Contract | Useful evidence |
|---|---|
| Persistent codec | Exact oracle-produced bytes, cross-decoding, signed/unsigned and truncation boundaries |
| Chess legality | Published perft positions/depths by variant, edge-rule fixtures and replay comparisons |
| Public facade | Real downstream compile/run, overload/import signatures, artifact class inventory |
| Wire client/server | Shared raw vectors, partial transport segments, version mismatch and unknown/absent fields |
| Authorization migration | Provider response fixtures, grant/identity distinctions, rotated-token persistence, outage vs rejection |
| Performance | Same semantic corpus before/after plus representative throughput, allocations and initialization cost |

A self-round-trip can pass when both encoder and decoder share the same bug. A reference port can also copy that bug if expected values were generated from it. Record which implementation produced each golden, including commit, toolchain and fixture derivation. Fixed seeds make randomized differential failures repeatable; minimize mismatches and retain the triggering input.

Exercise numeric and representation boundaries that the format actually supports: empty/minimum data, maximum unsigned bytes, high-bit masks, overflow, optional field omission, odd packing counts, invalid enum/variant values, early EOF and legacy versions. Keep deliberately unsupported behavior explicit. For an accepted stricter rejection, test the divergence as documented behavior and do not call it byte/semantic parity outside the supported domain.

For asynchronous clients compare observable semantics too: one reply completion, late/duplicate reply handling, bounded queues, idempotent teardown and stale-session exclusion. State which retryable operations have idempotency evidence; request timeout alone does not supply it. Avoid coupling an externally compatible patch with unrelated API cleanup, build migration or effect-system replacement.

Check the delivered artifact with the consuming toolchain, not merely the implementation's test runner. The existing [codec CI](https://github.com/w0rxbend/compression-flix/blob/920b0514bb1c34fe3bb5f25c4dbaad78e0c2a1ee/.github/workflows/test.yml) separately runs Flix tests, Scala facade compilation, a consumer smoke program and release-jar inspection. Keep generated test classes/fixtures out of a release where that is the current contract, and preserve required notices for derived AGPL or other upstream material. These original instructions do not grant a new license to the implementation being ported.

Explain a result as “compatible for these versions/fixtures/features” with any known exclusions. Reserve “drop-in replacement” for the supported consumer/API, artifact, numeric/error semantics and data formats actually verified. Do not turn this skill into a demand for exhaustive port verification when the task is a narrow ordinary edit; run the gates relevant to the changed contract plus repository-required checks.
