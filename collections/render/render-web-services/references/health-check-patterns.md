# Health check patterns for Render Web Services

Render sends HTTP **GET** to configured **`healthCheckPath`**. Response must be **`2xx` or `3xx`**. Anything else (including **`4xx`**, **`5xx`**, timeouts, connection failures) is **unhealthy**: can **block a deploy from going live** or trigger rollback.

## Endpoint design

- Prefer **dedicated** path, e.g. **`/health`** or **`/healthz`**.
- Return **`200 OK`**, small or empty body; avoid heavy work per request.
- Path must be served by **same process and port** as production traffic (whatever listens on **`PORT`**).

### What to verify (in order of usefulness)

1. **Application has finished starting** — routes registered, server accepting connections.
2. **Optional: critical dependencies** — e.g. open **database** connection or run trivial query, *if* you accept DB blips marking whole service unhealthy (often desirable for strict readiness).
3. Avoid equating “process alive” with “ready for traffic” if initialization is slow (migrations, cache warm-up, etc.).

Do **not** use health checks that always return 200 before server listens on **`PORT`**.

## Framework examples

### Express.js (Node)

```js
app.get("/health", (_req, res) => {
  res.status(200).send("ok");
});
```

### Flask (Python)

```python
@app.get("/health")
def health():
    return "", 200
```

### Django (Python)

```python
# urls.py
path("health", lambda r: HttpResponse(status=200)),
```

### Go (net/http)

```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
})
```

### Rust (Actix-web)

```rust
#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok().finish()
}
```

## Timeouts and tuning

- If app **starts listening after** health check window expects readiness, deploys may **fail or roll back**.
- **Slow-starting** apps (large JVM warmup, many workers): **listen** as early as possible, or **increase** health check **timeout** / **interval** in settings if platform allows. First passing check should come after server is truly up.
- Failing dependency check (DB down) keeps service **unhealthy**: often right for **readiness**, harsh if you only wanted **liveness**. Prefer **readiness** semantics for Render’s path unless you have reason not to.

## Common issues

| Symptom | Likely cause |
|--------|----------------|
| Deploy never goes live | Health path returns **4xx/5xx**, wrong path, or server not up yet |
| Connection refused | App bound to **127.0.0.1** only, or wrong **port** vs **`PORT`** |
| Intermittent failures | Timeouts too aggressive vs cold start; DB check flapping |
| Wrong service | Health path hits different process or static file only in old deploy |

Always confirm **`healthCheckPath`** matches **GET** route on service listening on **`0.0.0.0:$PORT`**.
