# Express (Node.js) Web Security Spec (Express 5.x / 4.19.2+, Node.js LTS)

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session secrets, cookies, tokens).
* MUST NOT “fix” security by disabling protections (e.g., weakening cookie flags, disabling CSRF defenses for cookie-authenticated apps, enabling permissive CORS, trusting proxy headers from open internet, enabling debugging/stack traces in production, disabling TLS without replacement).
* MUST give **evidence-based findings** in audits: cite file paths, code snippets, middleware/config values, runtime assumptions backing each claim.
* MUST treat uncertainty honestly: if protection may live in infrastructure (reverse proxy, gateway, WAF, CDN), report “not visible in app code; verify at runtime/config.”
* MUST prefer vetted libraries and platform controls over “roll your own” crypto/auth/session/CSRF. Express does not validate/handle user input automatically; application must. ([Express][1])

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing new Express code or modifying existing code:

* MUST follow every **MUST** requirement here.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default APIs and proven libraries over custom security code.
* MUST avoid new risky sinks (shell execution, dynamic code evaluation, unsafe redirects, serving user files as HTML, template rendering from untrusted strings, unsafe filesystem paths, SSRF URL fetch endpoints, etc.).

### 1.2 Passive review mode (always on while editing)

Anywhere in an Express repo, even if user did not ask for security scan:

* MUST “notice” spec violations in touched/nearby code.
* SHOULD mention issues as they arise, with brief explanation + safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. Entrypoints (server/app bootstrap), deployment manifests, Dockerfiles, process manager config, CI/CD.
2. Express settings + middleware stack order (helmet, parsers, auth, sessions, CSRF, CORS).
3. Proxy trust (`trust proxy`) and IP/protocol/host handling. ([Express][2])
4. Auth flows, sessions, cookies, password reset links, redirect handling. ([Express][1])
5. State-changing routes + CSRF protections (cookie-authenticated apps). ([OWASP Cheat Sheet Series][3])
6. Template rendering and XSS defenses (HTML generation, CSP, `res.locals`). ([OWASP Cheat Sheet Series][4])
7. File handling (uploads + downloads + static files) and path traversal. ([Express][5])
8. Injection classes (SQL, NoSQL, command execution, unsafe deserialization). ([OWASP Cheat Sheet Series][6])
9. Outbound requests (SSRF) and webhook/callback delivery. ([OWASP Cheat Sheet Series][7])
10. Rate limiting / brute-force defenses / abuse controls. ([Express][1])
11. Dependency hygiene / lockfiles / npm audit / vulnerable Express versions. ([Express][1])

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Common untrusted Express inputs:

* `req.params` (route parameters)
* `req.query` (query string parameters; can be strings/arrays/objects depending on parsing) ([OWASP Cheat Sheet Series][8])
* `req.body` from `express.json()`, `express.urlencoded()`, `express.text()`, `express.raw()` ([Express][5])
* `req.headers` / `req.get(...)`
* `req.cookies` / `req.signedCookies` (if cookie parsing middleware used)
* Upload metadata and filenames (e.g., multer `file.originalname`, `file.mimetype`)
* Data from external systems (webhooks, third-party APIs, message queues)
* Persisted user content (DB rows) originating from users

### 2.2 State-changing request

Request is state-changing if it can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook send), or start privileged actions.

### 2.3 Required audit finding format

For each issue found, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + function/route/middleware name + line(s)
* Evidence: the exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

Minimum baseline targets:

* `helmet()` used and configured (especially CSP where applicable); fingerprinting reduced (disable `x-powered-by`). ([Express][1])
* Custom 404 handler and custom error handler exist; production does not leak internal stack traces. ([Express][1])
* Cookie/session usage deliberate:

  * Default session cookie names not used
  * Cookies use secure attributes (`Secure`, `HttpOnly`, `SameSite`) as appropriate
  * Cookie-backed sessions never store secrets (client can read them)
  * Server-side sessions never use MemoryStore in production. ([Express][1])
* Body parsing has explicit limits (`express.json({ limit })`, `express.urlencoded({ limit, parameterLimit, depth })`). ([Express][5])
* `trust proxy` set explicitly to match proxy topology; not blindly `true`. ([Express][2])
* Login/auth endpoints have brute-force protection and rate limiting. ([Express][1])
* Dependencies regularly audited/updated (`npm audit` + advisory response). ([Express][1])

---

## 4) Rules (generation + audit)

### EXPRESS-INPUT-001: Treat all user input as untrusted and validate it

Severity: High

Required:

* MUST validate and normalize untrusted inputs before security-sensitive logic or dangerous sinks (DB queries, redirects, filesystem, HTML output, shell commands). Type-check and structure-check them before use or forwarding.
* SHOULD prefer allowlists (known-good) over blocklists when feasible.
* MUST reject or safely handle unexpected types/shapes in `req.query`, `req.params`, `req.body`.

Insecure patterns:

* Passing `req.query`, `req.params`, `req.body` straight into database/query builders, redirects, filesystem paths, or templates.
* Assuming `req.query.foo` is always a string (parsing can yield array/object). ([OWASP Cheat Sheet Series][8])

Detection hints:

* Identify “untrusted-to-sink” flows: request → sink (`res.redirect`, SQL execution, `sendFile`, `child_process`, template render, outbound fetch).
* Search for direct `req.query.*`, `req.body.*`, `req.params.*` in sensitive calls.

Fix:

* Add schema validation (e.g., zod/joi/express-validator) at route boundaries.
* Normalize types (e.g., force IDs to integers; reject arrays when scalar expected).

---

### EXPRESS-REDIRECT-001: Prevent open redirects; validate redirect targets

Severity: Medium

Required:

* MUST validate redirect destinations derived from untrusted input (`next`, `return_to`, `url`).
* SHOULD allowlist only same-site relative paths (preferred) or strict domain allowlist.
* MUST fall back to safe default on validation failure.

Insecure patterns:

* `res.redirect(req.query.next)` with no validation.
* `res.redirect(req.body.url)` or `res.location(...)` using untrusted URLs.

Detection hints:

* Search `res.redirect(` and `res.location(`; trace target source.
* Look for query params named `next`, `redirect`, `return`, `url`.

Fix:

* Allow only relative paths (starting with `/`); disallow `//`, backslashes, encoded variants.
* If cross-domain redirects required, allowlist exact hosts and enforce `https`.

Notes:

* Keep Express updated: an open-redirect-related CVE hit some versions; upgrading is part of mitigation. ([NVD][9])

---

### EXPRESS-HEADERS-001: Use Helmet (or equivalent) to set essential security headers

Severity: Medium

Required:

* SHOULD use `helmet()` for common security headers.
* SHOULD configure realistic CSP (avoid `unsafe-inline` where possible) on pages rendering user-influenced content.
* SHOULD set `X-Content-Type-Options: nosniff`, clickjacking defenses (`X-Frame-Options` or CSP `frame-ancestors`), and appropriate referrer policy.

NOTE: CSP's script-src matters most. Other directives are not as important; usually fine to skip for ease of development.

Insecure patterns:

* No security headers in app code and no evidence of them at edge.
* CSP missing on apps showing user content.
* Misconfigured framing headers unintentionally allowing clickjacking.

Detection hints:

* Search `helmet(` usage; check whether CSP is configured or disabled.
* Search `res.setHeader(` / `res.set(` setting security headers.
* If not visible in app code, check nginx/CDN config; otherwise flag “verify at edge.”

Fix:

* Add `helmet()` early in middleware order and configure:

  * CSP (`contentSecurityPolicy`)
  * Frame protections (`frameguard` or CSP `frame-ancestors`)
  * `X-Content-Type-Options` (`noSniff`)

Notes:

* OWASP HTTP Headers guidance helps when tuning policies. ([OWASP Cheat Sheet Series][10])

---

### EXPRESS-FINGERPRINT-001: Reduce fingerprinting by disabling `x-powered-by` and customizing error/404 responses

Severity: Low (defense-in-depth)

Required:

* SHOULD disable `X-Powered-By` via `app.disable('x-powered-by')`.
* SHOULD add custom 404 and error handlers, avoiding distinct default responses and controlling information leakage.

Insecure patterns:

* Default `X-Powered-By: Express` header left enabled.
* Default Express 404/error responses in production with identifiable formatting and/or stack traces.

Detection hints:

* Search `app.disable('x-powered-by')`.
* Check middleware tail for custom 404 (`app.use((req,res)=>...)`) and custom error handler (`app.use((err,req,res,next)=>...)`).
* Check `NODE_ENV` set correctly for production behavior (see EXPRESS-ERROR-001). ([Express][11])

Fix:

* Add:

  * `app.disable('x-powered-by')`
  * Custom 404 handler
  * Custom error handler: log server-side, return generic messages client-side

---

### EXPRESS-COOKIE-001: Cookies must use secure attributes and minimal scope

Severity: Medium

Required:

* MUST set cookie flags appropriately on any authentication/session cookie:

  * `Secure` when HTTPS (production). IMPORTANT NOTE: Set `Secure` only in production with TLS configured; do not set `Secure` in local dev over HTTP. Make it conditional on production mode. Also add a property like `SESSION_COOKIE_SECURE` to disable `Secure` cookies when testing over HTTP.
  * `HttpOnly` for auth/session cookies
  * `SameSite` set deliberately (`Lax` common baseline; `Strict` if compatible; `None` only with `Secure` and justified cross-site need)
* SHOULD avoid broad `domain` (avoid “all subdomains” unless required).
* SHOULD set bounded expiry fitting risk and UX.

Insecure patterns:

* Session/auth cookies without `HttpOnly`.
* Cookies without `Secure` in production HTTPS.
* `SameSite=None` + cookie-authenticated state-changing endpoints without CSRF protections.

Detection hints:

* Search `res.cookie(`, `Set-Cookie`, `cookie: { ... }`, `express-session`, `cookie-session`.
* Verify cookie flags in session middleware configuration.

Fix:

* Set attributes centrally in session/cookie middleware configuration.

Notes:

* Express production guidance lists cookie security options (`secure`, `httpOnly`, etc.). ([Express][1])
* `res.cookie()` sets `Set-Cookie` with options; omitted options follow RFC 6265 defaults. ([Express][5])
* OWASP session management guidance helps choose flags and lifetimes. ([OWASP Cheat Sheet Series][12])

---

### EXPRESS-SESS-001: Do not use the default session cookie name; avoid session fingerprinting

Severity: Low (defense-in-depth)

Required:

* SHOULD override default session cookie name (e.g., do not keep `connect.sid` with `express-session`).
* SHOULD use generic name (e.g., `sessionId`) unless there is a compatibility reason.

Insecure patterns:

* `express-session` with no `name:` configured (default cookie name).
* Multiple apps on same domain accidentally sharing a cookie name.

Detection hints:

* Search `express-session` config blocks; check for `name:`.

Fix:

* Set `name: 'sessionId'` (or similar) in `express-session` options.

---

### EXPRESS-SESS-002: Session storage and lifecycle must be production-safe

Severity: High

Required:

* MUST NOT use `MemoryStore` in production (not designed for production use).
* MUST keep session secrets outside source control and rotate them safely.
* SHOULD regenerate sessions on login / privilege changes to reduce session fixation risk.
* MUST NOT store sensitive secrets in client-readable cookie sessions.

Insecure patterns:

* `app.use(session({ store: new MemoryStore(), ... }))` or missing store (defaults to MemoryStore).
* Hard-coded secrets in repo, e.g. `secret: 'keyboard cat'` / `secret: 's3Cur3'`.
* `cookie-session` storing access tokens, refresh tokens, or PII.

Detection hints:

* Search `express-session`; look for `MemoryStore` usage or missing `store`.
* Search `secret:` in session config; check if hard-coded.
* Look for `req.session = ...` patterns storing sensitive data.

Fix:

* Use production session store (Redis, database-backed, etc.).
* Load secrets from environment/secret manager.
* On login: `req.session.regenerate(...)` or equivalent flow with safe privilege re-binding.

Notes:

* Express notes cookie-backed sessions serialize data into the cookie, visible to client; keep it small and non-secret. ([Express][1])

---

### EXPRESS-CSRF-001: Cookie-authenticated state-changing requests MUST be CSRF-protected

Severity: High

- IMPORTANT NOTE: If cookies are not used for auth (e.g., `Authorization: Bearer ...` headers or other passed token), classic browser CSRF typically does not apply.

Required:

* MUST protect all state-changing endpoints (POST/PUT/PATCH/DELETE) relying on cookies for authentication.
* SHOULD use well-understood CSRF mitigation (token-based is typical baseline).
* MAY add defense-in-depth: Origin/Referer validation, Fetch Metadata enforcement, SameSite cookies, custom header requirements for XHR/fetch—**but do not treat these as a full replacement** unless explicitly designed and justified.
* If form-based CSRF tokens are not practical, MUST at minimum require a custom HTTP header (second strongest method).

Insecure patterns:

* Cookie-authenticated state-changing endpoints with no CSRF protection.
* GET for state-changing actions (amplifies CSRF risk).
* “CSRF protection” that only checks a user-controlled field.

Detection hints:

* Enumerate routes with methods other than GET/HEAD; check whether cookies gate auth.
* Check presence/absence of CSRF middleware and token checks.
* Check JSON APIs too, not only HTML forms.

Fix:

* Add CSRF tokens to cookie-authenticated flows.
* Add Origin/Referer checks where feasible; set SameSite appropriately.

---

### EXPRESS-CORS-001: CORS must be explicit and least-privilege

Severity: Medium (High if misconfigured with credentials)

Required:

* If CORS not needed, MUST keep it disabled.
* If CORS needed:

  * MUST allowlist trusted origins (do not reflect arbitrary `Origin` without validation).
  * MUST NOT combine broad origins with credentialed cookies (`Access-Control-Allow-Credentials: true`).
  * SHOULD restrict methods, headers, and exposed headers to what’s required.

Insecure patterns:

* `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`.
* Reflecting `Origin` on all requests without allowlist validation.
* Permissive CORS middleware applied globally when only a subset needs cross-origin access.

Detection hints:

* Search `cors(`, `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`.
* Check whether cross-origin endpoints use cookie auth.

Fix:

* Use strict origin allowlist; allow credentialed requests only for intended origins.
* Consider CORS config per route group rather than global.

---

### EXPRESS-PROXY-001: Reverse proxy trust (`trust proxy`) must be configured correctly

Severity: Medium (High if using IP based authentication)

Required:

* If behind reverse proxy/LB, MUST configure `app.set('trust proxy', ...)` to match real proxy chain.
* MUST NOT blindly set `trust proxy = true` unless you fully control proxy behavior and header rewriting.
* MUST ensure last trusted proxy overwrites/removes `X-Forwarded-For`, `X-Forwarded-Host`, `X-Forwarded-Proto` so clients cannot spoof them.

Insecure patterns:

* `app.set('trust proxy', true)` in app directly exposed to internet or behind unknown proxies.
* `req.ip`, `req.protocol`, `req.hostname` used for security decisions without correct proxy trust configuration.
* Rate limiting keyed by `req.ip` with spoofable forwarded headers.

Detection hints:

* Search `app.set('trust proxy'`.
* Check infra docs (nginx/LB) for header rewriting behavior.
* Find security logic using `req.ip`, `req.ips`, `req.protocol`, `req.hostname`.

Fix:

* Set `trust proxy` to hop count, explicit IP/subnet list, or custom function matching your network.
* Ensure proxies overwrite forwarded headers.

Notes:

* Express warns: with `trust proxy` `true`, client IP comes from `X-Forwarded-For`; if proxies don’t overwrite forwarded headers, client can supply any value. Enabling trust proxy also makes `req.hostname` and `req.protocol` derive from forwarded headers. ([Express][2])

---

### EXPRESS-BODY-001: Request body size and parsing limits MUST be set appropriately

Severity: Low

Required:

* SHOULD set explicit body size limits for:

  * `express.json({ limit })`
  * `express.urlencoded({ limit, parameterLimit, depth })`
* SHOULD enable only needed parsers; do not parse large bodies by default on all routes.
* SHOULD enforce extra limits at reverse proxy / gateway level.

Insecure patterns:

* No explicit body limits (arbitrarily large JSON/urlencoded accepted).
* Global parsers on all routes when only some need bodies.
* `parameterLimit` very high without justification (DoS potential).

Detection hints:

* Search `express.json(`; confirm `limit` is set (or consciously accepted).
* Search `express.urlencoded(`; inspect `limit`, `parameterLimit`, `depth`.
* Review upload/webhook endpoints for special parsing needs.

Fix:

* Configure parsers with conservative defaults; override per route group when needed.

Notes:

* Express documents `express.json` options (including `limit`, default 100kb) and notes `req.body` is untrusted and should be validated. ([Express][5])

---

### EXPRESS-INPUT-002: Prevent HTTP Parameter Pollution and type confusion in `req.query`

Severity: Medium

Required:

* MUST treat `req.query` values as possibly multi-valued (array/object), depending on query parsing.
* SHOULD reject ambiguous multi-valued parameters for security-sensitive fields (e.g., `role`, `isAdmin`, `redirect`, `amount`, `userId`).
* SHOULD consider explicit parsing or dedicated middleware if parameter pollution is a concern.

Insecure patterns:

* `if (req.query.admin) { ... }` without type checks (arrays/objects may coerce truthy).
* Passing `req.query` directly into ORM/NoSQL query objects.

Detection hints:

* Search security-sensitive comparisons on `req.query.*` without type enforcement.
* Look for code assuming query params are strings.

Fix:

* Validate shape: enforce string-only for certain params; reject arrays/objects.
* Normalize query parsing settings (simple vs extended) where applicable and documented.

---

### EXPRESS-XSS-001: Prevent reflected/stored XSS in HTML responses and templating

Severity: High

Required:

* MUST escape untrusted content in HTML output (templates should auto-escape by default; do not bypass).
* MUST NOT inject untrusted strings into HTML without escaping/sanitization.
* SHOULD set CSP (via Helmet) for apps rendering user-controlled content.
* SHOULD keep user-controlled input meant for templates out of `res.locals` unless validated/escaped.

Insecure patterns:

* `res.send("<div>" + req.query.q + "</div>")`
* Passing untrusted HTML through “safe” template flags/filters.
* Writing untrusted strings into `res.locals`, then rendering without escaping.

Detection hints:

* Search `res.send(` with strings containing user input.
* Search template “safe” flags (engine-specific); trace data origin.
* Search `res.locals` assignments; check whether they may contain untrusted data.

Fix:

* Use template engine with autoescaping; pass only validated data.
* For rich text that must contain HTML, use trusted sanitizer with allowlist policy.
* Add CSP with realistic directives.

Notes:

* Express API docs warn `res.locals` “should not contain user-controlled input”; it often exposes things like CSRF tokens to templates. ([Express][5])
* OWASP XSS prevention guidance gives standard output-encoding and policy recommendations. ([OWASP Cheat Sheet Series][4])

---

### EXPRESS-TEMPLATE-001: Never render untrusted templates or template paths (SSTI / LFI risk)

Severity: Critical (if you can prove template strings/paths are user/attacker-controlled)

Required:

* MUST NOT render templates whose contents or path/name are influenced by untrusted input.
* MUST NOT load templates from user-controlled filesystem locations.
* SHOULD treat “email template editors”, “theme engines”, and “CMS-like template storage” as high-risk designs needing sandboxing and isolation.

Insecure patterns:

* `res.render(req.query.view, data)` where `view` is not allowlisted.
* Rendering template from string containing user input (engine-specific).
* Loading templates from uploads directories.

Detection hints:

* Search `res.render(` where first argument derives from request/DB without allowlist.
* Search template compilation APIs (engine-specific) fed by user content.

Fix:

* Use allowlisted template names and fixed templates directory.
* If user-defined templates required, sandbox strictly and isolate execution.

Notes:

* Express template behavior depends on chosen engine; assume unsafe if user input influences template selection or source.

---

### EXPRESS-FILES-001: Prevent path traversal and unsafe file serving (sendFile/download)

Severity: High

Required:

* MUST NOT pass user-controlled filesystem paths directly to `res.sendFile()` / `res.download()` / filesystem APIs.
* SHOULD use `res.sendFile` with fixed `root` and strict options (e.g., deny dotfiles) when serving user-selected files from a directory.
* MUST enforce authorization checks before serving user-specific files.

Insecure patterns:

* `res.sendFile(req.query.path)` or `res.download(req.params.file)` with no root restriction.
* File-serving routes accepting `..` segments, encoded traversal, or absolute paths.

Detection hints:

* Search `res.sendFile(`; trace `path` argument origin.
* Search `res.download(`; trace `path` argument origin.
* Look for `fs.readFile`/`createReadStream` on request-derived paths.

Fix:

* Use identifier-to-path mapping stored server-side (DB), not raw client paths.
* Use `root: <trusted_base_dir>` and `dotfiles: 'deny'` where appropriate; strictly validate filename component.

Notes:

* `res.download` sends file as attachment; you still must control/validate underlying `path`. ([Express][5])

---

### EXPRESS-STATIC-001: Harden `express.static` / serve-static and never serve untrusted uploads as active content

Severity: Medium (if serving untrusted user files without robust file-extension limits)

Required:

* MUST NOT serve user uploads from public static directory as active content (especially HTML/JS/SVG) unless explicitly intended and sandboxed. Content confirmed inactive (png, jpg, other images etc) may be safe; ideally allowlist image file extensions before serving.
* SHOULD configure static serving to:

  * deny/ignore dotfiles
  * avoid unintended directory indexes if not needed
  * apply appropriate cache controls for immutable assets

Insecure patterns:

* `app.use(express.static('uploads'))` where users can upload arbitrary files.
* Serving uploaded HTML or SVG inline from app's own origin.

Detection hints:

* Search `express.static(`; identify served directories.
* Compare served directories with upload storage locations.
* Check for `dotfiles` and `index` options in static middleware.

Fix:

* Store uploads outside any static web root; serve via controlled routes setting safe `Content-Type` and `Content-Disposition: attachment` when appropriate.
* Configure `express.static(root, { dotfiles: 'deny'|'ignore', index: false (if desired) })`.

---

### EXPRESS-UPLOAD-001: File uploads must be validated, stored safely, and served safely

Severity: Low - Medium

Required:

* SHOULD enforce upload size limits (app + edge).
* MUST validate file type using allowlists and content checks (not only filename extension).
* MUST store uploads outside executable/static roots when possible.
* SHOULD generate server-side filenames (random IDs); do not trust original names.
* MUST serve potentially active formats safely (download attachment) unless explicitly intended.

Insecure patterns:

* Accepting arbitrary file types and serving them back inline.
* Using `file.originalname` as storage path.
* Missing size/type validation.

Detection hints:

* Find multer/busboy/formidable usage; check for `limits`.
* Check where uploaded files are written and how they are served.
* Check whether uploads land under `public/` or any `express.static` root.

Fix:

* Add allowlist validation + safe storage + safe serving, per OWASP upload guidance. ([OWASP Cheat Sheet Series][13])

---

### EXPRESS-INJECT-001: Prevent SQL injection (use parameterized queries / ORM)

Severity: High

Required:

* MUST use parameterized queries or ORM/query builder that parameterizes under the hood.
* MUST NOT build SQL via string concatenation/template literals with untrusted input.

Insecure patterns:

* ``db.query(`SELECT * FROM users WHERE id = ${req.query.id}`)``
* `"SELECT ... WHERE name = '" + req.body.name + "'"`

Detection hints:

* Grep for `SELECT`, `INSERT`, `UPDATE`, `DELETE` strings in JS/TS.
* Trace untrusted input into `.query(...)`, `.execute(...)`, or raw SQL APIs.

Fix:

* Replace with parameterized queries (placeholders) or ORM query APIs.
* Validate types (e.g., integer IDs) before querying.

---

### EXPRESS-INJECT-002: Prevent NoSQL injection / operator injection (Mongo-style)

Severity: High (app-dependent)

Required:

* MUST validate types and schemas for any query object built from untrusted input.
* MUST prevent operator injection (e.g., `$ne`, `$gt`, `$where`) if user input is merged into query objects.
* SHOULD consider defensive libraries/middleware when appropriate.

Insecure patterns:

* `collection.find(req.body)` with attacker-controlled body.
* Merging `req.query`/`req.body` into Mongo queries without schema validation.

Detection hints:

* Search `find(`, `findOne(`, `aggregate(` calls with request-derived arguments.
* Check for patterns like `{ ...req.query }` or `Object.assign(query, req.body)`.

Fix:

* Validate schema at boundary; build query objects explicitly from validated fields only.

Notes:

* OWASP Node.js cheat sheet covers input validation and names Node ecosystem modules commonly used for NoSQL sanitization. ([OWASP Cheat Sheet Series][8])

---

### EXPRESS-CMD-001: Prevent OS command injection (child_process)

Severity: Critical to High (depends on exposure); prove it is user/attacker controlled

Required:

* MUST avoid executing shell commands with untrusted input.
* If subprocess necessary:

  * MUST avoid `exec()` / `execSync()` with attacker-influenced strings
  * MUST NOT use `shell: true` with attacker-influenced data
  * SHOULD use `spawn()` with argument array and strict allowlists. Hardcode or allow-list the executable; do not use a user-supplied command name.
  * SHOULD place user-controlled values after `--` when subcommand supports it, to avoid flag injection

Insecure patterns:

* `exec(req.query.cmd)`
* `exec(`convert ${userPath} ...`)`
* `spawn('sh', ['-c', userString])`
* `spawn(userString, ['foo'])`

Detection hints:

* Search `child_process`, `exec(`, `execSync(`, `spawn(`, `fork(`.
* Trace request/DB data into command construction.

Fix:

* If possible, implement in javascript or use a library instead of subprocess.
* If unavoidable, hard-code command and strictly allowlist parameters.

---

### EXPRESS-SSRF-001: Prevent server-side request forgery (SSRF) in outbound HTTP

Severity: Medium (High in cloud/LAN deployments)

NOTE: Mostly applies only to apps deployed in cloud/LAN or sharing a box with other http services. Some features need it unavoidably (webhooks).

Required:

* MUST treat outbound requests to user-provided URLs as high risk if other private http endpoints are reachable.
* SHOULD validate and restrict destinations (allowlist hosts/domains) for any user-influenced URL fetch.
* SHOULD block access to:

  * localhost / private IP ranges / link-local
  * cloud metadata endpoints
* MUST allow only `http`/`https` for URL fetch features (to avoid schemas such as `file:`,`javascript:`)
* SHOULD set timeouts and restrict redirects.

Insecure patterns:

* `fetch(req.query.url)`
* “URL preview” / “import from URL” endpoints accepting arbitrary URLs.

Detection hints:

* Search `fetch(`, `axios(`, `got(`, `request(`, `node-fetch` usage where URL originates from users/DB.
* Review webhook testers, previewers, image fetchers.

Fix:

* Enforce scheme allowlist, host allowlist, DNS/IP resolution checks, timeouts, and redirect policy.
* Consider network egress controls at infrastructure level.

Notes:

* OWASP SSRF prevention guidance covers standard controls and common pitfalls. ([OWASP Cheat Sheet Series][7])

---

### EXPRESS-ERROR-001: Error handling MUST not leak sensitive details in production

Severity: Low

Required:

* SHOULD define centralized error handler (`app.use((err, req, res, next) => ...)`) at end of middleware.
* MUST avoid returning stack traces, internal error messages, or secrets to clients in production.
* SHOULD log errors server-side with appropriate redaction.
* SHOULD run app with production settings so default behavior doesn’t leak details.
* MUST avoid logging or returning sensitive information (secrets, env vars, sessions, cookies) in production error messages.

Insecure patterns:

* Returning `err.stack` to clients.
* Using dev-only error middleware in production.
* `NODE_ENV` left as development, causing verbose error responses.

Detection hints:

* Verify final error-handling middleware exists.
* Search `res.status(500).send(err)` or similar.
* Check production environment variables and startup scripts.

Fix:

* Add production-safe error handler returning generic messages and logging details internally.
* Configure environment for production behavior.

Notes:

* Express error handling docs describe default error handler and how production mode changes what is exposed. ([Express][11])

---

### EXPRESS-AUTH-001: Prevent brute-force attacks against authorization endpoints

Severity: Medium

NOTE: Highly application specific; hard to fix without extra complex configuration. Prefer informing user; if they ask for implementation help, walk them through possible solutions.

Required:

* SHOULD protect login/auth endpoints against brute forcing.
* SHOULD rate-limit by:

  1. consecutive failed attempts per username+IP
  2. failed attempts per IP over a time window

Insecure patterns:

* Unlimited login attempts.

Detection hints:

* Find all auth endpoints; check for rate limiting/throttling.
* Search `rate-limiter-flexible`, `express-rate-limit`, or gateway policies.

Fix:

* Add rate-limiting/throttling (app or edge). Express docs point to `rate-limiter-flexible` for this. ([Express][1])

---

### EXPRESS-DEPS-001: Dependency and patch hygiene (Express + Node + critical middleware)

Severity: Medium / Low

NOTE: `npm audit` often reports many insignificant "vulnerabilities" that do not matter. Focus only on Express or other extremely critical packages; ignore dev tools, bundlers, etc.

Do not upgrade packages without user consent; upgrades may break existing code unexpectedly. Report outdated packages instead.

Required:

* MUST keep Express on maintained version line (avoid EOL major versions).
* MAY use `npm audit` in CI and during maintenance work.
* SHOULD pin dependencies via lockfiles; review major updates carefully.

Insecure patterns:

* Running EOL Express versions (e.g., very old major lines).
* Ignoring `npm audit` findings without triage.
* Unpinned dependency ranges auto-upgrading into insecure versions.

Detection hints:

* Check `package.json` and lockfiles for `express` and other critical middleware versions.
* Inspect CI pipelines for `npm audit`/SCA steps.

Fix:

* Upgrade to latest stable Express and apply patches.
* Add automated dependency scanning and upgrade process.

Notes:

* Track security issues affecting Express versions (including known open-redirect-related CVEs). ([NVD][9])

---

### EXPRESS-DOS-001: Configure DoS protections (timeouts, limits, reverse proxy)

Severity: Low

NOTE: App context may not show whether app runs behind reverse proxy. May inform user or recommend one, but do not configure one unless user initiates it. Highly deployment dependent.

Required:

* SHOULD use reverse proxy for caching, load balancing, and filtering controls when feasible.
* MAY configure server/proxy timeouts and connection limits against Slowloris and similar DoS patterns.
* MUST handle server/socket errors so malformed connections do not crash the process. (Express should handle exceptions, but edge cases exist)

Insecure patterns:

* No reverse proxy in front of public Node server, defaults everywhere.
* Missing error handlers on server/socket objects.
* Extremely permissive timeouts and unlimited body sizes.

Detection hints:

* Inspect server creation (`http.createServer`, `https.createServer`); check whether timeouts are set.
* Check proxy/gateway config for timeouts and max body size.

Fix:

* Explain how to configure reverse proxy and timeouts, set request size limits
* add robust error handling middleware

Notes:

* Node security guidance for HTTP DoS covers reverse proxies and correct server timeout configuration. ([Node.js][15])

---

### EXPRESS-NODE-INSPECT-001: Do not expose the Node inspector in production

Severity: Critical

NOTE: Confirm detection is in production path, not only local debugging.

Required:

* MUST NOT run Node with `--inspect` (especially bound to non-loopback) in production.
* MUST ensure `NODE_OPTIONS` or startup scripts do not enable inspector in prod.
* SHOULD firewall/debug locally only.

Insecure patterns:

* `node --inspect=0.0.0.0:9229 app.js` in production.
* Container/PM2/systemd configs enabling inspector.

Detection hints:

* Search `--inspect` in Dockerfiles, Procfiles, systemd units, PM2 configs, npm scripts.
* Check `NODE_OPTIONS`.

Fix:

* Remove inspector flags from production start commands; restrict to local dev.

Notes:

* Node security guidance covers inspector exposure risks (e.g., DNS rebinding); recommends not running inspector in production. ([Node.js][15])

---

### EXPRESS-NODE-HTTP-001: Do not enable insecure HTTP parsing in production

Severity: High

NOTE: Confirm detection is in production path, not only local dev.

Required:

* MUST NOT use Node’s `insecureHTTPParser` in production.
* MAY suggest front-end proxies normalize ambiguous requests to reduce request smuggling risk.

Insecure patterns:

* HTTP server created with `{ insecureHTTPParser: true }`.

Detection hints:

* Search `insecureHTTPParser` in server creation code.

Fix:

* Remove insecure parsing; rely on spec-compliant parsing and normalize at edge.

---

## 5) Practical scanning heuristics (how to “hunt”)

High-signal patterns when actively scanning an Express repo:

* TLS / transport:

  * `app.listen(80` without reverse proxy mention; missing `helmet`; cookies missing `secure` ([Express][1]) (NOTE: applies only to web-facing applications; internal apps likely won't have TLS)

Always try to confirm:

* data origin (untrusted vs trusted)
* sink type (HTML/template, SQL/NoSQL, subprocess, filesystem, redirect, outbound HTTP)
* protective controls present (validation, allowlists, middleware, proxy config, header policies)
* whether protections sit at edge or in app code

---

## 6) Sources (accessed 2026-01-27)

Primary Express documentation:

* Express: Production Best Practices — Security: `https://expressjs.com/en/advanced/best-practice-security.html` ([Express][1])
* Express: Behind Proxies (`trust proxy`): `https://expressjs.com/en/guide/behind-proxies.html` ([Express][2])
* Express 5.x API Reference (parsers, static, sendFile, redirect, cookies): `https://expressjs.com/en/5x/api.html` ([Express][5])
* Express: Error Handling: `https://expressjs.com/en/guide/error-handling.html` ([Express][11])

Session middleware documentation:

* express-session docs (cookie flags, secret rotation, fixation mitigation, MemoryStore warning): `https://expressjs.com/en/resources/middleware/session.html` ([Express][1])

Node.js and npm official references:

* Node.js — Security Best Practices (DoS, proxy guidance, inspector risks, request smuggling notes): `https://nodejs.org/en/learn/getting-started/security-best-practices` ([Node.js][15])
* npm Docs — `npm audit`: `https://docs.npmjs.com/cli/v9/commands/npm-audit/` ([npm Docs][16])

OWASP Cheat Sheet Series:

* Session Management: `https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][12])
* CSRF Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][3])
* XSS Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][4])
* Input Validation: `https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][17])
* SQL Injection Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][6])
* OS Command Injection Defense: `https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][14])
* SSRF Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][7])
* File Upload: `https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][13])
* Unvalidated Redirects: `https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][18])
* HTTP Headers: `https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][10])

Versioning / advisories:

* Express package version (npm): `https://www.npmjs.com/package/express`
* Express open redirect advisory (CVE): `https://nvd.nist.gov/vuln/detail/CVE-2024-29041` ([NVD][9])

[1]: https://expressjs.com/en/advanced/best-practice-security.html "Security Best Practices for Express in Production"
[2]: https://expressjs.com/en/guide/behind-proxies.html "Express behind proxies"
[3]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "Cross-Site Request Forgery Prevention - OWASP Cheat Sheet Series"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "Cross Site Scripting Prevention - OWASP Cheat Sheet Series"
[5]: https://expressjs.com/en/5x/api.html "Express 5.x - API Reference"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html "SQL Injection Prevention - OWASP Cheat Sheet Series"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html "Server Side Request Forgery Prevention - OWASP Cheat Sheet Series"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html "Nodejs Security - OWASP Cheat Sheet Series"
[9]: https://nvd.nist.gov/vuln/detail/cve-2024-29041?utm_source=chatgpt.com "CVE-2024-29041 Detail - NVD"
[10]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html "HTTP Headers - OWASP Cheat Sheet Series"
[11]: https://expressjs.com/en/guide/error-handling.html "Express error handling"
[12]: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html "Session Management - OWASP Cheat Sheet Series"
[13]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "File Upload - OWASP Cheat Sheet Series"
[14]: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html "OS Command Injection Defense - OWASP Cheat Sheet Series"
[15]: https://nodejs.org/en/learn/getting-started/security-best-practices "Node.js — Security Best Practices"
[16]: https://docs.npmjs.com/cli/v9/commands/npm-audit/ "npm-audit | npm Docs"
[17]: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html "Input Validation - OWASP Cheat Sheet Series"
[18]: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html "Unvalidated Redirects and Forwards - OWASP Cheat Sheet Series"
