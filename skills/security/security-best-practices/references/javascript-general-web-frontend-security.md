# Frontend JavaScript/TypeScript Web Security Spec (Vanilla Browser JS/TS, Modern Browsers)

**Security spec** for:

1. **Secure-by-default code generation** for new frontend JavaScript/TypeScript (no specific framework assumed).
2. **Security review / vulnerability hunting** in existing frontend code (passive “notice issues while working” and active “scan the repo and report findings”).

Holds **normative requirements** (“MUST/SHOULD/MAY”) plus **audit rules** (bad patterns, detection, fix/mitigation).

---

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, hard-code, or commit secrets (secret API keys, private keys, passwords, OAuth refresh tokens, session tokens, cookies).
  Notes:

  * End users can see all frontend code. Secret values must not be in browser-delivered code.
  * “Public” keys (e.g., publishable analytics keys) MUST be treated as non-secret and scoped accordingly.

* MUST NOT “fix” security by disabling protections (e.g., weakening CSP with `unsafe-inline`/`unsafe-eval` without justification, removing origin checks for `postMessage`, switching to `innerHTML` for convenience, accepting arbitrary redirects/URLs, turning off sanitization).

* MUST give **evidence-based findings** in audits: cite file paths, code snippets, and HTML/CSP/config values backing each claim.

* MUST treat uncertainty honestly:

  * Server/edge/CDN may set security headers (CSP, frame-ancestors, etc.) outside repo code. If not visible, report “not visible here; verify at runtime/edge config.” `<meta http-equiv=...>` only simulates a subset of headers; a meta tag does not mean other security headers exist. ([MDN Web Docs][1])

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing or modifying frontend JS/TS code:

* MUST follow every **MUST** requirement here.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default browser APIs and proven libraries over custom security code (especially HTML sanitization).
* MUST avoid new risky sinks (DOM XSS sinks like `innerHTML`, navigation to `javascript:` URLs, dynamic code execution via `eval`/`Function`, unsafe `postMessage`, unsafe third-party script loading, etc.). ([OWASP Cheat Sheet Series][2])

### 1.2 Passive review mode (always on while editing)

Anywhere in a frontend repo, even without security scan request:

* MUST “notice” spec violations in touched/nearby code.
* SHOULD flag issues as they come up, with brief explanation and safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST output findings in structured format (see §2.3).

Recommended audit order:

1. HTML entrypoints (`index.html`, server-rendered templates), script/style includes, CSP delivery (header vs meta). ([W3C][3])
2. DOM XSS sinks (`innerHTML`, `document.write`, `insertAdjacentHTML`, event-handler attributes) and their data sources (URL params/hash, storage, postMessage, API responses). ([OWASP Cheat Sheet Series][2])
3. Navigation/redirect handling (`window.location*`, link targets, URL allowlists), including `javascript:` URL hazards. ([MDN Web Docs][4])
4. Cross-origin communication (`postMessage`, iframe embed patterns, sandboxing). ([MDN Web Docs][5])
5. Sensitive data in storage (localStorage/sessionStorage) and trust assumptions. ([OWASP Cheat Sheet Series][6])
6. Third-party scripts / tag managers / CDNs, with integrity controls (SRI) and policy controls (CSP). ([OWASP Cheat Sheet Series][7])
7. DOM clobbering gadgets and unsafe reliance on `window`/`document` named properties. ([OWASP Cheat Sheet Series][8])

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Examples:

* URL-derived data: `location.href`, `location.search`, `location.hash`, `document.baseURI`, `new URLSearchParams(location.search)`, routing fragments. ([OWASP Cheat Sheet Series][2])
* DOM content possibly holding user-controlled markup (comments, profiles, CMS content, markdown-to-HTML output, etc.), especially when inserted dynamically. ([OWASP Cheat Sheet Series][2])
* `postMessage` event data (`event.data`) and metadata (`event.origin`) from other windows/frames. ([MDN Web Docs][5])
* Browser storage: `localStorage`, `sessionStorage`, IndexedDB (XSS or local machine access can influence contents; never treat as “trusted”). ([OWASP Cheat Sheet Series][6])
* Any network response data (even from “your API”): may hold stored attacker content, dangerous only once inserted into DOM. ([OWASP Cheat Sheet Series][2])

### 2.2 Dangerous sink (DOM XSS / code execution sink)

Sink: any API/operation that can execute script or interpret attacker-controlled strings as HTML/JS/URL in security-sensitive way. High-signal sinks:

* HTML parsing / insertion: `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `document.writeln`. ([OWASP Cheat Sheet Series][2])
* Dynamic code execution: `eval`, `new Function`, `setTimeout("...")`, `setInterval("...")`. ([MDN Web Docs][10])
* Navigation to script-bearing URLs (e.g., `javascript:`) via setters like `Location.href`/`window.location` (and link `href` if attacker-controlled). ([MDN Web Docs][4])
* Event handler attributes set from strings, e.g. `setAttribute("onclick", "...")`. ([OWASP Cheat Sheet Series][2])

### 2.3 Required audit finding format

For each issue, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + function/class/module + line(s)
* Evidence: the exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

Smallest baseline against common frontend JS/TS security misconfigurations. Some items live “in repo” (HTML/JS), some at server/edge.

### 3.1 Content Security Policy (CSP) baseline (SHOULD; MUST for high-risk apps)

* SHOULD deliver CSP via HTTP response headers when possible.
* MAY deliver CSP via HTML `<meta http-equiv="Content-Security-Policy" ...>` tag when headers cannot be set (e.g., purely static hosting constraints). ([MDN Web Docs][1])
* With CSP via `<meta http-equiv>`, MUST know limitations:

  * Policy applies only to content after meta element, so place it very early, before scripts/resources to govern. ([W3C][3])
  * Directives **not supported** (ignored) in meta-delivered policy: `report-uri`, `frame-ancestors`, `sandbox`. ([W3C][3])
  * Meta element cannot set “Report-only” CSP. ([W3C][3])

Practical baseline goals:

* Avoid script sources `unsafe-inline` and `unsafe-eval` (they significantly weaken CSP against XSS). ([MDN Web Docs][10])
* Prefer nonce- or hash-based script policies for needed inline scripts. ([MDN Web Docs][10])
* Consider Trusted Types enforcement where feasible. ([MDN Web Docs][11])

### 3.2 Third-party scripts baseline (SHOULD)

* SHOULD minimize third-party script execution; treat it as equivalent privilege to first-party JS (it runs with your origin’s privileges). ([OWASP Cheat Sheet Series][7])
* SHOULD use Subresource Integrity (SRI) for third-party scripts/styles loaded from CDNs. ([MDN Web Docs][12])

### 3.3 Cross-window communication baseline (SHOULD)

* SHOULD restrict `postMessage` communications to explicit origins; validate both origin and message shape. ([MDN Web Docs][5])

---

## 4) Rules (generation + audit)

### JS-XSS-001: Do not inject untrusted HTML into the DOM (avoid `innerHTML` and friends)

Severity: Critical if attacker-controlled input provably reaches these APIs; otherwise Medium

Required:

* MUST treat `innerHTML`, `outerHTML`, `insertAdjacentHTML` as dangerous sinks when input can contain untrusted data. ([OWASP Cheat Sheet Series][2])
* MUST prefer safe DOM APIs that do not parse HTML:

  * `textContent` for text. ([OWASP Cheat Sheet Series][2])
  * `document.createElement`, `appendChild`, `setAttribute` for non-event-handler attributes. ([OWASP Cheat Sheet Series][2])
* If HTML insertion is truly required, SHOULD sanitize with well-reviewed HTML sanitizer and strongly consider Trusted Types enforcement to confine usage to audited code paths. ([MDN Web Docs][11])

Insecure patterns:

* `el.innerHTML = userInput`
* `el.insertAdjacentHTML('beforeend', userInput)`
* `el.outerHTML = userInput`

Detection hints:

* Search for: `.innerHTML`, `.outerHTML`, `insertAdjacentHTML(`.
* Trace inserted string origin: URL params/hash, postMessage, storage, API responses, DOM attributes. ([OWASP Cheat Sheet Series][2])

Fix:

* Replace with `textContent` for plain text. ([OWASP Cheat Sheet Series][2])
* Structured UI: build DOM nodes explicitly.
* “Rich text” requirements:

  * Sanitize with allowlist-based sanitizer.
  * Prefer returning safe “components” over arbitrary HTML strings.
  * Enforce Trusted Types so only `TrustedHTML` reaches sinks, where supported. ([MDN Web Docs][11])

Mitigation:

* Deploy strict CSP; consider Trusted Types enforcement (`require-trusted-types-for 'script'`). ([MDN Web Docs][10])

False positive notes:

* String provably constant or fully built from trusted constants may be safe. Still prefer safer APIs.

---

### JS-XSS-002: Avoid `document.write` / `document.writeln` (XSS + document clobbering hazards)

Severity: Critical if attacker-controlled input provably reaches these APIs; otherwise Medium

Required:

* MUST avoid `document.write()` and `document.writeln()` in production code: XSS vectors, abusable with crafted HTML even where some browsers block injected `<script>` in some cases. ([MDN Web Docs][13])
* If legacy use is unavoidable, MUST ensure no untrusted input reaches these APIs; SHOULD enforce Trusted Types (`TrustedHTML`) where supported. ([MDN Web Docs][14])

Insecure patterns:

* `document.write(userInput)`
* `document.writeln(getParam('q'))`

Detection hints:

* Search for `document.write(`, `document.writeln(`. ([OWASP Cheat Sheet Series][2])

Fix:

* Replace with DOM manipulation (`createElement`, `appendChild`) or safe text insertion (`textContent`). ([OWASP Cheat Sheet Series][2])

Mitigation:

* Strict CSP plus Trusted Types enforcement shrinks blast radius if a sink remains. ([MDN Web Docs][10])

---

### JS-XSS-003: Do not use string-to-code execution (`eval`, `new Function`, string timeouts)

Severity: Critical if attacker-controlled input provably reaches these APIs; otherwise Medium

Required:

* MUST NOT pass untrusted data to:

  * `eval()`
  * `new Function(...)`
  * `setTimeout("...")` / `setInterval("...")` with string arguments ([MDN Web Docs][10])
* SHOULD avoid these APIs entirely in modern frontend code; refactor to non-eval logic. ([MDN Web Docs][10])
* MUST NOT “fix CSP breakage” by adding `unsafe-eval` without documented, reviewed justification and compensating controls. ([MDN Web Docs][10])

Insecure patterns:

* `eval(userInput)`
* `new Function("return " + userInput)()`
* `setTimeout(userInput, 0)` where userInput is a string

Detection hints:

* Search for `eval(`, `new Function`, `setTimeout("`, `setInterval("`.
* Also search for code strings built for later use.

Fix:

* Replace dynamic code with:

  * structured data and explicit branching/handlers,
  * JSON parsing (`JSON.parse`) instead of `eval` for JSON. ([OWASP Cheat Sheet Series][2])

Mitigation:

* CSP blocking `eval()`-like APIs by default; avoid `unsafe-eval`. ([MDN Web Docs][10])
* Consider Trusted Types for controlled cases as hardening layer, not license to keep eval patterns. ([MDN Web Docs][10])

---

### JS-XSS-004: Do not set event handler attributes from strings (e.g., `setAttribute("onclick", "...")`)

Severity: High

Required:

* MUST NOT use `setAttribute("on…", string)` or similar patterns with untrusted data; strings become executable code in event-handler context. ([OWASP Cheat Sheet Series][2])
* SHOULD prefer `addEventListener` with function references.

Insecure patterns:

* `el.setAttribute("onclick", userInput)`
* `el.onclick = userControlledString` (string assignment)

Detection hints:

* Search for `.setAttribute("on`, `.onclick =`, `.onmouseover =`, `.onload =` with strings, etc.
* Check whether URL/hash/storage/postMessage can influence RHS. ([OWASP Cheat Sheet Series][2])

Fix:

* Replace with `addEventListener("click", () => { ... })`.
* For dynamic dispatch, use allowlisted mapping from identifiers to functions (no string eval). ([OWASP Cheat Sheet Series][2])

---

### JS-URL-001: Sanitize and allowlist URLs before navigation (especially `window.location` / `location.replace`)

Severity: Low (High if attacker provably fully controls URL)

IMPORTANT: High false-positive rate. Do extra analysis to confirm URL is fully attacker controlled. If not, informational at best.

NOTE: Redirecting to any URL may be intended functionality. If so, at minimum check scheme, even when any origin is allowed.

Required:

* MUST treat any assignment to navigation targets as security-sensitive:

  * `window.location = ...`
  * `location.href = ...`
  * `location.assign(...)`
  * `location.replace(...)` ([MDN Web Docs][4])
* MUST prevent navigation to `javascript:` URLs (and other script-bearing/active schemes), especially for input from URL params, storage, or messages. ([MDN Web Docs][4]). Only allow `http:` and `https:`.
* SHOULD validate/allowlist destination. Safe baseline:

  * Allow only same-origin relative paths, OR
  * Allow only strict allowlist of origins and protocols (typically `https:`, optionally `http:` for localhost dev). ([OWASP Cheat Sheet Series][8])

Insecure patterns:

* `location.replace(getParam("next"))`
* `window.location = userSuppliedUrl`
* `location.assign(window.redirectTo || "/")` where `redirectTo` can be clobbered or attacker-set ([OWASP Cheat Sheet Series][8])

Detection hints:

* Search for `window.location`, `location.href`, `location.assign`, `location.replace`.
* Search for common redirect parameters: `next`, `returnTo`, `redirect`, `url`, `continue`.
* Search for `javascript:` literals (and other suspicious schemes like `data:text/html`). ([MDN Web Docs][4])

Fix:

* Parse and validate with `new URL(value, location.origin)`, then enforce:

  * `url.protocol` in `{ "https:" }` (include `http:` only in explicit dev-only code paths),
  * `url.origin` equals `location.origin` for internal redirects, or in strict allowlist for external redirects,
  * optionally allow only specific path prefixes. ([MDN Web Docs][4])
* On validation failure, navigate to safe default (home/dashboard).

Mitigation:

* Deploy strict CSP and Trusted Types enforcement to reduce DOM XSS sink impact; Trusted Types alone do not prevent every possible unsafe navigation scenario. ([W3C][15])

False positive notes:

* Some apps intentionally support external redirects (SSO, payment flows). Those MUST be allowlisted and documented.

---

### JS-URL-002: Sanitize URLs before inserting into DOM URL contexts (`href`, `src`, etc.)

Severity: Low (High if attacker provably fully controls URL)

IMPORTANT: High false-positive rate. Do extra analysis to confirm URL is fully attacker controlled. If not, informational at best.

Required:

* MUST treat setting URL-bearing DOM attributes/properties as security-sensitive, especially:

  * `a.href`, `img.src`, `script.src`, `iframe.src`, `form.action`, `link.href`.
* MUST prevent script-bearing schemes (`javascript:` and other active schemes) when values can be attacker-influenced. ([MDN Web Docs][4])
* SHOULD prefer setting properties (e.g., `a.href = url.toString()`) after parsing and validation, not string concatenation.

Insecure patterns:

* `link.href = getParam("u")`
* `el.setAttribute("href", userInput)` without validation
* building URLs by concatenating untrusted pieces

Detection hints:

* Search for `.href =`, `.src =`, `.action =`, `setAttribute("href"`, `setAttribute("src"`.
* Search for `javascript:` / `data:` usage in URLs. ([MDN Web Docs][4])

Fix:

* Use `new URL(...)` and validate:

  * protocol allowlist
  * avoid passing user-provided values into `<script src>` at all (treat as code execution). ([OWASP Cheat Sheet Series][8])

---

### JS-CSP-001: Use CSP; meta delivery is allowed

Severity: Medium to High (depends on threat model; High when handling untrusted content)

NOTE: CSP's script-src matters most. Other directives matter less and can usually be left out for ease of development.

Required:

* SHOULD deploy CSP as major defense-in-depth against XSS. ([MDN Web Docs][10])
* MAY provide CSP via `<meta http-equiv="Content-Security-Policy" ...>` when headers are unavailable. ([MDN Web Docs][1])
* With meta-delivered CSP, MUST:

  * place it early (before scripts/resources to govern), and
  * not rely on directives unsupported in meta policies (`report-uri`, `frame-ancestors`, `sandbox`). ([W3C][3])
* MUST avoid adding `unsafe-inline` as “quick fix” for CSP issues unless explicitly required and reviewed (defeats much of CSP’s purpose). ([MDN Web Docs][10])
* MUST avoid adding `unsafe-eval` unless explicitly required and reviewed (allows commonly abused eval-like APIs). ([MDN Web Docs][10])

Insecure patterns:

* No CSP anywhere (repo HTML or server/edge) for app rendering untrusted content.
* CSP includes `script-src 'unsafe-inline'` and/or `script-src 'unsafe-eval'` without strong justification. ([MDN Web Docs][10])
* CSP delivered via meta but includes `frame-ancestors` (ignored in meta). ([W3C][3])

Detection hints:

* Search HTML for `<meta http-equiv="Content-Security-Policy"`.
* Search server/edge configs for `Content-Security-Policy` header.
* If CSP is only in meta, check it appears before any `<script>` tags to govern. ([W3C][3])

Fix:

* Prefer header-delivered CSP at server/edge.
* If limited to meta, keep strong allowlist CSP and document limitations; put clickjacking protections (e.g., `frame-ancestors`) at server/edge, not in meta. ([W3C][3])

---

### JS-CSP-002: Prefer strict CSP (nonces/hashes); avoid inline/eval patterns in code

Severity: Medium

NOTE: CSP's script-src matters most. Other directives matter less and can usually be left out for ease of development.

Required:

* SHOULD write frontend code that works under strict CSP:

  * avoid inline scripts and inline event handlers,
  * avoid eval-like APIs (see JS-XSS-003),
  * allow scripts via nonce or hash when needed. ([MDN Web Docs][10])

Insecure patterns:

* Many inline script blocks and inline `onclick="..."` handlers.
* Libraries that require `unsafe-eval`.

Detection hints:

* Search for `<script>` blocks with inline code, `onclick="`, `onload="`, etc.
* Search for CSP directives containing `unsafe-inline` or `unsafe-eval`. ([MDN Web Docs][10])

Fix:

* Move inline scripts into external JS files (same-origin).
* Use nonces/hashes for any unavoidable inline blocks. ([MDN Web Docs][10])

---

### JS-TT-001: Use Trusted Types to reduce DOM XSS attack surface (where supported)

Severity: Low

Required:

* SHOULD consider Trusted Types enforcement via CSP `require-trusted-types-for 'script'` so many DOM XSS sinks reject raw strings. ([MDN Web Docs][11])
* With Trusted Types, SHOULD also use CSP `trusted-types` directive to restrict which policies can be created (less policy sprawl, better auditability). ([MDN Web Docs][16])
* MUST keep Trusted Types policy code small, heavily reviewed, and the only path producing trusted values for sinks. ([W3C][15])

Insecure patterns:

* “Trusted Types enabled” but policy returns input unchanged (no sanitization/validation).
* Many unrestricted ad-hoc policies across codebase.
* Belief that Trusted Types alone prevents all unsafe navigations or all XSS classes. (Targets DOM injection sinks; not a universal sandbox.) ([W3C][15])

Detection hints:

* Search for CSP directives: `require-trusted-types-for` and `trusted-types`.
* Search code for `trustedTypes.createPolicy(` and inspect policy implementations. ([MDN Web Docs][11])

Fix:

* Add small set of well-reviewed policies (e.g., `createHTML` that sanitizes).
* Restrict allowed policies via `trusted-types <policyName...>`.
* Migrate sinks to require `TrustedHTML` / `TrustedScriptURL` as appropriate. ([MDN Web Docs][11])

---

### JS-MSG-001: `postMessage` must use strict origin validation and explicit targetOrigin

Severity: Medium (High if dangerous behavior can be triggered via postMessage)

Required:

* When sending, MUST set explicit `targetOrigin` (not `*`) to avoid sending data to unexpected origin after redirects or window origin changes. ([MDN Web Docs][5])
* When receiving, MUST:

  * Validate `event.origin` exactly against allowlist of expected origins (no substring matching). ([OWASP Cheat Sheet Series][6])
  * Consider validating `event.source` (expected window reference) when applicable. ([MDN Web Docs][5])
  * Validate `event.data` structure (schema/shape); treat it purely as data (never evaluate it as code, never insert into DOM with `innerHTML`). ([OWASP Cheat Sheet Series][6])

Insecure patterns:

* `otherWindow.postMessage(payload, "*")`
* `window.addEventListener("message", (e) => { doSomething(e.data) })` with no `origin` check
* `if (e.origin.includes("trusted.com"))` (substring checks)
* `el.innerHTML = e.data` ([OWASP Cheat Sheet Series][6])

Detection hints:

* Search for `postMessage(`, `addEventListener("message"`, `onmessage =`.
* Audit all handlers for explicit allowlist checks on `event.origin`. ([OWASP Cheat Sheet Series][6])

Fix:

* Define allowlist:

  * `const ALLOWED = new Set(["https://app.example.com", "https://accounts.example.com"]);`
  NOTE: For ease of development, can use current page's origin `window.location.origin` as safe default origin.
* On receive:

  * `if (!ALLOWED.has(event.origin)) return;`
  * Validate `event.data` with strict schema; reject unknown/extra fields.
* On send:

  * use exact expected origin string as `targetOrigin`. ([OWASP Cheat Sheet Series][6])

Mitigation:

* Combine with strict CSP; avoid DOM sinks in message paths. ([MDN Web Docs][10])

---

### JS-STORAGE-001: Web Storage is not a safe place for secrets (and is attacker-influencable)

Severity: Low

Required:

* MUST NOT store sensitive secrets or session identifiers in `localStorage` (or `sessionStorage`) if compromise would matter; one XSS can exfiltrate everything in storage. ([OWASP Cheat Sheet Series][6])
* MUST treat values read from storage as untrusted input (XSS can plant malicious values in storage). ([OWASP Cheat Sheet Series][6])
* SHOULD prefer server-set `HttpOnly` cookies for session identifiers (JS cannot set `HttpOnly`, so keep session IDs out of JS-accessible storage). ([OWASP Cheat Sheet Series][6])
* SHOULD avoid hosting multiple unrelated apps on same origin if they rely on storage separation (storage is origin-wide). ([OWASP Cheat Sheet Series][6])

Insecure patterns:

* `localStorage.setItem("access_token", token)`
* `localStorage.setItem("session", sessionId)`
* Assuming `localStorage` is “trusted because same-origin.”

Detection hints:

* Search for `localStorage.getItem`, `localStorage.setItem`, `sessionStorage.*`.
* Flag storage keys named `token`, `jwt`, `session`, `auth`, `refresh`. ([OWASP Cheat Sheet Series][6])

Fix:

* Use server-managed sessions or short-lived tokens, delivered and rotated securely, with careful XSS defenses (CSP/Trusted Types) and minimal JS exposure.
* If storage is needed for non-sensitive state, keep it non-auth; validate/escape before use.

---

### JS-SUPPLY-001: Third-party JavaScript is a major supply-chain risk; minimize and control it

Severity: Low

Required:

* MUST treat third-party JS as having first-party privilege (can execute arbitrary code in your origin and access DOM data). ([OWASP Cheat Sheet Series][7])
* SHOULD minimize third-party scripts and prefer:

  * self-hosting / script mirroring,
  * strict CSP allowlists,
  * SRI for any CDN-hosted scripts,
  * ongoing monitoring for unexpected changes. ([OWASP Cheat Sheet Series][7])

Insecure patterns:

* Loading arbitrary remote scripts from many vendors without review.
* Tag managers that can dynamically inject scripts with no integrity controls.
* CSP allowing scripts from broad wildcards (e.g., `script-src *`). ([MDN Web Docs][10])

Detection hints:

* Search HTML for `<script src="https://...">` and `tag manager` snippets.
* Search CSP `script-src` sources for wildcards or overly broad domains.
* Search for dynamic script injection: `document.createElement("script")`, `script.src = ...`, `appendChild(script)`. ([OWASP Cheat Sheet Series][8])

Fix:

* Remove unnecessary third-party tags.
* Self-host or mirror scripts where possible.
* Lock down CSP `script-src` to smallest set of trusted sources.
* Add SRI for CDN scripts/styles. ([OWASP Cheat Sheet Series][7])

---

### JS-SRI-001: Use Subresource Integrity (SRI) for third-party scripts/styles

Severity: Low

Required:

* SHOULD use SRI so browsers load third-party resources only if they match expected cryptographic hash. ([MDN Web Docs][12])
* MUST update SRI hashes whenever underlying resource changes (pin versions; avoid “latest” URLs).

Insecure patterns:

* `<script src="https://cdn.example.com/lib.js"></script>` with no `integrity`.
* Loading `latest` or unpinned third-party resources.

Detection hints:

* Search for `<script src="https://` and `<link rel="stylesheet" href="https://` without `integrity=`.
* Check `integrity` is present and uses strong hashes (sha256/384/512 are typical). ([MDN Web Docs][12])

Fix:

* Add `integrity="sha384-..."` (or appropriate); set proper CORS mode where needed.
* Prefer self-hosting critical libraries.

---

### FS-DOMC-001: Prevent DOM clobbering (avoid relying on `window`/`document` named properties)

Severity: Medium to High (can become Critical if it enables script loading or `javascript:` navigation)

Required:

* MUST NOT rely on implicit global variables or `window.someName` / `document.someName` lookups; injected HTML elements with matching `id`/`name` can clobber them. ([OWASP Cheat Sheet Series][8])
* MUST avoid patterns like `let x = window.redirectTo || "/safe"; location.assign(x);` where `redirectTo` could be clobbered to an `<a>` element with attacker-controlled `href` (including `javascript:`). ([OWASP Cheat Sheet Series][8])
* SHOULD use explicit variable declarations, local scope, and explicit DOM queries (`getElementById`) over named property access. ([OWASP Cheat Sheet Series][8])
* If app inserts user-controlled markup (even sanitized), sanitization SHOULD account for `id`/`name` collisions. ([OWASP Cheat Sheet Series][8])

Insecure patterns:

* `const cfg = window.config || {};` used for security-sensitive URLs.
* `const redirect = window.redirectTo || "/"; location.assign(redirect);` ([OWASP Cheat Sheet Series][8])
* Loading scripts from `window.*` config values without strict validation.

Detection hints:

* Search for `window.` and `document.` used as config stores (especially `||` fallback patterns).
* Search for `location.assign/replace` with variables from `window`/`document` properties.
* Search for dynamic script creation (`createElement('script')`) with `.src` from non-local variable. ([OWASP Cheat Sheet Series][8])

Fix:

* Keep config in module-scoped constants (not on `window`/`document`); pass it explicitly.
* Validate any URL-like config with protocol/origin allowlists (see FEJS-URL-001). ([OWASP Cheat Sheet Series][8])
* Consider hardening: sanitization, CSP, (in limited cases) freezing sensitive objects. These are defense-in-depth, not substitute for safe coding patterns. ([OWASP Cheat Sheet Series][8])

---

## 5) Practical scanning heuristics (how to “hunt”)

Always try to confirm:

* data origin (untrusted vs trusted),
* sink type (HTML parse, navigation, code execution, message handling, storage),
* protective controls present (CSP, Trusted Types, sanitizers, strict allowlists, schema validation).

---

## 6) Sources (accessed 2026-01-27)

Primary standards / platform docs:

* W3C Content Security Policy Level 2 (HTML `<meta>` delivery restrictions; unsupported directives in meta CSP): `https://www.w3.org/TR/CSP2/` ([W3C][3])
* MDN: CSP Guide (strict CSP, nonces/hashes, `unsafe-inline`/`unsafe-eval`, eval blocking): `https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP` ([MDN Web Docs][10])
* MDN: `<meta http-equiv>` (CSP via meta; warning on meta-based security headers): `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv` ([MDN Web Docs][1])
* MDN: `frame-ancestors` (not supported in `<meta>`): `https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors` ([MDN Web Docs][18])

DOM XSS and dangerous sinks:

* OWASP: DOM Based XSS Prevention Cheat Sheet (dangerous sinks, safe patterns like `textContent`): `https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][2])
* MDN: `innerHTML` (security considerations): `https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML` ([MDN Web Docs][19])
* MDN: `insertAdjacentHTML` (security considerations): `https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML` ([MDN Web Docs][20])
* MDN: `document.write()` / `document.writeln()` (security considerations): `https://developer.mozilla.org/en-US/docs/Web/API/Document/write` and `https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln` ([MDN Web Docs][13])

URL scheme hazards:

* MDN: `javascript:` URLs (execution on navigation; discouraged; references `window.location`): `https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript` ([MDN Web Docs][4])

Trusted Types:

* W3C: Trusted Types spec (DOM XSS sinks include `Element.innerHTML` and `Location.href` setters; goals and limitations): `https://www.w3.org/TR/trusted-types/` ([W3C][15])
* MDN: `require-trusted-types-for` directive: `https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for` ([MDN Web Docs][11])
* MDN: `trusted-types` directive: `https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types` ([MDN Web Docs][16])

Cross-window messaging:

* MDN: `window.postMessage` (security guidance: specify targetOrigin; validate origin): `https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage` ([MDN Web Docs][5])
* OWASP: HTML5 Security Cheat Sheet (Web Messaging guidance: explicit origin, strict checks, no `innerHTML`): `https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][6])

Third-party scripts and integrity:

* OWASP: Third Party JavaScript Management Cheat Sheet (risks and mitigations, including SRI/mirroring): `https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][7])
* MDN: Subresource Integrity overview: `https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity` ([MDN Web Docs][12])
* W3C: Subresource Integrity spec: `https://www.w3.org/TR/sri-2/` ([W3C][21])

DOM clobbering:

* OWASP: DOM Clobbering Prevention Cheat Sheet (named property access risk; example attacks with `location.assign` and `javascript:`): `https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html` ([OWASP Cheat Sheet Series][8])

[1]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
[3]: https://www.w3.org/TR/CSP2/ "Content Security Policy Level 2"
[4]: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript "javascript: URLs - URIs | MDN"
[5]: https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage "https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html"
[9]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener"
[10]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP"
[11]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for"
[12]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity "https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity"
[13]: https://developer.mozilla.org/en-US/docs/Web/API/Document/write "https://developer.mozilla.org/en-US/docs/Web/API/Document/write"
[14]: https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln "https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln"
[15]: https://www.w3.org/TR/trusted-types/ "https://www.w3.org/TR/trusted-types/"
[16]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types"
[18]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors"
[19]: https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML "https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML"
[20]: https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML "https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML"
[21]: https://www.w3.org/TR/sri-2/ "https://www.w3.org/TR/sri-2/"
