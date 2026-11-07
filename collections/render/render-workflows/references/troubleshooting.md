# Troubleshooting

## Contents

- Task server issues
- Task registration issues
- Task execution issues
- Client issues
- Connection and networking
- Local development gotchas
- Limits reference

## Task Server Issues

### Task server won't start

**Symptom:** `render workflows dev` fails or hangs.

| Cause | Fix |
|-------|-----|
| CLI version < 2.11.0 | Check with `render --version`. Upgrade: `brew upgrade render` (macOS) or reinstall checksum-verified release (see SKILL.md Prerequisites). |
| Wrong start command | Python: `render workflows dev -- python workflows/main.py`. TypeScript: `render workflows dev -- npx tsx workflows/main.ts`. |
| Missing `app.start()` (Python) | Add `if __name__ == "__main__": app.start()` at bottom of entry point. |
| Port already in use | Use `--port` flag: `render workflows dev --port 8121 -- ...` |

### `app.start()` fails with `ValueError` (Python)

**Symptom:** `ValueError` about missing `RENDER_SDK_MODE` or `RENDER_SDK_SOCKET_PATH`.

**Cause:** `app.start()` expects env vars Render CLI sets. Running `python main.py` directly (without CLI) triggers this.

**Fix:** Always start via CLI: `render workflows dev -- python workflows/main.py`. CLI sets required env vars.

### Auto-start crashes with `process.exit(1)` (TypeScript)

**Symptom:** Process exits immediately, no useful error message.

**Cause:** SDK auto-starts task server via `setImmediate` when `RENDER_SDK_SOCKET_PATH` is set. If `startTaskServer()` throws, SDK calls `process.exit(1)` with only `console.error`.

**Fix:** Check `RENDER_SDK_SOCKET_PATH` points to valid, writable path. Use Render CLI for local dev. Set `RENDER_SDK_AUTO_START=false` to disable auto-start and start manually if needed.

## Task Registration Issues

### "Task not found" in CLI

**Symptom:** `render workflows tasks list --local` shows no tasks or misses expected ones.

| Cause | Fix |
|-------|-----|
| Module not imported (Python) | Entry point must import all task files or use `Workflows.from_workflows()`. |
| Module not imported (TypeScript) | Add `import './your-task-file'` to `index.ts` entry point. |
| Server not running | Start local task server first, then run `list --local` in second terminal. |
| Missing `--local` flag | Without `--local`, CLI lists deployed (remote) tasks, not local ones. |

### Late registration after auto-start (TypeScript)

**Symptom:** Dynamically imported tasks not available for execution; warning in logs.

**Cause:** SDK auto-starts via `setImmediate` after synchronous module loading. Tasks registered later (e.g., via dynamic `import()`) miss registration window.

**Fix:** Define all tasks at module scope with synchronous `import './module'` statements. Avoid dynamic imports for task files.

### Duplicate task names

**Symptom:** Python raises `ValueError("Task '{name}' already registered")`. TypeScript silently overwrites previous task.

**Cause:** Two tasks registered with same `name`.

**Fix:** Give every task unique name. In Python, `Workflows.from_workflows()` raises `ValueError` if any imported apps share task name.

### Empty task name (TypeScript)

**Symptom:** `Error: Task function must have a name or name must be provided`.

**Fix:** Always pass `name` in options object: `task({ name: "myTask" }, function myTask() { ... })`.

## Task Execution Issues

### Subtask hangs forever

**Symptom:** Task calling other tasks never completes.

| Cause | Fix |
|-------|-----|
| Missing `await` | Subtask calls return `TaskInstance` (Python) or `Promise` (TypeScript), not result. Must `await` them. |
| Missing `async` keyword | Python: chaining tasks must be declared `async def`. TypeScript: must use `async function`. |
| Sequential instead of parallel | Awaiting each subtask individually runs them serially. For parallel execution use `asyncio.gather()` (Python) or `Promise.all()` (TypeScript). |

### Calling subtask outside a task context (Python)

**Symptom:** `RuntimeError` about running subtask outside task execution context.

**Cause:** `@app.task` functions trigger subtask runs only when called inside another executing task. From regular code (e.g., script or REPL), internal `_current_client` context is not set, so call fails.

**Fix:** Outside tasks, use SDK client (`Render()` or `RenderAsync()`) with `start_task()` or `run_task()`. Subtask syntax is only for task-to-task chaining.

### Mixed positional and keyword arguments (Python)

**Symptom:** `ValueError` about not mixing positional and keyword arguments.

**Cause:** Python SDK does not allow calling subtask with both `*args` and `**kwargs` at once.

**Fix:** Use positional args or keyword args, not both: `await my_task(1, 2)` or `await my_task(a=1, b=2)`.

### "Not JSON serializable" error

**Symptom:** Task fails with serialization error.

| Cause | Fix |
|-------|-----|
| Non-serializable arguments | Task args must be JSON-serializable: dicts/objects, lists/arrays, strings, numbers, booleans, None/null. No class instances, functions, dates, sets, bytes, or `BigInt`. |
| Non-serializable return value | Same rule for return values. Convert complex objects to dicts/plain objects before returning. |
| Non-serializable default values (Python) | Defaults that aren't JSON-serializable are silently dropped; API metadata won't reflect them. Use only JSON-serializable defaults. |

### Task run fails silently

**Symptom:** Task run shows `failed` status with no useful error.

| Cause | Fix |
|-------|-----|
| Unhandled exception | Add logging inside task. Wrap risky code in try/except (Python) or try/catch (TypeScript). |
| No retry config | Add retry config so transient failures retry automatically. |
| Timeout exceeded | Default timeout: 2 hours. For more, set `timeout_seconds` (Python) or `timeoutSeconds` (TypeScript) per task. Max: 24 hours. |
| All retries exhausted | After `max_retries + 1` total attempts, run is marked failed. Inspect `TaskRunDetails.attempts` for per-attempt errors. |

### Timeout value rejected by API

**Symptom:** Task registration or run fails with validation error.

**Cause:** SDK does not validate `timeout_seconds`/`timeoutSeconds` client-side. Out-of-range values (outside 30–86,400) go to API, which rejects them.

**Fix:** Keep timeout values between 30 seconds and 86,400 seconds (24 hours).

## Client Issues

### `Render()` with `await` fails (Python)

**Symptom:** `TypeError` or unexpected behavior when using `await` with `Render()`.

**Fix:** `Render()` is synchronous client. Use `RenderAsync()` for async contexts:

```python
# Synchronous (Flask, Django, scripts)
from render_sdk import Render
render = Render()
result = render.workflows.run_task("my-workflow/task", [42])

# Asynchronous (FastAPI, async scripts)
from render_sdk import RenderAsync
render = RenderAsync()
result = await render.workflows.run_task("my-workflow/task", [42])
```

### "Invalid API key" or "Unauthorized"

| Cause | Fix |
|-------|-----|
| Missing `RENDER_API_KEY` | User sets env var in own shell: `export RENDER_API_KEY=rnd_...`. Never ask for key in chat. |
| Wrong key | Generate new key at `https://dashboard.render.com/u/*/settings#api-keys` |
| Key doesn't match workspace | Key must belong to workspace that owns workflow |
| No key and no token passed | Both `Render()` and `RenderAsync()` raise `ValueError` if no token is available |

### Argument too large

**Symptom:** Request rejected with size error.

**Fix:** Task arguments cannot exceed 4 MB total per invocation. Shrink payload or pass references (URLs, IDs) instead of raw data.

### SSE stream ends without event

**Symptom:** `RenderError("Task run completed with no event")` (Python) or unhandled stream error (TypeScript).

**Cause:** SSE connection closed before terminal event (`completed`, `failed`, `canceled`) arrived.

**Fix:** Typically transient network issue. SDK retries internally (up to 5 attempts with exponential backoff). If it persists, check network connectivity and retry. Fallback: poll with `get_task_run()`.

### AbortSignal does not cancel remote task (TypeScript)

**Symptom:** After aborting, task run keeps executing on Render.

**Cause:** `AbortSignal` cancels only local SDK wait (HTTP request or SSE stream). Remote task run keeps running.

**Fix:** After aborting, call `render.workflows.cancelTaskRun(taskRunId)` explicitly to cancel running task.

### Rate limiting (429)

**Symptom:** `RateLimitError` (Python) or `ClientError` with 429 status (TypeScript).

**Fix:** Send fewer requests. SDK retries rate-limited UDS calls internally (up to 15 attempts). For client-to-API rate limits, back off yourself.

## Connection & Networking

### UDS retries exhausted

**Symptom:** Error after about 2.5 minutes of retries during task execution.

**Cause:** Internal Unix Domain Socket client retries transient errors (5xx, timeouts, rate limits) up to 15 times with exponential backoff (250ms initial, 2x factor, 16s cap). After 15 failures, it throws last error.

**Fix:** Usually means task server is unhealthy or overwhelmed. Check server logs, restart task server, ensure socket path is valid.

### Runs queued at concurrency limit

**Symptom:** New task runs stay in `pending` status for long time.

**Cause:** Workspace hit its concurrent run limit. New runs queue (not rejected) until another run completes.

**Fix:** Wait for in-progress runs to finish, cancel unneeded runs, or purchase extra concurrency in workspace settings. More workflow services do not increase limit.

## Local Development Gotchas

| Gotcha | Details |
|--------|---------|
| Local IDs don't match production | Local task and run IDs are random UUIDs. They won't match deployed identifiers. |
| Data is in-memory only | Logs and results lost when local server shuts down. |
| Memory grows with many runs | Restart local server periodically during heavy testing. |
| Only task endpoints are simulated | Other Render API endpoints not available on local server. |
| Cross-workflow calls not tracked | Dashboard does not show calls between workflows via SDK client as chained runs. |

## Limits Reference

| Limit | Value |
|-------|-------|
| Max task definitions per workflow | 500 |
| Max argument size per run | 4 MB |
| Concurrent runs (Hobby) | 20 base, up to 200 |
| Concurrent runs (Professional) | 50 base, up to 200 |
| Concurrent runs (Org/Enterprise) | 100 base, up to 300 |
| Run timeout range | 30 seconds – 24 hours |
| Default run timeout | 2 hours |
| UDS internal retries | 15 attempts over ~2.5 minutes |
| SSE wait retries | 5 attempts with exponential backoff |
