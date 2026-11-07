---
name: node-inspect-debugger
description: "Debug Node.js via --inspect + Chrome DevTools Protocol CLI. Use when a Node.js bug needs breakpoints, stepping, variable inspection, or CPU/heap profiling from the terminal."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, nodejs, node-inspect, cdp, breakpoints, ui-tui]
    related_skills: [systematic-debugging, python-debugpy]
---

# Node.js Inspect Debugger

## Overview

Two tools, pick one:

- **`node inspect`** — built-in, zero install, CLI REPL. Best for quick poking.
- **`ndb` / CDP via `chrome-remote-interface`** — scriptable from Node/Python. Best when automating many breakpoints, collecting state across runs, or debugging non-interactively from agent loop.

**Prefer `node inspect` first.**

## When to Use

- Node test fails; need intermediate state
- ui-tui crashes or misbehaves; inspect React/Ink state pre-render
- tui_gateway child processes (`_SlashWorker`, PTY bridge workers) misbehave
- Closure value `console.log` can't reach without patching
- Perf: attach to running process for CPU profile or heap snapshot

**Don't use for:** things `console.log` solves in under a minute.

## Quick Reference: `node inspect` REPL

Launch paused on first line:

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

`debug>` prompt accepts:

| Command | Action |
|---|---|
| `c` or `cont` | continue |
| `n` or `next` | step over |
| `s` or `step` | step into |
| `o` or `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | breakpoint at file.js line 42 |
| `sb(42)` | breakpoint at line 42, current file |
| `sb('functionName')` | break on function call |
| `cb('file.js', 42)` | clear breakpoint |
| `breakpoints` | list breakpoints |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 source lines around current position |
| `watch('expr')` | evaluate expr each pause |
| `watchers` | show watched expressions |
| `repl` | REPL in current scope (Ctrl+C exits) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill script |
| `.exit` | quit debugger |

**In `repl` sub-mode:** any JS expression, locals/closure variables included. `Ctrl+C` returns to `debug>`.

## Attaching to a Running Process

Process already running (e.g. long-lived dev server, TUI gateway):

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

Start with inspector from beginning:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=127.0.0.1:9230 script.js   # custom port; keep loopback (0.0.0.0 exposes RCE, pitfall 7)
```

For TypeScript via tsx:

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

## Programmatic CDP (scripting from terminal)

To automate (many breakpoints, scope state capture, scripted repro), use `chrome-remote-interface`:

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

Driver script (save as `~/.hermes/cache/scratch/cdp-debug.js`):

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    // Evaluate an expression in the paused frame
    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  // Set a breakpoint by URL regex + line
  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,       // 0-indexed
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

Run it:

```bash
node ~/.hermes/cache/scratch/cdp-debug.js
```

Hermes-specific note: `chrome-remote-interface` is NOT in `ui-tui/package.json`. Install to throwaway location if you don't want to dirty project:

```bash
mkdir -p ~/.hermes/cache/scratch/cdp-tools && cd ~/.hermes/cache/scratch/cdp-tools && npm i chrome-remote-interface
NODE_PATH=~/.hermes/cache/scratch/cdp-tools/node_modules node ~/.hermes/cache/scratch/cdp-debug.js
```

## Debugging Hermes ui-tui

TUI uses Ink + tsx.

### Debugging a single Ink component under dev

`ui-tui/package.json` has `npm run dev` (tsx --watch). For `--inspect-brk`, run tsx directly:

```bash
cd <hermes-agent-repo>/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

Then inside `debug>`:

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

On pause, `repl`, then inspect `props`, state refs, `useInput` handler values, etc.

### Debugging a running `hermes --tui`

TUI spawns Node from Python CLI. Easiest path:

```bash
# 1. Launch TUI
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)

# 2. Enable inspector on that Node PID
kill -SIGUSR1 "$TUI_PID"

# 3. Find the WS URL
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'

# 4. Attach
node inspect ws://127.0.0.1:9229/<uuid>
```

Typing in TUI window keeps advancing execution. Debugger can pause it at any `sb(...)` breakpoint.

### Debugging `_SlashWorker` / PTY child processes

Those are Python, not Node: use `python-debugpy` skill. Only Node portions (Ink UI, tui_gateway client, tsx-run tests under `ui-tui/`) use this skill.

## Running Vitest Tests Under the Debugger

```bash
cd <hermes-agent-repo>/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

In another terminal: `node inspect -p <pid>`, then `sb('src/app/foo.tsx', 42)`, `cont`.

Use `--no-file-parallelism` (vitest) or `--runInBand` (jest) so only one worker runs.

## Heap Snapshots & CPU Profiles (Non-interactive)

From CDP driver above, swap Debugger for `HeapProfiler` / `Profiler`:

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
// Node does not expand '~' in paths; build the absolute path explicitly
const out = require('path').join(require('os').homedir(), '.hermes/cache/scratch/cpu.cpuprofile');
require('fs').mkdirSync(require('path').dirname(out), { recursive: true });
require('fs').writeFileSync(out, JSON.stringify(profile));
// Open ~/.hermes/cache/scratch/cpu.cpuprofile in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
const heapOut = require('path').join(require('os').homedir(), '.hermes/cache/scratch/heap.heapsnapshot');
require('fs').mkdirSync(require('path').dirname(heapOut), { recursive: true });
require('fs').writeFileSync(heapOut, chunks.join(''), { mode: 0o600 }); // holds in-memory secrets; owner-only, never share/commit
```

## Common Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit emitted JS, not `.ts`. Either (a) break in built `dist/*.js`, or (b) enable sourcemaps (`node --enable-source-maps`) and use `sb('src/app.tsx', N)`. (b) works only with CDP clients that follow sourcemaps; `node inspect` CLI does not.

2. **`--inspect` vs `--inspect-brk`.** `--inspect` starts inspector but doesn't pause. Attach too late and script races past first breakpoint. Use `--inspect-brk` to set breakpoints before any code runs.

3. **Port collisions.** Default `9229`. If multiple Node processes are inspecting, pass `--inspect=0` (random port). Read actual URL from process stderr (`Debugger listening on ws://127.0.0.1:<port>/...`), then query that port:
   ```bash
   curl -s http://127.0.0.1:<port>/json/list   # lists the inspectable target(s) on that port
   ```

4. **Child processes.** `--inspect` on parent does NOT inspect children. `NODE_OPTIONS` propagates inspector flags to every child, but plain children do not get new port. With `NODE_OPTIONS='--inspect'` each child tries 9229 and fails with "address already in use". Use `NODE_OPTIONS='--inspect=0' node parent.js` (or `--inspect-brk=0`) so each process picks free port and prints own `ws://` URL. (Only `cluster`/`child_process.fork` auto-adjust worker debug port.)

5. **Background kills.** `Ctrl+C` out of `node inspect` while target is paused leaves target paused. `cont` first, or `kill` target explicitly.

6. **Running `node inspect` through an agent terminal.** PTY-friendly REPL. In Hermes, launch with `terminal(pty=true)` or `background=true` + `process(action='submit', data='...')`. Non-PTY foreground works for one-shot commands, not interactive stepping.

7. **Security.** `--inspect=0.0.0.0:9229` exposes arbitrary code execution. Always bind `127.0.0.1` (default) unless network is isolated.

## Verification Checklist

After setup, verify:

- [ ] `curl -s http://127.0.0.1:9229/json/list` returns exactly expected target
- [ ] First breakpoint hits (if not: likely missed `--inspect-brk`, or attached after execution completed)
- [ ] Source listing at pause shows right file (mismatch means sourcemap issue, see pitfall 1)
- [ ] `exec process.pid` in `repl` returns intended PID

## One-Shot Recipes

**"Why is this variable undefined at line X?"**
```bash
node --inspect-brk script.js &
node inspect -p $!
# debug>
sb('script.js', X)
cont
# paused. Now:
repl
> myVariable
> Object.keys(this)
```

**"What's the call path into this function?"**
```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**"This async chain hangs — where?"**
```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```
