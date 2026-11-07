# Manual Scaffolding (Fallback)

Use only if `render workflows init` is not available. Follow steps in order.

## Contents

- Step 1: Detect language
- Step 2: Create the `workflows/` directory
- Step 3: Install dependencies
- Step 4: Verify setup

> **IMPORTANT:** Do NOT modify project's root `package.json` or `requirements.txt`. Do NOT run `npm install <package>` or `pip install <package>` at project root. `workflows/` is self-contained service with own dependency files.

> **Official starter templates likely changed since this skill was written.**
> Always check real template before scaffolding:
> - **Python:** [render-examples/workflows-template-python](https://github.com/render-examples/workflows-template-python)
>
> If SDK already installed, inspect it for current signatures:
> ```bash
> # Python: check SDK source
> SDK_ROOT=$(pip show render_sdk | grep Location | cut -d' ' -f2)/render_sdk
> head -40 "$SDK_ROOT/__init__.py"
>
> # TypeScript: check type definitions
> grep -r "export.*task\|export.*Render" node_modules/@renderinc/sdk/
> ```
>
> **Official examples:** [Python](https://github.com/render-oss/sdk/tree/main/python/example) | [TypeScript](https://github.com/render-oss/sdk/tree/main/typescript/examples)
>
> Inline snippets here are fallback. Official repos are source of truth.

## Step 1: Detect Language

**Principle:** If user named language in prompt, use it. Else auto-detect from config files. Ask only if genuinely ambiguous.

Check project for language indicators:

| Indicator | Language |
|-----------|----------|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| `package.json`, `tsconfig.json`, `*.ts` | TypeScript |

If both present or neither found, ask user which language.

## Step 2: Create the `workflows/` Directory

Official Render starter templates are source of truth for file structure and contents:

- **Python:** [render-examples/workflows-template-python](https://github.com/render-examples/workflows-template-python)
- **TypeScript:** [render-examples/workflows-template-ts](https://github.com/render-examples/workflows-template-ts)

Fetch template contents (clone, download, or read from repo) into `workflows/` at project root. Fetch only from these official repos (no tags: record commit SHA used). Show user fetched `requirements.txt` / `package.json` (deps, install scripts); get OK before Step 3. Minimum contents:

**Python:** `main.py`, `requirements.txt`
**TypeScript:** `index.ts` (or `main.ts`), `package.json`, `tsconfig.json`

Key template patterns:

**Python entry point** (`main.py`):
```python
from render_sdk import Workflows, Retry

app = Workflows(
    default_retry=Retry(max_retries=3, wait_duration_ms=1000, backoff_scaling=2.0),
)

@app.task
def ping() -> str:
    return "pong"

if __name__ == "__main__":
    app.start()
```

**TypeScript entry point** (`index.ts`):
```typescript
import { task } from "@renderinc/sdk/workflows";

task(
  {
    name: "ping",
    retry: { maxRetries: 3, waitDurationMs: 1000, backoffScaling: 2.0 },
  },
  function ping(): string {
    return "pong";
  },
);
```

Each template has zero-argument `ping` task for instant setup check.

## Step 3: Install Dependencies

Install dependencies after all Step 2 files exist.

**Python:**
```bash
pip install -r workflows/requirements.txt
```

**TypeScript:**
```bash
npm install --prefix workflows
```

## Step 4: Verify Setup

Confirm setup succeeded before handing off:

- [ ] `workflows/` exists with expected files
- [ ] Dependencies installed without errors

Then give user these commands to run in their own terminal:

- [ ] Start local task server:
  - Python: `render workflows dev -- python workflows/main.py`
  - TypeScript: `render workflows dev -- npx tsx workflows/main.ts`
- [ ] In second terminal: `render workflows tasks list --local`
- [ ] Select `ping`, choose `run`, enter `[]` as input
- [ ] Verify result is `"pong"`

Do NOT start dev server or run test commands yourself.

**If verification fails:**
- **Task server won't start:** check CLI version (`render --version`, needs 2.11.0+) and start command. See [Troubleshooting > Task Server Issues](troubleshooting.md#task-server-issues).
- **`ping` task not listed:** entry point must import task file. See [Task Registration Issues](troubleshooting.md#task-registration-issues).
- **Dependency install errors:** confirm install ran inside `workflows/`, not project root.
