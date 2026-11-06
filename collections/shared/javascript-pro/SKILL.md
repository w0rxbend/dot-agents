---
name: javascript-pro
description: Write and debug modern JavaScript runtime behavior in Node.js and browsers - event-loop and microtask ordering, async error handling, cancellation with AbortController, Promise combinators, ESM/CommonJS interop, the node:test runner and ES2022+ features. Use for async bugs, module-loading errors and modernizing JS; not for TypeScript type design or framework architecture.
risk: safe
source: community
date_added: '2026-02-27'
---

# Modern JavaScript

## 1. Pin the runtime first

Behavior depends on runtime. Check before using newer APIs:

- Node: `node -v`, `"engines"` in `package.json`, `"type"` (`"module"` or
  `"commonjs"`), file extensions (`.mjs` = ESM, `.cjs` = CommonJS).
- Browsers: project's browserslist / build target. Transpiling does not
  polyfill runtime APIs such as `AbortSignal.any` or `Object.groupBy`.

| Feature | Node | Notes |
|---------|------|-------|
| `Error` `cause`, `Object.hasOwn`, `.at()`, class `#private`, top-level `await` | 16.9+ | ES2022 |
| `toSorted`/`toReversed`/`with`, `findLast` | 20+ | ES2023, non-mutating array copies |
| `AbortSignal.any`, `AbortSignal.timeout` | 20.3+ / 17.3+ | |
| `import.meta.dirname` / `filename` | 20.11+ | replaces `fileURLToPath` dance |
| `Object.groupBy`, `Map.groupBy` | 21+ | returns null-prototype object |
| `Promise.withResolvers` | 22+ | |
| `require()` of ESM without flag | 22.12+ (backported to 20.19) | fails for ESM using top-level `await` |

Verify version cell against Node changelog when it matters for a release.

## 2. Event loop and microtask ordering

Order of work after current synchronous code:

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

ESM difference is real: ES module body already runs inside a promise job, so
promise microtasks drain before nextTick queue. Do not make correctness depend
on nextTick-vs-promise order. `setTimeout(0)` vs `setImmediate` order is
unspecified in main module; deterministic only inside an I/O callback, where
`setImmediate` runs first.

Rules:

- Long synchronous loops block everything, even already-resolved promises.
  Chunk CPU work (`await new Promise((r) => setImmediate(r))` between batches
  in Node, `setTimeout(r, 0)` in browsers) or move it to `worker_threads` /
  Web Workers.
- Endless microtask chain (recursive `queueMicrotask`/`nextTick`) starves I/O
  like a busy loop.

## 3. Async error handling

| Situation | Do this |
|-----------|---------|
| Fire-and-forget promise | Attach `.catch` (or `void task().catch(log)`); bare `task()` becomes unhandled rejection |
| Loop with `await` per item | `for...of` (sequential) or `Promise.all(items.map(...))` (parallel). Never `forEach(async ...)`, which does not wait |
| Need all results, some may fail | `Promise.allSettled`, inspect `status` |
| First success wins (mirrors, fallbacks) | `Promise.any`; on total failure rejects with `AggregateError` (`err.errors`) |
| First to settle wins (timeouts) | `Promise.race`; prefer `AbortSignal.timeout` so loser is cancelled too |
| Re-throwing with context | `throw new Error('load config failed', { cause: err })` |
| Process-wide safety net | `process.on('unhandledRejection', ...)` to log and set `process.exitCode = 1`; never to continue as if nothing happened |

Since Node 15, unhandled rejection crashes process by default. Attaching handler
later (after rejection) still counts as unhandled at that time, and emits
`PromiseRejectionHandledWarning`.

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

Thread one `signal` through every layer doing I/O or waiting.

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

- `fetch` rejects with `AbortError` for plain `abort()`, `TimeoutError` for
  `AbortSignal.timeout`, and with reason itself for `abort(reason)`. Check
  `signal.aborted` (or those names). Treat it as cancellation, not failure.
- In your own loops, call `signal.throwIfAborted()` between steps. Pass signal to
  `node:timers/promises` `setTimeout(ms, value, { signal })`, `events.once`,
  streams and `fetch`.
- Remove listeners added with `signal.addEventListener('abort', fn, { once: true })`
  when operation finishes, or long-lived signals leak.

Retry with backoff and jitter, respecting cancellation:

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

Retry only idempotent operations. Stop retrying once `signal.aborted` is true.

## 5. ESM and CommonJS interop (Node)

| From | Importing | Works how |
|------|-----------|-----------|
| ESM | CJS | `import pkg from './x.cjs'` always works (`module.exports` is default). Named imports work only when Node's static analysis detects them (`exports.a = ...`); `module.exports = { a: 1 }` may not expose `a` as named export |
| ESM | CJS via `require` | `import { createRequire } from 'node:module'; const require = createRequire(import.meta.url);` |
| CJS | ESM | `require('./x.mjs')` on Node 22.12+/20.19+ returns namespace (`.default` for default export); throws `ERR_REQUIRE_ASYNC_MODULE` if module uses top-level `await` |
| CJS | ESM (older Node, or TLA) | `const m = await import('./x.mjs')` (async) |

- ESM has no `__dirname`/`__filename`/`require`. Use `import.meta.dirname`,
  `import.meta.filename`, or `new URL('./file', import.meta.url)`.
- ESM relative imports need file extension (`./util.js`, not `./util`).
- Publishing library: declare `"exports"` with `"import"`/`"require"`
  conditions (or ship ESM only, relying on `require(esm)` for modern Node).
  Avoid dual-package hazard: never keep module-level state that would exist
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

- Always `await` (or return) async assertions. `assert.rejects` without `await`
  passes vacuously.
- Flags: `--test-only`, `--test-name-pattern`, `--watch`,
  `--experimental-test-coverage` (check `node --help` for your version's spelling).
- Keep project's existing runner (Vitest, Jest, Mocha) if any. Use node:test
  for zero-dependency packages and scripts.

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
| `Error` `{ cause }` | string concatenation of messages | preserves original stack |
| `Promise.withResolvers()` | capturing `resolve` in outer `let` | Node 22+ |

## 8. Debugging checklist for async bugs

1. Reproduce with smallest script. If ordering is involved, run it under both
   `.mjs` and `.cjs`.
2. `node --trace-warnings`, `--unhandled-rejections=strict` and
   `--stack-trace-limit=50` surface lost rejections and truncated stacks.
3. Look for missing `await`, `forEach(async ...)`, promises created but never
   awaited, and `try/catch` around non-awaited call (catches nothing).
4. Hangs: find pending promise or open handle (`node --inspect` and async stack
   in DevTools; `why-is-node-running` if available).
5. Memory growth: listeners never removed, unbounded caches/maps, timers never
   cleared, signals living forever.

## Done when

- Runtime target and module type known; every API used exists there.
- No floating promises: each is awaited, returned, or has `.catch`.
- Long-running or remote operations accept `AbortSignal` and have timeout.
- Behavior covered by tests that `await` their assertions. Snippet or test was
  actually run with target Node version.
