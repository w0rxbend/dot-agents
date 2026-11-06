# Post-deploy checks

Run after any deploy or service creation. Keep short; stop when check fails.

## 1) Confirm deploy status

```
list_deploys(serviceId: "<service-id>", limit: 1)
```

- Expect `status: "live"`.
- If status is failed, inspect build/runtime logs immediately.

## 2) Verify service health

- Hit health endpoint (preferred) or `/`, confirm 200 response.
- If no health endpoint exists, add one and redeploy.

## 3) Scan recent error logs

```
list_logs(resource: ["<service-id>"], level: ["error"], limit: 50)
```

- On clear error signature, jump to matching fix in
  [troubleshooting-basics.md](troubleshooting-basics.md) or
  [error-patterns.md](error-patterns.md).

## 4) Verify env vars and port binding

- Confirm all required env vars set (especially secrets marked `sync: false`).
- App must bind to `0.0.0.0:$PORT` (not localhost).

## 5) Redeploy only after fixing the first failure

- Avoid repeated deploys without changes. Fix one issue at a time.
