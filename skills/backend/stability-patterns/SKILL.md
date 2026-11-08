---
name: stability-patterns
description: "When a service calls other processes or holds queues and pools, bound connect and read deadlines, retries, circuit breakers, bulkheads, and buffers so one failed or slow dependency cannot exhaust the process. Use when adding or reviewing a remote call, pool, queue, cache, or retry. Use saga-orchestration for multi-step compensation, designing-sdks for a client library's retry API, and using-message-queues for broker setup."
license: MIT
---

# Stability patterns

One failed or slow dependency must not take the process down. Bound the wait, the retry, the concurrency, and the buffer.

## When to Use

Use when a service calls another process, or when you add or change a queue, a pool, a cache, a buffer, or a retry.

Skip an in-process pure call. Skip installing a broker. Skip designing a multi-step compensation.

Other skills keep their jobs:

- `designing-sdks` owns the public retry surface of a client library.
- `designing-apis` owns idempotency and rate-limit fields on a network contract.
- `saga-orchestration` owns compensation across services.
- `using-message-queues` owns the broker.
- `observability-and-instrumentation` owns metrics and alerts.
- `backend-patterns` is a Node snippet file. Its sample retry is not this policy.

## Before the edit

1. Read [references/rules.md](references/rules.md). Apply it to every call, pool, and buffer you add or change.
2. Name the dependency, the resource it can exhaust, and the critical function that must still run.
3. Find the bound that already exists in a mesh, a gateway, or a pool. Do not add a second copy of that same bound.
4. Do not invent a threshold from a sample. Use the project's numbers. Put the unit in the name.

## While editing

- Set an explicit connect deadline and an explicit read deadline on every cross-process call.
- Retry only idempotent or idempotency-keyed work, at one layer, with a hard attempt cap, capped backoff, and jitter.
- When a dependency's recent failure rate crosses its threshold, fail immediately. Admit a few probes before full traffic.
- Give each upstream its own pool or concurrency limit.
- Cap every queue, cache, and buffer. When it is full, reject or slow the producer.
- Reclaim logs, rows, temp files, and cache entries in application code.
- Reject bad input, and a dependency already known to be down, before taking a lock, a connection, or a worker slot.
- Under overload, shed or degrade low-value work first. Keep a path that still serves the critical function.

## Stop

Stop when each call and buffer you touched has a named bound, and one stalled dependency cannot hold every thread, connection, or worker. Do not tune unrelated calls.

## Report

For each dependency: deadlines, retry rule, breaker threshold, pool or concurrency limit, and buffer cap. Name the critical path you kept. Name any bound the platform already enforced, and any number the project did not supply.

## Limitations

This skill does not choose a product, write a load test, or design compensation. It does not copy sample timeouts from a source. Cite [references/sources.md](references/sources.md). Conflict winners live only in that file.
