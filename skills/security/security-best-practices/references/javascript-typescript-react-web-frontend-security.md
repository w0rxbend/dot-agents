# React (JavaScript/TypeScript) Web Security Spec (React 19.x, TypeScript 5.x)

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, OAuth client secrets, private keys, session cookies, JWTs, signing keys).

  * Frontend note: anything shipped to browser is visible to end users and attackers (view-source, devtools, proxies). Never treat client code or “env vars in the bundle” as secret. ([create-react-app.dev][1])
* MUST NOT “fix” security by disabling protections: turning off CSP to “make it work”, adding `unsafe-inline`/`unsafe-eval` without documented, constrained plan, disabling CSRF protections with cookie auth, widening CORS, skipping sanitization, shipping “temporary” bypasses. ([OWASP Cheat Sheet Series][2])
* MUST give **evidence-based findings** in audits: cite file paths, code snippets, config values.
* MUST be honest about uncertainty: if protection may exist in infra (CDN/WAF/reverse proxy), report “not visible in app code; verify via runtime headers / edge config”.
* MUST assume data crossing trust boundary (URL, storage, network, postMessage, third-party scripts) is attacker-influenced unless proven otherwise (see §2.1).

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing or modifying React code:

* MUST follow every **MUST** requirement here.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default APIs and proven libraries over custom security code.
* MUST avoid new risky sinks (raw HTML insertion, direct DOM sinks like `innerHTML`, dynamic code execution, untrusted redirects/navigation, third‑party script injection, unsafe token storage, etc.). ([MDN Web Docs][3])

### 1.2 Passive review mode (always on while editing)

Anywhere in React repo, even without security scan request:

* MUST “notice” spec violations in touched/nearby code.
* SHOULD flag issues as they come up, with brief explanation and safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. App entrypoints, build tooling (Vite/Webpack/CRA/Next), deployment configs, CDN/static hosting config.
2. Secrets & config exposure (env vars, runtime config injection, source maps).
3. Untrusted data rendering (XSS/DOM XSS), especially `dangerouslySetInnerHTML`, markdown/HTML renderers, URL attributes.
4. Direct DOM use and dangerous JS execution (`innerHTML`, `eval`, `new Function`, `document.write`, etc.).
5. Auth & session patterns (token storage, cookies, CSRF interactions, OAuth flows).
6. Network layer (axios/fetch wrappers, dynamic base URLs, credentialed requests, data exfil risks).
7. Navigation & redirects (open redirects, `window.location`, `target=_blank`, `window.open`).
8. Third-party scripts/tags/analytics and integrity controls (CSP, SRI).
9. Service worker/PWA behavior (HTTPS, caching rules, update strategy).
10. Security headers (CSP, clickjacking, nosniff, referrer policy) in app or at edge. ([OWASP Cheat Sheet Series][2])

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Examples:

* URL-derived data: `window.location`, query params, hash fragments, route params.
* Browser storage: `localStorage`, `sessionStorage`, `IndexedDB` (including data app wrote itself; XSS or extensions can tamper with it). ([OWASP Cheat Sheet Series][4])
* Cross-window messaging: `window.postMessage` payloads. ([OWASP Cheat Sheet Series][4])
* Remote APIs, webhooks proxied to client, GraphQL responses, CMS content, feature flag services.
* Persisted user content (profiles, comments, rich text, markdown) rendered in UI.
* Third-party scripts or tag managers (untrusted unless strongly controlled). ([OWASP Cheat Sheet Series][5])

### 2.2 State-changing request (frontend perspective)

Request is state-changing if it can create/update/delete data, change auth/session state, trigger side effects (purchase, email send, webhook), or start privileged actions.

Frontend-specific note:

* `fetch/axios` calls or form submissions often trigger state changes. With cookie-based auth, these calls can be CSRF-relevant (§4 REACT-CSRF-001). ([OWASP Cheat Sheet Series][6])

### 2.3 Required audit finding format

Per issue, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + component/function + line(s)
* Evidence: exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

### 3.1 Production build and configuration hygiene (MUST)

* MUST ship production build (minified, no dev-only overlays/tools, correct mode flags).
* SHOULD treat source maps as sensitive operational artifacts:

  * Either don’t publish them publicly, or publish only where intended (e.g., behind auth or to error-reporting provider). They reveal code structure and internal URLs.

### 3.2 Browser-enforced protections (SHOULD, but baseline expectation for modern apps)

* SHOULD enable clickjacking defenses via `frame-ancestors` (CSP) and/or `X-Frame-Options`, unless embedding is explicit product requirement. ([MDN Web Docs][8])

### 3.3 High-risk features baseline (MUST if used)

* If rendering any user-provided HTML/markdown/rich text: MUST sanitize before insertion and avoid raw DOM sinks. ([OWASP Cheat Sheet Series][9])
* If using service workers / PWA: MUST serve over HTTPS and implement safe caching/update strategy (service workers are powerful request/response proxies). ([MDN Web Docs][10])

---

## 4) Rules (generation + audit)

### REACT-CONFIG-001: Never embed secrets in the client bundle (env vars are public)

Severity: Critical (if secrets exposed)

Required:

* MUST NOT put secrets in React code, `public/` assets, or client-facing build-time environment variables.
* MUST assume attacker can extract any value React app holds at runtime.

Insecure patterns:

* Build-time env vars holding secrets:

  * `process.env.REACT_APP_*` containing private keys or credentials.
  * `import.meta.env.VITE_*` containing secrets.
* Hard-coded secrets in JS/TS, committed `.env`, or secrets in `public/config.json` served to all users.

Detection hints:

* Search for:

  * `REACT_APP_`, `VITE_`, `NEXT_PUBLIC_`, `process.env.`, `import.meta.env.`
  * `apiKey`, `secret`, `token`, `private`, `password`, `client_secret`
* Inspect `public/` for runtime config JSON.

Fix:

* Move secrets server-side (API, BFF, serverless function).
* If browser needs to call third-party APIs, have backend mint short-lived, scoped tokens.

Notes:

* CRA warns not to store secrets: env vars are embedded in build, visible to anyone inspecting files. ([create-react-app.dev][1])
* Vite: variables exposed to client code end up in client bundle and should not contain sensitive info. ([vitejs][11])

---

### REACT-XSS-001: Do not use `dangerouslySetInnerHTML` with untrusted content (sanitize or avoid)

Severity: High (only if you can prove attacker-controlled HTML reaches it)

Required:

* MUST avoid `dangerouslySetInnerHTML` unless absolutely necessary.
* If unavoidable:

  * MUST sanitize untrusted HTML with proven sanitizer (e.g., DOMPurify) and allowlist-oriented config.
  * MUST keep sanitization logic centralized and heavily reviewed.
  * SHOULD add CSP and consider Trusted Types (see REACT-TT-001).

Insecure patterns:

* `<div dangerouslySetInnerHTML={{ __html: userHtml }} />` where `userHtml` is from API/URL/storage.
* “Sanitization” via regexes, ad-hoc stripping, or incomplete allowlists.

Detection hints:

* Grep: `dangerouslySetInnerHTML`, `__html:`
* Trace HTML string origin (API/CMS/URL/localStorage).

Fix:

* Replace with safe rendering:

  * Render structured data as React elements/components, not HTML strings.
  * If rich text required, sanitize with DOMPurify (or equivalent) and render sanitized output.

Notes:

* React warns `dangerouslySetInnerHTML` is dangerous and can introduce XSS if misused. ([React][12])
* OWASP names React’s `dangerouslySetInnerHTML` without sanitization as common framework “escape hatch” pitfall. ([OWASP Cheat Sheet Series][9])
* DOMPurify describes itself as XSS sanitizer for HTML/SVG/MathML. ([GitHub][13])

---

### REACT-XSS-002: Rely on React’s escaping-by-default behavior; do not bypass it

Severity: High (when bypassed)

Required:

* MUST render untrusted strings via normal JSX interpolation (`{value}`) and React props (escaped by default).
* MUST NOT build HTML strings from untrusted data and inject them into DOM by any means.
* SHOULD treat any “escape hatch” as high risk needing review.

Insecure patterns:

* Untrusted text turned into HTML and injected:

  * `element.innerHTML = userValue`
  * `document.write(userValue)`
  * `insertAdjacentHTML(..., userValue)`

Detection hints:

* Grep for DOM sinks: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `DOMParser`, `createContextualFragment`.

Fix:

* If HTML truly needed, sanitize and apply REACT-XSS-001 and REACT-TT-001.

Notes:

* React docs (JSX): React DOM escapes values embedded in JSX before rendering, helping prevent injection attacks. ([React][14])

---

### REACT-DOM-001: Avoid DOM XSS injection sinks in React code (use safe alternatives)

Severity: High

Required:

* MUST avoid direct DOM injection sinks, even outside React rendering, unless strongly controlled.
* If DOM sink required:

  * MUST ensure inputs are trusted/validated/sanitized.
  * SHOULD enforce Trusted Types (REACT-TT-001).

Insecure patterns:

* `someEl.innerHTML = untrusted`
* `document.write(untrusted)`
* `new DOMParser().parseFromString(untrusted, 'text/html')` followed by insertion

Detection hints:

* Grep for: `innerHTML`, `outerHTML`, `document.write`, `DOMParser`, `Range().createContextualFragment`, `insertAdjacentHTML`

Fix:

* Prefer:

  * `textContent` for text insertion.
  * React rendering over manual DOM manipulation.
  * Vetted sanitizer for any required HTML parsing.

Notes:

* Trusted Types docs define HTML sinks like `Element.innerHTML` and `document.write()` as injection sinks that can execute script given attacker-controlled input. ([MDN Web Docs][3])
* OWASP HTML5 guidance: assign untrusted data with `textContent`, not `innerHTML`. ([OWASP Cheat Sheet Series][4])

---

### REACT-URL-001: Validate and constrain untrusted URLs used in `href`, `src`, navigation, and redirects

Severity: High only when you can prove they are attacker controlled

Required:

* MUST treat any URL derived from untrusted input as dangerous.
* MUST allowlist schemes and (when applicable) hosts:

  * Typically allow only `https:` (maybe `http:` for localhost/dev) and relative URLs for in-app navigation.
  * MUST explicitly block `javascript:` and dangerous `data:` uses unless specialized validation and clear use case exist.
* SHOULD prefer same-site relative paths (e.g., `/settings`) over absolute URLs.
* MUST validate “returnTo/next/redirect” parameters (see REACT-REDIRECT-001).

Insecure patterns:

* `<img src={userProvidedUrl}>...` (usable for tracking / data exfil; also risky for scripts/iframes)
* `window.location = next`
* `navigate(next)` where `next` comes from query params without validation

Detection hints:

* Search for:

  * `href={`, `src={`, `window.location`, `location.href`, `window.open`, `navigate(`, `redirectTo`, `returnTo`, `next=`
* Track whether value derives from URL/query/storage/API.

Fix:

* Add shared `safeUrl()` utility:

  * Parse with `new URL(value, base)`
  * Enforce scheme allowlist and host allowlist (or enforce same-origin)
* Fall back to safe default when validation fails.

Notes:

* OWASP notes React’s `dangerouslySetInnerHTML` risk and states React cannot safely handle `javascript:` or `data:` URLs without specialized validation. ([OWASP Cheat Sheet Series][9])

---

### REACT-MARKUP-001: Markdown / rich text rendering must be configured safely

Severity: Medium

Required:

* MUST assume markdown/rich text from users or CMS can be attacker-controlled.
* MUST NOT render raw HTML unless sanitized.
* SHOULD prefer markdown renderers that:

  * Do not allow raw HTML by default, or
  * Can be configured to disallow raw HTML, or
  * Sanitize HTML output before rendering.

Insecure patterns:

* Markdown rendering with “raw HTML passthrough” enabled (e.g., options/plugins allowing HTML).
* Rendering user-provided SVG/MathML/HTML inline without sanitization.

Detection hints:

* Search for common libraries and risky options:

  * `marked`, `markdown-it`, `react-markdown`, `rehype-raw`, `sanitize: false`, `allowDangerousHtml`, etc.
* Look for `dangerouslySetInnerHTML` used with “markdown output”.

Fix:

* Disable raw HTML passthrough.
* Sanitize output with proven sanitizer (e.g., DOMPurify) before rendering.

Notes:

* OWASP XSS guidance: framework escape hatches need output encoding and/or HTML sanitization. ([OWASP Cheat Sheet Series][9])

---

### REACT-TT-001: Use Trusted Types (with CSP) to harden DOM XSS sinks where feasible

Severity: Low

Required:

* SHOULD consider Trusted Types in report-only mode first; enforce once violations are fixed.
* SHOULD centralize Trusted Types policies and treat them as high-risk code needing review.
* MUST NOT create permissive policies that “pass through” untrusted strings.

Insecure patterns:

* Trusted Types policy returning raw string without sanitization for HTML sinks.
* Many policies scattered across codebase (hard to audit).

Detection hints:

* Search for:

  * `trustedTypes.createPolicy`
  * CSP directives: `require-trusted-types-for`, `trusted-types`
* Search for remaining DOM sinks (REACT-DOM-001).

Fix:

* Use few, tightly scoped policies:

  * HTML policy uses sanitizer (DOMPurify or equivalent).
  * Script URL policy uses strict allowlists.

Notes:

* MDN: Trusted Types ensure input is transformed (commonly sanitized) before reaching injection sinks. Highlights HTML sinks (`innerHTML`, `document.write`) and JS URL sinks (`script.src`). ([MDN Web Docs][3])
* W3C Trusted Types spec: reduces DOM XSS risk by locking sinks to typed values created by reviewed policies. ([W3C][15])

---

### REACT-CSP-001: Deploy and maintain a CSP as defense-in-depth (especially when rendering untrusted content)

Severity: Medium to High

Required:

* SHOULD deploy CSP in production. MUST for apps that render untrusted content or integrate third-party scripts.
* SHOULD avoid `unsafe-inline` and `unsafe-eval` when possible.
* SHOULD use CSP nonces/hashes for inline scripts if needed; keep policy realistic.
* SHOULD use CSP to require/encourage SRI where appropriate.

Insecure patterns:

* No CSP at all on app shell (SPA entry HTML).
* CSP relying broadly on `unsafe-inline`/`unsafe-eval` without justification.
* `script-src *` or overly broad sources.

Detection hints:

* Look for CSP config:

  * Server/CDN config, headers in `index.html` responses, or framework config.
* If absent in repo, mark “verify at edge”.

Fix:

* Add CSP via HTTP response headers (preferred).
* Start report-only to reduce breakage, then enforce.

Notes:

* OWASP: CSP is “defense in depth” against XSS. Can help enforce SRI even on static sites, but should not be the only defense. ([OWASP Cheat Sheet Series][2])

---

### REACT-SRI-001: Use Subresource Integrity (SRI) for third-party scripts and styles (or self-host)

Severity: Low

Required:

* MUST treat third-party JS as arbitrary code running in your origin.
* If loading from CDN or third party:

  * SHOULD use SRI (`integrity=...`) and `crossorigin` where applicable.
  * SHOULD pin exact versions (avoid “latest” URLs).
  * SHOULD prefer self-hosting for critical code.

Insecure patterns:

* `<script src="https://cdn.example.com/lib/latest.js"></script>` with no integrity.
* Tag managers dynamically loading arbitrary scripts without governance.

Detection hints:

* Search in `public/index.html`, templates, or SSR wrappers for:

  * `<script src=`, `<link rel="stylesheet" href=`
  * Tag manager snippets (GTM, Segment, etc.)
* Find scripts loaded dynamically in runtime JS.

Fix:

* Add SRI hashes for stable third-party assets, or self-host.
* Apply governance controls for tag managers (see REACT-3P-001).

Notes:

* MDN: SRI lets browsers verify fetched resources (e.g., from CDN) weren’t manipulated, by checking cryptographic hash. ([MDN Web Docs][7])

---

### REACT-3P-001: Third-party JavaScript and tag managers must be minimized and governed

Severity: High

Required:

* MUST minimize third-party scripts; treat each as supply-chain risk.
* MUST know exactly what third-party JS executes in your origin and why.
* SHOULD apply governance:

  * Review and pin versions (or mirror in-house).
  * Restrict data access (data-layer approach).
  * Use SRI and CSP; consider sandboxing untrusted UI in iframes where possible.

Insecure patterns:

* Unreviewed analytics/ads scripts with full access to DOM, cookies, storage, user data.
* Tag managers non-engineering roles can change with no change control.

Detection hints:

* Search for common vendor snippets in HTML/JS:

  * GTM, Segment, Hotjar, FullStory, etc.
* Look for dynamic script insertion:

  * `document.createElement('script')`, `.src = ...`, `.appendChild(script)`

Notes:

* OWASP: compromised third-party JS server can inject malicious JS. Risks include arbitrary code execution and leaking sensitive info to third parties. ([OWASP Cheat Sheet Series][5])

---

### REACT-AUTH-001: Token and session handling must be resilient to XSS (avoid sensitive storage in Web Storage)

Severity: Medium

Required:

* SHOULD avoid storing session identifiers or long-lived tokens in `localStorage` (or any Web Storage): XSS can exfiltrate them.
* If tokens must exist client-side:

  * SHOULD prefer in-memory storage with short lifetimes and refresh mechanisms.
  * MUST scope and rotate tokens; avoid long-lived bearer tokens in persistent storage.
* SHOULD prefer HTTPOnly cookies for session tokens when possible (requires CSRF strategy: see REACT-CSRF-001).

Insecure patterns:

* `localStorage.setItem('token', ...)` / `sessionStorage.setItem('token', ...)` for auth tokens.
* Refresh tokens persisted in `localStorage`.
* Treating Web Storage data as trusted.

Detection hints:

* Grep for: `localStorage.`, `sessionStorage.`, `setItem(`, `getItem(`, `token`, `jwt`, `refresh`
* Search auth code for “remember me” storing tokens persistently.

Notes:

* OWASP HTML5 guidance: keep sensitive info and session identifiers out of local storage. One XSS can steal all Web Storage data. ([OWASP Cheat Sheet Series][4])
* OAuth browser-based apps guidance: tokens in persistent browser storage like localStorage can be reachable by malicious JS (e.g., via XSS). ([IETF Datatracker][16])

---

### REACT-CSRF-001: Cookie-authenticated, state-changing requests MUST be CSRF-protected

Severity: High

NOTE: If app does not use cookie-based auth (e.g., uses Authentication header), CSRF is not a concern.

Required:

* If app relies on cookies for authentication:

  * MUST protect state-changing requests (POST/PUT/PATCH/DELETE) against CSRF.
  * SHOULD include CSRF token mechanism (synchronizer token or double-submit cookie) or other robust pattern fitting backend.
  * SHOULD use SameSite cookies as defense-in-depth, not sole defense.

Insecure patterns:

* `fetch('/api/transfer', { method: 'POST', credentials: 'include' })` with no CSRF token/header, relying only on cookies.
* GET for state-changing operations.

Detection hints:

* Enumerate state-changing network calls and check:

  * Is `credentials: 'include'` or `withCredentials: true` used?
  * Is a CSRF token header included (e.g., `X-CSRF-Token`)?
* Search for “csrf” utilities; treat absence as suspicious.

Fix:

* Add CSRF token flow:

  * Fetch token from safe endpoint, attach to state-changing requests.
  * Validate server-side.
* Keep SameSite cookies and Origin/Referer validation as defense-in-depth.

Notes:

* OWASP CSRF guidance: SameSite (Lax/Strict/None) is defense-in-depth, and Lax is often the usability/security balance. SameSite is not a complete substitute for CSRF protections. ([OWASP Cheat Sheet Series][6])

---

### REACT-AUTHZ-001: Do not rely on frontend-only authorization

Severity: High (only if used as primary protection)

Required:

* MUST treat all frontend authorization checks as UX only.
* MUST enforce authorization on server for any protected resource or action.

Insecure patterns:

* “Protected” actions hidden in UI but callable by API without server checks.
* Client checks like `if (user.isAdmin) { showAdminPanel(); }` with no server-side enforcement.

Detection hints:

* Find UI gating around sensitive actions; verify server endpoints enforce authorization.
* In frontend-only audit, report “client checks are not security; verify backend”.

---

### REACT-NET-001: Prevent data exfiltration and credential leakage via dynamic outbound requests

Severity: Medium to High

Required:

* MUST avoid authenticated requests to attacker-controlled origins.
* SHOULD avoid letting user input control request destination (scheme/host/port).
* SHOULD centralize network clients (fetch/axios) with:

  * fixed `baseURL` (or strict allowlist),
  * strict redirect handling,
  * explicit `credentials` usage.

Insecure patterns:

* `fetch(userProvidedUrl, { credentials: 'include' })`
* `axios.create({ baseURL: userProvidedBase })`
* Client “URL fetch/preview” features hitting arbitrary domains with sensitive headers.

Detection hints:

* Search for `fetch(` / `axios(` where first argument or `baseURL` derives from:

  * query params, localStorage, API responses, postMessage
* Search for `credentials: 'include'`, `withCredentials: true`.

Fix:

* Enforce destination allowlists; disallow cross-origin requests unless explicitly required.
* Strip credentials/Authorization headers for any non-allowlisted destination.

Notes:

* Even where browser limits some cross-origin behavior, leaking tokens/headers to untrusted endpoints stays a common failure mode.

---

### REACT-REDIRECT-001: Prevent open redirects and untrusted navigation

Severity: Medium

Required:

* MUST validate redirect/navigation targets derived from untrusted input (`next`, `returnTo`, `redirect`).
* SHOULD only allow same-site relative paths, or strict allowlist of trusted origins for absolute URLs.

Insecure patterns:

* `window.location.href = new URLSearchParams(location.search).get('next')`
* `navigate(next)` where `next` comes from query params.

Detection hints:

* Search for: `next`, `returnTo`, `redirect`, `window.location`, `navigate(`
* Trace redirect target origin.

Fix:

* Only allow relative paths (`/^\/[^\s]*$/`) or allowlisted origins.
* Fall back to safe default (e.g., `/`) when invalid.

Notes:

* Open redirects are common in phishing and can undermine SSO/OAuth flows.

---

### REACT-SW-001: Service workers are high-privilege; require HTTPS and safe caching/update rules

Severity: Medium

Required:

* MUST serve service workers over HTTPS (except `localhost` dev); deploy only in secure contexts.
* MUST avoid caching sensitive authenticated API responses unless explicitly designed and threat-modeled.
* SHOULD use safe update strategy (prompt reload, versioned caches, remove old caches on activate).

Insecure patterns:

* Service worker on authenticated app caching “everything” indiscriminately.
* Long-lived caches holding PII or user-specific content shared across accounts.

Detection hints:

* Search for:

  * `navigator.serviceWorker.register`
  * `workbox`, `precacheAndRoute`, custom `fetch` handlers
* Inspect caching patterns (`caches.open`, `cache.put`, `respondWith`).

Fix:

* Restrict caching to static assets only (JS/CSS/images) unless you have designed offline model.
* Make cache keys user-scoped if user-specific data must be cached.
* Provide clear update mechanism.

Notes:

* MDN: service workers require HTTPS for security reasons and act like proxy for requests/responses. ([MDN Web Docs][10])
* “Secure contexts” stop MITM attackers from reaching powerful APIs. Service workers are one such feature. ([MDN Web Docs][18])

---

### REACT-HEADERS-001: Ensure essential security headers are set for the React app shell (app or edge)

Severity: Medium

Required (typical SPA served from an origin):

* SHOULD set:

  * CSP (`Content-Security-Policy`)
  * `X-Content-Type-Options: nosniff`
  * Clickjacking protection (`frame-ancestors` in CSP and/or `X-Frame-Options`)
  * `Referrer-Policy`
  * `Permissions-Policy` as appropriate
* MUST ensure these are set somewhere (CDN/edge/server), even if not in repo.

Insecure patterns:

* No security headers anywhere (app or edge).
* CSP missing on apps that render untrusted content or use third-party scripts.

Detection hints:

* Check server/CDN config in repo (nginx, Cloudflare, Vercel config, etc.).
* If absent, flag “verify at runtime/edge”.

Fix:

* Set headers centrally at edge.

Notes:

* MDN clickjacking guidance covers defenses including `X-Frame-Options` and CSP `frame-ancestors`. ([MDN Web Docs][8])

---

### REACT-POSTMSG-001: `postMessage` must validate origin and treat payload as untrusted data

Severity: Medium to High (depends on what messages can do)

Required:

* MUST specify exact `targetOrigin` when sending messages (not `*`) unless strict reason exists.
* MUST validate `event.origin` on receipt and validate message shape.
* MUST NOT evaluate message data as code or insert it into DOM as HTML.

Insecure patterns:

* `window.postMessage(data, '*')` to unknown targets.
* Receiving:

  * `window.addEventListener('message', (e) => { eval(e.data) })`
  * `element.innerHTML = e.data`

Detection hints:

* Search: `postMessage(`, `addEventListener('message'`
* Check for origin checks and safe handling.

Fix:

* Add strict origin allowlists and schema validation (e.g., zod).
* Treat message payload strictly as data; render safely via React.

Notes:

* OWASP HTML5 guidance: specify expected origin for `postMessage`, check sender origin, validate data, avoid eval/innerHTML with message content. ([OWASP Cheat Sheet Series][4])

---

### REACT-FILE-001: File uploads and previews must not create client-side active content vulnerabilities

Severity: Medium (can be High if stored-XSS possible)

Required:

* MUST treat user-uploaded files and previews as potentially malicious.
* MUST NOT render uploaded HTML/SVG/other active content inline unless sanitized and explicitly required.
* SHOULD validate file types client-side for UX, but MUST rely on server-side validation for security.

Insecure patterns:

* Rendering user-uploaded HTML as content.
* Inline rendering of untrusted SVG/HTML via `dangerouslySetInnerHTML` or `<iframe srcdoc=...>` without sanitization.

Detection hints:

* Search for upload components and preview logic:

  * `input type="file"`, `FileReader`, `URL.createObjectURL`, `<iframe>`, `<object>`, `<embed>`.
* Trace where uploaded content is later displayed.

Fix:

* Restrict accepted types, sanitize where needed, prefer download/attachment flows for risky types.
* Ensure server enforces real policy (type checking, renaming, scanning, storing outside webroot).

Notes:

* OWASP file upload guidance: allowlist extensions, validate file type, generate filenames, limit size, store outside webroot, and consider “client-side active content (XSS, CSRF, etc.)” when files are publicly retrievable. ([OWASP Cheat Sheet Series][19])

---

### REACT-SUPPLY-001: Dependency and supply-chain hygiene (frontend + build tooling)

Severity: Low

Required:

* MUST use lockfile and enforce reproducible installs in CI.
* SHOULD audit dependencies regularly and respond fast to advisories for:

  * React, react-dom, router libs, build tooling (Vite/Webpack), sanitizers, auth libs, etc.
* SHOULD reduce exposure to install-time script attacks and typosquatting.

Audit focus:

* CI should use `npm ci` (or Yarn frozen lockfile / pnpm equivalent) to prevent drift.
* Use vulnerability scanning (`npm audit`, GitHub Dependabot/alerts, etc.).

Insecure patterns:

* No lockfile, or lockfile ignored in CI.
* `npm install` in CI producing non-reproducible builds.
* Unpinned or unreviewed high-risk deps; sudden major updates without review.
* Blindly running install scripts from third-party packages.

Detection hints:

* Check for lockfiles: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`.
* Check CI scripts for `npm install` vs `npm ci`.
* Search for `postinstall` scripts and suspicious build steps.

Notes:

* npm docs: `npm audit` submits project dependency tree to registry and returns known-vulnerability report. Can optionally apply remediations via `npm audit fix`. Some vulns need manual review. ([npm Docs][20])
* npm docs: `npm ci` targets automated/CI environments, requires existing lockfile, fails if `package.json` and lockfile do not match. ([npm Docs][21])
* OWASP NPM security guidance: enforce lockfile, use `npm ci` / `yarn install --frozen-lockfile` to abort on inconsistencies. Flags install-time script risk; `--ignore-scripts` reduces attack surface. ([OWASP Cheat Sheet Series][22])

---

## 5) Practical scanning heuristics (how to “hunt”)

High-signal patterns for active scans: each §4 rule's detection hints, plus dangerous JS execution:

* `eval(`, `new Function(`, `setTimeout("`, `setInterval("`

Always try to confirm:

* data origin (untrusted vs trusted)
* sink type (React escape hatch vs DOM sink vs navigation vs storage)
* protective controls present (sanitization, allowlists, CSP/Trusted Types, CSRF tokens, headers, governance)

---

## 6) Sources (accessed 2026-01-26)

Primary React documentation:

* React 19 stable announcement — `https://react.dev/blog/2024/12/05/react-19` ([React][23])
* React DOM docs: `dangerouslySetInnerHTML` warning — `https://react.dev/reference/react-dom/components/common#dangerouslysetting-the-inner-html` ([React][12])
* React (legacy) JSX escaping statement — `https://legacy.reactjs.org/docs/introducing-jsx.html` ([React][14])

OWASP Cheat Sheet Series:

* Cross Site Scripting Prevention (framework escape hatches; React `dangerouslySetInnerHTML`; URL validation notes) — `https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][9])
* Content Security Policy — `https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][2])
* Cross-Site Request Forgery Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][6])
* HTML5 Security (Web Storage, postMessage, tabnabbing, sandboxed frames) — `https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][4])
* Third Party JavaScript Management — `https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][5])
* File Upload — `https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][19])
* NPM Security best practices — `https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][22])

Browser / platform references (MDN, W3C):

* Trusted Types API — `https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API` ([MDN Web Docs][3])
* W3C Trusted Types spec — `https://www.w3.org/TR/trusted-types/` ([W3C][15])
* Subresource Integrity — `https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity` ([MDN Web Docs][7])
* Clickjacking defenses overview — `https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking` ([MDN Web Docs][8])
* Using Service Workers (HTTPS requirement; proxy-like behavior) — `https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers` ([MDN Web Docs][10])
* Secure contexts (powerful APIs restricted to HTTPS) — `https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts` ([MDN Web Docs][18])
* Link `rel` values (noopener/noreferrer) — `https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel` ([MDN Web Docs][17])

Build tooling / env exposure references:

* Create React App env variables warning — `https://create-react-app.dev/docs/adding-custom-environment-variables/` ([create-react-app.dev][1])
* Vite env variables security notes — `https://vite.dev/guide/env-and-mode` ([vitejs][11])

Auth/token storage guidance:

* OAuth 2.0 for Browser-Based Apps (token storage discussion) — `https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps` ([IETF Datatracker][16])

Dependency tooling references:

* npm audit docs — `https://docs.npmjs.com/cli/v10/commands/npm-audit/` ([npm Docs][20])
* npm ci docs — `https://docs.npmjs.com/cli/v10/commands/npm-ci/` ([npm Docs][21])

Sanitizer reference:

* DOMPurify — `https://github.com/cure53/DOMPurify` ([GitHub][13])

[1]: https://create-react-app.dev/docs/adding-custom-environment-variables/ "Adding Custom Environment Variables | Create React App"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html "Content Security Policy - OWASP Cheat Sheet Series"
[3]: https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API "Trusted Types API - Web APIs | MDN"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html "HTML5 Security - OWASP Cheat Sheet Series"
[5]: https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html "Third Party Javascript Management - OWASP Cheat Sheet Series"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "Cross-Site Request Forgery Prevention - OWASP Cheat Sheet Series"
[7]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity "Subresource Integrity - Security | MDN"
[8]: https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking "Clickjacking - Security | MDN"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "Cross Site Scripting Prevention - OWASP Cheat Sheet Series"
[10]: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers "Using Service Workers - Web APIs | MDN"
[11]: https://vite.dev/guide/env-and-mode "Env Variables and Modes | Vite"
[12]: https://react.dev/reference/react-dom/components/common "Common components (e.g. <div>) – React"
[13]: https://github.com/cure53/DOMPurify "GitHub - cure53/DOMPurify: DOMPurify - a DOM-only, super-fast, uber-tolerant XSS sanitizer for HTML, MathML and SVG. DOMPurify works with a secure default, but offers a lot of configurability and hooks. Demo:"
[14]: https://legacy.reactjs.org/docs/introducing-jsx.html "Introducing JSX – React"
[15]: https://www.w3.org/TR/trusted-types/ "Trusted Types"
[16]: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps "
            
                draft-ietf-oauth-browser-based-apps-26
            
        "
[17]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel "HTML attribute: rel - HTML | MDN"
[18]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts "Secure contexts - Security | MDN"
[19]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "File Upload - OWASP Cheat Sheet Series"
[20]: https://docs.npmjs.com/cli/v10/commands/npm-audit "npm-audit | npm Docs"
[21]: https://docs.npmjs.com/cli/v10/commands/npm-ci "npm-ci | npm Docs"
[22]: https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html "NPM Security - OWASP Cheat Sheet Series"
[23]: https://react.dev/blog/2024/12/05/react-19 "React v19 – React"
