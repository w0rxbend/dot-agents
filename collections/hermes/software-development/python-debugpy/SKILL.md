---
name: python-debugpy
description: "Debug Python: pdb REPL + debugpy remote (DAP). Use when a Python bug needs breakpoints, stepping or attaching a debugger to a running process."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [debugging, python, pdb, debugpy, breakpoints, dap, post-mortem]
    related_skills: [systematic-debugging, node-inspect-debugger]
---

# Python Debugger (pdb + debugpy)

## Overview

Pick by situation:

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add `breakpoint()`, run normally, get REPL at that line. |
| **`python -m pdb`** | Run existing script under pdb, no source edits. Quick poking. |
| **`debugpy`** | Remote / headless / "attach to already-running process." Speaks DAP, terminal-scriptable, suits long-lived processes (gateway, daemon, PTY children). |

**Start with `breakpoint()`.** Cheapest thing that works.

## When to Use

- Test fails; traceback doesn't show why a value is wrong
- Step through a function, watch a collection mutate
- Long-running process (hermes gateway, tui_gateway) misbehaves; can't restart it
- Post-mortem: inspect locals at crash site of exception in prod-ish code
- Real bug site is a subprocess / child (Python `_SlashWorker`, PTY bridge worker)

**Don't use for:** anything `print()` / `logging.debug` solves in under a minute or `pytest -vv --tb=long --showlocals` already reveals.

## pdb Quick Reference

Inside any pdb prompt (`(Pdb)`):

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `j N` | jump to line N (same function only) |
| `l` / `ll` | list source around current line / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up / down the stack |
| `a` | print args of current function |
| `p expr` / `pp expr` | print / pretty-print expression |
| `display expr` | auto-print expr on every stop |
| `b file:line` | set breakpoint |
| `b func` | break on function entry |
| `b file:line, cond` | conditional breakpoint |
| `cl N` | clear breakpoint N |
| `tbreak file:line` | one-shot breakpoint |
| `!stmt` | execute arbitrary Python (assignments included) |
| `interact` | drop into full Python REPL in current scope (Ctrl+D to exit) |
| `q` | quit |

`interact` is most powerful: import anything, inspect complex objects, call state-mutating methods. Locals read-only by default; mutate with `!x = 42` at `(Pdb)` prompt.

## Recipe 1: Local breakpoint

Easiest. Edit file:

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

**Remove `breakpoint()` before committing.** Check with `git diff` or pre-commit grep:
```bash
rg -n 'breakpoint\(\)' --type py
```

## Recipe 2: Launch a script under pdb (no source edits)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```

## Recipe 3: Debug a pytest test

Use `terminal` and canonical runner for noninteractive diagnostics:

```bash
# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

`scripts/run_tests.sh` captures each file in separate subprocess, so `--pdb`
/ `--trace` cannot give interactive prompt there. For interactive debugger
only, use independent development/test interpreter from Recipe 5 (never a
production generation):

```bash
.venv/bin/python -m pytest tests/foo_test.py::test_bar --pdb
```

Bypasses hermetic-env guarantees. Fine for debugging; re-run under wrapper to confirm before pushing.

## Recipe 4: Post-mortem on any exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Or wrap whole script:

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Or set global hook in repl/jupyter:

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```

## Recipe 5: Remote debug with debugpy (attach to running process)

### Setup

Hermes: use separate development checkout and data home, not live
production generation. Follow
[PM developer workflow](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow),
activate that checkout (PowerShell: `. .\activate.ps1`). Declared `dev` extra
has debugpy; PM activation does not sync it (`all` excludes it). Via
`terminal`, build fresh caller-owned debug/test environment with prepared
checkout's Python:

```bash
source ./activate
python -m pm.build_env --source . --out .venv --group dev --group test
.venv/bin/python -c "import debugpy; print(debugpy.__file__)"
```

Output must not exist yet. To rebuild, stop its processes, then
intentionally remove only that disposable environment. Keep same isolated
`HERMES_HOME` for debug target. `.venv/bin/python` means this explicitly
built debug environment, not a guessed application venv; patterns below use
it. Do not add debugpy to a running production environment. Reproduce there
only with an already-prepared debug target, or arrange a restart in
development environment.

### Pattern A: Source-edit — process waits for debugger at launch

Add near top of entry point (or inside function to debug):

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

Start process; it blocks on `wait_for_client()`.

### Pattern B: No source edit — launch with `-m debugpy`

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

Equivalent for module entry:

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Pattern C: Attach to an already-running process

Needs PID and debugpy preinstalled in target's environment:

```bash
.venv/bin/python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Some kernels/security configs block ptrace-based injection (`/proc/sys/kernel/yama/ptrace_scope`). Prefer restarting target under debugpy (Pattern A/B). Lowering `ptrace_scope` weakens system-wide hardening: do it only after user explicitly agrees, and restore it afterwards:
```bash
cat /proc/sys/kernel/yama/ptrace_scope              # note the current value (usually 1)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope  # ONLY with user consent
# ... attach and debug ...
echo 1 | sudo tee /proc/sys/kernel/yama/ptrace_scope  # restore the value you noted
```

### Connecting a client from the terminal

Easiest terminal-side DAP client: VS Code CLI or a small script. From inside Hermes, two practical options:

**Option 1: `debugpy`'s own CLI REPL** — unofficial; tiny DAP client script:

```python
# ~/.hermes/cache/scratch/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

Fine for one-off automation, painful as interactive UX.

**Option 2: Attach from VS Code / Cursor / Zed** — if user has one open, they can add `launch.json`:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "<hermes-agent-repo>" }
  ]
}
```

**Option 3: Ditch DAP, use `remote-pdb`** — usually what a terminal agent wants:

Independently owned Python project: declare `remote-pdb` in its development
dependencies, prepare debug environment via its package manager. Not a Hermes
SDK install recipe. Hermes: prefer declared debugpy dependency. Examples
below with remote-pdb need separately declared, freshly built debug
environment, never in-place pip install into selected application generation.

In code:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

Then from terminal:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

Use `debugpy` only when IDE integration is needed.

## Debugging Hermes-specific Processes

### `run_agent.py` / CLI — one-shot
In prepared debug checkout, add `breakpoint()` near suspect line, then
run `python hermes`. Control returns to terminal at pause point.

### `tui_gateway` subprocess (spawned by `hermes --tui`)
Gateway runs as child of Node TUI. Options:

**A. Source-edit the gateway:**
```python
# tui_gateway/server.py near the top of serve()
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
Start `python hermes --tui` from prepared debug checkout. TUI looks frozen (backend waiting). Attach client; execution resumes on `continue`. Check child's interpreter and imports before assuming it inherited debug environment.

**B. Use `remote-pdb` at a specific handler:**
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # in the RPC handler you want to trap
```
Trigger matching slash command from TUI, then `nc 127.0.0.1 4444` in another terminal.

### `_SlashWorker` subprocess
Same pattern: `remote-pdb` with `set_trace()` inside worker's `exec` path. Worker persists across slash commands. First trigger blocks until you connect; later slash commands pass through normally unless you re-arm.

### Gateway (`gateway/run.py`)
Long-lived. Use `remote-pdb` at a handler, or `debugpy` with `--wait-for-client` if restarting gateway anyway.

## Common Pitfalls

1. **pdb under a parallel/output-capturing runner silently does nothing.** No prompt appears; test hangs (true of pytest-xdist and `scripts/run_tests.sh`'s captured per-file subprocesses). For interactive debugging, run pytest directly on single file.

2. **`breakpoint()` in CI / non-TTY contexts hangs the process.** Safe locally; never commit it.

3. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls. Check env if breakpoint isn't hitting:
   ```bash
   echo $PYTHONBREAKPOINT
   ```

4. **`debugpy.listen` blocks only if you also call `wait_for_client()`.** Without it, execution continues; first breakpoint may fire before client attaches.

5. **Attach to PID fails on hardened kernels.** `ptrace_scope=1` (Ubuntu default) allows only same-user ptrace of child processes. Preferred workaround: launch under `debugpy` from start. Lowering `ptrace_scope` needs root plus user's explicit consent, and must be restored afterwards (see Pattern C).

6. **Threads.** `pdb` only debugs current thread. For multithreaded code, use `debugpy` (thread-aware DAP) or set `threading.settrace()` per thread.

7. **asyncio.** `pdb` works in coroutines, but typing `await` at pdb prompt works only from Python 3.14. Older versions cannot await directly at prompt. Schedule coroutine instead (for example `!asyncio.ensure_future(coro())`), inspect it after continuing. Or use `python -m asyncio` for interactive awaiting.

8. **`scripts/run_tests.sh` strips credentials and sets `HOME=<tmpdir>`.** If bug depends on user config or real API keys, it won't reproduce under wrapper. Repro with raw `pytest` first, then re-confirm under wrapper.

9. **Forking / multiprocessing.** pdb does not follow forks. Each child needs its own `breakpoint()` or `set_trace()`. For Hermes subagents, debug one process at a time.

## Verification Checklist

- [ ] In independently built debug environment, confirm: `.venv/bin/python -c "import debugpy; print(debugpy.__version__); print(debugpy.__file__)"`
- [ ] For remote debug, confirm port is listening: `ss -tlnp | grep 5678`
- [ ] First breakpoint hits (if not: likely `PYTHONBREAKPOINT=0`, parallel/capturing runner, or execution finished before attach)
- [ ] `where` / `w` shows expected call stack
- [ ] Post-debug cleanup: no stray `breakpoint()` / `set_trace()` in committed code
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```

## One-Shot Recipes

**"Why is this dict missing a key?"**
```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**"This test passes in isolation but fails in the suite."**
```bash
scripts/run_tests.sh tests/the_test.py   # confirm it fails under the isolated runner first
# For interactive debugging, or if it only fails WITH other tests, use the
# independent development/test interpreter prepared in Recipe 5:
.venv/bin/python -m pytest tests/ -x --pdb
# Now it pdb-traps at the exact failing test after state accumulated.
```

**"My async handler deadlocks."**
```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```
Trigger handler, run `nc 127.0.0.1 4444`, then `w` shows suspended frame, `!import asyncio; asyncio.all_tasks()` shows what else is pending.

**"Post-mortem on a crash in an Ink child process / subprocess."**
```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```
