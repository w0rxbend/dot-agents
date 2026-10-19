---
name: javascript-pro
description: Write and debug modern JavaScript runtime behavior in Node.js and browsers - event-loop and microtask ordering, async error handling, cancellation with AbortController, Promise combinators, ESM/CommonJS interop, the node:test runner and ES2022+ features. Use for async bugs, module-loading errors and modernizing JS; not for TypeScript type design or framework architecture.
risk: safe
source: community
date_added: '2026-02-27'
---

# Modern JavaScript

## 1. Pin the runtime first

Behavior below depends on the runtime. Check before using newer APIs:

- Node: `node -v`, `"engines"` in `package.json`, `"type"` (`"module"` or
  `"commonjs"`), and file extensions (`.mjs` = ESM, `.cjs` = CommonJS).
- Browsers: the project's browserslist / build target; transpiling does not
  polyfill runtime APIs such as `AbortSignal.any` or `Object.groupBy`.

| Feature | Node | Notes |
|---------|------|-------|
| `Error` `cause`, `Object.hasOwn`, `.at()`, class `#private`, top-level `await` | 16.9+ | ES2022 |
| `toSorted`/`toReversed`/`with`, `findLast` | 20+ | ES2023, non-mutating array copies |
| `AbortSignal.any`, `AbortSignal.timeout` | 20.3+ / 17.3+ | |
| `import.meta.dirname` / `filename` | 20.11+ | replaces the `fileURLToPath` dance |
| `Object.groupBy`, `Map.groupBy` | 21+ | returns a null-prototype object |
| `Promise.withResolvers` | 22+ | |
| `require()` of ESM without flag | 22.12+ (backported to 20.19) | fails for ESM using top-level `await` |

Verify a version cell against the Node changelog when it matters for a release.

## 2. Event loop and microtask ordering

Order of work after the current synchronous code:

1. `process.nextTick` queue (Node only)
2. Promise microtasks (`.then`, `await` continuations, `queueMicrotask`)
3. Macrotasks: timers, I/O callbacks, `setImmediate`, browser events and rendering

```js
console.log('1 sync');
setTimeout(() => console.log('timeout'), 0);
Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
process.nextTick(() => console.log('nextTick'));
console.log('2 sync');
// CommonJS: 1 sync, 2 sync, nextTick, promise, microtask, timeout
// ESM (.mjs): 1 sync, 2 sync, promise, microtask, nextTick, timeout
```

The ESM difference is real: an ES module body already runs inside a promise
job, so promise microtasks drain before the nextTick queue. Do not write code
whose correctness depends on nextTick-vs-promise order. Likewise,
`setTimeout(0)` vs `setImmediate` order is unspecified in the main module (it is
deterministic only inside an I/O callback, where `setImmediate` runs first).

Practical rules:

- Long synchronous loops block everything, including already-resolved promises.
  Chunk CPU work (`await new Promise((r) => setImmediate(r))` between batches
  in Node, `setTimeout(r, 0)` in browsers) or move it to `worker_threads` /
  Web Workers.
- An endless chain of microtasks (recursive `queueMicrotask`/`nextTick`) starves
  I/O just like a busy loop.

## 3. Async error handling

| Situation | Do this |
|-----------|---------|
| Fire-and-forget promise | Attach `.catch` (or `void task().catch(log)`); a bare `task()` becomes an unhandled rejection |
| Loop with `await` per item | `for...of` (sequential) or `Promise.all(items.map(...))` (parallel) - never `forEach(async ...)`, which does not wait |
| Need all results, some may fail | `Promise.allSettled` and inspect `status` |
| First success wins (mirrors, fallbacks) | `Promise.any`; on total failure it rejects with `AggregateError` (`err.errors`) |
| First to settle wins (timeouts) | `Promise.race`, but prefer `AbortSignal.timeout` so the loser is cancelled too |
| Re-throwing with context | `throw new Error('load config failed', { cause: err })` |
| Process-wide safety net | `process.on('unhandledRejection', ...)` to log and set `process.exitCode = 1`; never to continue as if nothing happened |

Since Node 15, an unhandled rejection crashes the process by default. Attaching a
handler later (after the rejection) still counts as unhandled at the time and
emits `PromiseRejectionHandledWarning`.

Bounded concurrency without a library:

```js
async function mapLimit(items, limit, fn) {
  const results = new Array(items.length);
  let next = 0;
  const worker = async () => {
    while (next < items.length) {
      const i = next++;
      results[i] = await fn(items[i], i);
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}
```

## 4. Cancellation with AbortController

Thread one `signal` through every layer that does I/O or waits.

```js
async function fetchJson(url, { signal, timeoutMs = 5000 } = {}) {
  const timeout = AbortSignal.timeout(timeoutMs);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
  const res = await fetch(url, { signal: combined });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

const ac = new AbortController();
const pending = fetchJson('https://example.com/data.json', { signal: ac.signal });
ac.abort();   // pending rejects with AbortError
```

- `fetch` rejects with `AbortError` for a plain `abort()`, `TimeoutError` for
  `AbortSignal.timeout`, and with the reason itself if you call
  `abort(reason)`. Check `signal.aborted` (or those names) and treat it as
  cancellation, not failure.
- In your own loops call `signal.throwIfAborted()` between steps, and pass the
  signal to `node:timers/promises` `setTimeout(ms, value, { signal })`,
  `events.once`, streams and `fetch`.
- Remove listeners you add with `signal.addEventListener('abort', fn, { once: true })`
  when the operation finishes, or long-lived signals leak.

Retry with backoff and jitter that respects cancellation:

```js
import { setTimeout as sleep } from 'node:timers/promises';

async function retry(fn, { retries = 3, baseMs = 100, signal } = {}) {
  for (let attempt = 0; ; attempt++) {
    signal?.throwIfAborted();
    try {
      return await fn(attempt);
    } catch (err) {
      if (attempt >= retries) throw new Error(`failed after ${attempt + 1} attempts`, { cause: err });
      const delay = baseMs * 2 ** attempt * (0.5 + Math.random() / 2);
      await sleep(delay, undefined, { signal }); // rejects with AbortError on abort
    }
  }
}
```

Only retry idempotent operations, and stop retrying once `signal.aborted` is true.

## 5. ESM and CommonJS interop (Node)

| From | Importing | Works how |
|------|-----------|-----------|
| ESM | CJS | `import pkg from './x.cjs'` always works (`module.exports` is the default). Named imports work only when Node's static analysis detects them (`exports.a = ...`); `module.exports = { a: 1 }` may not expose `a` as a named export |
| ESM | CJS via `require` | `import { createRequire } from 'node:module'; const require = createRequire(import.meta.url);` |
| CJS | ESM | `require('./x.mjs')` on Node 22.12+/20.19+ returns the namespace (`.default` for the default export); throws `ERR_REQUIRE_ASYNC_MODULE` if the module uses top-level `await` |
| CJS | ESM (older Node, or TLA) | `const m = await import('./x.mjs')` (async) |

- ESM has no `__dirname`/`__filename`/`require`; use `import.meta.dirname`,
  `import.meta.filename`, or `new URL('./file', import.meta.url)`.
- ESM relative imports need the file extension (`./util.js`, not `./util`).
- Publishing a library: declare `"exports"` with `"import"`/`"require"`
  conditions (or ship ESM only and rely on `require(esm)` for modern Node).
  Avoid the dual-package hazard: never keep module-level state that would exist
  twice when both builds load.
- JSON in ESM: `import data from './data.json' with { type: 'json' };`.

## 6. Testing with node:test

```js
// retry.test.mjs - run with: node --test
import { test } from 'node:test';
import assert from 'node:assert/strict';

test('retries then succeeds', async (t) => {
  const fn = t.mock.fn(async (attempt) => {
    if (attempt < 2) throw new Error('boom');
    return 'ok';
  });
  assert.equal(await retry(fn, { baseMs: 1 }), 'ok');
  assert.equal(fn.mock.callCount(), 3);
});

test('keeps the last error as cause', async () => {
  await assert.rejects(
    retry(async () => { throw new Error('nope'); }, { retries: 1, baseMs: 1 }),
    (err) => err.cause.message === 'nope',
  );
});

test('fake timers', (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const cb = t.mock.fn();
  setTimeout(cb, 1000);
  t.mock.timers.tick(1000);
  assert.equal(cb.mock.callCount(), 1);
});
```

- Always `await` (or return) async assertions; `assert.rejects` without `await`
  passes vacuously.
- Useful flags: `--test-only`, `--test-name-pattern`, `--watch`,
  `--experimental-test-coverage` (check `node --help` for your version's spelling).
- Keep the project's existing runner (Vitest, Jest, Mocha) if there is one; use
  node:test for zero-dependency packages and scripts.

## 7. Modern language features worth using

| Prefer | Over | Why |
|--------|------|-----|
| `arr.at(-1)` | `arr[arr.length - 1]` | clarity |
| `toSorted()`, `toReversed()`, `with(i, v)` | `[...arr].sort()` | no accidental mutation of shared arrays |
| `Object.hasOwn(o, k)` | `o.hasOwnProperty(k)` | works on null-prototype objects |
| `structuredClone(v)` | `JSON.parse(JSON.stringify(v))` | keeps `Date`, `Map`, `Set`, cycles |
| `Object.groupBy(items, fn)` | hand-written reduce | readable grouping (Node 21+) |
| class `#private` fields and `#x in obj` brand checks | `_underscore` convention, `WeakMap` privacy | real encapsulation |
| `??`, `??=`, `?.` | `||` defaults | keeps `0`, `''`, `false` |
| `Error` `{ cause }` | string concatenation of messages | preserves the original stack |
| `Promise.withResolvers()` | capturing `resolve` in an outer `let` | Node 22+ |

## 8. Debugging checklist for async bugs

1. Reproduce with the smallest script; run it under both `.mjs` and `.cjs` if
   ordering is involved.
2. `node --trace-warnings`, `--unhandled-rejections=strict` and
   `--stack-trace-limit=50` surface lost rejections and truncated stacks.
3. Look for missing `await`, `forEach(async ...)`, promises created but never
   awaited, and `try/catch` around a non-awaited call (it catches nothing).
4. For hangs: find the pending promise or open handle (`node --inspect` and the
   async stack in DevTools; `why-is-node-running` if available).
5. For memory growth: listeners never removed, unbounded caches/maps, timers
   never cleared, signals that live forever.

## Done when

- Runtime target and module type are known, and every API used exists there.
- No floating promises: each one is awaited, returned, or has a `.catch`.
- Long-running or remote operations accept an `AbortSignal` and have a timeout.
- Behavior is covered by tests that `await` their assertions, and the snippet or
  test was actually run with the target Node version.
