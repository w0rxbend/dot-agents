---
name: python-async-patterns
user-invocable: false
description: Write and debug asyncio code on Python 3.11+ - TaskGroup structured concurrency, asyncio.timeout, cancellation, queues, semaphores, async context managers/iterators, and offloading blocking or CPU work with to_thread/executors. Use for async Python code; use python-patterns for sync-vs-async architecture choices.
allowed-tools:
  - Bash
  - Read
---

# Python Async Patterns

Use asyncio for I/O-bound concurrency. Check the project's minimum Python
(`requires-python` in `pyproject.toml`) first: `asyncio.TaskGroup` and
`asyncio.timeout()` need 3.11+. On 3.8-3.10 use the fallbacks noted below, or
`anyio` if the project already depends on it.

## Decision Table

| Need | Use (3.11+) | Pre-3.11 fallback |
|------|-------------|-------------------|
| Run a program | `asyncio.run(main())` | same (3.7+) |
| Run N coroutines, fail fast, no leaks | `async with asyncio.TaskGroup()` | `gather()` + manual cancel |
| Run N, collect failures individually | `gather(..., return_exceptions=True)` | same |
| First result wins / progress as they finish | `asyncio.wait(FIRST_COMPLETED)` / `as_completed` | same |
| Deadline on a block of code | `async with asyncio.timeout(s)` | `asyncio.wait_for(coro, s)` |
| Limit concurrency | `asyncio.Semaphore(n)` | same |
| Call a blocking function | `await asyncio.to_thread(fn, *args)` (3.9+) | `loop.run_in_executor(None, ...)` |
| CPU-bound work | `ProcessPoolExecutor` via `loop.run_in_executor` | same |
| Producer/consumer | `asyncio.Queue` (+ `Queue.shutdown()` on 3.13+) | sentinels |

## Basics

```python
import asyncio

async def fetch(url: str) -> str:
    await asyncio.sleep(0.1)  # stands in for real I/O
    return f"data from {url}"

async def main() -> None:
    print(await fetch("https://api.example.com"))

asyncio.run(main())  # the only entry point you normally need
```

Calling `fetch(url)` without `await` only creates a coroutine object; nothing runs.

## Structured Concurrency with TaskGroup

A `TaskGroup` owns its tasks: the `async with` block does not exit until every
task has finished. If one task raises, the group cancels the others and raises
an `ExceptionGroup`. No task can outlive the block, so nothing leaks and no
error is silently dropped.

```python
import asyncio

async def fetch(n: int) -> int:
    await asyncio.sleep(0.1)
    if n == 3:
        raise ValueError(f"bad item {n}")
    return n * 2

async def main() -> None:
    # Happy path: results are read from the task objects after the block
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(n)) for n in (1, 2)]
    print([t.result() for t in tasks])  # [2, 4]

    # Failure path: siblings are cancelled, errors arrive as an ExceptionGroup
    try:
        async with asyncio.TaskGroup() as tg:
            for n in (1, 2, 3):
                tg.create_task(fetch(n))
    except* ValueError as eg:
        for exc in eg.exceptions:
            print("failed:", exc)

asyncio.run(main())
```

Choose between the multi-task APIs:

- `TaskGroup`: default for "do these together". It fails fast and cancels the
  rest.
- `gather(*coros, return_exceptions=True)`: when partial success is acceptable
  and you inspect each result. Without `return_exceptions`, `gather` propagates
  the first error but **does not cancel** the other tasks.
- `asyncio.wait` / `as_completed`: races and incremental processing. Always
  cancel and await the leftovers.

```python
async def first_successful(urls: list[str]) -> str:
    tasks = {asyncio.create_task(fetch_url(u)) for u in urls}
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        return done.pop().result()
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)  # reap cancelled tasks
```

### Background tasks

`asyncio.create_task()` outside a TaskGroup creates an unowned task. The event
loop keeps only a weak reference to it, so keep a strong reference or it can be
garbage-collected mid-run. Its exceptions surface only when it is awaited.

```python
background: set[asyncio.Task[None]] = set()

def spawn(coro) -> None:
    task = asyncio.create_task(coro)
    background.add(task)
    task.add_done_callback(background.discard)
```

Prefer a long-lived `TaskGroup` (for example in an app lifespan handler) over
loose tasks.

## Timeouts and Cancellation

```python
import asyncio

async def main() -> None:
    try:
        async with asyncio.timeout(2.0):     # 3.11+; covers the whole block
            await slow_operation()
            await another_step()
    except TimeoutError:                     # builtin; asyncio.TimeoutError is an alias since 3.11
        print("timed out")

    # Single awaitable, any version:
    try:
        await asyncio.wait_for(slow_operation(), timeout=2.0)
    except asyncio.TimeoutError:             # needed spelling before 3.11
        print("timed out")
```

Cancellation is delivered as `asyncio.CancelledError` at the next `await`:

```python
async def worker() -> None:
    try:
        while True:
            await do_unit_of_work()
    except asyncio.CancelledError:
        await flush_buffers()   # cleanup is fine
        raise                   # always re-raise; swallowing it breaks TaskGroup and timeout()
```

- Never use a bare `except:` or `except BaseException:` that swallows
  `CancelledError` (it subclasses `BaseException` since 3.8).
- Use `asyncio.shield()` only for work that must finish even if the caller is
  cancelled, and still bound it with a timeout.
- `task.cancel()` only requests cancellation; `await` the task to know it is done.

## Bounding Concurrency

```python
import asyncio
import httpx

async def fetch_all(urls: list[str], limit: int = 10) -> list[str]:
    sem = asyncio.Semaphore(limit)

    async with httpx.AsyncClient(timeout=10) as client:
        async def fetch_one(url: str) -> str:
            async with sem:
                r = await client.get(url)
                r.raise_for_status()
                return r.text

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch_one(u)) for u in urls]
    return [t.result() for t in tasks]
```

Reuse one client/session (httpx `AsyncClient` or aiohttp `ClientSession`) per
application, not per request. Spawning thousands of tasks is fine; opening
thousands of sockets at once is not, so the semaphore is the limit that matters.

Use `asyncio.Lock` only to protect state across an `await`. Code with no
`await` between read and write is already atomic with respect to other tasks.

## Producer / Consumer with Queue

```python
import asyncio

async def producer(queue: asyncio.Queue[int], n: int) -> None:
    for i in range(n):
        await queue.put(i)          # blocks when the queue is full (backpressure)

async def consumer(name: str, queue: asyncio.Queue[int]) -> None:
    while True:
        item = await queue.get()
        try:
            await asyncio.sleep(0.01)
            print(f"{name} processed {item}")
        finally:
            queue.task_done()

async def main() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=5)
    consumers = [asyncio.create_task(consumer(f"c{i}", queue)) for i in range(2)]

    await producer(queue, 10)
    await queue.join()              # every item has been task_done()

    for c in consumers:
        c.cancel()
    await asyncio.gather(*consumers, return_exceptions=True)

asyncio.run(main())
```

On 3.13+, `queue.shutdown()` makes waiting `get()` calls raise
`asyncio.QueueShutDown`, which replaces sentinel values and manual cancellation.

## Async Context Managers and Iterators

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

@asynccontextmanager
async def connection(url: str) -> AsyncIterator[Conn]:
    conn = await Conn.open(url)
    try:
        yield conn
    finally:
        await conn.close()           # runs on error and on cancellation

async def paginate(client, url: str) -> AsyncIterator[dict]:
    while url:
        page = await client.get_json(url)
        for item in page["items"]:
            yield item
        url = page.get("next")

async def main() -> None:
    async with connection("db://localhost") as conn:
        async for item in paginate(conn, "/items"):
            ...
```

Use `contextlib.AsyncExitStack` to manage a dynamic number of async resources.
If you stop iterating an async generator early, close it explicitly with
`contextlib.aclosing(gen)` (3.10+) so its `finally` runs promptly.

## Blocking and CPU-bound Work

The event loop runs one thing at a time. Any blocking call (`time.sleep`,
`requests`, sync DB drivers, large JSON parsing, file hashing) stalls every task.

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def checksum(path: str) -> str: ...      # blocking I/O
def crunch(n: int) -> int:               # CPU-bound
    return sum(i * i for i in range(n))

async def main() -> None:
    digest = await asyncio.to_thread(checksum, "big.bin")   # 3.9+, default thread pool

    loop = asyncio.get_running_loop()                       # never get_event_loop() here
    with ProcessPoolExecutor() as pool:
        results = await asyncio.gather(
            *(loop.run_in_executor(pool, crunch, 10_000_000) for _ in range(4))
        )

if __name__ == "__main__":   # required for ProcessPoolExecutor with spawn start methods
    asyncio.run(main())
```

- Threads help with blocking I/O; for CPU-bound Python code they do not
  (the GIL), except on free-threaded builds. Use processes for CPU work.
- Arguments and results crossing a process pool must be picklable.

## Legacy and Embedding: Manual Loop Management

Application code should not create, set, or fetch event loops. Use
`asyncio.run()` at the entry point and `asyncio.get_running_loop()` inside
coroutines. `asyncio.get_event_loop()` without a running loop is deprecated and
warns or fails on current Python versions.

Touch loops directly only when embedding asyncio in a host that owns the thread
(GUI toolkits, plugin hosts, tests of the loop itself). There, prefer
`asyncio.Runner` (3.11+) over hand-written `new_event_loop` /
`run_until_complete` / `close` sequences:

```python
with asyncio.Runner() as runner:
    runner.run(setup())
    runner.run(serve())
```

To submit work to a loop running in another thread, use
`asyncio.run_coroutine_threadsafe(coro, loop)` and wait on the returned
`concurrent.futures.Future`.

## Debugging

- Run with `PYTHONASYNCIODEBUG=1` or `asyncio.run(main(), debug=True)` to log
  never-awaited coroutines and callbacks that block the loop for more than 100 ms.
- "Task exception was never retrieved" means an unowned task failed; move it into
  a TaskGroup or await it.
- "Task was destroyed but it is pending" usually means the task had no strong
  reference or the loop closed first.
- Test with `pytest-asyncio` or anyio's pytest plugin; see `pytest-fixtures` for
  async fixtures.

## Common Pitfalls

- Forgetting `await` (the coroutine never runs; a `RuntimeWarning` appears).
- Blocking calls inside `async def` (`time.sleep`, `requests`, sync drivers).
- `gather()` without `return_exceptions` and assuming siblings were cancelled.
- Swallowing `CancelledError`, or a bare `except:` around awaits.
- Unbounded fan-out: thousands of simultaneous connections with no semaphore.
- Fire-and-forget `create_task` without keeping a reference.
- Creating a new HTTP client per request.
- Forgetting `task_done()` after `queue.get()`, so `queue.join()` hangs.

## Done When

- No unowned tasks: concurrent work runs in a `TaskGroup` (or is explicitly
  reaped), and every network call has a timeout.
- Blocking and CPU work is offloaded; running with `debug=True` shows no slow
  callbacks or never-awaited coroutines.
- Cancellation was exercised (timeout or Ctrl-C) and cleanup ran.

## Resources

- [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [asyncio task groups and timeouts](https://docs.python.org/3/library/asyncio-task.html)
- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html)
