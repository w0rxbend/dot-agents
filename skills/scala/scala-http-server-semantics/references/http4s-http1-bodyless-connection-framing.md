# Review Ember response framing before connection reuse

> Library: http4s (Ember client/core, HTTP/1). Formerly `scala-http4s-http1-bodyless-connection-framing` skill, merged into `scala-http-server-semantics`. Evidence: [evidence/scala-http4s-http1-bodyless-connection-framing.json](evidence/scala-http4s-http1-bodyless-connection-framing.json).

## When to Use

HEAD/no-body fix changes `discardBody`, parser returns different remainder metadata, or client refactor moves response cleanup between body stream and enclosing Resource. Trace whole parser-to-pool path, even for one-branch diffs.

## When Not to Use

Not for HTTP/2 framing, request-smuggling diagnosis, universal pool-acquisition algorithms, or a rule that every body must be drained. Ordinary application decoding without transport ownership change: out of scope. URI segment encoding: [the URI segment case](http4s-uri-segment-representation.md).

## Prerequisites

Identify request method, response status, HTTP version, framing headers, parser input/read callback, body consumer, response Resource finalizer, pool reuse flag. Find definitions and callers before interpreting names like `Drain`.

Anchors differ: PR #4348 at `32893c3373bd735b101f28f28bec70936293a7f7` is series/0.21 (Scala 2.12.13/2.13.4, Cats Effect 2.3.1, FS2 2.5.0); #7369 at `7e5a97468d631e9aece50aecbbc74bc792e30b60` uses Scala 2.12.18/2.13.12/3.3.1, Cats Effect 3.5.3, FS2 3.9.4. Keep each branch's Resource exit-case API. Current targets need fresh source/build discovery; do not transplant CE2 finalizers into CE3.

## Workflow

1. Per response branch record four facts: body exposed to callers, bytes buffered after framing, bytes unread on socket, connection disposition. Empty public body does not establish other three.
2. Trace drain metadata producer and consumer. #4348: fixed-body drain observes parser state. `Some(Array.emptyByteArray)` means body boundary known, no buffered next bytes. `None` means implementation cannot establish reusable completion. #7369: HEAD discard branch deliberately returns pure `None`, does not call read callback.
3. Inspect owner before changing either meaning. Historical ClientHelpers keeps `DontReuse` on `None`; on `Some(bytes)` without close policy, stores remainder bytes before marking reuse. CE3 head also starts next read before marking reuse. Do not collapse these with `getOrElse(empty)` or infer safety from `rest.isEmpty`.
4. Keep response cleanup in a scope that runs even when body is never pulled. #4348 moved processing from body finalizer to enclosing response Resource release. Trace ordering against returning connection to pool; keep success/error/cancel policy. Stream finalizer alone is insufficient for unconsumed body.
5. Distinguish HEAD from status-implied no-body. HEAD can advertise representation length without sending those bytes; waiting for that Content-Length can hang. Inspected parser keeps `finalBuffer` for status-implied emptiness, non-reuse metadata for HEAD. Do not silently unify branches.
6. Reuse changes need byte-boundary and owner-level evidence. If safe alignment cannot be established, keep deliberate retirement policy; do not guess how many unexpected bytes to skip. Actual drain reads need byte/time budget and cancellation owner; historical name does not establish bounded I/O.

## Review and Refactoring Checks

Invariant: reusable connection starts next exchange at known message boundary, keeping all legitimate buffered next-message bytes. Keep `None` versus `Some(empty)`. Body consumption is optional for callers; response Resource release is not.

False positives: `Some(empty)` completion is no reason to close merely because next response has not arrived. Explicit close after HEAD is no evidence bytes were drained. Do not infer exploit from reviewer's security concern. Safe deliberate closure may trade reuse performance for simpler framing; measure separately.

## Validation

Inspect `build.sbt`, suite declarations, platform layout first. In authorized isolated checkout: `sbt projects`, `sbt 'ember-core / Test / definedTests'`. #4348: `sbt 'ember-core / testOnly org.http4s.ember.core.ParsingSpec' 'ember-client / testOnly org.http4s.ember.client.internal.ClientHelpersSuite'`. #7369: file is ParserSuite.scala, class is **ParsingSuite**, so `sbt 'ember-core / testOnly org.http4s.ember.core.ParsingSuite'`. Inspected CE3 crossproject build: JVM project IDs have no JVM suffix. Verify selectors on target branch; require nonzero discovery.

Three oracle layers: (a) fixed-body partial/full completion, exact body/remainder bytes; (b) reuse flag and saved-byte transitions, including never-pulled bodies; (c) real owner/socket closure or safe reuse. Layer (c) must stage valid HEAD with no body, buffered excess bytes, delayed excess bytes, subsequent exchange, explicit close headers, early consumer termination, cancellation. Observe connection identity and close/reuse events; single-chunk parser assertion cannot replace this. #4348's two-response test is parser-level, not network. No upstream tests or sockets ran for this procedure.

## Examples

### Good

Five-byte body shares input chunk with next response prelude. Consume exactly first body, keep remaining prelude, parse next response from it. Historical two-response test expects `hello` then `world`; helper tests separate reusable empty remainder from incomplete `None`. Keep these oracles when simplifying parser.

### Broken and Correction

HEAD patch returns empty body and `None`; pool cleanup maps `None` to empty array, marks connection reusable. Test checks only empty body/rest. Correction: keep non-reuse for unknown/discarded state, trace owner release. If reuse is required, implement and test justified framing policy with delayed-input and subsequent-exchange cases. Do not fix by reading HEAD representation's Content-Length.

### Negative

Previous ordinary response fully consumed, drain returns `Some(empty)`, next exchange not started. Do not flag missing already-buffered next-response bytes as unsafe. #4348 explicitly separates this common non-pipelined case from incompletely consumed body. Preserve other close/version policies before permitting reuse.

## Output Contract

Per finding: `file:line`, severity, method/status/framing branch, four-fact byte/disposition table, evidence ID, smallest correction, discriminating test. Tag each observation parser-only, helper-state-only, reviewer testimony or executed transport evidence. Include exact versions, discovered selectors, outstanding socket tests. Never turn structural pass into safety certification.

## Limitations

Historical review accepted #7369 with reviewer-reported aggressive HEAD closure. Source inspection supports its non-reuse path; no close event reproduced. #4348 deferred more exhaustive chunking and socket-draining work. Neither history proves current transport safety, protocol-wide compliance or performance. Generic CE cancellation/resource internals and other libraries' pool-handoff races: separate procedures.

## Sources

See [evidence and claims](evidence/scala-http4s-http1-bodyless-connection-framing.json): `c-framing-connection-contract` and `c-drain-reuse-state`.

- [Resource-level cleanup discussion](https://github.com/http4s/http4s/pull/4348#discussion_r573734431) and [empty versus incomplete remainder](https://github.com/http4s/http4s/pull/4348#discussion_r574987281).
- [Historical reuse consumer](https://github.com/http4s/http4s/blob/32893c3373bd735b101f28f28bec70936293a7f7/ember-client/src/main/scala/org/http4s/ember/client/internal/ClientHelpers.scala#L132-L146).
- [HEAD drain concern](https://github.com/http4s/http4s/pull/7369#discussion_r1587508509) and [qualified final disposition](https://github.com/http4s/http4s/pull/7369#pullrequestreview-2038478780).
