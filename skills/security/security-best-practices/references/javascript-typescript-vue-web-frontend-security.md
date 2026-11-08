# Vue.js Web Security Spec (Vue 3.x, TypeScript/JavaScript, common tooling: Vite)

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session cookies, auth tokens).
* MUST NOT “fix” security by disabling protections (e.g., weakening CSP, enabling unsafe template compilation, using `v-html` as shortcut, bypassing backend auth, or “just store the token in localStorage”).
* MUST give **evidence-based findings** in audits: cite file paths, code snippets and configuration values justifying the claim.
* MUST treat uncertainty honestly: if protection might exist at edge (CDN, reverse proxy, WAF, server headers), report “not visible in repo; verify runtime/infra config”.
* MUST remember frontend trust model: **any code shipped to browsers is attacker-readable and attacker-modifiable**. Secrets and “security enforcement” cannot rely on frontend-only logic.

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing new Vue code or modifying existing code:

* MUST follow every **MUST** requirement in this spec.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default framework features and proven libraries over custom security code.
* MUST avoid introducing new risky sinks (runtime template compilation, `v-html` / `innerHTML`, unsafe URL navigation, dynamic script injection, etc.). ([Vue.js][1])

### 1.2 Passive review mode (always on while editing)

While working anywhere in Vue repo (even if user did not ask for security scan):

* MUST “notice” spec violations in touched/nearby code.
* SHOULD mention issues as they come up, with brief explanation and safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. Build/deploy entrypoints and hosting config (Docker, CI, static hosting, SSR server).
2. Secrets exposure (env usage, `.env*`, hard-coded keys). ([vitejs][2])
3. XSS surface: templates, `v-html` / `innerHTML`, URL/style injection, DOM APIs. ([Vue.js][1])
4. Auth/session handling in browser (token storage, credentialed requests, CSRF integration). ([Vue.js][1])
5. Routing/navigation (open redirects, “return_to/next”, unsafe external navigation). ([Vue.js][1])
6. Third-party scripts and content (CDN assets, analytics, widgets, iframes). ([Vue.js][1])
7. Security headers and browser hardening expectations (CSP, clickjacking). ([Vue.js][1])
8. SSR-specific concerns (state serialization, template boundaries) when applicable. ([Vue.js][1])

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Untrusted input in Vue app includes (non-exhaustive):

* Anything from APIs: `fetch`, `axios`, GraphQL responses, webhooks, third-party SDKs.
* Router-controlled data: `route.params`, `route.query`, `route.hash`, and anything derived from `window.location`.
* User-controlled persisted content: DB-backed content shown in UI (comments, profiles, CMS content).
* Browser-controlled storage: `localStorage`, `sessionStorage`, `IndexedDB`.
* Cross-window messages: `postMessage` inputs.
* Anything attacker can influence through DOM clobbering or injected HTML (especially if Vue mounts onto non-sterile DOM). ([Vue.js][1])

### 2.2 State-changing action (frontend perspective)

Action is state-changing if it can:

* Create/update/delete data via API calls.
* Change authentication/session state (login, logout, refresh token).
* Trigger privileged operations (payments, admin actions).
* Cause side effects (sending emails, triggering webhooks, changing account settings).

### 2.3 Required audit finding format

For each issue, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + component/function + line(s)
* Evidence: the exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

* MUST ship **production build** (not development build or dev server). ([Vue.js][3])
* MUST NOT ship secrets in frontend bundles; treat all client-exposed env variables as public. ([vitejs][2])
* MUST NOT render non-trusted templates or allow user-provided Vue templates (equivalent to arbitrary JS execution). ([Vue.js][1])
* SHOULD avoid raw HTML injection (`v-html`, `innerHTML`) unless content is trusted or strongly sandboxed. ([Vue.js][1])
* SHOULD deploy baseline security headers (especially CSP and clickjacking defenses) at server/CDN layer. ([OWASP Cheat Sheet Series][4])
* SHOULD use safe auth patterns (prefer HttpOnly cookies for session tokens; coordinate with backend on CSRF). ([Vue.js][1])

---

## 4) Rules (generation + audit)

### VUE-DEPLOY-001: Do not run dev/preview servers in production

Severity: High

Required:

* MUST NOT deploy Vite/Vue dev server (`vite`, `npm run dev`, HMR) as production server.
* MUST NOT use `vite preview` as production server. ([vitejs][5])
* MUST build (`vite build`) and serve built assets from production-grade static server/CDN, or production SSR server if doing SSR. ([vitejs][6])

Insecure patterns:

* Docker/Procfile/systemd running `vite`, `npm run dev`, or `vite preview` as production entrypoint.
* Publicly exposed HMR endpoints.

Detection hints:

* Search: `vite`, `npm run dev`, `pnpm dev`, `yarn dev`, `vite preview`, `vue-cli-service serve`.
* Check Docker `CMD`, `ENTRYPOINT`, CI deploy scripts, platform config.

Fix:

* Build artifacts with `vite build`.
* Serve `dist/` with hardened hosting (CDN/static server) or integrate into backend server as static assets.

Notes:

* Dev/preview servers are fine locally; flag only if one is production entrypoint.

---

### VUE-DEPLOY-002: Use Vue production builds and keep devtools off in production

Severity: Medium (High if production devtools/debug hooks enabled)

Required:

* If loading Vue from CDN/self-host without bundler, MUST use `.prod.js` builds in production. ([Vue.js][3])
* SHOULD ensure production bundles do not enable Vue devtools. SHOULD not intentionally enable production devtools flags. ([Vue.js][7])

Insecure patterns:

* Production includes development build artifacts.
* Explicitly enabling production devtools/diagnostic hooks.

Detection hints:

* Search HTML for `vue.global.js` / non-`.prod.js` variants when using CDN builds.
* Search build config for Vue feature flags like `__VUE_PROD_DEVTOOLS__`. ([Vue.js][7])

Fix:

* Switch to production build artifacts; configure compile-time flags for production.

---

### VUE-SECRETS-001: Never ship secrets in frontend code or env variables

Severity: High (Critical if real credentials are exposed)

Required:

* MUST treat all frontend code and configuration as public.
* MUST NOT embed secrets in:

  * source code
  * `.env` files committed to repo
  * `import.meta.env.*` variables included in bundle
* MUST assume any env var ending up in client bundle is attacker-readable. ([vitejs][2])

Insecure patterns:

* `VITE_API_KEY=...` containing true secret (not just public identifier).
* Hard-coded API keys, private tokens, service credentials, signing keys in JS/TS.

Detection hints:

* Search: `VITE_`, `import.meta.env`, `.env`, `.env.production`, `.env.*.local`.
* Grep for `API_KEY`, `SECRET`, `TOKEN`, `PRIVATE_KEY`, `BEGIN`, `sk-`, `AKIA`, etc.

Fix:

* Move secrets to backend/edge functions.
* Use backend-minted short-lived tokens for browser when needed.

Notes:

* Vite warns `.env.*.local` should be gitignored and `VITE_*` vars end up in client bundle, so they must not contain sensitive info. ([vitejs][2])

---

### VUE-SECRETS-002: Do not broaden Vite env exposure

Severity: High

Required:

* MUST NOT configure Vite to expose all environment variables to client.
* SHOULD keep `envPrefix` strict and explicit.

Insecure patterns:

* Setting `envPrefix` to overly broad values (or `''`) to “make env vars work”.
* Custom scripts injecting server secrets into HTML global variables at build time.

Detection hints:

* Check `vite.config.*` for `envPrefix`.
* Look for `define: { 'process.env': ... }` or manual injection into `window.__CONFIG__`.

Fix:

* Keep secrets server-side.
* Expose only non-sensitive values intentionally designed to be public.

Notes:

* Vite docs: only prefixed variables are exposed, and exposed variables land in client bundle. ([vitejs][2])

---

### VUE-XSS-001: Prefer Vue’s default escaping; avoid raw HTML injection

Severity: High

Required:

* MUST rely on Vue’s automatic escaping for text interpolation and attribute binding where possible. ([Vue.js][1])
* MUST NOT render user-provided HTML via:

  * `v-html`
  * `innerHTML` in render functions / JSX
  * direct DOM APIs (`element.innerHTML`, `insertAdjacentHTML`)
    unless HTML is trusted or robustly sanitized and risk is explicitly accepted. ([Vue.js][1])

Insecure patterns:

* `<div v-html="userProvidedHtml"></div>`
* `h('div', { innerHTML: userProvidedHtml })`
* `<div innerHTML={userProvidedHtml}></div>`
* `el.innerHTML = untrusted`

Detection hints:

* Search: `v-html`, `innerHTML`, `insertAdjacentHTML`, `DOMParser`, `document.write`.

Fix:

* Render untrusted content as text (interpolation).
* If HTML rendering required (e.g., Markdown), sanitize with well-maintained HTML sanitizer and add defense-in-depth (CSP, Trusted Types). ([Vue.js][1])

Notes:

* Vue docs warn user-provided HTML is never “100% safe” unless sandboxed or strictly self-only exposure. ([Vue.js][1])

---

### VUE-XSS-002: Never use non-trusted templates (client-side template/code injection)

Severity: Critical

Required:

* MUST NOT use non-trusted content as Vue component template.
* MUST treat “user can write a Vue template” as “user can execute arbitrary JavaScript in your app”, and potentially in SSR contexts too. ([Vue.js][1])
* SHOULD prefer runtime-only build (templates compiled at build time) and avoid shipping runtime compiler unless need is vetted.

Insecure patterns:

* `createApp({ template: '<div>' + userProvidedString + '</div>' }).mount(...)`
* Storing templates in DB and compiling/rendering them in browser.
* Admin/CMS features that accept Vue template syntax.

Detection hints:

* Search: `template:` where value is not static string.
* Search: `@vue/compiler-dom`, `compile(`, “runtime compiler” build selection, dynamic SFC compilation.
* Search for “template editor”, “custom template”, “theme HTML” features.

Fix:

* Treat templates as code: keep them developer-controlled.
* If end-user customization required, use safe format (restricted Markdown subset) rendered via sanitizer, or isolate in sandboxed iframe.

---

### VUE-XSS-003: Do not mount Vue onto DOM that may contain user-provided server-rendered HTML

Severity: Medium

Required:

* MUST NOT mount Vue on nodes that may contain server-rendered and user-provided content (attacker-controlled HTML “safe as HTML” may become unsafe as Vue template). ([Vue.js][1])
* SHOULD mount Vue into “sterile” root element and render app DOM from Vue-controlled templates/components.

Insecure patterns:

* Server renders user content into `#app`, then Vue mounts on `#app` and compiles/interprets that DOM as template.
* “Sprinkling Vue” on large server-rendered pages with user-generated content.

Detection hints:

* Check server templates (e.g., Rails/Django/Express templates) for user HTML inserted inside Vue mount root.
* Look for `mount('#app')` where `#app` includes server-rendered UGC.

Fix:

* Move user-rendered HTML outside Vue mount root, or render it safely (text/sanitized HTML) from Vue components.

---

### VUE-XSS-004: Prevent URL injection in bindings and navigations

Severity: High

Required:

* MUST validate/sanitize any user-influenced URL before binding to navigation sinks (`href`, `src`, `action`, `window.location`, `window.open`, router navigation to external).
* MUST prevent `javascript:` URL execution in bindings like `<a :href="userProvidedUrl">`. ([Vue.js][1])
* SHOULD validate protocol and destination (allowlist `https:` and expected hosts; allow `mailto:`/`tel:` only if intended).

Insecure patterns:

* `<iframe :src="userProvidedUrl">`
* `window.location = route.query.next`
* `window.open(userProvidedUrl)`

Detection hints:

* Search: `:href=`, `:src=`, `window.location`, `location.href`, `window.open`, `router.push(` with untrusted input.
* Look for `next`, `return_to`, `redirect` query params.

Fix:

* Prefer internal navigation via route names/paths you control.
* For external URLs: parse with `new URL(...)`, allowlist protocol/host, reject `javascript:` and other dangerous schemes.
* Sanitize and validate on backend before storing user URLs (Vue docs recommend backend sanitization). ([Vue.js][1])

---

### VUE-XSS-005: Prevent style/CSS injection and UI redress

Severity: Low

Required:

* MUST NOT bind attacker-controlled CSS strings broadly (e.g., `:style="userProvidedStyles"`).
* SHOULD use Vue’s style object syntax and allow only safe, specific properties if user customization is needed. ([Vue.js][1])
* SHOULD isolate “user can control layout/CSS” features inside sandboxed iframes.

Insecure patterns:

* `:style="userProvidedStyles"` where styles are attacker-controlled.
* Rendering user-provided `<style>` content (even if Vue blocks some patterns, do not try to work around it).

Detection hints:

* Search: `:style="` bound to non-constant variables originating from API/user content.
* Search for “custom CSS”, “theme editor”, “profile CSS”.

Fix:

* Allowlist properties and values; avoid raw style strings.
* Use sandboxed iframes for rich user customization.

---

### VUE-XSS-006: Never bind user-provided JavaScript into event handler attributes

Severity: Critical

Required:

* MUST NOT bind attacker-provided strings into event handler attributes (e.g., `onclick`, `onfocus`, etc.).
* MUST treat “user-provided JS” as unsafe unless sandboxed and self-only exposure is guaranteed. ([Vue.js][1])

Insecure patterns:

* `<div :onclick="userProvidedString">`
* `<a :onmouseenter="userProvidedString">`

Detection hints:

* Search: `:on` followed by event attribute names (`:onclick`, `:onload`, etc.).
* Search for `setAttribute('on` patterns.

Fix:

* Use real event listeners with developer-controlled handlers.
* If user scripting is truly needed, isolate it (sandboxed iframe and strict boundaries).

---

### VUE-ROUTER-001: Do not treat client-side route guards as authorization

Severity: High

Required:

* MUST NOT rely on Vue Router guards, UI hiding, or client-side checks to enforce authorization.
* MUST enforce authorization on backend for every privileged action and sensitive data response. ([OWASP Cheat Sheet Series][8])

Insecure patterns:

* “Admin route is protected because `beforeEach` checks `user.isAdmin`.”
* Sensitive API endpoints that assume “the frontend won’t call this unless allowed.”

Detection hints:

* Search `router.beforeEach` for role-based gating; check whether backend also enforces.
* Look for “security by route meta” patterns (`meta.requiresAdmin`) with no server corroboration.

Fix:

* Keep route guards as UX only (reduce accidental access); enforce real checks server-side.

---

### VUE-ROUTER-002: Prevent open redirects and unsafe “return_to/next” handling

Severity: Low

Required:

* MUST validate redirect destinations derived from untrusted input (`next`, `return_to`, `redirect`).
* SHOULD allow only same-site relative paths or explicit destination allowlist.
* MUST NOT allow non `http` / `https` protocols (such as `javascript:`)

Insecure patterns:

* `router.push(route.query.next as string)`
* `window.location.href = route.query.redirect`

Detection hints:

* Search for `route.query.next`, `route.query.redirect`, `return_to`, `continue`, `callback`.
* Trace value into router/window navigation sinks.

Fix:

* Allow only relative paths starting with `/` (and reject `//host`, `javascript:`, etc.).
* Prefer redirecting to named routes you control.

Notes:

* Even Vue docs note sanitized URLs may still not guarantee safe destinations. ([Vue.js][1])

---

### VUE-AUTH-001: Token storage must assume XSS is possible

Severity: Low

Required:

* MUST assume any token accessible to JavaScript can be stolen via XSS.
* SHOULD prefer HttpOnly cookies (set by backend) for session tokens, with CSRF protections where relevant. ([Vue.js][1])
* SHOULD avoid storing long-lived tokens (especially refresh tokens) in `localStorage`/`sessionStorage`.

Insecure patterns:

* `localStorage.setItem('token', ...)` for long-lived bearer tokens.
* Storing refresh tokens in JS-accessible storage.

Detection hints:

* Search: `localStorage`, `sessionStorage`, `indexedDB`, `persist`, `pinia-plugin-persistedstate`.
* Identify whether stored values are auth/session material.

Fix:

* Prefer backend-managed sessions via HttpOnly cookies.
* If bearer tokens unavoidable, keep them short-lived, in memory, and rotate frequently. Combine with strong XSS mitigations (CSP, Trusted Types, strict sanitization). ([OWASP Cheat Sheet Series][4])

---

### VUE-CSRF-001: Coordinate with the backend for CSRF when using cookies

Severity: High (for cookie-authenticated state-changing requests)

NOTE: If app does not use cookie-based authentication (for example, passes an Authorization header), CSRF is not a concern

Required:

* If API requests include cookies (`credentials: 'include'` / `withCredentials: true`) and cookies authenticate user, MUST include CSRF protections coordinated with backend (token/header patterns, Origin checks, SameSite cookies as defense-in-depth). ([Vue.js][1])
* MUST NOT “solve CORS/CSRF errors” by disabling protections on backend or using `mode: 'no-cors'` on frontend.

Insecure patterns:

* `fetch(url, { credentials: 'include', method: 'POST', body: ... })` with no CSRF token/header usage anywhere.
* Enabling cross-origin credentialed requests without strict origin allowlists (backend-side).

Detection hints:

* Search: `credentials: 'include'`, `withCredentials`, `xsrf`, `csrf`, `X-CSRF-Token`, `X-XSRF-TOKEN`.
* Check API wrapper modules for headers and cookie settings.

Fix:

* Use backend-issued CSRF tokens; require them on state-changing requests.
* Keep cookies `SameSite=Lax/Strict` where compatible and verify Origin/Referer where appropriate (backend-driven). ([OWASP Cheat Sheet Series][9])

---

### VUE-HTTP-001: Do not put secrets in URLs; avoid leaking sensitive data in navigation/logs

Severity: Medium

Required:

* MUST NOT place tokens/secrets in query strings or fragments (they leak via logs, referrers, browser history).
* SHOULD avoid logging sensitive values to console in production.

Insecure patterns:

* `/?token=...`, `/#access_token=...` used beyond short-lived OAuth handoff.
* `console.log(userSession)` including tokens/PII.

Detection hints:

* Search for `token=` in router parsing, auth callback handlers, and analytics logs.
* Search for `console.log(` around auth code.

Fix:

* Use Authorization headers or HttpOnly cookies.
* Scrub logs; gate debug logs behind dev-only checks.

---

### VUE-HEADERS-001: Require security headers at the deployment layer

Severity: Medium

Required:

* SHOULD deploy CSP (`Content-Security-Policy`) suited to your Vue app.
* SHOULD deploy clickjacking defenses (CSP `frame-ancestors` and/or `X-Frame-Options`) unless intentional embedding is required.
* SHOULD deploy `X-Content-Type-Options: nosniff`, plus other headers as appropriate (Referrer-Policy, Permissions-Policy). ([OWASP Cheat Sheet Series][4])

Insecure patterns:

* No evidence of headers in server/CDN config for app with UGC or rich HTML rendering.
* CSP includes `unsafe-inline`/`unsafe-eval` without strong justification.

Detection hints:

* Look for hosting config: nginx, Netlify/Vercel headers config, CloudFront/Cloudflare rules.
* If absent in repo, flag as “verify at edge”.

Fix:

* Set headers at edge or in server. Start with conservative CSP, then tighten.

---

### VUE-CSP-001: Use Trusted Types and DOM XSS hardening when feasible

Severity: Low

Required:

* For apps with significant DOM injection surface (rich text, plugins, `v-html`), SHOULD consider enabling Trusted Types to reduce DOM XSS risk. ([web.dev][10])
* SHOULD treat Trusted Types as defense-in-depth, not replacement for sanitization.

Insecure patterns:

* Frequent use of `innerHTML`/`v-html` without sanitization or CSP hardening.

Detection hints:

* Search: `v-html`, `innerHTML`, `insertAdjacentHTML`.
* Check CSP for `require-trusted-types-for 'script'` usage (if headers in repo).

Fix:

* Reduce/centralize HTML injection, sanitize inputs, add Trusted Types policies where appropriate.

---

### VUE-THIRDPARTY-001: Avoid dynamic third-party script injection; prefer static, vetted loading

Severity: Low

Required:

* MUST NOT inject `<script src="...">` where URL is user-controlled.
* SHOULD treat third-party widgets/analytics as supply-chain risk; load only from vetted, pinned sources.

Insecure patterns:

* `const s=document.createElement('script'); s.src = userProvidedUrl; ...`
* “Plugin marketplace” loading arbitrary remote scripts.

Detection hints:

* Search: `createElement('script')`, `.src =`, `appendChild(script)`.
* Search for “loadExternalScript”, “injectScript”, “cdnUrl”.

Fix:

* Bundle dependencies, or allowlist strict origins and enforce integrity (see SRI rule).
* Consider sandboxed iframes for untrusted third-party UI.

---

### VUE-SRI-001: Use Subresource Integrity for CDN-hosted scripts/styles

Severity: Low

Required:

* If loading scripts/styles from CDN, SHOULD use Subresource Integrity (`integrity` attribute) with appropriate `crossorigin` configuration. ([MDN Web Docs][11])
* SHOULD prefer self-hosting or bundling over runtime CDN dependencies for security-critical code.

Insecure patterns:

* `<script src="https://cdn.example/...">` with no `integrity`.
* Remote script URLs that can change content without version pinning.

Detection hints:

* Search `index.html` and server templates for `https://` script/style tags.
* Check for `integrity=`.

Fix:

* Add SRI hashes (and pin versions), or bundle assets with your build.

---

### VUE-SUPPLY-001: Dependency and patch hygiene is mandatory

Severity: Low

Required:

* SHOULD keep Vue and official companion libraries updated; Vue recommends latest versions to stay as secure as possible. ([Vue.js][1])
* MUST respond to security advisories promptly.
* SHOULD pin dependencies and commit lockfiles (reduces drift in production artifacts).

Insecure patterns:

* Outdated major versions with known CVEs.
* No lockfile in repo; wide semver ranges for critical deps.
* Ignoring advisories for template/rendering/compiler packages.

Detection hints:

* Inspect `package.json`, lockfiles, CI install commands.
* Search for `npm audit` disabled, “ignore vulnerabilities” scripts.

Fix:

* Upgrade dependencies; add regression tests around impacted behavior.
* Add dependency scanning in CI.

---

### VUE-SSR-001: SSR adds additional trust boundaries; treat state injection as XSS-sensitive

Severity: Medium

Required:

* When using SSR, MUST treat anything injected into HTML document (initial state, serialized data, inline scripts) as XSS-sensitive.
* MUST apply “trusted templates only” rule even more strictly, because unsafe templates can cause server-side execution during rendering. ([Vue.js][1])
* SHOULD follow Vue SSR documentation and best practices for SSR security. ([Vue.js][1])

Insecure patterns:

* Concatenating untrusted strings into SSR templates.
* Injecting JSON into `<script>` blocks without robust escaping/serialization controls.

Detection hints:

* Search server code for `__INITIAL_STATE__`, `window.__*STATE__`, template concatenation, and SSR render pipelines.
* Trace untrusted data into those sinks.

Fix:

* Use safe serialization patterns recommended by your SSR stack.
* Avoid rendering untrusted HTML; sanitize or isolate.

---

## 5) Practical scanning heuristics (how to “hunt”)

High-signal patterns for active scanning:

* URL injection / open redirects:

  * `javascript:` occurrences
* External links security:

  * `target="_blank"` without `rel="noopener"`/`noreferrer` (still recommended for legacy and explicitness) ([MDN Web Docs][12])

Always confirm:

* data origin (untrusted vs trusted)
* sink type (HTML/DOM insertion, template compilation, URL navigation, style injection, script injection)
* protective controls present (sanitization, allowlists, CSP/Trusted Types, backend validation)

---

## 6) Sources (accessed 2026-01-27)

Primary Vue documentation:

* Vue Docs: Security — `https://vuejs.org/guide/best-practices/security` ([Vue.js][1])
* Vue Docs: Template Syntax (security warning about in-DOM templates) — `https://vuejs.org/guide/essentials/template-syntax` ([Vue.js][13])
* Vue Docs: Production Deployment — `https://vuejs.org/guide/best-practices/production-deployment` ([Vue.js][3])
* Vue Docs: Feature Flags — `https://link.vuejs.org/feature-flags` ([Vue.js][7])

Vite documentation (common Vue tooling):

* Vite Docs: Env Variables and Modes (VITE_* exposure + security notes) — `https://vite.dev/guide/env-and-mode` ([vitejs][2])
* Vite Docs: CLI (`vite preview` not designed for production) — `https://vite.dev/guide/cli` ([vitejs][5])
* Vite Docs: Server Options (`server.host` can listen on public addresses) — `https://vite.dev/config/server-options` ([vitejs][14])

OWASP and web platform hardening references:

* OWASP Cheat Sheet Series: XSS Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html` ([Vue.js][1])
* OWASP Cheat Sheet Series: CSRF Prevention — `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][9])
* OWASP Cheat Sheet Series: Authorization — `https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][8])
* OWASP Cheat Sheet Series: HTTP Headers — `https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][4])
* HTML5 Security Cheat Sheet (referenced by Vue) — `https://html5sec.org/` ([Vue.js][1])

Browser/platform references:

* MDN: `rel="noopener"` — `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener` ([MDN Web Docs][12])
* MDN: Subresource Integrity — `https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity` ([MDN Web Docs][11])
* web.dev: Trusted Types — `https://web.dev/trusted-types/` ([web.dev][10])

[1]: https://vuejs.org/guide/best-practices/security "https://vuejs.org/guide/best-practices/security"
[2]: https://vite.dev/guide/env-and-mode "https://vite.dev/guide/env-and-mode"
[3]: https://vuejs.org/guide/best-practices/production-deployment "https://vuejs.org/guide/best-practices/production-deployment"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html"
[5]: https://vite.dev/guide/cli "https://vite.dev/guide/cli"
[6]: https://vite.dev/guide/build "https://vite.dev/guide/build"
[7]: https://vuejs.org/guide/best-practices/production-deployment?utm_source=chatgpt.com "Production Deployment"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html"
[10]: https://web.dev/articles/trusted-types "https://web.dev/articles/trusted-types"
[11]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity?utm_source=chatgpt.com "Subresource Integrity - Security - MDN Web Docs"
[12]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener"
[13]: https://vuejs.org/guide/essentials/template-syntax "Template Syntax | Vue.js"
[14]: https://vite.dev/config/server-options "https://vite.dev/config/server-options"
