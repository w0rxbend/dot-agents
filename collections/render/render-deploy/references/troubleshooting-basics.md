# Basic troubleshooting (deploy-time and startup)

Use when deploy fails, service crashes on start, or health checks time out.
Keep fixes minimal. Redeploy after each change.

## 1) Classify the failure

- **Build failure**: errors in build logs, missing dependencies, build command issues.
- **Startup failure**: app exits fast, crashes, or cannot bind to `$PORT`.
- **Runtime/health failure**: service live but health checks fail or 5xx errors.

## 2) Quick checks by class

**Build failure**
- Confirm build command fits runtime.
- Ensure required dependencies are in `package.json`, `requirements.txt`, etc.
- Check for missing build-time env vars.

**Startup failure**
- Confirm start command and working directory.
- Ensure port binding is `0.0.0.0:$PORT`.
- Check for missing runtime env vars (secrets, DB URLs).

**Runtime/health failure**
- Verify health endpoint path and response.
- Confirm app listens on `$PORT`.
- Check database connectivity and migrations.

## 3) Map error signatures to fixes

[error-patterns.md](error-patterns.md): compact catalog of common log messages.

## 4) If still blocked

Gather latest build logs and runtime error logs. Then consider optional
`render-debug` skill for deeper diagnostics (metrics, DB checks, expanded patterns).
