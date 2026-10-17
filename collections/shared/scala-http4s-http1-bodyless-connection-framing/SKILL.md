---
name: scala-http4s-http1-bodyless-connection-framing
description: Use when changing http4s Ember HTTP/1 HEAD handling, drain metadata, response remainders, or connection reuse. Trace parser completion separately from socket consumption and pool eligibility.
license: MIT
---

# Review Ember response framing before connection reuse

## When to Use

Use when a HEAD/no-body fix changes `discardBody`, a parser returns different remainder metadata, or a client refactor moves response cleanup between a body stream and its enclosing Resource. Trace the whole parser-to-pool path even when the diff changes only one branch.

## When Not to Use

Do not generalize this procedure into HTTP/2 framing, a request-smuggling diagnosis, a universal pool-acquisition algorithm, or a rule that every body must be drained. Ordinary application decoding with no transport ownership change is outside scope. URI segment encoding belongs to its separate skill.

## Prerequisites

Identify request method, response status, HTTP version, framing headers, parser input/read callback, body consumer, response Resource finalizer, and pool reuse flag. Locate their definitions and callers before interpreting names such as `Drain`.

Historical anchors differ: PR #4348 at `32893c3373bd735b101f28f28bec70936293a7f7` is series/0.21 with Scala 2.12.13/2.13.4, Cats Effect 2.3.1 and FS2 2.5.0; #7369 at `7e5a97468d631e9aece50aecbbc74bc792e30b60` uses Scala 2.12.18/2.13.12/3.3.1, Cats Effect 3.5.3 and FS2 3.9.4. Preserve each branch's Resource exit-case API. Current targets require fresh source/build discovery, not transplantation of CE2 finalizers into CE3.

## Workflow

1. Record four distinct facts for each response branch: body exposed to callers, bytes already buffered after framing, bytes still unread on the socket, and connection disposition. Empty public body does not establish the other three facts.
2. Trace the producer and consumer of drain metadata. In #4348, fixed-body drain observes parser state; `Some(Array.emptyByteArray)` means the body boundary is known with no buffered next bytes. `None` means the implementation cannot establish reusable completion. In #7369, the HEAD discard branch deliberately returns pure `None`; it does not call the read callback.
3. Inspect the owner before changing either meaning. Historical ClientHelpers retains `DontReuse` on `None`; with `Some(bytes)` and no close policy, it stores remainder bytes before marking reuse. The CE3 head also starts the next read before marking reuse. Do not replace these distinctions with `getOrElse(empty)` or infer safety from `rest.isEmpty`.
4. Keep response cleanup at a scope that runs when the body is never pulled. #4348 moved processing from a body finalizer into the enclosing response Resource release. Trace ordering relative to returning the managed connection to its pool; preserve the success/error/cancel policy. A stream finalizer alone is insufficient for an unconsumed body.
5. Distinguish HEAD from status-implied no-body responses. HEAD can advertise representation length without sending those bytes; waiting for that Content-Length can hang. The inspected parser preserves `finalBuffer` for status-implied emptiness but chooses non-reuse metadata for HEAD. Do not silently unify the branches.
6. For any reuse change, require byte-boundary and owner-level evidence. When safe alignment cannot be established, retain a deliberate retirement policy rather than guessing how many unexpected bytes to skip. If proposing actual drain reads, specify their byte/time budget and cancellation owner; the historical name does not establish bounded I/O.

## Review and Refactoring Checks

Preserve the invariant that a reusable connection begins the next exchange at a known message boundary; retain all legitimate buffered next-message bytes. Preserve `None` versus `Some(empty)` and the fact that body consumption is optional for callers but response Resource release is not.

False positives: successful completion with `Some(empty)` is not a reason to close merely because the next response has not arrived. Conversely, explicit closure after HEAD is not evidence that bytes were drained. Do not infer an exploit from a reviewer's security concern. Safe deliberate closure may trade reuse performance for simpler framing; measure that tradeoff separately.

## Validation

Inspect `build.sbt`, suite declarations and platform layout first. In an authorized isolated checkout use `sbt projects` and `sbt 'ember-core / Test / definedTests'`. At #4348, run `sbt 'ember-core / testOnly org.http4s.ember.core.ParsingSpec' 'ember-client / testOnly org.http4s.ember.client.internal.ClientHelpersSuite'`. At #7369 the file is ParserSuite.scala but the class is **ParsingSuite**: use `sbt 'ember-core / testOnly org.http4s.ember.core.ParsingSuite'`. JVM project IDs have no JVM suffix in the inspected CE3 crossproject build. Verify selectors on the target branch and require nonzero discovery.

Use three layers of oracles: (a) fixed-body partial/full completion and exact body/remainder bytes, (b) reuse flag and saved-byte transitions including never-pulled bodies, and (c) real owner/socket closure or safe reuse. The third layer must stage valid HEAD with no body, buffered excess bytes, delayed excess bytes, a subsequent exchange, explicit close headers, early consumer termination, and cancellation. Observe connection identity and close/reuse events; a single-chunk parser assertion cannot replace this. #4348's two-response test is parser-level, not a network test. No upstream tests or sockets were executed while authoring this skill.

## Examples

### Good

A five-byte response body shares an input chunk with the next response prelude. Consume exactly the first body, retain the remaining prelude, and parse the next response using that remainder. The historical two-response test expects `hello` then `world`; helper tests distinguish reusable empty remainder from incomplete `None`. Retain those oracles when simplifying the parser.

### Broken and Correction

A HEAD patch returns empty body and `None`, then a pool cleanup maps `None` to an empty array and marks the connection reusable. The test only checks empty body/rest. Correction: preserve non-reuse for the unknown/discarded state and trace the owner release; if reuse is a requirement, implement and test a justified framing policy with delayed-input and subsequent-exchange cases. Do not repair it by reading the HEAD representation's Content-Length.

### Negative

The previous ordinary response has been fully consumed and drain returns `Some(empty)` while the next exchange has not started. Do not flag the lack of already-buffered next-response bytes as unsafe. #4348 explicitly distinguishes this common non-pipelined case from an incompletely consumed body. Preserve other close/version policies before permitting reuse.

## Output Contract

For each finding provide `file:line`, severity, method/status/framing branch, the four-fact byte/disposition table, evidence ID, smallest correction and discriminating test. State which observations are parser-only, helper-state-only, reviewer testimony, or executed transport evidence. Include exact versions, discovered selectors and outstanding socket tests; never turn a structural pass into a safety certification.

## Limitations

The historical review accepted #7369 with reviewer-reported aggressive HEAD closure. Source inspection supports its non-reuse path, but is not a reproduced close event. #4348 deferred more exhaustive chunking and socket-draining work. Neither history proves current transport safety, protocol-wide compliance or performance. Generic CE cancellation/resource internals and other libraries' pool-handoff races remain separate procedures.

## Sources

See [evidence and claims](references/evidence.json): `c-framing-connection-contract` and `c-drain-reuse-state`.

- [Resource-level cleanup discussion](https://github.com/http4s/http4s/pull/4348#discussion_r573734431) and [empty versus incomplete remainder](https://github.com/http4s/http4s/pull/4348#discussion_r574987281).
- [Historical reuse consumer](https://github.com/http4s/http4s/blob/32893c3373bd735b101f28f28bec70936293a7f7/ember-client/src/main/scala/org/http4s/ember/client/internal/ClientHelpers.scala#L132-L146).
- [HEAD drain concern](https://github.com/http4s/http4s/pull/7369#discussion_r1587508509) and [qualified final disposition](https://github.com/http4s/http4s/pull/7369#pullrequestreview-2038478780).
