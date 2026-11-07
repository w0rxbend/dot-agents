# FastAPI (Python) Web Security Spec (FastAPI 0.128.x, Python 3.x) ([PyPI][1])

FastAPI typically runs on an ASGI server (e.g., Uvicorn) and builds on Starlette + Pydantic; spec covers those layers where security-relevant. ([PyPI][1])

---

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session cookies, signing keys, database URLs with credentials).
* MUST NOT “fix” security by disabling protections (e.g., weakening auth, making CORS permissive, skipping signature checks, disabling validation, turning off TLS verification, adding `allow_origins=["*"]` with credentials).
* MUST give **evidence-based findings** in audits: cite file paths, code snippets, configuration values backing each claim.
* MUST treat uncertainty honestly: if protection might live in infrastructure (reverse proxy, WAF, CDN, service mesh), report “not visible in app code; verify at runtime/config”.
* MUST treat browser controls correctly:

  * CORS is **not** an auth mechanism; only affects browsers.
  * CSRF defenses apply when browser auto-attaches credentials (cookies); usually not relevant for pure header-token APIs. ([OWASP Cheat Sheet Series][2])

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing or modifying FastAPI code:

* MUST follow every **MUST** requirement here.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default APIs and proven libraries over custom security code.
* MUST avoid adding new risky sinks (shell execution, unsafe deserialization, dynamic eval, untrusted template rendering, unsafe file serving, unsafe redirects, arbitrary outbound fetching).

### 1.2 Passive review mode (always on while editing)

Anywhere in a FastAPI repo (even if user did not ask for a security scan):

* MUST “notice” spec violations in touched/nearby code.
* SHOULD mention issues as they arise, with brief explanation + safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. App entrypoints / deployment scripts / Dockerfiles / Procfiles / Helm/terraform.
2. ASGI server configuration (Uvicorn/Gunicorn), proxy settings, debug/reload settings.
3. FastAPI app configuration (docs exposure, middleware, trusted hosts, CORS).
4. Authn/Authz design (dependencies, JWT/session handling, password storage).
5. Cookie/session usage + CSRF (if cookies used).
6. Input validation and output shaping (Pydantic models, mass assignment, excessive data exposure).
7. Template rendering and XSS/SSTI (if HTML served).
8. File handling (uploads + downloads), StaticFiles, Range support.
9. Injection classes (SQL, command execution, unsafe deserialization).
10. Outbound requests (SSRF), redirect handling, WebSockets security.

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Examples:

* Query parameters / path parameters
* JSON bodies (including nested fields)
* Headers (including `Host`, `Origin`, `X-Forwarded-*`)
* Cookies (including session cookies)
* File uploads (multipart parts)
* WebSocket messages, query params, and headers during handshake ([Starlette][3])
* Any data from external systems (webhooks, third-party APIs, message queues)
* Any persisted user-originated content (DB rows)

### 2.2 State-changing request

Request is state-changing if it can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook send), or start privileged actions.

### 2.3 Required audit finding format

Per issue found, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + function/route name + line(s)
* Evidence: the exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

* No debug tracebacks or auto-reload in production. ([PyPI][4])
* Production ASGI server configuration (workers, timeouts, resource controls). ([PyPI][4])
* Host header validation enabled (TrustedHostMiddleware or equivalent). ([PyPI][5])
* CORS disabled unless explicitly needed; if enabled, strict and least-privilege. ([OWASP Cheat Sheet Series][6])
* Auth enforced consistently via dependencies (no “oops, forgot auth on this route”). ([FastAPI][7])
* If cookies/sessions used: secure cookie flags, CSRF addressed. ([OWASP Cheat Sheet Series][8])
* Request size and multipart limits at edge, validated in app as needed (mitigates memory/CPU DoS). ([advisories.gitlab.com][9])
* Dependencies patched promptly, especially Starlette/python-multipart (history of multiple DoS and traversal advisories). ([advisories.gitlab.com][10])

---

## 4) Rules (generation + audit)

### FASTAPI-DEPLOY-001: Do not use auto-reload / dev-only server modes in production

Severity: High (if production)

Required:

* MUST NOT run production in auto-reload/watch mode (e.g., Uvicorn reload).
* MUST use production process model (e.g., multiple workers where appropriate) and stable server settings. ([PyPI][4])

Insecure patterns:

* `uvicorn ... --reload` (or equivalent “reload=True” configs) in production entrypoints.

Detection hints:

* Search for `--reload`, `reload=True`, `watchfiles`, `fastapi dev`, “development” run scripts.
* Check Docker CMD/ENTRYPOINT, Procfile, systemd units, shell scripts.

Fix:

* Remove reload in production; run Uvicorn/Gunicorn with stable settings and explicit worker config. ([PyPI][4])

Note:

* Reload is fine for local development. Flag only when clearly a production entrypoint.

---

### FASTAPI-DEPLOY-002: Debug mode MUST be disabled in production

Severity: Critical

Required:

* MUST NOT enable debug tracebacks in production (FastAPI/Starlette debug mode can expose sensitive internals, ease some exploit chains). ([PyPI][5])
* MUST treat any config returning detailed stack traces to clients as sensitive.

Insecure patterns:

* `app = FastAPI(debug=True)` (or Starlette `debug=True`), or equivalent environment toggles enabling debug in production. ([PyPI][5])
* Server/log config exposing tracebacks to end users.

Detection hints:

* Search for `debug=True`, `DEBUG = True`, environment flags mapped to debug.
* Review exception middleware and error handler setup.

Fix:

* Enable debug only in local dev/test.
* Return generic error responses to clients; log details internally.

---

### FASTAPI-OPENAPI-001: OpenAPI and interactive docs MUST be disabled or protected in production

Severity: Medium (can be High in sensitive/internal apps)

Required:

* SHOULD disable `/docs`, `/redoc`, and `/openapi.json` in production for public-facing services unless business explicitly needs them.
* If enabled, MUST protect them (e.g., auth, network allowlists, or internal-only routing).
* MUST NOT assume “security through obscurity”; treat docs exposure as information disclosure amplifier.

Insecure patterns:

* Publicly reachable `/docs` and `/openapi.json` for internal/admin APIs.
* Docs enabled on same hostname as production without access control.

Detection hints:

* Look for `FastAPI(docs_url=..., redoc_url=..., openapi_url=...)` or defaults.
* Check reverse proxy routing and allowlists.

Fix:

* Disable docs endpoints in prod (`docs_url=None`, `redoc_url=None`, `openapi_url=None`) or restrict access at edge.

---

### FASTAPI-AUTH-001: Authentication MUST be explicit and consistently enforced via dependencies

Severity: High

Required:

* MUST implement authentication as dependency (or router-level dependency) so protected endpoints cannot “forget” auth.
* MUST default to “deny” for privileged routers/endpoints; explicitly mark truly public routes.
* SHOULD centralize auth enforcement at router boundaries (e.g., protected `APIRouter` for authenticated endpoints). ([FastAPI][7])

Insecure patterns:

* Ad-hoc per-route auth checks scattered in handlers (easy to miss).
* Mix of protected/unprotected endpoints with no clear policy.

Detection hints:

* List routers and endpoints; check protected ones include `Depends(...)`/`Security(...)`.
* Search for `if user is None: raise ...` inside handlers (instead of dependencies).

Fix:

* Move authentication into a dependency; attach it to router/endpoint consistently via `Depends()`/`Security()`. ([FastAPI][7])

---

### FASTAPI-AUTH-002: Use standard auth transports; avoid secrets in URLs

Severity: High

Required:

* SHOULD use `Authorization: Bearer <token>` header for token auth, not query parameters. ([FastAPI][11])
* MUST NOT put secrets (tokens, reset links containing long-lived secrets, API keys) in query strings when avoidable.

Insecure patterns:

* `?token=...`, `?api_key=...`, `?auth=...` as primary auth.
* Long-lived access tokens embedded in URLs (leak via logs, referrers, caches).

Detection hints:

* Search for parameter names like `token`, `api_key`, `key`, `secret`, `password`.
* Look for security schemes using query API keys without justification.

Fix:

* Move tokens to Authorization headers; rotate/shorten lifetimes; use POST bodies for sensitive values.

---

### FASTAPI-AUTH-003: Password storage MUST be strongly hashed; never store plaintext passwords

Severity: Critical

Required:

* MUST store passwords using strong, slow password hashing scheme (e.g., Argon2id, bcrypt).
* MUST NOT store plaintext passwords, or rely on reversible encryption as primary protection.
* SHOULD use established libraries for hashing and verification (do not roll your own).

Insecure patterns:

* Plaintext passwords in DB.
* Fast hashes (e.g., SHA256) without proper password hashing KDF.
* Password hashes in API responses.

Detection hints:

* Search for persisted `password=` fields and `hashlib.md5/sha1/sha256` usage on passwords.
* Inspect response models for password/hash fields.

Fix:

* Migrate to proper password hashing library; add re-hash-on-login upgrade path.

---

### FASTAPI-AUTH-004: JWT validation MUST be strict; JWTs MUST NOT carry secrets

Severity: High

Required:

* MUST validate JWT signature and enforce algorithm allowlist.
* MUST validate standard claims fitting your system (at least `exp`; typically also `iss`/`aud` if multi-service or multi-tenant).
* MUST treat JWT contents as client-readable; no secrets in JWT payloads. ([FastAPI][12])

Insecure patterns:

* `jwt.decode(..., options={"verify_signature": False})` or equivalent.
* Accepting `alg=none` / algorithm confusion.
* Sensitive secrets (API keys, passwords) stored in JWT payload.

Detection hints:

* Search for `jwt.decode`, `python-jose`, `PyJWT`, `verify_signature`.
* Check for missing exp validation or long expirations.

Fix:

* Enforce strict validation (signature, allowed algorithms, exp, any required issuer/audience constraints).
* Store only identifiers/claims safe to expose to client. ([FastAPI][12])

---

### FASTAPI-AUTHZ-001: Authorization MUST be enforced per-object and per-property

Severity: High

Required:

* MUST do object-level authorization whenever accessing resource by user-controlled identifier (ID in path/query/body).
* MUST do property-level authorization and response shaping to prevent “excessive data exposure” (e.g., admin-only fields). ([OWASP Foundation][13])

Insecure patterns:

* `GET /users/{id}` returns user record without verifying caller can access that `id`.
* Response models include internal fields (roles, permissions, billing data, password hashes).

Detection hints:

* Enumerate endpoints accepting IDs; trace whether authz check runs.
* Compare response models for public vs internal fields.

Fix:

* Add object-level checks (ownership, ACLs, tenant boundaries).
* Use dedicated response models with only allowed fields.

---

### FASTAPI-SESS-001: If using cookie-based sessions and TLS, cookie attributes MUST be secure in production

Severity: High (only if TLS is enabled)

Required (production, HTTPS):

* MUST set session cookies to HTTPS-only (secure). IMPORTANT NOTE: Only set `Secure` in production environment when TLS is configured. In local dev over HTTP, do not set `Secure` on cookies. Set it conditionally on production mode. Also add a property like `SESSION_COOKIE_SECURE` to disable `Secure` cookies when testing over HTTP.
* MUST set HttpOnly for session cookies (not accessible to JS).
* SHOULD use `SameSite=Lax` (or `Strict` if UX allows); if cross-site cookies required, document CSRF implications and add compensating controls. ([OWASP Cheat Sheet Series][8])
* If using Starlette `SessionMiddleware`, MUST set `https_only=True` in production and choose appropriate `same_site`. ([PyPI][5])

Insecure patterns:

* Session cookies without Secure/HttpOnly.
* `SameSite=None` cookies used for authenticated state-changing endpoints without CSRF protections.

Detection hints:

* Search for `SessionMiddleware(`; inspect parameters like `https_only`, `same_site`.
* Search for `set_cookie(` usage and cookie flags.

Fix:

* Set secure cookie attributes; prefer short lifetimes for high-privilege sessions. ([OWASP Cheat Sheet Series][8])

---

### FASTAPI-SESS-002: Do not store sensitive secrets in signed session cookies

Severity: High

Required:

* MUST assume cookie-based session data is client-readable (signed ≠ encrypted); do not store secrets/PII unless encrypted server-side.
* Store only opaque identifiers (e.g., session ID) or non-sensitive state in cookie; keep sensitive session state server-side. ([OWASP Cheat Sheet Series][8])

Insecure patterns:

* Access tokens, refresh tokens, or PII directly in cookie session payloads.
* Treating “signed cookies” as confidential storage.

Detection hints:

* Search for `request.session[...] =` or `session[...] =`-equivalent patterns; check what is stored.
* Identify use of `SessionMiddleware` or other cookie session mechanisms.

Fix:

* Move sensitive values to server-side storage; keep cookie minimal.

---

### FASTAPI-CSRF-001: Cookie-authenticated state-changing requests MUST be CSRF-protected

Severity: High

Required:

* MUST protect all state-changing endpoints (POST/PUT/PATCH/DELETE) that rely on cookies for authentication.
* SHOULD use proven CSRF approach (synchronizer token pattern, or well-reviewed middleware), not a homegrown one. ([OWASP Cheat Sheet Series][2])
* MAY add defense-in-depth (Origin/Referer checks, SameSite cookies, Fetch Metadata), but tokens are primary defense for cookie-authenticated apps. ([OWASP Cheat Sheet Series][2])
* IMPORTANT NOTE: If cookies are not used for auth (auth via `Authorization` header), CSRF usually not applicable. ([FastAPI][11])

Insecure patterns:

* Cookie-authenticated endpoints changing state with no CSRF validation.
* GET for state-changing actions (amplifies CSRF risk).

Detection hints:

* Enumerate non-GET routes; check whether cookies are used for auth.
* Look for CSRF token generation/verification or middleware.

Fix:

* Add and validate CSRF tokens on state-changing actions when cookie auth is in use. ([OWASP Cheat Sheet Series][2])

---

### FASTAPI-VALID-001: Request parsing and validation MUST be schema-driven; prevent mass assignment

Severity: Medium (especially for APIs that write to DB)

Required:

* SHOULD use Pydantic models for request bodies, not arbitrary `dict`/`Any`.
* SHOULD configure models to reject unexpected fields where appropriate (prevents “mass assignment” style bugs).
* MUST validate and normalize identifiers (IDs, email, URLs) before using them for access control or side effects. ([OWASP Cheat Sheet Series][14])

Insecure patterns:

* `payload = await request.json()` followed by `Model(**payload)` or direct DB writes with `payload` (no allowlist).
* Models silently accepting unknown fields on write endpoints.

Detection hints:

* Search for `await request.json()`, `request.body()`, `dict`-typed bodies, `Any`-typed bodies.
* Look for endpoints doing `db.update(**payload)` or `Model(**payload)` with unfiltered input.

Fix:

* Use explicit Pydantic models with allowlisted fields; reject extras on write endpoints. ([OWASP Cheat Sheet Series][14])

---

### FASTAPI-RESP-001: Prevent excessive data exposure via response models and explicit serialization

Severity: Medium

Required:

* MUST define response models with only intended fields (especially user, auth-related, billing objects).
* SHOULD use separate models for “create input”, “db/internal”, and “public output” to avoid leaking sensitive fields. ([FastAPI][15])

Insecure patterns:

* Returning ORM objects or dicts with internal columns.
* Reusing “DB model” as response model (includes `password_hash`, `is_admin`, etc).

Detection hints:

* Look for endpoints that `return user` where `user` is an ORM instance.
* Check for missing `response_model` on endpoints returning sensitive resources.

Fix:

* Add explicit response models; create “public” schemas excluding sensitive fields. ([FastAPI][15])

---

### FASTAPI-XSS-001: Prevent reflected/stored XSS in HTML responses and templates

Severity: High (if the service serves HTML)

Required:

* MUST use templating with auto-escaping enabled for HTML.
* MUST NOT mark untrusted content as safe (no unsafe “raw HTML” rendering of user-controlled data).
* SHOULD deploy CSP when serving HTML with any user content. ([OWASP Cheat Sheet Series][16])

Insecure patterns:

* User content rendered directly into HTML without escaping/sanitization.
* Disabling auto-escaping or using “raw HTML” features without sanitization.

Detection hints:

* Search for template rendering and string concatenation building HTML.
* Review templates for “unsafe” filters/constructs and unquoted attributes.

Fix:

* Keep auto-escaping on; sanitize user HTML only if absolutely required, with trusted sanitizer; add CSP. ([OWASP Cheat Sheet Series][16])

Note:

* For pure JSON API, XSS is usually a client/app concern, but error pages/docs pages might still render HTML.

---

### FASTAPI-SSTI-001: Never render untrusted templates (Server-Side Template Injection)

Severity: Critical

Required:

* MUST NOT render templates containing user-controlled template syntax.
* MUST treat “template-from-string” rendering as dangerous if untrusted input influences it.
* If untrusted templates are absolutely required (rare, high-risk):

  * MUST use sandboxed templating and restrict capabilities.
  * MUST assume sandbox escapes are possible; add isolation and strict allowlists. ([OWASP Foundation][17])

Insecure patterns:

* Rendering templates from user input or DB via normal Jinja environment.
* Building templates dynamically from user-controlled strings.

Detection hints:

* Grep for Jinja `Environment.from_string`, `Template(...)`, or similar.
* Trace template string origin (request, DB, uploads, admin panels).

Fix:

* Replace with non-executable templating (simple string substitution).
* If truly needed, use Jinja’s sandbox environment plus strong isolation. ([jinja.palletsprojects.com][18])

---

### FASTAPI-HEADERS-001: Set essential security headers (in app or at the edge)

Severity: Medium

Required (typical API/web app):

* SHOULD set:

  * `X-Content-Type-Options: nosniff`
  * Clickjacking protection (`X-Frame-Options` and/or CSP `frame-ancestors`) if HTML is served
  * `Referrer-Policy` and `Permissions-Policy` as appropriate

NOTE:

* Proxy/CDN may set headers. If not visible in app code, flag as “verify at edge”. ([OWASP Cheat Sheet Series][6])

Insecure patterns:

* No security headers anywhere (app or edge) for apps serving HTML or sensitive APIs.

Detection hints:

* Search for header-setting middleware; check reverse proxy config.

Fix:

* Set headers centrally (middleware) or via reverse proxy/CDN.

---

### FASTAPI-CORS-001: CORS MUST be explicit and least-privilege

Severity: Medium (High if misconfigured with credentials)

Required:

* If CORS not needed, MUST keep it disabled.
* If CORS needed:

  * MUST allowlist trusted origins (do not reflect arbitrary origins).
  * MUST NOT combine credentialed requests with wildcard origins (unsafe; compliant middleware commonly rejects it). ([OWASP Cheat Sheet Series][6])
  * SHOULD restrict allowed methods and headers.

Insecure patterns:

* `allow_origins=["*"]` together with `allow_credentials=True`.
* Reflecting `Origin` without validation.
* `allow_origin_regex=".*"` used broadly.

Detection hints:

* Search for `CORSMiddleware` configuration.
* Look for `allow_origins=["*"]`, `allow_credentials=True`, `allow_origin_regex`.

Fix:

* Use explicit origin allowlist, minimal methods/headers; keep credentials off unless required. ([OWASP Cheat Sheet Series][6])

---

### FASTAPI-HOST-001: Host header MUST be validated in production

Severity: Low

Required:

* SHOULD use `TrustedHostMiddleware` (or edge equivalent) to restrict accepted Host values. ([PyPI][5])
* MUST NOT trust `Host` header for security-sensitive decisions without validation.

Insecure patterns:

* No Host validation while building external URLs (password reset links, callback URLs) from request host.
* Arbitrary Host headers allowed in apps behind permissive proxies.

Detection hints:

* Search for `TrustedHostMiddleware` usage.
* Search for logic building external URLs from `request.url`, `request.base_url`, or host-derived values.

Fix:

* Configure strict allowed-hosts list in production; enforce at edge too if possible.

---

### FASTAPI-PROXY-001: Reverse proxy trust MUST be configured correctly

Severity: High (when behind a proxy)

Required:

* If behind reverse proxy, MUST configure forwarded-header trust correctly.
* MUST NOT blindly trust `X-Forwarded-*` headers from open internet.
* If using Uvicorn proxy header support, MUST restrict which IPs may send forwarded headers. ([PyPI][4])

Insecure patterns:

* Enabling proxy headers broadly without restricting trusted proxy IPs.
* Using forwarded headers to decide “is secure” / “is internal” / “client IP” without proper trust boundaries.

Detection hints:

* Search for `--proxy-headers`, `--forwarded-allow-ips`, or equivalent config.
* Search for security-sensitive use of `request.client.host`, `request.url.scheme`, `request.headers["x-forwarded-for"]`.

Fix:

* Enable Uvicorn proxy headers only behind a known proxy; restrict `forwarded_allow_ips` to that proxy. ([PyPI][4])
* Keep Host allowlisting even behind proxies.

---

### FASTAPI-LIMITS-001: Request and multipart limits MUST be enforced to prevent DoS

Severity: Low

Required:

* MUST enforce request size limits at edge (reverse proxy/load balancer) and validate in app where needed.
* MUST scrutinize multipart/form-data handling; past vulnerabilities include unbounded buffering and DoS vectors. ([advisories.gitlab.com][9])
* SHOULD rate limit and/or add per-IP/per-user throttles for expensive endpoints.

Insecure patterns:

* Accepting arbitrarily large JSON bodies or multipart forms.
* Parsing multipart forms without size/field-count controls.

Detection hints:

* Identify file upload endpoints and `multipart/form-data` usage.
* Look for missing proxy-level limits (nginx `client_max_body_size`, ALB limits, etc.) and missing app-level checks.

Fix:

* Enforce strict body limits and multipart constraints; keep Starlette and python-multipart on patched versions. ([advisories.gitlab.com][9])

---

### FASTAPI-FILES-001: Prevent path traversal and unsafe static file exposure

Severity: High

Required:

* MUST NOT pass user-controlled file paths to `FileResponse`/filesystem calls without strict validation and safe base directories.
* If using `StaticFiles`, MUST keep Starlette updated and know its security history (older versions have a path traversal advisory). ([advisories.gitlab.com][10])
* MUST NOT serve user uploads as executable/active content (especially HTML/JS) from static root without safe handling.

Insecure patterns:

* `FileResponse(request.query_params["path"])`
* Mounting `StaticFiles(directory="uploads")` where uploads include HTML/JS/SVG and are served inline.

Detection hints:

* Search for `FileResponse(`, `StaticFiles(`, `open(` in routes.
* Trace whether path comes from untrusted input.

Fix:

* Use opaque IDs for files; map IDs to server-side stored paths.
* Serve untrusted content as attachment downloads where appropriate.

---

### FASTAPI-FILES-002: Mitigate Range-header DoS on file-serving endpoints

Severity: Low (if affected versions and file serving is enabled)

Required:

* MUST keep Starlette patched against known file-serving DoS issues if using `FileResponse`/`StaticFiles`.
* MUST treat unusual `Range` header handling and file serving as DoS surface. ([advisories.gitlab.com][19])

Insecure patterns:

* Serving large files with vulnerable Starlette versions.
* No rate limiting / CDN shielding for file endpoints.

Detection hints:

* Identify Starlette version; flag if in affected range.
* Find uses of `FileResponse` and `StaticFiles`.

Fix:

* Upgrade Starlette to fixed version per advisory. ([advisories.gitlab.com][19])
* Add edge caching/rate limiting for file endpoints where appropriate.

---

### FASTAPI-UPLOAD-001: File uploads MUST be validated, stored safely, and served safely

Severity: Medium

Required:

* MUST enforce upload size limits (app + edge).
* MUST validate file type with allowlists and content checks (not only extension). ([OWASP Cheat Sheet Series][20])
* SHOULD generate server-side filenames (random IDs); avoid trusting original names.
* MUST serve potentially active formats safely (download attachment) unless explicitly intended.

Insecure patterns:

* Accepting arbitrary file types and serving them back inline.
* User-supplied filename as storage path.

Detection hints:

* Find upload handlers and where/how files are written.
* Look for direct exposure of upload directories.

Fix:

* Implement allowlist validation + safe storage + safe serving; add scanning/quarantine if applicable. ([OWASP Cheat Sheet Series][20])

---

### FASTAPI-INJECT-001: Prevent SQL injection (use parameterized queries / ORM)

Severity: High

Required:

* MUST use parameterized queries or ORM that parameterizes under the hood.
* MUST NOT build SQL by string concatenation / f-strings with untrusted input. ([OWASP Cheat Sheet Series][21])

Insecure patterns:

* `f"SELECT ... WHERE id={user_id}"`
* `"... WHERE name = '%s'" % user_input`

Detection hints:

* Grep for SQL keywords in Python strings near `.execute(...)`.
* Trace untrusted data into DB calls.

Fix:

* Replace with parameterized queries / ORM query APIs; validate types before querying. ([OWASP Cheat Sheet Series][21])

---

### FASTAPI-INJECT-002: Prevent OS command injection

Severity: Critical to High (depends on exposure)

Required:

* MUST avoid executing shell commands with untrusted input.
* If subprocess needed:

  * MUST pass args as a list (not a string)
  * MUST NOT use `shell=True` with attacker-influenced strings
  * SHOULD use strict allowlists for any variable component ([OWASP Cheat Sheet Series][22])

Insecure patterns:

* `os.system(user_input)`
* `subprocess.run(f"cmd {user}", shell=True)`
* Passing user strings into `bash -c`, `sh -c`, PowerShell, etc.

Detection hints:

* Search for `os.system`, `subprocess`, `Popen`, `shell=True`.
* Trace data from request/DB into these calls.

Fix:

* Use library APIs, not shell commands.
* If unavoidable, hard-code command and allowlist validated parameters; use `--` separator where supported. ([OWASP Cheat Sheet Series][22])

---

### FASTAPI-SSRF-001: Prevent server-side request forgery (SSRF) in outbound HTTP

Severity: Medium (can be High in cloud/VPC environments)

- Note: Less important for small stand-alone projects. Most important when deploying into a LAN or alongside other services listening on same server.

Required:

* MUST treat outbound requests to user-provided URLs as high risk.
* SHOULD validate and restrict destinations (allowlist hosts/domains) for any user-influenced URL fetch.
* SHOULD block localhost/private IP ranges/link-local and cloud metadata endpoints.
* MUST restrict protocols to http/https.
* SHOULD set timeouts and control redirects carefully. ([OWASP Cheat Sheet Series][23])

Insecure patterns:

* `httpx.get(request.query_params["url"])`
* “URL preview/import/webhook tester” features accepting arbitrary URLs.

Detection hints:

* Search for `requests`, `httpx`, `urllib`, `aiohttp` calls with URLs from requests/DB.
* Identify endpoints named `fetch`, `preview`, `proxy`, `webhook`, `import`.

Fix:

* Implement strict URL parsing + allowlists; add egress controls; set short timeouts; disable redirects if not required. ([OWASP Cheat Sheet Series][23])

---

### FASTAPI-REDIRECT-001: Prevent open redirects

Severity: Low

Required:

* MUST validate redirect targets from untrusted input (`next`, `redirect`, `return_to`).
* SHOULD redirect only to same-site relative paths or allowlisted domains. ([OWASP Cheat Sheet Series][24])

Insecure patterns:

* Returning `RedirectResponse(next)` where `next` is user-controlled with no validation.

Detection hints:

* Search for `RedirectResponse(` or redirect logic; check target source.

Fix:

* Allow only relative paths or allowlisted domains; fall back to safe default. ([OWASP Cheat Sheet Series][24])

---

### FASTAPI-WS-001: WebSocket endpoints MUST be authenticated and protected against cross-site abuse

Severity: Medium to High (depends on data/privilege)

Required:

* MUST authenticate WebSocket connections for any non-public channel (WebSockets don’t inherently provide auth). ([OWASP Cheat Sheet Series][25])
* SHOULD enforce origin/CSRF-like protections for browser-based WebSocket clients (Origin validation is a common control).
* SHOULD rate limit message frequency and connection attempts; close idle/abusive connections.

Insecure patterns:

* `@app.websocket(...)` accepts and trusts connection with no auth check.
* Query-string tokens for auth without considering leakage/rotation.

Detection hints:

* Search for `@app.websocket` / `websocket_endpoint`; check auth runs before sensitive operations are accepted.
* Review origin checks, token parsing, per-connection authorization.
* Look for use of `ws://` in prod configs.

Fix:

* Require authentication during handshake (e.g., token or session); enforce authorization for actions/messages.
* Validate Origin for browser-based clients where appropriate; apply rate limits and timeouts. ([OWASP Cheat Sheet Series][25])

---

### FASTAPI-SUPPLY-001: Dependency and patch hygiene (focus on security-relevant deps)

Severity: Low

Required:

* SHOULD pin and regularly update security-critical dependencies (FastAPI, Starlette, Uvicorn, Pydantic, python-multipart, auth/JWT libs).
* MUST respond promptly to known security advisories.
* MUST treat file serving and multipart parsing dependencies as security-sensitive (historical CVEs). ([advisories.gitlab.com][10])

Audit focus examples (historical):

* Starlette StaticFiles path traversal (fixed in 0.27.0). ([advisories.gitlab.com][10])
* Starlette multipart/form-data DoS (fixed in 0.40.0). ([advisories.gitlab.com][9])
* Starlette FileResponse Range header DoS (fixed in 0.49.1). ([advisories.gitlab.com][19])

Detection hints:

* Check `requirements.txt`, lockfiles, container images, runtime environments for actually installed versions.
* Map file upload/file serving features to dependency versions.

Fix:

* Upgrade to patched versions per advisories; add regression tests for affected behavior.

---

## 5) Practical scanning heuristics (how to “hunt”)

Always try to confirm:

* data origin (untrusted vs trusted)
* sink type (SQL/subprocess/files/template/http/redirect/ws)
* protective controls present (validation, allowlists, middleware, edge controls)
* installed dependency versions vs vulnerable ranges ([advisories.gitlab.com][10])

---

## 6) Sources (accessed 2026-01-27)

Primary framework documentation:

* FastAPI (PyPI metadata, versioning) — `https://pypi.org/project/fastapi/` ([PyPI][1])
* FastAPI docs: Security “First Steps” (Authorization Bearer header conventions) — `https://fastapi.tiangolo.com/tutorial/security/first-steps/` ([FastAPI][11])
* FastAPI reference: Dependencies (`Depends`, `Security`) — `https://fastapi.tiangolo.com/reference/dependencies/` ([FastAPI][7])
* FastAPI reference: APIRouter (router-level dependencies) — `https://fastapi.tiangolo.com/reference/apirouter/` ([FastAPI][28])
* FastAPI docs: WebSockets — `https://fastapi.tiangolo.com/advanced/websockets/` ([FastAPI][27])

ASGI/server stack documentation:

* Starlette (PyPI, general capabilities) — `https://pypi.org/project/starlette/` ([PyPI][5])
* Starlette docs: WebSockets — `https://starlette.dev/websockets/` ([Starlette][3])
* Uvicorn (PyPI metadata) — `https://pypi.org/project/uvicorn/` ([PyPI][4])
* Pydantic docs (v2.12.x) — `https://docs.pydantic.dev/latest/` ([Pydantic][29])

Security standards and cheat sheets:

* OWASP Cheat Sheet Series: Session Management — `https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][8])
* OWASP Cheat Sheet Series: CSRF Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][2])
* OWASP Cheat Sheet Series: XSS Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][16])
* OWASP Cheat Sheet Series: Mass Assignment — `https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][14])
* OWASP API Security Top 10 (2023) — `https://owasp.org/API-Security/editions/2023/en/0x11-t10/` ([OWASP Foundation][13])
* OWASP Cheat Sheet Series: SQL Injection Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][21])
* OWASP Cheat Sheet Series: OS Command Injection Defense — `https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][22])
* OWASP Cheat Sheet Series: SSRF Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][23])
* OWASP Cheat Sheet Series: File Upload — `https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][20])
* OWASP Cheat Sheet Series: Unvalidated Redirects and Forwards — `https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][24])
* OWASP Cheat Sheet Series: HTTP Security Response Headers — `https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][6])
* OWASP Cheat Sheet Series: WebSocket Security — `https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][25])
* OWASP WSTG: Testing for Server-Side Template Injection — `https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection` ([OWASP Foundation][17])
* OWASP WSTG: Testing WebSockets — `https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets` ([OWASP Foundation][26])

Template safety references:

* Jinja: Sandbox — `https://jinja.palletsprojects.com/en/stable/sandbox/` ([jinja.palletsprojects.com][18])

Selected supply-chain/advisory references (Starlette examples):

* CVE-2023-29159 (StaticFiles path traversal; fixed 0.27.0) — `https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2023-29159/` ([advisories.gitlab.com][10])
* CVE-2024-47874 (multipart/form-data DoS; fixed 0.40.0) — `https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2024-47874/` ([advisories.gitlab.com][9])
* CVE-2025-62727 (FileResponse Range header DoS; fixed 0.49.1) — `https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2025-62727/` ([advisories.gitlab.com][19])

[1]: https://pypi.org/project/fastapi/ "https://pypi.org/project/fastapi/"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html"
[3]: https://starlette.dev/websockets/?utm_source=chatgpt.com "Websockets"
[4]: https://pypi.org/project/uvicorn/ "https://pypi.org/project/uvicorn/"
[5]: https://pypi.org/project/starlette/ "https://pypi.org/project/starlette/"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html?utm_source=chatgpt.com "HTTP Security Response Headers Cheat Sheet"
[7]: https://fastapi.tiangolo.com/reference/dependencies/?utm_source=chatgpt.com "Dependencies - Depends() and Security() - FastAPI"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"
[9]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2024-47874/ "Starlette Denial of service (DoS) via multipart/form-data | GitLab Advisory Database"
[10]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2023-29159/ "Starlette has Path Traversal vulnerability in StaticFiles | GitLab Advisory Database"
[11]: https://fastapi.tiangolo.com/tutorial/security/first-steps/?utm_source=chatgpt.com "Security - First Steps - FastAPI"
[12]: https://fastapi.tiangolo.com/tutorial/response-model/ "https://fastapi.tiangolo.com/tutorial/response-model/"
[13]: https://owasp.org/API-Security/editions/2023/en/0x11-t10/ "https://owasp.org/API-Security/editions/2023/en/0x11-t10/"
[14]: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html"
[15]: https://fastapi.tiangolo.com/tutorial/extra-models/ "https://fastapi.tiangolo.com/tutorial/extra-models/"
[16]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
[17]: https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection?utm_source=chatgpt.com "Testing for Server Side Template Injection"
[18]: https://jinja.palletsprojects.com/en/stable/sandbox/?utm_source=chatgpt.com "Sandbox — Jinja Documentation (3.1.x)"
[19]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2025-62727/ "Starlette vulnerable to O(n^2) DoS via Range header merging in ``starlette.responses.FileResponse`` | GitLab Advisory Database"
[20]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html"
[21]: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
[22]: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
[23]: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
[24]: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html?utm_source=chatgpt.com "Unvalidated Redirects and Forwards Cheat Sheet"
[25]: https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html?utm_source=chatgpt.com "WebSocket Security - OWASP Cheat Sheet Series"
[26]: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets?utm_source=chatgpt.com "WSTG - Latest | OWASP Foundation"
[27]: https://fastapi.tiangolo.com/advanced/websockets/?utm_source=chatgpt.com "WebSockets - FastAPI"
[28]: https://fastapi.tiangolo.com/reference/apirouter/?utm_source=chatgpt.com "APIRouter class - FastAPI"
[29]: https://docs.pydantic.dev/latest/ "https://docs.pydantic.dev/latest/"
