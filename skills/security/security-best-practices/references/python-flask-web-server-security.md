# Flask (Python) Web Security Spec (Flask 3.1.x, Python 3.x)

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

- MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session cookies, SECRET_KEY).
- MUST NOT “fix” security by disabling protections (e.g., turning off CSRF, relaxing CORS, disabling escaping or auth checks).
- MUST give **evidence-based findings** in audits: cite file paths, code snippets, config values backing each claim.
- MUST be honest about uncertainty: if protection may live in infrastructure (reverse proxy, WAF, CDN), report “not visible in app code; verify at runtime/config”.

## 1) Operating modes

### 1.1 Generation mode (default)
When writing or modifying Flask code:
- MUST follow every **MUST** in this spec.
- SHOULD follow every **SHOULD** unless user explicitly says otherwise.
- MUST prefer safe-by-default APIs and proven libraries over custom security code.
- MUST avoid new risky sinks (template rendering from strings, shell execution, dynamic imports, unsafe redirects, serving user files as HTML, etc.).

### 1.2 Passive review mode (always on while editing)
Anywhere in a Flask repo (even without security scan request):
- MUST “notice” spec violations in touched/nearby code.
- SHOULD flag issues as they come up, with brief explanation + safe fix.

### 1.3 Active audit mode (explicit scan request)
When user asks to “scan”, “audit”, or “hunt for vulns”:
- MUST systematically search codebase for spec violations.
- MUST report findings in structured format (see §2.3).

Recommended audit order:
1) App entrypoints / deployment scripts / Dockerfiles / Procfiles.
2) Flask config and environment handling.
3) Auth + sessions + cookies.
4) CSRF protections and state-changing routes.
5) Template rendering and XSS/SSTI.
6) File handling (uploads + downloads) and path traversal.
7) Injection classes (SQL, command execution, unsafe deserialization).
8) Outbound requests (SSRF).
9) Redirect handling (open redirects).
10) CORS and security headers.

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)
Examples:
- `request.args`, `request.form`, `request.values`
- `request.get_json()`, `request.json`, `request.data`
- `request.headers`, `request.cookies`
- URL path parameters (e.g., `/user/<id>`)
- Data from external systems (webhooks, third-party APIs, message queues)
- Persisted user-originated content (DB rows)

### 2.2 State-changing request
Can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook send), or start privileged actions.

### 2.3 Required audit finding format
Per issue, output:

- Rule ID:
- Severity: Critical / High / Medium / Low
- Location: file path + function/route name + line(s)
- Evidence: the exact code/config snippet
- Impact: what could go wrong, who can exploit it
- Fix: safe change (prefer minimal diff)
- Mitigation: defense-in-depth if immediate fix is hard
- False positive notes: what to verify if uncertain

## 3) Secure baseline: minimum production configuration (MUST in production)

### 3.1 App initialization pattern (SHOULD)
SHOULD use app factory and environment-based config so production config is not hard-coded.
- Load config from environment / secret store.
- Fail closed if critical settings missing in production.

Key baseline config targets:
- `SECRET_KEY` set and not committed
- `SESSION_COOKIE_SECURE=True` (when HTTPS; see FLASK-SESS-001 IMPORTANT NOTE)
- `SESSION_COOKIE_HTTPONLY=True`
- `SESSION_COOKIE_SAMESITE='Lax'` (or `'Strict'` if compatible)
- `TRUSTED_HOSTS` set in production
- Security headers set (CSP, etc.) in app or at edge

## 4) Rules (generation + audit)

### FLASK-DEPLOY-001: Do not use Flask’s development server in production
Severity: High (if production)

Required:
- MUST NOT use built-in development server as production server.
- MUST run behind production-grade WSGI server or managed platform (such as gunicorn)

Insecure patterns:
- `app.run(...)` in production entrypoint.
- Deployment docs/scripts using `flask run` in production.

Detection hints:
- Grep `app.run(`, `flask run`, `--debug`, `FLASK_DEBUG`, `FLASK_ENV=development`.
- Check Docker CMD/ENTRYPOINT, Procfile, systemd units, shell scripts.

Fix:
- Use production WSGI server (keep Flask as app object).
- Use dev server only for local development.

Note:
- Fine in dev mode or local testing. Only flag when clearly the production entrypoint.

---

### FLASK-DEPLOY-002: Debug mode MUST be disabled in production
Severity: Critical

Required:
- MUST NOT enable debug mode in production.
- MUST treat exposed interactive debugger as equal to remote code execution.

Insecure patterns:
- `app.run(debug=True)`
- `flask run --debug` in production.
- `DEBUG=True` via env/config in production.

Detection hints:
- Grep `debug=True`, `FLASK_DEBUG=1`, `DEBUG = True`, `app.debug = True`.
- Look for `TRAP_HTTP_EXCEPTIONS`/debugger settings enabled outside test contexts.

Fix:
- Enable debug only in local dev/test.
- Prefer environment-based toggles and safe defaults.

Note:
- Fine in dev mode or local testing. Only flag when clearly the production entrypoint.

---

### FLASK-CONFIG-001: SECRET_KEY must be strong, secret, and rotated safely
Severity: High (Critical if missing in production with sessions or signing)

Required:
- MUST set strong random `SECRET_KEY` in production.
- MUST keep `SECRET_KEY` out of source control and logs.
- MAY rotate keys periodically; MAY use `SECRET_KEY_FALLBACKS` to rotate without instantly invalidating existing sessions, then drop old keys after rotation window. Likely unneeded for small apps; good practice for large ones. Complicates deployment, so suggest it rather than implement it by default.

Insecure patterns:
- Missing `SECRET_KEY` in production.
- Hard-coded `SECRET_KEY` in repo (including test keys accidentally used in prod).
- Logging or printing `SECRET_KEY`.

Detection hints:
- Grep `SECRET_KEY =`, `app.secret_key =`, `SECRET_KEY_FALLBACKS =`.
- Check for `.env` files committed to repo.
- Check config modules for constants.

Fix:
- Load from secret manager or environment variable.
- Add rotation process:
  - Set new `SECRET_KEY`
  - Keep old key(s) temporarily in `SECRET_KEY_FALLBACKS`
  - Remove old key(s) after safe window.

Notes:
- If app uses Flask sessions (cookie-based by default), `SECRET_KEY` is directly security-critical.

---

### FLASK-SESS-001: Session cookies must use secure attributes in production
Severity: Medium

Required (production, HTTPS):
- MUST set `SESSION_COOKIE_SECURE=True` (cookies only over HTTPS). IMPORTANT NOTE: Set `Secure` only in production with TLS configured; do not set `Secure` on cookies in local dev over HTTP. Make it conditional on production mode, with a property like `SESSION_COOKIE_SECURE` to disable `Secure` cookies when testing over HTTP.
- MUST ensure `SESSION_COOKIE_HTTPONLY=True` (no JS access).
- SHOULD set `SESSION_COOKIE_SAMESITE='Lax'` (recommended) or `'Strict'` if UX allows.
- SHOULD keep `SESSION_COOKIE_DOMAIN=None` unless subdomain-wide cookies explicitly needed.
- For embedded/iframe third-party use, MAY use `SESSION_COOKIE_PARTITIONED=True` (requires HTTPS).

Insecure patterns:
- `SESSION_COOKIE_SECURE=False` in production.
- `SESSION_COOKIE_HTTPONLY=False`.
- `SESSION_COOKIE_SAMESITE=None` with cookie-authenticated state-changing endpoints (higher CSRF risk).

Detection hints:
- Inspect `app.config.update(...)` blocks and config classes.
- Check `set_cookie(..., secure=..., httponly=..., samesite=...)` on non-session cookies too.

Fix:
- Set these explicitly in production config.

Notes:
- SameSite is defense-in-depth, not full replacement for CSRF tokens.

---

### FLASK-SESS-002: Sessions must be bounded and resistant to fixation/replay
Severity: Medium

Required:
- SHOULD bound session lifetime to suit app.
- SHOULD set `session.permanent = True` only for intended persistent sessions, with justified `PERMANENT_SESSION_LIFETIME`.
- SHOULD clear session on login and privilege changes (reduces session fixation risk).
- MUST NOT store sensitive secrets in default Flask session cookie. It is signed, not encrypted.

Insecure patterns:
- Extremely long or unlimited lifetimes for privileged sessions.
- No session clearing on login.
- Secrets (passwords, access tokens, PII) directly in `session[...]` with default cookie sessions.

Detection hints:
- Grep `PERMANENT_SESSION_LIFETIME`, `session.permanent`, `session[...] =`.
- Check for server-side session storage; if absent, assume default cookie sessions.

Fix:
- Clear/rotate session on login.
- Keep sensitive data server-side; only identifiers in session cookie.

---

### FLASK-CSRF-001: State-changing requests using cookie auth MUST be CSRF-protected
Severity: High

- IMPORTANT NOTE: If cookies are not used for auth (ie auth via Authentication header or other passed token), no CSRF risk.

Required:
- MUST protect all state-changing endpoints (POST/PUT/PATCH/DELETE) relying on cookie auth.
- MAY use well-tested CSRF library/integration (form framework or middleware) over rolling your own.
- MAY add defenses (Origin/Referer checking, SameSite cookies, Fetch Metadata headers, custom headers for AJAX/API); tokens stay primary defense for cookie-authenticated apps.
If tokens are impractical, or for small apps:
* MUST at minimum require a custom header and set session cookie SESSION_COOKIE_SAMESITE=lax. Strongest method short of form token; may be much easier to implement.

Insecure patterns:
- Cookie-authenticated state-changing endpoints without CSRF protection.
- GET for state-changing actions (amplifies CSRF risk).

Detection hints:
- Enumerate non-GET routes; identify auth mechanism.
- Look for CSRF integrations (e.g., Flask-WTF, global CSRF middleware). If absent, treat as suspicious.
- Check JSON API endpoints too, not only HTML forms.

Fix:
- If app is pure API using Authorization headers (bearer tokens) instead of cookies, document that choice and ensure cookies aren’t used for auth.

Notes:
- XSS can defeat CSRF protections; CSRF defenses do not replace XSS prevention.

---

### FLASK-XSS-001: Prevent reflected/stored XSS in templates and HTML generation
Severity: High

Required:
- MUST rely on Jinja auto-escaping for HTML templates.
- MUST NOT mark untrusted content safe:
  - Avoid `Markup(...)` on user data.
  - Avoid Jinja `|safe` on user-controlled content.
- MUST quote HTML attributes containing Jinja expressions (`value="{{ x }}"` not `value={{ x }}`).
- MUST NOT serve uploaded HTML as active HTML; serve as download (`Content-Disposition: attachment`) or convert to safe format. Note: Only relevant if document content (html, js, css, etc.) can be uploaded. Image-only uploads are no concern.
- SHOULD deploy Content Security Policy (CSP) to mitigate XSS classes (including `javascript:` in `href`).

Insecure patterns:
- `Markup(request.args.get(...))`
- Template filters: `{{ user_html|safe }}`
- Unquoted attributes in templates
- Serving user-uploaded content directly with `text/html` or inline rendering

Detection hints:
- Grep `Markup(` and trace data origin.
- Grep templates for `|safe`, `|tojson` misuse, unquoted attributes.
- Review file-serving routes that may return user uploads without `as_attachment=True` (only if document content can be uploaded; image-only is no concern).

Fix:
- Remove unsafe marking; sanitize only when strictly necessary, with trusted HTML sanitizer.
- Add CSP; reduce inline scripts.

---

### FLASK-SSTI-001: Never render untrusted templates (Server-Side Template Injection)
Severity: Critical

Required:
- MUST NOT render templates containing user-controlled template syntax.
- MUST treat `render_template_string` and `Environment.from_string(...).render(...)` as dangerous when untrusted input influences template string.
- MUST NOT use `.format()` on user controlled strings
- If untrusted templates absolutely required, treat as special high-risk design:
  - MUST use sandboxed templating with restricted capabilities.
  - MUST keep Jinja updated and assume sandbox escapes possible; isolate further.

Insecure patterns:
- `render_template_string(request.args["tmpl"], ...)`
- Storing user templates in DB and rendering with normal Jinja environment.
- `request.args["tmpl"].format(...)`

Detection hints:
- Grep `render_template_string`, `from_string`, `.render(` with dynamic strings.
- Trace template string origin (DB, request, uploads, admin panels).

Fix:
- Replace with safe templating that does not evaluate code (e.g., string.Template, str.replace).
- If templates must be user-defined, use sandbox + strict allowlists + heavy isolation.

---

### FLASK-HEADERS-001: Set essential security headers (in app or at the edge)
Severity: Medium

Required (typical web app):
- SHOULD set:
  - CSP (`Content-Security-Policy`)
  - `X-Content-Type-Options: nosniff`
  - Clickjacking protection (`X-Frame-Options: SAMEORIGIN` and/or CSP `frame-ancestors`) (if user wants to iframe their site elsewhere, work with them to allow it safely)
- SHOULD consider extra hardening headers per app (Referrer-Policy, Permissions-Policy).
- MUST set cookies with secure attributes (see FLASK-SESS-001).

NOTE: Headers may be set via proxy or other cloud provider; check for evidence of that.

Insecure patterns:
- No security headers anywhere (app or edge).
- No CSP on apps displaying untrusted content.

Detection hints:
- Grep `after_request` hooks, Flask-Talisman usage, reverse proxy config.
- If not visible in app code, flag “verify at edge”.

Fix:
- Set headers centrally (middleware / after_request) or via reverse proxy/CDN.
- Keep CSP realistic and compatible; avoid `unsafe-inline` where possible.

---

### FLASK-LIMITS-001: Request size and form parsing limits MUST be set appropriately
Severity: Low (Medium if file uploads / large bodies are possible)

Required:
- SHOULD set and justify:
  - `MAX_CONTENT_LENGTH` (global maximum request bytes)
  - `MAX_FORM_MEMORY_SIZE` (max per non-file form field in multipart)
  - `MAX_FORM_PARTS` (max number of multipart fields)
- MUST enforce extra limits at reverse proxy / WSGI / platform level where possible.

Insecure patterns:
- Unlimited request body size for uploads or user content.
- Arbitrarily large multipart forms or many fields.

Detection hints:
- Inspect Flask config for these keys.
- Inspect upload routes and APIs accepting large JSON.

Fix:
- Set conservative defaults; override per-route only when needed.
- Use dedicated upload mechanisms for large uploads.

---

### FLASK-HOST-001: Host header must be validated in production
Severity: Low (depends on app’s use of external URLs)

Required:
- MUST set `TRUSTED_HOSTS` in production to restrict accepted Host values.
- MUST NOT rely on `SERVER_NAME` for host restriction.

Insecure patterns:
- `TRUSTED_HOSTS` unset in production.
- External URLs for emails/password resets generated without host validation.

Detection hints:
- Find `TRUSTED_HOSTS` config usage.
- Find `url_for(..., _external=True)`; check how host is determined.

Fix:
- Set `TRUSTED_HOSTS` to expected domains (and required subdomains).
- Generate external URLs from trusted host/scheme.

---

### FLASK-PROXY-001: Reverse proxy trust must be configured correctly
Severity: Medium (High if relying on IPs for auth)

Required:
- Behind reverse proxy, MUST configure Flask/Werkzeug to trust forwarded headers only from intended proxy.
- MUST NOT blindly trust `X-Forwarded-*` headers from open internet.

Insecure patterns:
- `ProxyFix` with overly broad trust settings, or applied without knowing how many proxies sit in front.
- Forwarded headers trusted for scheme/host without validation.

Detection hints:
- Grep `ProxyFix`.
- Grep `request.remote_addr`, `request.scheme`, `request.host` in security-sensitive logic.

Fix:
- Configure `ProxyFix` (or platform-specific settings) with correct hop counts.
- Keep `TRUSTED_HOSTS` in place even behind proxies.

---

### FLASK-PATH-001: Prevent path traversal and unsafe file serving
Severity: High

Required:
- MUST NOT pass user-controlled file paths to `send_file` or direct file I/O.
- MUST use safe file serving patterns:
  - `send_from_directory` for user-specified paths under trusted base directory
  - `safe_join` to join trusted base directory with untrusted path components
  - `secure_filename` for uploaded filenames (still generate own unique storage name)
- MUST NOT serve user uploads as executable/active content (especially HTML).
- SHOULD prefer `safe_join` over `os.path.join` for almost any filesystem path computation.

Insecure patterns:
- `send_file(request.args["path"])`
- `open(os.path.join(base_dir, user_path))` where `user_path` is untrusted
- Serving uploads from static web root without restrictions

Detection hints:
- Grep `send_file(`, `open(`, `os.path.join(`, `pathlib.Path(...)/...` in file routes.
- Identify filename sources (request args, DB, headers).

Fix:
- Serve only from non-user-controlled base directory.
- Store uploads outside static roots; serve via controlled routes.
- Always validate and normalize file identifiers.

Note: import `safe_join` from `werkzeug.security`

---

### FLASK-UPLOAD-001: File uploads must be validated, stored safely, and served safely
Severity: High

Required:
- MUST enforce upload size limits (app + edge).
- MUST validate file type with allowlists and content checks (not only extension).
- MUST store uploads outside executable/static roots when possible.
- SHOULD generate server-side filenames (random IDs); avoid trusting original names.
- MUST serve potentially active formats safely (download attachment) unless explicitly intended.

Insecure patterns:
- Accepting arbitrary file types and serving them back inline.
- User-supplied filename as storage path.
- Missing size/type validation.

Detection hints:
- Look for `request.files[...]` handlers.
- Check `secure_filename` usage (and whether it’s combined with uniqueness).
- Check where files are stored and how served.

Fix:
- Add scanning / quarantine if applicable.

---

### FLASK-INJECT-001: Prevent SQL injection (use parameterized queries / ORM)
Severity: High

Required:
- MUST use parameterized queries or ORM that parameterizes under the hood.
- MUST NOT build SQL via string concatenation / f-strings with untrusted input.

Insecure patterns:
- `f"SELECT ... WHERE id={request.args['id']}"`
- `"... WHERE name = '%s'" % user_input`

Detection hints:
- Grep `SELECT`, `INSERT`, `UPDATE`, `DELETE` strings in Python code.
- Trace untrusted data into DB execute calls.

Fix:
- Validate types (e.g., int IDs) before querying.

---

### FLASK-INJECT-002: Prevent OS command injection
Severity: Critical to High (depends on exposure)

Required:
- MUST avoid shell commands with untrusted input.
- If subprocess necessary:
  - MUST pass args as list (not string)
  - MUST NOT use `shell=True` with attacker-influenced strings
  - SHOULD use strict allowlists for any variable component
- Where possible, prefer pure python or python library over subprocess or system command
- Do not assume command arguments are safe even with `shell=False`. Commands may treat them as command line flags or other trusted values.

Insecure patterns:
- `os.system(user_input)`
- `subprocess.run(f"cmd {user}", shell=True)`
- Passing user strings into `bash -c`, `sh -c`, PowerShell, etc.

Detection hints:
- Grep `os.system`, `subprocess`, `Popen`, `shell=True`.
- Trace data from request/DB into these calls.

Fix:
- If unavoidable, hard-code command and allowlist validated parameters. If subcommand supports it, put user values after `--` so they are not parsed as command line flags.

---

### FLASK-SSRF-001: Prevent server-side request forgery (SSRF) in outbound HTTP
Severity: Medium

- Note: Less important for small stand alone projects. Most important for LAN deployments or with other services listening on same server.

Required:
- MUST treat outbound requests to user-provided URLs as high risk.
- SHOULD validate and restrict destinations (allowlist hosts/domains) for any user-influenced URL fetch.
- SHOULD block access to:
  - localhost / private IP ranges / link-local addresses
  - cloud metadata endpoints
- MUST NOT allow non http/https protocols (ie file: etc)
- SHOULD set timeouts and restrict redirects.

Insecure patterns:
- `requests.get(request.args["url"])`
- Webhooks/preview/fetch endpoints accepting arbitrary URLs.

Detection hints:
- Grep `requests.get/post`, `httpx`, `urllib`, `aiohttp` usage with untrusted URL sources.
- Identify URL fetch features (preview, import, webhook tester).

Fix:
- Enforce allowlists and network egress controls.
- Add strict parsing and IP resolution checks; set timeouts; disable redirects if not needed.

---

### FLASK-REDIRECT-001: Prevent open redirects
Severity: Low

Required:
- MUST validate redirect targets from untrusted input (e.g., `next`, `redirect`, `return_to`).
- SHOULD use allowlists of internal paths or known domains.
- SHOULD prefer redirecting only to same-site relative paths.

Insecure patterns:
- `redirect(request.args.get("next"))` with no validation.

Detection hints:
- Grep `redirect(`; check where `location` comes from.

Fix:
- Fall back to safe default if validation fails.

---

### FLASK-HTTP-001: Use HTTP methods safely; do not change state via GET; avoid secrets in URLs
Severity: Medium

Required:
- MUST NOT perform state-changing actions over GET.
- MUST NOT put secrets in URLs (query strings commonly get logged and leaked via referrers).
- SHOULD require POST/PUT/PATCH/DELETE for state change; apply CSRF protections when cookie-authenticated.

Insecure patterns:
- `/delete?id=...` implemented as GET
- Password reset tokens or API keys in query params

Detection hints:
- Enumerate GET routes; check whether they mutate state.
- Look for URL parameters named `token`, `key`, `secret`, `password`, etc.

Fix:
- Move sensitive values to secure channels (POST bodies, headers) and protect them.

---

### FLASK-CORS-001: CORS must be explicit and least-privilege
Severity: Medium (High if misconfigured with credentials)

Required:
- If CORS not needed, MUST keep it disabled.
- If CORS needed:
  - MUST allowlist trusted origins (do not reflect arbitrary origins).
  - MUST be careful with credentialed requests; do not combine broad origins with cookies.
  - SHOULD restrict allowed methods and headers.

Insecure patterns:
- `Access-Control-Allow-Origin: *` paired with credentialed cookies or overly broad access.
- Reflecting `Origin` without validation.
- `flask_cors.CORS(app)` with permissive defaults.

Detection hints:
- Grep `flask_cors`, `CORS(`, `Access-Control-Allow-Origin`.
- Check for `supports_credentials=True` and wildcard origins.

Fix:
- Do not expose cookie-authenticated endpoints cross-origin unless necessary.

---

### FLASK-SUPPLY-001: Dependency and patch hygiene (focus on security-relevant deps)
Severity: Low

Required:
- SHOULD pin and regularly update security-critical dependencies (Flask, Werkzeug, Jinja2, itsdangerous).
- MUST respond promptly to known security advisories.

Audit focus example:
- On Windows, if serving files with untrusted paths, ensure Werkzeug’s `safe_join` behavior is not vulnerable to Windows device-name edge cases.

Detection hints:
- Check `requirements.txt`, lockfiles, runtime environments.
- Identify where security helpers are used (safe_join, send_from_directory).

Fix:
- Upgrade to patched versions; add regression tests for impacted behavior.

## 5) Practical scanning heuristics (how to “hunt”)

High-signal patterns for active scanning:

- Dev server / debug:
  - `app.run(`, `flask run`, `--debug`, `DEBUG=True`, `FLASK_DEBUG`
- Secrets:
  - `SECRET_KEY`, `secret_key`, `.env` committed, `print(config)`
- Cookies / sessions:
  - `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`
  - `session[...] =` with sensitive values
- CSRF:
  - POST/PUT/PATCH/DELETE handlers without CSRF checks in cookie-authenticated apps
- XSS/SSTI:
  - `Markup(`, `|safe`, unquoted attributes, `render_template_string`
- Files:
  - `send_file(` with user-controlled path; `open(` on user path; `os.path.join` with untrusted
  - upload handlers using user filename for path
- Injection:
  - SQL strings + string formatting into `.execute(...)`
  - `subprocess.*`, `shell=True`, `os.system`
- SSRF:
  - `requests.get/post` or `httpx` with URL from request/DB
- Redirect:
  - `redirect(request.args.get("next"))`
- CORS:
  - `flask_cors.CORS` permissive configs; wildcard origins with credentials

Always confirm:
- data origin (untrusted vs trusted)
- sink type (template/SQL/subprocess/files/redirect/http)
- protective controls present (validation, allowlists, middleware)

## 6) Sources (accessed 2026-01-26)

Primary framework documentation:
- Flask Docs: Deploying to Production — https://flask.palletsprojects.com/en/stable/deploying/
- Flask Docs: Debugging Application Errors — https://flask.palletsprojects.com/en/stable/debugging/
- Flask Docs: Configuration Handling — https://flask.palletsprojects.com/en/stable/config/
- Flask Docs: Security Considerations — https://flask.palletsprojects.com/en/stable/web-security/
- Flask Docs: Tell Flask it is Behind a Proxy — https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
- Flask API Docs: Sessions — https://flask.palletsprojects.com/en/stable/api/#sessions

Werkzeug documentation & advisories:
- Werkzeug Docs: Utilities (send_file / send_from_directory / safe_join / secure_filename / password hashing) — https://werkzeug.palletsprojects.com/en/stable/utils/
- GitHub Advisory: CVE-2025-66221 (Werkzeug safe_join Windows device names) — https://github.com/advisories/GHSA-hgf8-39gv-g3f2

OWASP Cheat Sheet Series:
- Session Management — https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- CSRF Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- XSS Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- Input Validation — https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- SQL Injection Prevention — https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- Injection Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html
- OS Command Injection Defense — https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
- SSRF Prevention — https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- File Upload — https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- Unvalidated Redirects — https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
- HTTP Headers — https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html

Template safety references:
- Jinja: Sandbox (rendering untrusted templates) — https://jinja.palletsprojects.com/en/stable/sandbox/
- OWASP WSTG: Testing for Server-Side Template Injection — https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection
- PortSwigger Web Security Academy: Server-side template injection — https://portswigger.net/web-security/server-side-template-injection

HTTP semantics:
- RFC 9110: HTTP Semantics (safe methods) — https://www.rfc-editor.org/rfc/rfc9110
