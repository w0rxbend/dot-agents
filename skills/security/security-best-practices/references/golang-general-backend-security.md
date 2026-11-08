# Go (Golang) Security Spec (Go 1.25.x, Standard Library, net/http)

--------------------------------------------------------------------

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

- MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session cookies, JWTs, database URLs with credentials, signing keys, client secrets).
- MUST NOT “fix” security by disabling protections (e.g., `InsecureSkipVerify`, `GOSUMDB=off` for public modules, wildcard CORS + credentials, removing auth checks, disabling CSRF defenses on cookie-auth apps).
- MUST provide **evidence-based findings** during audits: cite file paths, code snippets, build/deploy configs, concrete values justifying claim.
- MUST treat uncertainty honestly: if control might exist in infrastructure (reverse proxy, WAF, service mesh, platform config), report as “not visible in app code; verify at runtime/config.”
- MUST keep fixes minimal, correct, production-safe. Avoid breaking changes without warning (especially around auth/session flows and proxies).

--------------------------------------------------------------------

## 1) Operating modes

### 1.1 Generation mode (default)
When writing new Go code or modifying existing code:
- MUST follow every **MUST** requirement in this spec.
- SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
- MUST prefer safe-by-default APIs and proven libraries over custom security code.
- MUST avoid introducing new risky sinks (shell execution, dynamic template execution, serving user files as HTML, unsafe redirects, weak crypto, unbounded parsing, etc.).

### 1.2 Passive review mode (always on while editing)
While working anywhere in Go repo (even if user did not ask for security scan):
- MUST “notice” violations of this spec in touched/nearby code.
- SHOULD mention issues as they come up, with brief explanation and safe fix.

### 1.3 Active audit mode (explicit scan request)
When user asks to “scan”, “audit”, or “hunt for vulns”:
- MUST systematically search codebase for violations of this spec.
- MUST output findings in structured format (see §2.3).

Recommended audit order:
1) Build/deploy entrypoints: `main.go`, `cmd/*`, Dockerfiles, Kubernetes manifests, systemd units, CI workflows.
2) Go toolchain & dependency policy: Go version, modules, `go.mod/go.sum`, proxy/sumdb settings, govulncheck usage.
3) Secret management and config loading (env, files, secret stores) + logging patterns.
4) HTTP server configuration (timeouts, body limits, proxy trust, security headers).
5) AuthN/AuthZ boundaries, session/cookie settings, token validation.
6) CSRF protections for cookie-authenticated state-changing endpoints.
7) Template usage and output encoding (XSS), any “render template from string” behavior (SSTI).
8) File handling (uploads/downloads/path traversal/temp files), static file serving.
9) Injection sinks: SQL, OS command execution, SSRF/outbound fetch, open redirects.
10) Concurrency/resource exhaustion (unbounded goroutines/queues, missing timeouts/contexts).
11) Use of `unsafe` / `cgo` / `reflect` in security-sensitive paths.
12) Debug/diagnostic endpoints (pprof/expvar/metrics) exposure.
13) Cryptography usage (randomness, password hashing).

--------------------------------------------------------------------

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)
Examples:
- `*http.Request` fields: `r.URL.Path`, `r.URL.RawQuery`, `r.Form`, `r.PostForm`, headers, cookies, `r.Body`
- Path parameters from routers (including values extracted from URL paths)
- JSON/XML/YAML bodies, multipart form parts, uploaded files
- Any data from external systems (webhooks, third-party APIs, message queues)
- Any persisted user content (DB rows) originating from users
- Configuration values that may be attacker-influenced in some deployments (headers set by upstream proxies, environment variables in multi-tenant systems)

### 2.2 State-changing request
Request is state-changing if it can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook send), or initiate privileged actions.

### 2.3 Required audit finding format
For each issue found, output:

- Rule ID:
- Severity: Critical / High / Medium / Low
- Location: file path + function/handler name + line(s)
- Evidence: the exact code/config snippet
- Impact: what could go wrong, who can exploit it
- Fix: safe change (prefer minimal diff)
- Mitigation: defense-in-depth if immediate fix is hard
- False positive notes: what to verify if uncertain (edge configs, proxy behavior, auth assumptions)

--------------------------------------------------------------------

## 3) Secure baseline: minimum production configuration (MUST in production)

### 3.1 Toolchain, patching, and dependency hygiene (MUST)
- MUST treat Go standard library patch releases as security-relevant (many security fixes land in stdlib components like `net/http`, `crypto/*`, parsing packages).
- MUST use Go modules with committed `go.mod` and `go.sum`.
- MUST NOT disable module authenticity mechanisms for public modules (checksum DB) unless a controlled, documented replacement exists.
- MUST run `govulncheck` (source scan and/or binary scan) in CI and address findings.

### 3.2 HTTP server baseline (MUST for network-facing services)
If program serves HTTP (directly or via framework built on `net/http`):
- MUST configure `http.Server` with explicit timeouts and header limits (GO-HTTP-001).
- MUST set request body size limits, global and per-route as needed (GO-HTTP-002).
- MUST avoid exposing diagnostic endpoints (pprof/expvar) publicly (GO-DEPLOY-002).
- SHOULD set consistent security headers, or verify they are set at edge (GO-HTTP-004).
- MUST set cookie security attributes for any cookies issued.
- SHOULD add rate limiting and abuse controls for auth and expensive endpoints.

Illustrative baseline skeleton (adjust to project):
- Create dedicated mux (avoid implicit global defaults unless intentionally managed).
- Wrap handlers with: panic-safe error handling, request ID, logging, auth, limits.

--------------------------------------------------------------------

## 4) Rules (generation + audit)

### GO-DEPLOY-001: Keep the Go toolchain and standard library updated (security releases)
Severity: Medium

NOTE: Upgrading dependencies and core Go version can break projects unexpectedly. Focus only on security-critical dependencies. If noticed, tell user instead of upgrading automatically.

Required:
- MUST run supported Go major release and apply patch releases promptly.
- SHOULD treat patch releases as security-relevant, even if application code didn’t change.

Insecure patterns:
- Production builds pinned to old Go versions without patching process.
- Docker images like `golang:1.xx` or custom base images not updated regularly.
- CI pipelines intentionally suppressing Go updates.

Detection hints:
- Inspect CI (`.github/workflows`, `gitlab-ci.yml`, etc.) for `go-version:` or toolchain setup.
- Inspect Dockerfiles for `FROM golang:` tags.
- Inspect `go.mod` `go` directive and any toolchain pinning.

Fix:
- Upgrade to latest patch of supported Go version.
- Add automated CI check failing when Go is below approved minimum.

---

### GO-SUPPLY-001: Go module authenticity MUST NOT be disabled for public dependencies
Severity: High

Required:
- MUST keep module checksum verification enabled for public modules.
- SHOULD commit `go.sum` and treat changes as security-sensitive.
- MUST NOT use insecure module fetching settings for public modules.
- MAY configure private module behavior via `GOPRIVATE`/`GONOSUMDB` for private repos, but must do so narrowly and intentionally.

Insecure patterns:
- `GOSUMDB=off` in CI or production build environments for public modules.
- `GONOSUMDB=*` or overly broad patterns effectively disabling verification.
- `GOINSECURE=*` or broad `GOINSECURE` patterns for public modules.
- `GOPROXY=direct` everywhere without clear policy.

Detection hints:
- Search build configs for `GOSUMDB`, `GONOSUMDB`, `GOINSECURE`, `GOPROXY`, `GOPRIVATE`.
- Look for documentation/scripts recommending disabling checksum DB “to make builds work”.

Fix:
- Restore defaults for public module verification.
- For private modules:
  - Set `GOPRIVATE=your.private.domain/*`
  - Configure internal proxy or direct fetching; restrict `GONOSUMDB` to private patterns only.

---

### GO-CONFIG-001: Secrets must be externalized and never logged or committed
Severity: High (Critical if credentials are committed)

Required:
- MUST load secrets from environment variables, secret managers, or secure config files with restricted permissions.
- MUST NOT hard-code secrets in Go source, test fixtures that may reach production, or build args.
- MUST NOT log secrets or full credential-bearing connection strings.
- SHOULD fail closed in production if required secrets are missing.

Insecure patterns:
- String constants containing tokens/keys/passwords.
- `.env` files or config files with secrets committed to repo.
- Logging `os.Environ()`, dumping full configs, or printing DSNs.

Detection hints:
- Search for suspicious literals (`API_KEY`, `SECRET`, `PASSWORD`, `Authorization:`).
- Inspect config loaders and logging statements.
- Inspect CI logs or debug print paths.

Fix:
- Move secrets to secret store / environment variables.
- Redact sensitive fields in logs.
- Add secret scanning to CI and pre-commit.

---

### GO-HTTP-001: HTTP servers MUST set timeouts and MaxHeaderBytes
Severity: High (DoS risk)

Required:
- MUST set: `ReadHeaderTimeout`, and SHOULD set `ReadTimeout`, `WriteTimeout`, `IdleTimeout` per service needs.
- MUST set `MaxHeaderBytes` to justified limit for the app.
- MUST NOT rely on default zero-values for timeouts in production for internet-facing servers.

Insecure patterns:
- `http.ListenAndServe(":8080", handler)` with default `http.Server` (no explicit timeouts).
- `&http.Server{}` with timeouts left at zero.
- Missing `MaxHeaderBytes`.

Detection hints:
- Search for `http.ListenAndServe(`, `ListenAndServeTLS(`, `Server{` and inspect configured fields.
- Check for reverse proxies. App-level timeouts still matter even with proxy.

Fix:
- Use `http.Server{ReadHeaderTimeout: ..., ReadTimeout: ..., WriteTimeout: ..., IdleTimeout: ..., MaxHeaderBytes: ...}`.
- Calibrate timeouts per endpoint type (streaming vs JSON APIs).

Notes:
- Net/http documents these timeouts; zero/negative values mean “no timeout”.

---

### GO-HTTP-002: Request body and multipart parsing MUST be size-bounded
Severity: Medium (DoS risk; can be High for upload-heavy apps)

Required:
- MUST enforce global maximum request body size for endpoints accepting bodies.
- MUST enforce strict multipart upload limits and avoid unbounded form parsing.
- SHOULD enforce per-route limits when some endpoints legitimately need larger bodies.
- SHOULD set upstream (proxy) limits as defense-in-depth.

Insecure patterns:
- Reading `r.Body` with `io.ReadAll(r.Body)` without size cap.
- Calling `r.ParseMultipartForm(...)` with overly large limits (or forgetting size controls).
- Accepting file uploads with no limits on file size, number of parts, or total body size.

Detection hints:
- Search for `io.ReadAll(r.Body)`, `json.NewDecoder(r.Body)`, `ParseMultipartForm`, `FormFile`, `multipart`.
- Look for missing `http.MaxBytesReader` or equivalent per-handler limiting.
- Look for “upload” endpoints and check limits.

Fix:
- Wrap request bodies with `http.MaxBytesReader(w, r.Body, maxBytes)` before parsing.
- For multipart, set conservative limits and validate file sizes/part counts explicitly.
- Set proxy limits (e.g., at ingress) on top of app limits.

Notes:
- Known vulnerability classes and advisories cover excessive resource consumption in multipart/form parsing. Treat unbounded parsing as security issue.

---

### GO-DEPLOY-002: Diagnostic endpoints (pprof/expvar/metrics) MUST NOT be publicly exposed
Severity: High

NOTE: Applies only to production configurations. These endpoints often serve debug or dev use. If found, confirm it would be reachable from actual production deployment.

Required:
- MUST NOT expose `net/http/pprof` handlers on public internet-facing listener without strong access controls.
- SHOULD run diagnostics on separate, internal-only listener (loopback/VPC-only) and require auth.
- MUST review what diagnostic endpoints reveal (stack traces, memory, command lines, environment, internal URLs).

Insecure patterns:
- Side-effect import `import _ "net/http/pprof"` in server binary with public mux.
- `/debug/pprof/*` reachable without auth.
- `/debug/vars` (expvar) reachable without auth.

Detection hints:
- Search for `net/http/pprof` imports (including blank imports).
- Search for route prefixes `/debug/pprof`, `/debug/vars`.
- Check whether `http.DefaultServeMux` is used and any debug handlers register globally.

Fix:
- Remove diagnostics from production builds, or bind them to internal-only listener.
- Add strong authentication/authorization (and ideally network-level restrictions).

---

### GO-HTTP-003: Reverse proxy and forwarded header trust MUST be explicit
Severity: High (auth, URL generation, logging/auditing correctness)

Required:
- If behind reverse proxy, MUST define which proxy is trusted and how client IP/scheme/host are derived.
- MUST NOT trust `X-Forwarded-For`, `X-Forwarded-Proto`, `Forwarded`, or similar headers from open internet.
- MUST ensure “secure cookie” logic, redirects, and absolute URL generation do not rely on spoofable headers.

Insecure patterns:
- Using `r.Header.Get("X-Forwarded-For")` as client IP without validating proxy boundary.
- Deriving “is HTTPS” from `X-Forwarded-Proto` without confirming it came from trusted proxy.
- Using forwarded `Host` values for password reset links without allowlisting.

Detection hints:
- Search for `X-Forwarded-For`, `X-Forwarded-Proto`, `Forwarded`, `Real-IP`, and any custom “client IP” helpers.
- Inspect ingress/proxy configs; if not visible, mark as “verify at edge”.

Fix:
- Enforce proxy trust at edge and in app:
  - Accept forwarded headers only from known proxy IP ranges.
  - Prefer platform-provided mechanisms where available.
- If generating external links, use configured allowlisted canonical origin (not request’s Host header).

---

### GO-HTTP-004: Security headers SHOULD be set (in app or at the edge)
Severity: Medium

Required (typical web app serving browsers):
- SHOULD set:
  - `Content-Security-Policy` (CSP) per app. NOTE: CSP's script-src matters most. All other directives are not as important; can usually be excluded for ease of development.
  - `X-Content-Type-Options: nosniff`
  - Clickjacking protection (`X-Frame-Options` and/or CSP `frame-ancestors`)
  - `Referrer-Policy` and `Permissions-Policy` where appropriate

NOTE:
- These headers may be set via reverse proxy/CDN; if not visible in app code, report as “verify at edge”.

Insecure patterns:
- No security headers anywhere (app or edge) for browser-facing app.
- CSP missing for apps rendering untrusted content.

Detection hints:
- Search for middleware setting headers: `w.Header().Set("Content-Security-Policy", ...)`, etc.
- Search for reverse proxy config setting headers.

Fix:
- Add centralized header middleware in Go, or configure at edge.
- Keep CSP realistic; avoid `unsafe-inline` where possible.

---

### GO-HTTP-005: Cookies MUST use secure attributes in production
Severity: Medium

Required (production, HTTPS):
- MUST set `Secure` on cookies carrying auth/session state. IMPORTANT NOTE: Only set `Secure` in production when TLS is configured. In local dev over HTTP, do not set `Secure` on cookies. Make this conditional on whether app runs in production mode. Also add a property like `SESSION_COOKIE_SECURE` to disable `Secure` cookies when testing over HTTP.
- MUST set `HttpOnly` on auth/session cookies.
- SHOULD set `SameSite=Lax` by default (or `Strict` if compatible); use `None` only when necessary (and only with `Secure`).
- SHOULD set bounded lifetimes (`Max-Age`/`Expires`) fitting the app.

Insecure patterns:
- Setting auth/session cookies without `Secure` in HTTPS deployments.
- Cookies without `HttpOnly` for session identifiers.
- `SameSite=None` for cookie-authenticated apps without strong CSRF strategy.

Detection hints:
- Search for `http.SetCookie`, `&http.Cookie{`, `Set-Cookie`.
- Inspect cookie flags in auth/session code.

Fix:
- Set correct fields on `http.Cookie`; centralize cookie creation.

Notes:
- SameSite is defense-in-depth and does not replace CSRF protections for cookie-auth apps.

---

### GO-HTTP-006: Cookie-authenticated state-changing endpoints MUST be CSRF-protected
Severity: High

- IMPORTANT NOTE: If cookies are not used for auth (e.g., pure bearer token in Authorization header with no ambient cookies), CSRF is not a risk for those endpoints.

Required:
- MUST protect all state-changing endpoints (POST/PUT/PATCH/DELETE) relying on cookies for authentication.
- SHOULD use well-tested CSRF library/middleware instead of rolling your own.
- MAY add extra defenses (Origin/Referer checks, Fetch Metadata, SameSite cookies), but tokens remain primary defense for cookie-authenticated apps.
If tokens are impractical, or for small applications:
* MUST at minimum require custom header and set session cookie SESSION_COOKIE_SAMESITE=lax. Strongest method besides requiring form token, and may be much easier to implement.


Insecure patterns:
- Cookie-authenticated JSON endpoints mutating state with no CSRF checks.
- Using GET for state-changing actions.

Detection hints:
- Enumerate all non-GET routes and identify auth mechanism.
- Look for CSRF middleware usage; if absent, treat as suspicious in browser-facing apps.

Fix:
- Add CSRF middleware covering all state-changing routes.
- If service is API for non-browser clients, avoid cookie auth; use Authorization headers.

---

### GO-HTTP-007: CORS must be explicit and least-privilege
Severity: Medium (High if misconfigured with credentials)

Required:
- If CORS is not needed, MUST keep it disabled.
- If CORS is needed:
  - MUST allowlist trusted origins (do not reflect arbitrary origins)
  - MUST be careful with credentialed requests; do not combine broad origins with cookies
  - SHOULD restrict allowed methods/headers

Insecure patterns:
- `Access-Control-Allow-Origin: *` paired with cookies (`Access-Control-Allow-Credentials: true`).
- Reflecting `Origin` without validation.

Detection hints:
- Search for `Access-Control-Allow-` header setting.
- Search for CORS middleware configuration.

Fix:
- Use strict origin allowlists and minimal methods/headers.
- Ensure cookie-auth endpoints are not exposed cross-origin unless required.

---

### GO-XSS-001: Use html/template and avoid bypassing auto-escaping with untrusted data
Severity: High

Required:
- MUST use `html/template` for HTML rendering (not `text/template`).
- MUST NOT convert untrusted data into “trusted” template types (`template.HTML`, `template.JS`, `template.URL`, etc.).
- SHOULD keep templates static and developer-controlled; treat dynamic templates as high risk.
- MUST NOT serve user-uploaded HTML/JS as active content unless explicitly intended and safely sandboxed.

Insecure patterns:
- `text/template` used to generate HTML.
- Using `template.HTML(userInput)` or similar typed wrappers.
- Writing unescaped user content directly into HTML responses.

Detection hints:
- Search for `text/template`, `template.New(...).Parse(...)`, and typed wrappers like `template.HTML(`.
- Inspect handlers returning HTML via string concatenation.

Fix:
- Use `html/template` and pass untrusted data as data, not markup.
- If limited HTML must be allowed, use vetted HTML sanitizer; still be careful with attributes/URLs.

---

### GO-SSTI-001: Never parse/execute templates from untrusted input (SSTI)
Severity: Critical

Required:
- MUST NOT call `template.Parse` / `template.ParseFiles` / `template.New(...).Parse(...)` on template text influenced by untrusted input.
- MUST treat “user-defined templates” as special high-risk design:
  - MUST use heavy sandboxing and strict allowlists
  - MUST isolate execution (process/container boundary) if truly required

Insecure patterns:
- `tmpl := template.Must(template.New("x").Parse(r.FormValue("tmpl")))`
- Reading templates from uploads / DB entries and executing them in same trust domain as server code.

Detection hints:
- Search for `.Parse(` and trace origin of template string.
- Look for “custom email templates”, “user theming templates”, etc.

Fix:
- Replace with safe substitution mechanisms (no code execution).
- If templates must be user-controlled, isolate and sandbox aggressively.

---

### GO-PATH-001: Prevent path traversal and unsafe file serving
Severity: High

Required:
- MUST NOT pass user-controlled paths to `os.Open`, `os.ReadFile`, `http.ServeFile`, or `http.FileServer` without strict validation and base-dir enforcement.
- MUST treat `..`, absolute paths, and OS-specific path tricks as hostile input.
- SHOULD store user uploads outside any static web root; serve through controlled handlers.
- MUST avoid directory listing for sensitive file trees.

Insecure patterns:
- `http.ServeFile(w, r, r.URL.Query().Get("path"))`
- `os.Open(filepath.Join(baseDir, userPath))` without checking result stays under `baseDir`
- `http.FileServer(http.Dir("."))` serving project root or user-writable directories

Detection hints:
- Search for `ServeFile(`, `FileServer(`, `http.Dir(`, `os.Open(`, `ReadFile(`, `filepath.Join(`.
- Trace whether path components come from request/DB.

Fix:
- Use allowlist of file identifiers (e.g., database IDs) mapped to server-side paths.
- Enforce base directory containment after cleaning and joining.
- Serve active formats as downloads (`Content-Disposition: attachment`) unless explicitly intended.

---

### GO-UPLOAD-001: File uploads must be validated, stored safely, and served safely
Severity: High

Required:
- MUST enforce upload size limits (app + edge).
- MUST validate file type via allowlists and content checks (not only extensions).
- MUST store uploads outside executable/static roots when possible.
- SHOULD generate server-side filenames (random IDs) and avoid trusting original names.
- MUST serve potentially active formats safely (download attachment) unless explicitly intended.

Insecure patterns:
- Accepting arbitrary file types and serving them back inline.
- Using user-supplied filename as storage path.
- Missing size/type validation.

Detection hints:
- Search for `multipart`, `FormFile`, `ParseMultipartForm`, `io.Copy` to disk.
- Check where files are stored and how served.

Fix:
- Add allowlist validation, safe storage, safe serving.
- Add scanning/quarantine workflows where applicable.

---

### GO-INJECT-001: Prevent SQL injection (parameterized queries / ORM)
Severity: High

Required:
- MUST use parameterized queries or ORM that parameterizes under the hood.
- MUST NOT build SQL by string concatenation / `fmt.Sprintf` / string interpolation with untrusted input.

Insecure patterns:
- `fmt.Sprintf("SELECT ... WHERE id=%s", r.URL.Query().Get("id"))`
- `query := "UPDATE users SET role='" + role + "' WHERE id=" + id`

Detection hints:
- Grep for `SELECT`, `INSERT`, `UPDATE`, `DELETE` and check how query strings are built.
- Trace untrusted data into `db.Query`, `db.Exec`, `QueryRow`, etc.

Fix:
- Replace with placeholders (`?`, `$1`, etc.) and pass parameters separately.
- Validate and type-check IDs before use.

---

### GO-INJECT-002: Prevent OS command injection; avoid shelling out with untrusted input
Severity: Critical to High (depends on exposure)

Required:
- MUST avoid executing external commands with attacker-controlled strings.
- If subprocess is necessary:
  - MUST use `exec.CommandContext` with argument list (not `sh -c`).
  - MUST NOT pass untrusted input to shell (`bash -c`, `sh -c`, PowerShell).
  - SHOULD use strict allowlists for any variable component (subcommand, flags, filenames).
- MUST assume CLI tools may interpret attacker-controlled args as flags or special values.

Insecure patterns:
- `exec.Command("sh", "-c", userString)`
- `exec.Command("bash", "-c", fmt.Sprintf("tool %s", user))`
- Calling shell for glob expansion of user-supplied globs.

Detection hints:
- Search for `os/exec`, `exec.Command(`, `CommandContext(`, `"sh"`, `"bash"`, `"-c"`.
- Trace untrusted input into command name/args.

Fix:
- Use library APIs instead of subprocesses.
- Hardcode command and allowlist/validate args.
- If shell is unavoidable, escape robustly and treat as high risk (prefer avoiding).

---

### GO-SSRF-001: Prevent SSRF in outbound HTTP requests
Severity: Medium (High in cloud/LAN environments)

- Note: Less important for small standalone projects. Most important when deploying into LAN or with other services listening on same server.

Required:
- MUST treat outbound requests to user-provided URLs as high risk.
- SHOULD allowlist hosts/domains for any user-influenced URL fetch.
- SHOULD block access to localhost/private IP ranges/link-local addresses and cloud metadata endpoints.
- MUST restrict schemes to `http`/`https` (no `file:`, `gopher:`, etc.).
- MUST set client timeouts and restrict redirects.

Insecure patterns:
- `http.Get(r.URL.Query().Get("url"))`
- “URL preview” / “webhook test” endpoints fetching arbitrary URLs.

Detection hints:
- Search for `http.Get`, `client.Do`, and URL values derived from requests/DB.
- Identify features fetching remote resources.

Fix:
- Parse URLs strictly; enforce scheme and allowlisted hostnames.
- Resolve DNS and enforce IP-range restrictions (with care for DNS rebinding).
- Set timeouts, disable redirects unless needed, cap response sizes.

---

### GO-HTTPCLIENT-001: Outbound HTTP clients MUST set timeouts and close bodies
Severity: High (DoS and resource exhaustion)

Required:
- MUST set overall timeout on `http.Client` usage (or equivalent per-request deadlines via context + transport timeouts).
- MUST call `resp.Body.Close()` for all successful requests (typically `defer resp.Body.Close()` right after error check).
- SHOULD limit response body reads (do not `io.ReadAll` unbounded responses).
- SHOULD restrict redirects for security-sensitive fetches (SSRF, auth flows).

Insecure patterns:
- Using `http.DefaultClient` / `http.Get` for user-influenced destinations with no timeout policy.
- Missing `defer resp.Body.Close()` causing resource leaks.
- `io.ReadAll(resp.Body)` with no limit.

Detection hints:
- Search for `http.Get(`, `http.Post(`, `client := &http.Client{}` without `Timeout`, `client.Do(` and missing closes.
- Search for `io.ReadAll(resp.Body)`.

Fix:
- Use configured client with timeouts.
- Always close response bodies.
- Use bounded readers (`io.LimitReader`) for large/untrusted responses.

Notes:
- net/http exposes `DefaultClient` as zero-valued `http.Client`; easily leads to “no timeout” behavior unless configured.

---

### GO-REDIRECT-001: Prevent open redirects
Severity: Medium (can be High with auth flows)

Required:
- MUST validate redirect targets derived from untrusted input (`next`, `redirect`, `return_to`).
- SHOULD prefer only same-site relative paths.
- SHOULD fall back to safe default on validation failure.

Insecure patterns:
- `http.Redirect(w, r, r.URL.Query().Get("next"), http.StatusFound)` with no validation.

Detection hints:
- Search for `http.Redirect(` and check origin of location.

Fix:
- Allowlist internal paths or known domains.
- Reject absolute URLs unless explicitly needed and allowlisted.

---

### GO-CRYPTO-001: Cryptographic randomness MUST come from crypto/rand
Severity: High (Critical if used for auth/session tokens or keys)

Required:
- MUST use `crypto/rand` for:
  - session IDs, password reset tokens, API keys, CSRF tokens, nonces
  - encryption keys, signing keys, salts when required
- MUST NOT use `math/rand` for any security-sensitive value.
- SHOULD use built-in helpers producing appropriately strong tokens when available.

Insecure patterns:
- `math/rand.Seed(time.Now().UnixNano())` followed by token generation for auth or sessions.
- Using UUIDv4-like constructs built from `math/rand`.

Detection hints:
- Search for `math/rand`, `rand.Seed`, `rand.Intn` in code touching auth/session/token flows.
- Search for custom token generators.

Fix:
- Switch to `crypto/rand` (`rand.Reader`, `rand.Read`, or secure token helpers).
- Ensure sufficient entropy and use URL-safe encoding.

---

### GO-AUTH-001: Password storage MUST use adaptive hashing (bcrypt/argon2id) and safe comparisons
Severity: High

Required:
- MUST hash passwords with adaptive password hashing function (bcrypt or argon2id).
- MUST NOT store plaintext passwords or reversible encryption of passwords.
- MUST compare secrets in constant time when relevant (tokens, MACs, API keys) to reduce timing leaks.
- SHOULD ensure password policies do not exceed algorithm constraints (e.g., bcrypt has input length limits; handle long passphrases appropriately).

Insecure patterns:
- `sha256(password)` stored as password hash.
- Plaintext password storage.
- Comparing secrets with `==` in timing-sensitive contexts.

Detection hints:
- Search for `sha1`, `sha256`, `md5` used on passwords.
- Search for `bcrypt`/`argon2` usage; if absent, suspect.
- Search for `==` comparisons on tokens/API keys.

Fix:
- Use `bcrypt.GenerateFromPassword` / `CompareHashAndPassword` or argon2id with recommended parameters.
- Use constant-time compare helpers when comparing MACs/tokens.

Notes:
- Go provides bcrypt in `golang.org/x/crypto/bcrypt` and constant-time comparisons in `crypto/subtle`.

---

### GO-CONC-001: Data races and concurrency hazards MUST be treated as security-relevant
Severity: Medium to High (depends on what races affect)

Required:
- MUST run tests with race detector (`go test -race`) in CI for security-sensitive services.
- MUST fix detected races; do not suppress without deep justification.
- SHOULD treat shared mutable state in handlers as high risk; enforce synchronization or avoid shared mutability.

Insecure patterns:
- Global maps/slices mutated from multiple goroutines without mutex.
- Caches or auth/session state stored in globals without concurrency protection.
- Racy access to authorization state (can lead to bypasses or inconsistent enforcement).

Detection hints:
- Search for `var someMap = map[...]...` used in handlers.
- Look for missing `sync.Mutex`, `sync.Map`, channels, or other synchronization.
- Ensure CI includes `-race` and runs relevant tests.

Fix:
- Add proper synchronization or redesign to avoid shared mutable state.
- Add race tests and run them continuously.

Notes:
- Go race detector only finds races in executed code paths. Improve test coverage and run realistic workloads with `-race` where feasible.

---

### GO-UNSAFE-001: Use of unsafe/cgo MUST be minimized and audited like memory-unsafe code
Severity: High (Critical in high-risk code paths)

Required:
- SHOULD avoid importing `unsafe` in application code unless absolutely necessary.
- If `unsafe` is used, MUST treat it as “manual memory safety” requiring careful review and test coverage.
- If `cgo` is used, MUST treat C/C++ boundary as memory-unsafe; apply secure coding practices on C side and isolate where possible.

Insecure patterns:
- Widespread `unsafe.Pointer` casts in parsing, serialization, auth, or network code.
- `cgo` used for parsing or security boundaries without sandboxing.

Detection hints:
- Search for `import "unsafe"`, `unsafe.Pointer`, `// #cgo`, `import "C"`.
- Prioritize review where unsafe touches untrusted input.

Fix:
- Replace unsafe/cgo usage with safe standard library alternatives where possible.
- Isolate unsafe code in small, well-tested modules with fuzz/race tests.

--------------------------------------------------------------------

## 5) Practical scanning heuristics (how to “hunt”)

When actively scanning, use each §4 rule's detection hints plus these high-signal patterns:

Toolchain & dependencies:
- `FROM golang:` (Dockerfiles), `go-version:` (CI), `toolchain go` (go.mod), pinned old versions
- `replace` directives in `go.mod` to forks/paths

Body parsing / DoS:
- `ParseMultipartForm`, `FormFile`, `multipart.NewReader` without explicit limits

Crypto:
- `InsecureSkipVerify: true`

Always confirm:
- data origin (untrusted vs trusted)
- sink type (template/SQL/subprocess/files/http)
- protective controls present (limits, validation, allowlists, middleware, network controls)

--------------------------------------------------------------------

## 6) Sources (accessed 2026-01-28)

Primary Go documentation:
- Go Security Policy — https://go.dev/doc/security/policy
- Go Release History (security fixes in patch releases) — https://go.dev/doc/devel/release
- Go 1.25 Release Notes — https://go.dev/doc/go1.25
- net/http (server timeouts, MaxHeaderBytes, DefaultClient) — https://pkg.go.dev/net/http
- html/template (auto-escaping and trusted-template assumptions) — https://pkg.go.dev/html/template
- crypto/tls (MinVersion defaults, InsecureSkipVerify warnings) — https://pkg.go.dev/crypto/tls
- crypto/rand (secure randomness, token helpers) — https://pkg.go.dev/crypto/rand
- crypto/subtle (constant-time comparisons) — https://pkg.go.dev/crypto/subtle
- os/exec (no shell by default; command execution guidance) — https://pkg.go.dev/os/exec
- unsafe (bypasses type safety) — https://go.dev/src/unsafe/unsafe.go
- net/http/pprof (debug endpoints) — https://pkg.go.dev/net/http/pprof
- cmd/go (module authentication via go.sum/checksum DB; env vars like GOINSECURE) — https://pkg.go.dev/cmd/go
- Module Mirror and Checksum Database Launched (Go blog) — https://go.dev/blog/module-mirror-launch
- govulncheck documentation — https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- Go Race Detector documentation — https://go.dev/doc/articles/race_detector
- bcrypt (password hashing) — https://pkg.go.dev/golang.org/x/crypto/bcrypt
- Go vulnerability entry example (multipart resource consumption) — https://pkg.go.dev/vuln/GO-2023-1569

OWASP Cheat Sheet Series (general web security):
- Session Management — https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- CSRF Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- SSRF Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- XSS Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- HTTP Security Response Headers — https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
