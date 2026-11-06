# Django (Python) Web Security Spec (Django 6.0.x, Python 3.x)

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session cookies, `SECRET_KEY`, `SECRET_KEY_FALLBACKS`, database passwords).
* MUST NOT “fix” security by disabling protections (e.g., removing `CsrfViewMiddleware`, sprinkling `@csrf_exempt`, loosening `ALLOWED_HOSTS` to `['*']`, disabling `SecurityMiddleware`, disabling template auto-escaping, disabling permission checks).
* MUST give **evidence-based findings** in audits: cite file paths, code snippets, and concrete config values backing each claim.
* MUST treat uncertainty honestly: if protection might exist in infrastructure (reverse proxy, WAF, CDN, ingress controller), report it as “not visible in app code; verify at runtime / edge config”.
* MUST keep fixes compatible with Django’s intended security model: prefer Django built-ins (middleware, auth, forms, ORM) over custom security logic where possible. Django’s deployment checklist and system checks are part of that model. ([Django Project][1])

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing new Django code or modifying existing code:

* MUST follow every **MUST** requirement in this spec.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default Django APIs and proven libraries over custom security code.
* MUST avoid introducing new risky sinks (dynamic template rendering from untrusted strings, unsafe redirects, unsafe file serving, shell execution, raw SQL string formatting, SSRF-capable URL fetchers from untrusted input).

### 1.2 Passive review mode (always on while editing)

While working anywhere in a Django repo (even if user did not ask for a security scan):

* MUST “notice” spec violations in touched/nearby code.
* SHOULD mention issues as they come up, with brief explanation + safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. Deployment entrypoints (ASGI/WSGI), Dockerfiles, Procfiles, systemd units, platform manifests.
2. `settings.py` and environment-specific settings modules.
3. Middleware ordering and enabled protections.
4. Authn/authz (login, session management, permissions, admin).
5. CSRF protections and state-changing endpoints.
6. Templates and XSS.
7. File handling (uploads/downloads/static/media) and path traversal.
8. Injection classes (SQL, command execution, unsafe deserialization).
9. Outbound requests (SSRF).
10. Redirect handling (open redirects) + CORS + security headers (CSP, HSTS, etc.).
11. Dependency/pinning and patch posture.

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Examples:

* `request.GET`, `request.POST`, `request.FILES`
* `request.body`, JSON bodies (e.g., `json.loads(request.body)`), DRF `request.data`
* URL path parameters (e.g., `<int:id>`, `<slug:...>`)
* `request.headers` / `request.META` (including `HTTP_HOST`, `HTTP_ORIGIN`, `HTTP_REFERER`, `HTTP_X_FORWARDED_*`)
* `request.COOKIES`
* Any data from external systems (webhooks, third-party APIs, message queues)
* Any persisted content originating from users (DB rows, cached content, file uploads)

Django stresses “never trust user-controlled data” and recommends forms/validation. ([Django Project][2])

### 2.2 State-changing request

Request is state-changing if it can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook send), or start privileged actions.

### 2.3 Required audit finding format

For each issue found, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + function/class/view name + line(s)
* Evidence: the exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

Smallest “production baseline” preventing common Django misconfigurations. Django provides a “Deployment checklist” and recommends running `manage.py check --deploy` against production settings. ([Django Project][1])

### 3.1 Settings management pattern (SHOULD)

* SHOULD use environment-based config (or secret manager) so production settings are not hard-coded.
* SHOULD separate dev vs prod settings modules, with safe production defaults (fail closed if critical settings are missing). ([Django Project][1])

### 3.2 Minimum baseline targets (production)

* MUST NOT use `manage.py runserver` as production entrypoint (DJANGO-DEPLOY-001); MUST set `DEBUG = False` (DJANGO-DEPLOY-002); MUST set strong, secret `SECRET_KEY`, MAY use `SECRET_KEY_FALLBACKS` for safe rotation (DJANGO-CONFIG-001); MUST set strict `ALLOWED_HOSTS` (DJANGO-HOST-001).
* SHOULD enable key `SecurityMiddleware` headers/settings: HSTS, Referrer-Policy, COOP, nosniff, SSL redirect (with correct proxy config) (DJANGO-HEADERS-001).
* MUST treat user uploads as untrusted, never executable by web server; keep `MEDIA_ROOT` separate from `STATIC_ROOT` (DJANGO-UPLOAD-001, DJANGO-PATH-001).
* MUST enforce HTTPS for authenticated areas (ideally site-wide for any login-capable app) and set `CSRF_COOKIE_SECURE=True` and `SESSION_COOKIE_SECURE=True` when HTTPS is used. ([Django Project][1])

---

## 4) Rules (generation + audit)

### DJANGO-DEPLOY-001: Do not use Django’s development server in production

Severity: High (if production)

Required:

* MUST NOT deploy `manage.py runserver` as production server.
* MUST run behind a production-grade WSGI or ASGI server. ([Django Project][1])

Insecure patterns:

* Production docs/scripts using `python manage.py runserver 0.0.0.0:8000`.
* Docker `CMD`/entrypoint uses `runserver`.
* Kubernetes/Procfile/systemd units invoking `runserver`.

Detection hints:

* Search for `manage.py runserver`, `runserver 0.0.0.0`, `--insecure`.
* Check Docker `CMD/ENTRYPOINT`, Procfile, systemd unit files, Helm charts.

Fix:

* Use a production server (WSGI/ASGI) per Django’s deployment checklist. ([Django Project][1])

Note:

* `runserver` is fine for local development. Flag only if used as production entrypoint.

---

### DJANGO-DEPLOY-002: `DEBUG` MUST be disabled in production

Severity: High

Required:

* MUST set `DEBUG = False` in production.
* MUST treat any mechanism exposing debug pages/tracebacks to untrusted users as critical information disclosure. Django’s checklist warns `DEBUG=True` leaks source excerpts, local variables, settings, and more. ([Django Project][1])

Insecure patterns:

* `DEBUG = True` in production settings.
* Environment defaults to `DEBUG=True` unless explicitly overridden.

Detection hints:

* Search `DEBUG = True`, `DEBUG=os.environ.get(..., True)`, `DJANGO_DEBUG`, `.env` files.
* Look for “production” settings modules importing from dev defaults.

Fix:

* Set `DEBUG=False` in prod settings; use explicit environment config.
* Report errors via safe logging/monitoring, not debug pages. ([Django Project][1])

---

### DJANGO-CONFIG-001: `SECRET_KEY` must be strong, secret, and rotated safely

Severity: High (Critical if missing in production with signing/sessions)

Required:

* MUST set a large random `SECRET_KEY` in production and keep it secret. ([Django Project][1])
* MUST NOT commit it to source control or print/log it. ([Django Project][1])
* SHOULD load it from env or a file/secret store (not hard-coded). ([Django Project][1])
* MAY rotate keys using `SECRET_KEY_FALLBACKS` to avoid instantly invalidating all signed data; MUST remove old keys from fallbacks promptly. ([Django Project][1])

Insecure patterns:

* Hard-coded `SECRET_KEY = "..."` in repo for production.
* `SECRET_KEY` reused across environments.
* `SECRET_KEY_FALLBACKS` holds long-expired keys indefinitely.

Detection hints:

* Search for `SECRET_KEY =`, `SECRET_KEY_FALLBACKS`, `.env` committed files, `print(settings.SECRET_KEY)`.

Fix:

* Load from secret manager / environment variable.
* If rotating:

  * Set new `SECRET_KEY`
  * Keep old key(s) temporarily in `SECRET_KEY_FALLBACKS`
  * Remove old key(s) after rotation window. ([Django Project][1])

---

### DJANGO-HOST-001: Host header must be validated (`ALLOWED_HOSTS` must be strict)

Severity: Medium

Required:

* MUST set `ALLOWED_HOSTS` in production to expected domains/hosts. ([Django Project][1])
* MUST NOT set `ALLOWED_HOSTS = ['*']` in production unless you also implement robust `Host` validation yourself (Django warns wildcards require own validation to avoid CSRF-class attacks). ([Django Project][1])
* SHOULD configure fronting web server to reject unknown hosts early (defense-in-depth). ([Django Project][1])

Insecure patterns:

* `ALLOWED_HOSTS = ['*']` (or env expands to `*`) in production.
* `ALLOWED_HOSTS = []` with `DEBUG=False` (site won’t run, or misconfigured deployments attempt workarounds).

Detection hints:

* Search `ALLOWED_HOSTS`.
* Check platform environment settings overriding `ALLOWED_HOSTS`.

Fix:

* Set `ALLOWED_HOSTS = ['example.com', 'www.example.com', ...]` for prod.
* Keep dev hosts separate.

Notes:

* Django uses Host header for URL construction; fake Host values can lead to CSRF, cache poisoning, and poisoned email links (per Django security docs). ([Django Project][2])

---

### DJANGO-HTTPS-001: If TLS is used cookie transport must be secured

Severity: High (Critical for auth-enabled apps)

NOTE: Only enforce if TLS is enabled; it breaks non-TLS applications.

If using TLS:
* MUST set:

  * `CSRF_COOKIE_SECURE = True` ([Django Project][1])
  * `SESSION_COOKIE_SECURE = True` ([Django Project][1])
* SHOULD consider enabling:

  * `SECURE_SSL_REDIRECT = True` (with correct proxy config) ([Django Project][3])
  * HSTS via `SECURE_HSTS_SECONDS` (+ includeSubDomains/preload as appropriate). ([Django Project][3])

Insecure patterns:

* Login pages over HTTP, or mixed HTTP/HTTPS with same session cookie.
* `CSRF_COOKIE_SECURE=False` or `SESSION_COOKIE_SECURE=False` in production HTTPS.
* HSTS enabled incorrectly (can break site for the duration).

Detection hints:

* Inspect `settings.py` for `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`.
* Inspect proxy/ingress config for HTTP->HTTPS redirect behavior.

Fix:

* Enable HTTPS redirect and secure cookies.
* Add HSTS carefully (start low, validate, then increase). Django warns misconfig can break site for HSTS duration. ([Django Project][3])

---

### DJANGO-PROXY-001: Reverse proxy trust must be configured correctly (`SECURE_PROXY_SSL_HEADER`)

Severity: Medium (when behind a TLS proxy)

Required:

* If behind reverse proxy terminating TLS, MUST configure Django so `request.is_secure()` reflects *external* scheme; otherwise CSRF and other logic can break. Django documents `SECURE_PROXY_SSL_HEADER` for this. ([Django Project][3])
* MUST only set `SECURE_PROXY_SSL_HEADER` if you control the proxy (or have guarantees) and it strips inbound spoofed headers. Django warns misconfig can compromise security and lists required conditions. ([Django Project][3])

Insecure patterns:

* `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` where proxy does not strip user-supplied `X-Forwarded-Proto`.
* Infinite redirect loops after setting `SECURE_SSL_REDIRECT=True` (often means proxy HTTPS detection is wrong). ([Django Project][3])

Detection hints:

* Search `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`.
* Inspect ingress/proxy behavior for stripping forwarded headers.

Fix:

* Set `SECURE_PROXY_SSL_HEADER` only if proxy strips and sets header correctly (per Django’s documented prerequisites). ([Django Project][3])

---

### DJANGO-SESS-001: Session cookies must use secure attributes in production

Severity: Medium (Only if TLS enabled)

Required (production, HTTPS):

* MUST set `SESSION_COOKIE_SECURE=True` (only transmit over HTTPS). ([Django Project][3])
* MUST keep `SESSION_COOKIE_HTTPONLY=True` (Django default is `True`). ([Django Project][3])
* SHOULD keep `SESSION_COOKIE_SAMESITE='Lax'` (Django default is `Lax`) unless a justified cross-site flow requires `None`. ([Django Project][3])
* SHOULD avoid setting `SESSION_COOKIE_DOMAIN` unless you truly need cross-subdomain cookies (subdomain-wide cookies expand attack surface).

Insecure patterns:

* `SESSION_COOKIE_SECURE=False` in production HTTPS.

IMPORTANT NOTE: Only set `Secure` in production when TLS is configured. In local dev over HTTP, do not set `Secure` on cookies. Set it conditionally, based on whether app runs in production mode. Also include a property like `SESSION_COOKIE_SECURE` that can disable `Secure` cookies when testing over HTTP.

* `SESSION_COOKIE_HTTPONLY=False`.
* `SESSION_COOKIE_SAMESITE=None` combined with cookie-authenticated state-changing endpoints (higher CSRF risk).

Detection hints:

* Search for `SESSION_COOKIE_` settings, `response.set_cookie(..., httponly=..., secure=..., samesite=...)`.

Fix:

* Set the above explicitly in production settings.
* Check compatibility with your auth flows. ([Django Project][3])

---

### DJANGO-SESS-002: CSRF cookie settings must be deliberate (HttpOnly has tradeoffs)

Severity: Medium

Required:

* SHOULD set `CSRF_COOKIE_SECURE=True` when using HTTPS/TLS. ([Django Project][3])
* SHOULD keep `CSRF_COOKIE_SAMESITE='Lax'` unless you have a cross-site requirement. Django default is `Lax`. ([Django Project][3])
* MAY set `CSRF_COOKIE_HTTPONLY=True` (default is `False`) if frontend does not need to read CSRF cookie. If enabled, JS must read CSRF token from DOM instead (Django documents this). ([Django Project][3])

Insecure patterns:

* `CSRF_COOKIE_SECURE=False` in production HTTPS/TLS.
* Setting `CSRF_COOKIE_HTTPONLY=True` but still relying on “read csrftoken cookie in JS” patterns (breaks CSRF for AJAX).
* `CSRF_COOKIE_SAMESITE=None` without clear reason.

Detection hints:

* Search for `CSRF_COOKIE_` settings.
* Search JS for `document.cookie` usage fetching `csrftoken`.

Fix:

* Align cookie settings with CSRF token acquisition method (cookie vs DOM) as Django describes. ([Django Project][4])

---

### DJANGO-CSRF-001: Cookie-authenticated state-changing requests MUST be CSRF-protected

Severity: High

Required:

* MUST keep `django.middleware.csrf.CsrfViewMiddleware` enabled (on by default). ([Django Project][4])
* MUST include `{% csrf_token %}` in internal POST forms; MUST NOT include it in forms POSTing to external URLs (Django warns this leaks the token). ([Django Project][4])
* MUST protect all state-changing endpoints (POST/PUT/PATCH/DELETE) relying on cookies for authentication.
* For AJAX/SPA calls, MUST send CSRF token via `X-CSRFToken` header (or configured header name) as documented. ([Django Project][4])
* MUST be careful with `@csrf_exempt`; use it only when absolutely necessary. If used, MUST replace CSRF with an appropriate alternative control (e.g., request signing for webhooks). Django warns about `csrf_exempt`. ([Django Project][2])

Insecure patterns:

* Missing `CsrfViewMiddleware` in `MIDDLEWARE`.
* `@csrf_exempt` on general-purpose authenticated views.
* POST/PUT/PATCH/DELETE endpoints with session auth and no CSRF tokens.
* GET for state-changing actions (amplifies CSRF risk).

Detection hints:

* Inspect `settings.py` `MIDDLEWARE` for `CsrfViewMiddleware` and its order (Django notes it should come before middleware assuming CSRF is handled). ([Django Project][4])
* Search for `csrf_exempt`, `csrf_protect`, `ensure_csrf_cookie`.
* Enumerate URL patterns for non-GET methods; confirm CSRF coverage.

Fix:

* Re-enable `CsrfViewMiddleware`, add CSRF tokens to forms, add AJAX header handling.
* Caching decorators: if caching a view that needs CSRF tokens, apply `@csrf_protect` as Django documents, to avoid caching a response without CSRF cookie/Vary headers. ([Django Project][4])

Notes:

* Under HTTPS, Django’s CSRF middleware also checks Referer header for same-origin (per Django security docs). ([Django Project][2])

---

### DJANGO-XSS-001: Prevent reflected/stored XSS in templates and HTML generation

Severity: High

Required:

* MUST rely on Django template auto-escaping (safe-by-default) for HTML templates. Django security docs note templates escape dangerous characters but have limitations. ([Django Project][2])
* MUST NOT disable auto-escaping broadly (`{% autoescape off %}`) unless content is trusted or safely sanitized. ([Django Project][5])
* MUST NOT mark untrusted content as safe:

  * Avoid `mark_safe(...)` on user data.
  * Avoid `|safe` on user-controlled content.
* MUST be careful with HTML context pitfalls (e.g., unquoted attributes); Django shows an example where escaping does not protect an unquoted attribute context. ([Django Project][2])
* SHOULD prefer safe HTML construction helpers (e.g., `format_html`) over manual concatenation that risks missing escapes. ([Django Project][6])

Insecure patterns:

* `{% autoescape off %}{{ user_input }}{% endautoescape %}`
* `{{ user_input|safe }}`
* `mark_safe(request.GET["q"])`
* Unquoted attribute injections: `<style class={{ var }}>...` (Django’s own example). ([Django Project][2])

Detection hints:

* Search templates for `|safe`, `autoescape off`, `safeseq`.
* Search Python for `mark_safe`, `SafeString`, or direct HTML concatenation with request/DB values.
* Review code returning `HttpResponse(user_value)` where `user_value` contains HTML.

Fix:

* Remove unsafe marking; sanitize only when strictly necessary (use an allowlist-based HTML sanitizer).
* Quote attributes; avoid placing untrusted values in dangerous contexts.
* Add CSP as defense-in-depth (see DJANGO-CSP-001). ([Django Project][2])

---

### DJANGO-TEMPLATE-001: Never render untrusted template source strings

Severity: High to Critical (depends on context and exposure)

Required:

* MUST NOT render templates whose source string is influenced by untrusted input (request, user content, DB rows editable by untrusted users).
* MUST treat “template from string” patterns as dangerous, even if Django templates are more constrained than some other engines: they can still leak context data, bypass escaping, and create XSS or content injection.

Insecure patterns:

* `Template(request.GET["tmpl"]).render(Context(...))`
* Saving user templates in DB and rendering them with normal privileges/context.

Detection hints:

* Search for `django.template.Template(`, `Engine.from_string`, `.render(Context(` with non-constant strings.
* Trace where template string comes from (admin panels, DB, uploads, requests).

Fix:

* Replace with non-executing formatting (e.g., `string.Template`, explicit placeholders) or a strict allowlisted rendering model.
* If you *must* support user-defined templates, isolate heavily (separate service/tenant context, strict allowlists, assume bypasses are possible).

---

### DJANGO-SQL-001: Prevent SQL injection (use ORM or parameterized raw SQL)

Severity: High

Required:

* MUST use Django ORM/querysets for normal DB access; Django notes querysets are parameterized and protected from SQL injection under typical use. ([Django Project][2])
* MUST be careful with raw SQL. If using `raw()`, `cursor.execute()`, `extra()`, or `RawSQL`, MUST pass parameters separately (e.g., `params=`) and MUST NOT string-interpolate untrusted input into SQL. Django’s raw SQL docs warn to escape user-controlled parameters via `params`. ([Django Project][7])
* MUST NOT quote placeholders in SQL templates (Django docs warn quoting `%s` placeholders makes it unsafe). ([Django Project][8])
* SHOULD avoid `extra()` and `RawSQL` unless necessary; Django security docs urge caution. ([Django Project][2])

Insecure patterns:

* `cursor.execute(f"SELECT ... WHERE id={request.GET['id']}")`
* `Model.objects.raw("... %s" % user_input)` (string formatting)
* `extra(where=[f"headline='{q}'"])`
* Quoted placeholders: `WHERE othercol = '%s'` (documented as unsafe). ([Django Project][8])

Detection hints:

* Grep for `.raw(`, `.extra(`, `RawSQL(`, `connection.cursor()`, `.execute(`.
* Grep for SQL keywords (`SELECT`, `UPDATE`, `DELETE`, `INSERT`) in Python strings.
* Track untrusted inputs into these call sites.

Fix:

* Prefer ORM queries.
* If raw SQL is unavoidable, use parameters (`params`, DB-API param binding) and do not quote placeholders. ([Django Project][7])

---

### DJANGO-CMD-001: Prevent OS command injection

Severity: Critical to High (depends on exposure)

Required:

* MUST avoid executing system commands with attacker-influenced input.
* If subprocess is necessary:

  * MUST pass args as a list (not a shell string).
  * MUST NOT use `shell=True` with attacker-influenced content.
  * SHOULD use strict allowlists for variable components.
* SHOULD prefer pure-Python libraries over shelling out.

Insecure patterns:

* `os.system(request.GET["cmd"])`
* `subprocess.run(f"convert {path}", shell=True)` where `path` is user-controlled.

Detection hints:

* Search `os.system`, `subprocess`, `Popen`, `shell=True`.
* Trace request/DB inputs into those calls.

Fix:

* Replace with library APIs; if unavoidable, hard-code executable and allowlist validated parameters.

---

### DJANGO-UPLOAD-001: File uploads must be validated, stored safely, and served safely

Severity: High

Required:

* MUST treat all user uploads as untrusted. Django warns “Media files are uploaded by your users. They’re untrusted!” ([Django Project][1])
* MUST ensure web server never interprets user uploads as executable code (e.g., don’t allow uploaded `.php` or HTML to execute/inline as active content). ([Django Project][1])
* MUST enforce size limits (at least at web server; Django security docs recommend limiting upload size at server to prevent DoS). ([Django Project][2])
* SHOULD validate file types with allowlists and content checks (not only extensions).
* SHOULD store uploads outside application code directory and outside any static root.
* SHOULD consider serving uploads from a separate top-level/second-level domain to reduce same-origin impact; Django security docs recommend a distinct domain; a subdomain may be insufficient for some protections. ([Django Project][2])
* MUST know polyglot upload risks: Django documents a case where HTML can be uploaded “as an image” via a valid PNG header (and may be served as HTML depending on web server). ([Django Project][2])

Insecure patterns:

* Serving uploads inline with `text/html` or without forcing download for potentially active formats.
* Upload allowlist based only on extension.
* Upload storage inside static roots or code roots.

Detection hints:

* Search for `request.FILES`, `FileField`, `ImageField`, upload forms/views.
* Inspect upload serving paths and Nginx/Apache config (media handlers).
* Check `MEDIA_URL`, `MEDIA_ROOT`, and static config.

Fix:

* Configure web server to serve uploads as inert bytes (no execution); consider forcing `Content-Disposition: attachment` for risky types.
* Use a separate domain for user content when warranted. ([Django Project][2])

---

### DJANGO-PATH-001: Prevent path traversal and unsafe file serving (static/media separation)

Severity: High

Required:

* MUST NOT treat user input as a filesystem path for reads/writes/serving.
* MUST keep `MEDIA_ROOT` and `STATIC_ROOT` distinct; Django settings docs warn they must differ to avoid security implications. ([Django Project][3])
* SHOULD prefer Django storage APIs keyed by server-side identifiers over accepting arbitrary relative paths from users.

Insecure patterns:

* `open(os.path.join(MEDIA_ROOT, request.GET["path"]))`
* Download endpoints taking `?file=../../...` style parameters.
* Misconfigured `MEDIA_ROOT == STATIC_ROOT`.

Detection hints:

* Grep for `open(`, `Path(`, `os.path.join(` used with request values.
* Check `MEDIA_ROOT`, `STATIC_ROOT` in settings. ([Django Project][3])

Fix:

* Use server-side IDs mapped to known files.
* Keep static and media separated; ensure web server treats media as untrusted. ([Django Project][3])

---

### DJANGO-REDIRECT-001: Prevent open redirects (`next`, `return_to`, `redirect`)

Severity: Medium (High when combined with auth flows)

Required:

* MUST validate redirect targets derived from untrusted input (e.g., `next`, `return_to`).
* SHOULD restrict to same-site relative paths or allowlisted hosts/schemes.
* SHOULD use Django’s safe URL helpers (e.g., `django.utils.http.url_has_allowed_host_and_scheme`) over custom parsing.

Insecure patterns:

* `return redirect(request.GET.get("next"))` with no validation.
* Redirect allowlist implemented with naive string checks.

Detection hints:

* Search for `redirect(` and track target origin.
* Search for parameters named `next`, `return_to`, `redirect`, `url`.

Fix:

* Validate with allowlists; default to a safe internal path if validation fails.
* Keep host validation via `ALLOWED_HOSTS` strict (see DJANGO-HOST-001). ([Django Project][3])

---

### DJANGO-HEADERS-001: Enable essential security headers (SecurityMiddleware + clickjacking protection)

Severity: Medium to High

Required:

* SHOULD use `django.middleware.security.SecurityMiddleware`, configured appropriately (production) for:

  * `X-Content-Type-Options: nosniff` (Django setting `SECURE_CONTENT_TYPE_NOSNIFF`, default `True`). ([Django Project][3])
  * `Referrer-Policy` (Django setting `SECURE_REFERRER_POLICY`, default `'same-origin'`). ([Django Project][3])
  * COOP (Django setting `SECURE_CROSS_ORIGIN_OPENER_POLICY`, default `'same-origin'`). ([Django Project][3])
  * HTTPS redirects and HSTS as appropriate (see DJANGO-HTTPS-001). ([Django Project][3])
* SHOULD enable clickjacking protection via X-Frame-Options middleware; Django security docs strongly recommend it for sites that don’t need third-party framing. ([Django Project][2])

Insecure patterns:

* Missing SecurityMiddleware.
* Missing clickjacking protection (or disabling it globally) without clear framing requirement.
* Over-broad framing allowances for sensitive endpoints.

Detection hints:

* Inspect `MIDDLEWARE` for SecurityMiddleware and XFrameOptionsMiddleware.
* Search for per-view disabling of framing/CSRF protections.

Fix:

* Add/enable middleware and configure settings intentionally. ([Django Project][3])

---

### DJANGO-CSP-001: Deploy a Content Security Policy (CSP) as defense-in-depth

Severity: Medium (High for apps rendering untrusted content)

NOTE: CSP's script-src matters most. Other directives matter less and can usually be excluded for ease of development.

Required:

* SHOULD deploy a CSP to mitigate XSS and content injection classes; Django’s security docs recommend CSP (new in Django 6.0). ([Django Project][2])
* MUST understand CSP limitations:

  * Avoid excluding routes from CSP coverage; Django warns an unprotected page can undermine protected pages due to same-origin policy. ([Django Project][2])
* MAY start with `SECURE_CSP_REPORT_ONLY` to iterate safely (Django supports report-only). ([Django Project][3])

Insecure patterns:

* No CSP on apps rendering user-controlled content.
* CSP excludes “just a couple pages” (weakens overall protection), especially pages with any injection surface. ([Django Project][2])
* CSP uses overly permissive directives (e.g., widespread `unsafe-inline`) without justification.

Detection hints:

* Search `SECURE_CSP`, `SECURE_CSP_REPORT_ONLY`, and CSP middleware config.
* Inspect reverse proxy/CDN config for CSP headers.

Fix:

* Implement a realistic CSP, ideally report-only first, then enforce. ([Django Project][3])

---

### DJANGO-AUTH-001: Password storage must use Django’s secure hashers; password policy must be configured

Severity: High

Required:

* MUST use Django’s built-in password hashing (never store plaintext or reversible encrypted passwords).
* SHOULD prefer modern hashers and keep defaults updated; Django documents `PASSWORD_HASHERS` with modern options (Argon2, bcrypt, scrypt, PBKDF2 variants). ([Django Project][3])
* SHOULD configure `AUTH_PASSWORD_VALIDATORS` (default is empty) for production password policy. ([Django Project][3])

Insecure patterns:

* Custom password storage or hashing.
* Plaintext passwords stored in DB fields.
* No password validation on consumer-facing apps.

Detection hints:

* Search for `.set_password(` usage vs manual hashing.
* Inspect settings for `PASSWORD_HASHERS` and `AUTH_PASSWORD_VALIDATORS`. ([Django Project][3])

Fix:

* Use Django auth user model APIs.
* Enable password validators fitting product’s risk profile. ([Django Project][3])

---

### DJANGO-AUTHZ-001: Authorization must be explicit and consistent

Severity: High

Required:

* MUST enforce authorization checks on every privileged action (view, modify, admin-like operations).
* MUST NOT rely on UI-only restrictions (e.g., hiding buttons) without server-side permission checks.
* SHOULD use Django’s permissions/groups and per-object authorization patterns where applicable.

Insecure patterns:

* Views assuming “user is logged in” implies “user may do action”.
* Missing authorization checks on update/delete endpoints.

Detection hints:

* Enumerate state-modifying views; ensure they validate ownership/permission.
* Look for use of only `is_authenticated` or only `is_staff` without object-level access checks.

Fix:

* Add explicit permission checks and tests for unauthorized access.

---

### DJANGO-ADMIN-001: Django admin must be treated as a high-value target

Severity: High

Required:

* MUST protect admin with strong authentication and HTTPS-only transport (see DJANGO-HTTPS-001). ([Django Project][1])
* SHOULD restrict admin exposure (network allowlists, VPN, SSO, or extra authentication controls) when possible.
* SHOULD audit installed admin extensions and third-party apps for XSS/CSRF exposure.

Insecure patterns:

* Admin exposed to internet with weak authentication.
* Admin served over HTTP.

Detection hints:

* Search `urlpatterns` for `admin.site.urls`.
* Check deployment config for IP allowlisting or auth gateways.

Fix:

* Add network controls and enforce HTTPS.

---

### DJANGO-LOG-001: Logging and error reporting must not leak secrets

Severity: Medium to High

Required:

* MUST NOT log secrets (including `SECRET_KEY`, session cookies, auth headers, password reset tokens).
* MUST configure production logging deliberately; Django’s deployment checklist says to review logging before production. ([Django Project][1])
* MUST ensure `DEBUG=False` in production so exceptions aren’t rendered with sensitive context. ([Django Project][1])

Insecure patterns:

* Logging full request headers or cookies in production.
* Printing settings dictionaries.
* Debug error pages.

Detection hints:

* Inspect `LOGGING` config; search for middleware logging request headers/cookies.
* Grep for `print(settings` / `logging.info(request.META)` patterns.

Fix:

* Redact sensitive values; log IDs, not secrets.
* Use structured logging and a safe error monitoring tool. ([Django Project][1])

---

### DJANGO-SUPPLY-001: Dependency and patch hygiene (Django + security-critical deps)

Severity: Medium (High if known vulnerable versions)

Required:

* SHOULD pin and regularly update Django and security-critical dependencies.
* MUST respond to Django security releases promptly.

Detection hints:

* Check `requirements.txt`, lockfiles, build images.
* Identify Django version; compare against latest supported release (Django’s download page lists current stable and supported branches). ([Django Project][9])

Fix:

* Upgrade to patched versions; add regression tests for previously vulnerable classes.

---

## 5) Practical scanning heuristics (how to “hunt”)

When actively scanning, use each rule's Detection hints and Insecure patterns as high-signal search patterns.

Always confirm:

* data origin (untrusted vs trusted)
* sink type (template/SQL/subprocess/files/redirect/http)
* protective controls present (middleware, validation, allowlists, authz checks)
* whether security headers/controls are set in-app vs at the edge

---

## 6) Sources (accessed 2026-01-27)

Primary Django documentation:

```text
- Django Downloads (current stable & supported branches): https://www.djangoproject.com/download/
- Django 6.0 Release Notes: https://docs.djangoproject.com/en/6.0/releases/6.0/
- Django: Deployment checklist (incl. check --deploy, runserver warning, HTTPS/cookies guidance): https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/
- Django: Settings reference (SecurityMiddleware settings, cookies, SECRET_KEY_FALLBACKS, CSP settings): https://docs.djangoproject.com/en/6.0/ref/settings/
- Django: Security in Django (XSS/CSRF/SQLi/clickjacking/HTTPS/host header validation/uploads/CSP): https://docs.djangoproject.com/en/6.0/topics/security/
- Django: CSRF how-to (middleware, csrf_token usage, AJAX header patterns, csrf_exempt cautions): https://docs.djangoproject.com/en/6.0/howto/csrf/
- Django: Performing raw SQL queries (parameterization guidance): https://docs.djangoproject.com/en/6.0/topics/db/sql/
- Django: QuerySet API reference (extra() cautions; “do not quote placeholders” guidance): https://docs.djangoproject.com/en/6.0/ref/models/querysets/
- Django: Template built-ins (autoescape tag): https://docs.djangoproject.com/en/6.0/ref/templates/builtins/
- Django: Template language reference (turning off autoescape & risks): https://docs.djangoproject.com/en/6.0/ref/templates/language/
- Django: Utilities reference (e.g., format_html): https://docs.djangoproject.com/en/6.0/ref/utils/
```

OWASP:

```text
- OWASP Cheat Sheet Series: Django Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html
```

[1]: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/ "https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/"
[2]: https://docs.djangoproject.com/en/6.0/topics/security/ "Security in Django | Django documentation | Django"
[3]: https://docs.djangoproject.com/en/6.0/ref/settings/ "Settings | Django documentation | Django"
[4]: https://docs.djangoproject.com/en/6.0/howto/csrf/ "How to use Django’s CSRF protection | Django documentation | Django"
[5]: https://docs.djangoproject.com/en/6.0/ref/templates/builtins/ "https://docs.djangoproject.com/en/6.0/ref/templates/builtins/"
[6]: https://docs.djangoproject.com/en/6.0/ref/utils/ "https://docs.djangoproject.com/en/6.0/ref/utils/"
[7]: https://docs.djangoproject.com/en/6.0/topics/db/sql/ "https://docs.djangoproject.com/en/6.0/topics/db/sql/"
[8]: https://docs.djangoproject.com/en/6.0/ref/models/querysets/ "https://docs.djangoproject.com/en/6.0/ref/models/querysets/"
[9]: https://www.djangoproject.com/download/ "Download Django | Django"
