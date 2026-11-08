# Sections

Section ID (in parentheses) is filename prefix grouping rules.

---

## 1. Codebase & Version Control (code)

**Impact:** CRITICAL
**Description:** One codebase in revision control, many deploys. Foundation for consistent deploys and team collaboration.

## 2. Dependencies (dep)

**Impact:** CRITICAL
**Description:** Explicitly declare and isolate all dependencies. Never rely on implicit system-wide packages or tools.

## 3. Configuration (config)

**Impact:** CRITICAL
**Description:** Store config in environment variables. Strict config/code separation gives deploy flexibility.

## 4. Backing Services (svc)

**Impact:** HIGH
**Description:** Treat backing services as attached resources. Reach databases, caches, queues via URLs in config.

## 5. Build, Release, Run (build)

**Impact:** HIGH
**Description:** Strictly separate build, release, run stages. Each release immutable, uniquely identified.

## 6. Processes & State (proc)

**Impact:** HIGH
**Description:** Run app as stateless processes. Store persistent data in backing services, never in local filesystem or memory.

## 7. Concurrency & Scaling (scale)

**Impact:** HIGH
**Description:** Scale out via process model. Assign workloads to process types; execution environment manages processes.

## 8. Disposability (disp)

**Impact:** HIGH
**Description:** Maximize robustness: fast startup, graceful shutdown. Processes are disposable, started or stopped at will.

## 9. Port Binding (port)

**Impact:** MEDIUM
**Description:** Export services via port binding. App is self-contained; does not rely on runtime webserver injection.

## 10. Dev/Prod Parity (parity)

**Impact:** MEDIUM
**Description:** Keep development, staging, production as similar as possible. Minimize gaps in time, personnel, tools.

## 11. Logging (log)

**Impact:** MEDIUM
**Description:** Treat logs as event streams. Write unbuffered to stdout; let execution environment handle routing and storage.

## 12. Admin Processes (admin)

**Impact:** MEDIUM
**Description:** Run admin/management tasks as one-off processes, with same codebase, config, environment as regular processes.
