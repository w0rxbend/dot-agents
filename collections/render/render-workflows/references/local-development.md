# Local Development

## Contents

- Prerequisites
- Starting the local task server
- Triggering task runs (CLI and application code)
- Viewing results
- Limitations

## Prerequisites

- **Render CLI 2.11.0+**: `render --version`
  - macOS: `brew install render`
  - Linux/macOS without Homebrew: download pinned release zip plus its `SHA256SUMS` from [CLI releases page](https://github.com/render-oss/cli/releases/), verify checksum, put `cli_v<version>` binary on `PATH` as `render` (see render-cli skill). Ask user before installing anything; do not pipe install script from `curl` into `sh`.
  - Windows: download executable from [CLI releases page](https://github.com/render-oss/cli/releases/)
- Workflow project with registered tasks

## Starting the Local Task Server

From project directory:

```bash
# Python
render workflows dev -- python workflows/main.py

# TypeScript
render workflows dev -- npx tsx workflows/main.ts
```

Server listens on port `8120`. Change with `--port`:

```bash
render workflows dev --port 8121 -- python workflows/main.py
```

Server picks up code changes automatically.

## Triggering Task Runs

### From the CLI

List and run tasks interactively:

```bash
render workflows tasks list --local
```

**`--local` flag is required.** Without it, CLI lists deployed (remote) tasks.

Interactive menu:
1. Select task
2. Choose `run`
3. Give input as JSON array (e.g., `[5]` or `[]`)
4. View live logs

### From Application Code

Point app at local task server.

**Python:**

Set env vars:
```bash
RENDER_USE_LOCAL_DEV=true
```

Or for custom port:
```bash
RENDER_USE_LOCAL_DEV=true
RENDER_LOCAL_DEV_URL=http://localhost:8121
```

SDK clients (`Render()` and `RenderAsync()`) auto-detect these and route requests to local server.

**TypeScript:**

Same env vars, or pass config directly:
```typescript
import { Render } from "@renderinc/sdk";

const render = new Render({
  useLocalDev: true,
  localDevUrl: "http://localhost:8120",
});
```

**Render API (any language):**

Swap base URL for task endpoints:
```
http://localhost:8120
```

Local server simulates only task endpoints. Other Render API endpoints not supported locally.

## Viewing Results

After running task via CLI:
1. Press **Esc** for command menu
2. Select `runs` to list task runs
3. Select run, choose `results` to see output

## Limitations

- Logs and results live **in memory**, lost on server shutdown
- Many runs raise memory use; restart server periodically
- Task and run IDs are random UUIDs, not matching deployed identifiers
- Subtasks run locally in same server process
