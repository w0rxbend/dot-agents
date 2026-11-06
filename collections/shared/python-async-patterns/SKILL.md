---
name: python-async-patterns
user-invocable: false
description: Write and debug asyncio code on Python 3.11+ - TaskGroup structured concurrency, asyncio.timeout, cancellation, queues, semaphores, async context managers/iterators, and offloading blocking or CPU work with to_thread/executors. Use for async Python code; use python-patterns for sync-vs-async architecture choices.
allowed-tools:
  - "Bash(pytest:*)"
  - "Bash(python -m pytest:*)"
  - "Bash(uv run pytest:*)"
  - Read
---

# Python Async Patterns

Use asyncio for I/O-bound concurrency. Check minimum Python first
(`requires-python` in `pyproject.toml`): `asyncio.TaskGroup` and
`asyncio.timeout()` need 3.11+. On 3.8-3.10 use fallbacks below, or `anyio` if
already a dependency.

## Decision Table

| Need | Use (3.11+) | Pre-3.11 fallback |
|------|-------------|-------------------|
| Run program | `asyncio.run(main())` | same (3.7+) |
| Run N coroutines, fail fast, no leaks | `async with asyncio.TaskGroup()` | `gather()` + manual cancel |
| Run N, collect failures individually | `gather(..., return_exceptions=True)` | same |
| First result wins / progress as each finishes | `asyncio.wait(FIRST_COMPLETED)` / `as_completed` | same |
| Deadline on code block | `async with asyncio.timeout(s)` | `asyncio.wait_for(coro, s)` |
| Limit concurrency | `asyncio.Semaphore(n)` | same |
| Call blocking function | `await asyncio.to_thread(fn, *args)` (3.9+) | `loop.run_in_executor(None, ...)` |
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

## Structured Concurrency with TaskGroup

`TaskGroup` owns its tasks: `async with` exits only after every task finishes.
If one task raises, group cancels others and raises `ExceptionGroup`.

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

Multi-task APIs:

- `TaskGroup`: default for "do these together". Fails fast, cancels rest.
- `gather(*coros, return_exceptions=True)`: when partial success is acceptable
  and you inspect each result. Without `return_exceptions`, `gather` propagates first error
  but **does not cancel** other tasks.
- `asyncio.wait` / `as_completed`: races, incremental processing. Always cancel
  and await leftovers.

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

`asyncio.create_task()` outside TaskGroup makes unowned task. Event loop holds
only weak reference. Keep strong reference, or task can be garbage-collected
mid-run. Its exceptions surface only on await.

```python
background: set[asyncio.Task[None]] = set()

def spawn(coro) -> None:
    task = asyncio.create_task(coro)
    background.add(task)
    task.add_done_callback(background.discard)
```

Prefer long-lived `TaskGroup` (for example in app lifespan handler) over loose
tasks.

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

Cancellation arrives as `asyncio.CancelledError` at next `await`:

```python
async def worker() -> None:
    try:
        while True:
            await do_unit_of_work()
    except asyncio.CancelledError:
        await flush_buffers()   # cleanup is fine
        raise                   # always re-raise; swallowing it breaks TaskGroup and timeout()
```

- Never use bare `except:` or `except BaseException:` that swallows
  `CancelledError` (subclasses `BaseException` since 3.8).
- Use `asyncio.shield()` only for work that must finish even if caller is
  cancelled. Still bound it with timeout.
- `task.cancel()` only requests cancellation. `await` task to confirm done.

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
application, not per request. Thousands of tasks: fine. Thousands of sockets
at once: not fine. Semaphore is the limit that matters.

Use `asyncio.Lock` only to protect state across `await`. Code with no `await`
between read and write is already atomic relative to other tasks.

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
`asyncio.QueueShutDown`, replacing sentinels and manual cancellation.

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

Use `contextlib.AsyncExitStack` for dynamic number of async resources. Stopping
async generator early: close it with `contextlib.aclosing(gen)` (3.10+) so its
`finally` runs promptly.

## Blocking and CPU-bound Work

Event loop runs one thing at a time. Any blocking call (`time.sleep`,
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

- Threads help blocking I/O, not CPU-bound Python code (GIL), except on
  free-threaded builds. Use processes for CPU work.
- Process pool arguments and results must be picklable.

## Legacy and Embedding: Manual Loop Management

Do not create, set or fetch event loops in application code. Use
`asyncio.run()` at entry point, `asyncio.get_running_loop()` inside coroutines.
`asyncio.get_event_loop()` without running loop is deprecated; warns or fails on
current Python versions.

Touch loops directly only when embedding asyncio in host owning the thread (GUI
toolkits, plugin hosts, tests of loop itself). There, prefer `asyncio.Runner`
(3.11+) over hand-written `new_event_loop` / `run_until_complete` / `close`
sequences:

```python
with asyncio.Runner() as runner:
    runner.run(setup())
    runner.run(serve())
```

Submit work to loop in another thread with
`asyncio.run_coroutine_threadsafe(coro, loop)`; wait on returned
`concurrent.futures.Future`.

## Debugging

- `PYTHONASYNCIODEBUG=1` or `asyncio.run(main(), debug=True)` logs
  never-awaited coroutines and callbacks blocking loop for more than 100 ms.
- "Task exception was never retrieved": unowned task failed. Move it into
  TaskGroup or await it.
- "Task was destroyed but it is pending": usually no strong reference, or loop
  closed first.
- Test with `pytest-asyncio` or anyio's pytest plugin. Async fixtures: see
  `pytest-fixtures`.

## Common Pitfalls

- Forgetting `await` (coroutine never runs; `RuntimeWarning` appears).
- Missing `task_done()` after `queue.get()`, so `queue.join()` hangs.

## Done When

- No unowned tasks: concurrent work runs in `TaskGroup` (or explicitly
  reaped). Every network call has timeout.
- Blocking and CPU work offloaded. `debug=True` run shows no slow callbacks or
  never-awaited coroutines.
- Cancellation exercised (timeout or Ctrl-C); cleanup ran.

## Resources

- [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [asyncio task groups and timeouts](https://docs.python.org/3/library/asyncio-task.html)
- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html)
