# Task Patterns

## Contents

- Fan-out / fan-in
- ETL pipeline
- Retry-heavy tasks
- Error handling in tasks
- Integration patterns (cron triggers, cross-workflow calls)

## Fan-Out / Fan-In

Process batch of items in parallel with subtasks, then aggregate results.

**Python:**
```python
import asyncio

@app.task
async def process_batch(image_urls: list[str]) -> dict:
    results = await asyncio.gather(
        *[process_image(url) for url in image_urls]
    )
    successful = sum(1 for r in results if r["success"])
    return {
        "total": len(image_urls),
        "processed": successful,
        "failed": len(image_urls) - successful,
        "results": list(results),
    }

@app.task
def process_image(url: str) -> dict:
    return {"url": url, "success": True}
```

**TypeScript:**
```typescript
const processImage = task(
  { name: "processImage" },
  function processImage(url: string): { url: string; success: boolean } {
    return { url, success: true };
  },
);

task(
  { name: "processBatch" },
  async function processBatch(imageUrls: string[]): Promise<object> {
    const results = await Promise.all(
      imageUrls.map(url => processImage(url)),
    );
    const successful = results.filter(r => r.success).length;
    return {
      total: imageUrls.length,
      processed: successful,
      failed: imageUrls.length - successful,
      results,
    };
  },
);
```

## ETL Pipeline

Extract, transform, load with chained subtasks.

**Python:**
```python
@app.task
async def etl_pipeline(source: str, destination: str) -> dict:
    raw_data = await extract(source)
    transformed = await transform(raw_data)
    result = await load(destination, transformed)
    return result

@app.task
def extract(source: str) -> dict:
    return {"records": []}

@app.task
def transform(data: dict) -> dict:
    return {"records": []}

@app.task
def load(destination: str, data: dict) -> dict:
    return {"loaded": len(data["records"])}
```

**TypeScript:**
```typescript
const extract = task(
  { name: "extract" },
  function extract(source: string): object {
    return { records: [] };
  },
);

const transform = task(
  { name: "transform" },
  function transform(data: object): object {
    return { records: [] };
  },
);

const load = task(
  { name: "load" },
  function load(destination: string, data: object): object {
    return { loaded: 0 };
  },
);

task(
  { name: "etlPipeline" },
  async function etlPipeline(source: string, destination: string): Promise<object> {
    const rawData = await extract(source);
    const transformed = await transform(rawData);
    return await load(destination, transformed);
  },
);
```

## Retry-Heavy Tasks

Aggressive retry for unreliable external APIs.

**Python:**
```python
from render_sdk import Retry

@app.task(retry=Retry(max_retries=5, wait_duration_ms=2000, backoff_scaling=2.0))
def call_external_api(endpoint: str, payload: dict) -> dict:
    import urllib.request
    import json

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())
```

**TypeScript:**
```typescript
task(
  {
    name: "callExternalApi",
    retry: { maxRetries: 5, waitDurationMs: 2000, backoffScaling: 2.0 },
    timeoutSeconds: 60,
  },
  async function callExternalApi(endpoint: string, payload: object): Promise<object> {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },
);
```

## Error Handling in Tasks

Raised exceptions trigger automatic retry per task's retry config. Use intentionally. Common execution issues and fixes: see [troubleshooting.md](troubleshooting.md).

**Python:**
```python
@app.task(retry=Retry(max_retries=3, wait_duration_ms=1000))
def resilient_task(data: dict) -> dict:
    result = process(data)
    if not result["valid"]:
        raise ValueError("Invalid result, retrying...")
    return result
```

**TypeScript:**
```typescript
task(
  {
    name: "resilientTask",
    retry: { maxRetries: 3, waitDurationMs: 1000 },
  },
  function resilientTask(data: object): object {
    const result = process(data);
    if (!result.valid) {
      throw new Error("Invalid result, retrying...");
    }
    return result;
  },
);
```

---

## Integration Patterns

Trigger workflow tasks from outside workflow context.

## Cron-Triggered Workflows

Render Workflows have no built-in scheduling. Use Render cron job to trigger tasks on schedule.

**Python cron job (synchronous)** (`cron_trigger.py`):
```python
from render_sdk import Render

def main():
    render = Render()
    result = render.workflows.run_task("my-workflow/daily-cleanup", [])
    print(f"Cleanup completed: {result.status}")

if __name__ == "__main__":
    main()
```

**Python cron job (asynchronous)** (`cron_trigger.py`):
```python
import asyncio
from render_sdk import RenderAsync

async def main():
    render = RenderAsync()
    started = await render.workflows.start_task("my-workflow/daily-cleanup", [])
    finished = await started
    print(f"Cleanup completed: {finished.status}")

asyncio.run(main())
```

**TypeScript cron job** (`cron-trigger.ts`):
```typescript
import { Render } from "@renderinc/sdk";

const render = new Render();

async function main() {
  const result = await render.workflows.runTask("my-workflow/daily-cleanup", []);
  console.log("Cleanup completed:", result.status);
}

main();
```

Set up cron job with desired schedule in Render Dashboard or via MCP.

## Cross-Workflow Calls

Task in one workflow can trigger tasks in **different** workflow via SDK client (not subtask syntax):

**Python:**
```python
from render_sdk import RenderAsync

@app.task
async def orchestrate(data: dict) -> dict:
    render = RenderAsync()
    result = await render.workflows.run_task(
        "other-workflow/process",
        [data],
    )
    return result.results
```

**TypeScript:**
```typescript
import { Render } from "@renderinc/sdk";

task(
  { name: "orchestrate" },
  async function orchestrate(data: object): Promise<unknown> {
    const render = new Render();
    const result = await render.workflows.runTask(
      "other-workflow/process",
      [data],
    );
    return result.results;
  },
);
```

> **Note:** Dashboard does not track cross-workflow calls as subtask relationships.
