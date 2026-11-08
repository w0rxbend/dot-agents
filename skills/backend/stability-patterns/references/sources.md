# Sources

Distilled. Not a copy. Read the original before you cite a page.

## Pages

- Michael Nygard, *Release It!* second edition, pattern list on https://pragprog.com/titles/mnee2/release-it-second-edition/
- Martin Fowler, "Circuit Breaker" (2014), https://martinfowler.com/bliki/CircuitBreaker.html
- Microsoft, "Circuit Breaker pattern", https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- Microsoft, "Bulkhead pattern", https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
- Marc Brooker, "Timeouts, retries, and backoff with jitter", https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Google SRE, "Addressing Cascading Failures", https://sre.google/sre-book/addressing-cascading-failures/

The Pragmatic Bookshelf page names the patterns. It does not include the chapters. The AWS article now redirects to the Builder Center copy of the same piece.

## What each source contributes

- The *Release It!* page names Timeouts, Circuit Breaker, Bulkheads, Steady State, Fail Fast, Shed Load, and Create Back Pressure. It also names antipatterns: blocked threads, cascading failures, slow responses, and unbounded result sets. This skill uses those names. It does not adopt every pattern on that page.
- Fowler's breaker is a closed path that trips, then fails without calling the dependency. A later half-open probe checks recovery. Not every error trips it. Callers still need a response for the open state. State changes are worth monitoring. `observability-and-instrumentation` owns how that monitoring is built.
- The Azure breaker page separates retry from breaking. Retry expects a later success. The breaker stops calls that are likely to fail. Half-open traffic is a limited probe, not the full load. A time window keeps occasional faults from tripping the breaker. A breaker does not replace handling a business error. A mesh may already implement it.
- The Azure bulkhead page gives each dependency its own pool so one stalled call cannot empty the client's threads or connections. Partition critical consumers away from the rest. A platform limit that already isolates the resource does not need a second copy in application code.
- Brooker requires explicit timeouts, retries only for transient failure, a cap, exponential backoff, and jitter, so retries do not stampede a sick dependency. A connect timeout and a read timeout are different bounds.
- The SRE chapter treats overload as the usual start of a cascade. Bound queues, fail early, shed load, and degrade before the process dies. Retry at one layer. A stack of retries multiplies attempts. Do not retry a permanent error. Propagate deadlines so work that can no longer finish does not keep its slot.

## Winners

- **Numbers.** Source examples use toy thresholds. Do not copy them. The project supplies the number. The name carries the unit. If the project has no number, say so. Do not invent one.
- **What trips.** Fowler's short example counts failures and resets on success. Azure uses a recent window. The SRE text cares about overload, not a domain rejection. Trip on the recent failure rate. Do not trip on a permanent client error or a domain rejection.
- **Probes.** After the breaker opens, admit a few probes, then full traffic only if those probes succeed. Do not close the breaker by sending the normal load at once.
- **Where the retry sits.** Brooker and the SRE chapter both warn that stacked retries amplify load. One layer retries. A client library that already retries is that layer. `designing-sdks` owns the library's public retry API. This skill owns the bound inside the service.
- **Platform versus process.** Azure allows a mesh or a gateway to own breaking and throttling. Do not duplicate that bound. Still set the deadline on the call that waits.
- **Patterns left out.** The *Release It!* page also names Handshaking, Let It Crash, Governor, and Decoupling Middleware. This skill does not require them. `using-message-queues` owns the broker. `saga-orchestration` owns compensation.
- **Snippets.** `backend-patterns` shows a retry loop without an idempotency check, jitter, or a permanent-error split. This policy wins.
