# Rules

Apply to every cross-process call, pool, queue, cache, and buffer you add or change. One slow dependency does not exhaust the process.

When two sources disagree, follow [sources.md](sources.md). Do not pick a new winner here.

## Deadlines

- Set a connect deadline and a read deadline. A connect deadline does not bound the read.
- Do not keep a library default that waits for minutes or forever.
- Put the unit in the name. Do not copy a sample number from a page or a snippet.
- A deadline the caller already exceeded is not work worth starting.

## Retries

- Retry only work that is idempotent, or work that carries an idempotency key that makes a repeat safe.
- Retry at one layer. Do not let a client, a gateway, and a worker each retry the same call.
- Use a hard attempt cap, a capped backoff, and jitter.
- Never retry a permanent client error: malformed input, failed auth, or a missing resource.
- Do not retry a call the breaker has already rejected.
- An overload response may back off inside that same single retry layer. It still has a cap.

## Circuit breaker

- Give the dependency its own breaker.
- Trip when the recent failure rate crosses the threshold. Do not use a counter that never expires.
- Do not trip on a permanent client error or a domain rejection.
- While open, fail the call immediately. Do not wait for the deadline.
- Then admit only a few probes. Probes that succeed restore full traffic. A failed probe opens the breaker again.
- If a mesh or gateway already breaks this dependency, do not add a second breaker for the same failure. The call deadline still belongs on the waiter.

## Bulkheads

- Give each upstream its own pool or concurrency limit.
- A stalled call occupies only that upstream's limit.
- Do not share one thread pool, connection pool, or worker set across unrelated upstreams.
- Isolate the critical path from a pool that serves low-value work.

## Buffers

- Cap every queue, cache, and buffer.
- When it is full, reject the work or slow the producer. Do not allocate a larger buffer.
- Do not put an unbounded in-memory queue in front of a slow consumer.
- A cache cap includes eviction. Growth without eviction is not a cap.

## Steady state

- Reclaim logs, rows, temp files, and cache entries in application code.
- Steady running does not depend on a person purging them.
- A successful call still frees the temporary resource it took.

## Fail fast and shed

- Reject invalid input before taking a lock, a connection, or a worker slot.
- If the dependency is already known to be down, fail before taking that slot.
- Under overload, shed or degrade low-value work first.
- Keep one path that still serves the critical function.
- Do not build a second full copy of the feature to act as the degraded path.

## What not to add

- Do not add a retry wrapper that lacks an idempotency check, a cap, backoff, and jitter.
- Do not add a breaker around an in-process pure call.
- Do not hide a dropped deadline inside a shared helper that has no unit in its name.
