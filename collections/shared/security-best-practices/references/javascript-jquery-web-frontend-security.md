# jQuery Frontend Security Spec (jQuery 4.0.x, modern browsers)

---

## 0) Safety, boundaries, and anti-abuse constraints (MUST FOLLOW)

* MUST NOT request, output, log, or commit secrets (API keys, passwords, private keys, session tokens, refresh tokens, CSRF tokens, session cookies).
* MUST treat browser as attacker-controlled:

  * Frontend checks (UI gating, “disable button”, hidden fields, client-side validation) MUST NOT count as authorization or security boundary.
  * Server-side authorization and validation MUST exist even if frontend is “correct”.
* MUST NOT “fix” security by disabling protections (e.g., relaxing CSP to allow `unsafe-inline`, enabling JSONP “because it works”, adding broad CORS, disabling sanitization, suppressing security checks).
* MUST give evidence-based audit findings: cite file paths, code snippets, relevant config values.
* MUST be honest about uncertainty: if protection might exist at edge (CDN/WAF/reverse proxy headers like CSP), report “not visible in repo; verify at runtime/config”.

---

## 1) Operating modes

### 1.1 Generation mode (default)

When writing or modifying jQuery code:

* MUST follow every **MUST** requirement in this spec.
* SHOULD follow every **SHOULD** requirement unless user explicitly says otherwise.
* MUST prefer safe-by-default patterns (text insertion, DOM node construction, allowlists, proven sanitization libraries) over custom escaping.
* MUST avoid adding risky sinks (HTML string building, dynamic script loading, JSONP, inline script/event-handler attributes, unsafe URL assignment, unsafe object merging).

### 1.2 Passive review mode (always on while editing)

In any jQuery repo, even without security scan request:

* MUST “notice” spec violations in touched/nearby code.
* SHOULD flag issues as they come up, with brief explanation + safe fix.

### 1.3 Active audit mode (explicit scan request)

When user asks to “scan”, “audit”, or “hunt for vulns”:

* MUST systematically search codebase for spec violations.
* MUST report findings in structured format (§2.3).

Recommended audit order:

1. jQuery sourcing, versions, dependency hygiene (script tags, lockfiles, CDN usage, SRI).
2. CSP / Trusted Types / security headers posture (in repo, and at runtime if observable).
3. DOM XSS: untrusted sources → jQuery sinks (`.html`, `.append`, `$("<…>")`, `.load`, etc.).
4. Script execution sinks: JSONP, `dataType:"script"`, `$.getScript`, dynamic `<script>` insertion.
5. URL/attribute assignment (`href`, `src`, `style`, `on*` attributes).
6. Prototype pollution / unsafe object merging (`$.extend` patterns).
7. AJAX auth patterns + CSRF for cookie-based sessions.
8. Third-party plugins, untrusted content rendering paths (comments, WYSIWYG, markdown-to-HTML).

---

## 2) Definitions and review guidance

### 2.1 Untrusted input (treat as attacker-controlled unless proven otherwise)

Examples:

* Server data originating from users (user profiles, comments, “display name”, rich text, filenames).
* Data from third-party APIs or services.
* Browser-controlled sources:

  * `location.href`, `location.search`, `location.hash`
  * `document.URL`, `document.baseURI`, `document.referrer`
  * `window.name`
  * `localStorage` / `sessionStorage`
  * `postMessage` event data (unless strict origin and schema validation exists)
  * Any DOM content possibly injected earlier (stored XSS)

### 2.2 High-risk “sinks” in jQuery contexts

Sink: code path where untrusted input can be interpreted as executable code or HTML.

Key jQuery sink categories:

* HTML insertion / parsing:

  * DOM manipulation methods taking HTML strings, e.g. `.html()`, `.append()`, related methods (see CVE notes below). ([NVD][1])
  * `$(htmlString)` (when argument can be interpreted as HTML markup).
  * `jQuery.parseHTML(html, …, keepScripts)`, especially with `keepScripts=true`. ([jQuery API][2])
  * `.load(url)` (loads HTML into DOM; special script execution behavior). ([jQuery API][3])
* Script execution / dynamic code loading:

  * `$.getScript()` / `$.ajax({ dataType: "script" })` (executes fetched JavaScript). ([jQuery API][4])
  * JSONP (`dataType: "jsonp"` or implicit JSONP behavior) (executes remote JavaScript as response). ([jQuery API][5])
  * `eval`, `new Function`, `setTimeout("…")`, `setInterval("…")`, `$.globalEval` (if present)
* Dangerous attribute assignment:

  * Untrusted strings assigned to `href`, `src`, `srcdoc`, `style`, or event-handler attributes (`onload`, `onclick`, etc.)
  * `javascript:` URLs: especially dangerous, discouraged. ([MDN Web Docs][6])

### 2.3 Required audit finding format

Per issue, output:

* Rule ID:
* Severity: Critical / High / Medium / Low
* Location: file path + function/component + line(s)
* Evidence: exact code/config snippet
* Impact: what could go wrong, who can exploit it
* Fix: safe change (prefer minimal diff)
* Mitigation: defense-in-depth if immediate fix is hard
* False positive notes: what to verify if uncertain

---

## 3) Secure baseline: minimum production configuration (MUST in production)

### 3.1 Use a supported, patched jQuery version (MUST)

* MUST use supported jQuery major version; keep it updated.
* As of 2026-01-27, latest jQuery major release is jQuery 4.0.0. ([blog.jquery.com][7])
* jQuery 4 does not support very old browsers (notably IE < 11). Supporting them may require staying on jQuery 3.x. Treat as higher-risk posture; patch aggressively. ([blog.jquery.com][7])

### 3.2 Load jQuery safely (MUST)

* MUST load jQuery only from:

  * Your own build pipeline (bundled via npm/yarn + lockfile), or
  * Official jQuery CDN / trusted CDN with Subresource Integrity (SRI) enabled.

### 3.3 CSP + Trusted Types (SHOULD, and MUST where available/required by policy)

* SHOULD deploy Content Security Policy (CSP) to reduce XSS impact (especially `script-src` restrictions, avoiding `unsafe-inline`). If not set by HTTP server, use `<meta http-equiv="Content-Security-Policy" content="...">` tag. ([OWASP Cheat Sheet Series][9]) NOTE: CSP's script-src matters most. Other directives matter less and can generally be excluded for ease of development.
* SHOULD consider Trusted Types as strong defense-in-depth against DOM XSS. ([W3C][10])
* If CSP directive `require-trusted-types-for` is deployed, code MUST route DOM injection through Trusted Types policies. ([MDN Web Docs][11])
* Note: jQuery 4.0 added Trusted Types support: TrustedHTML works with jQuery manipulation methods without violating `require-trusted-types-for`. ([blog.jquery.com][7])

### 3.4 Security headers and cookie posture (defense in depth; SHOULD)

Usually set server-side. If context is only the frontend web app, these cannot be acted on.

* SHOULD set common security headers (CSP, `X-Content-Type-Options: nosniff`, clickjacking protection via `frame-ancestors` / `X-Frame-Options`, `Referrer-Policy`). ([OWASP Cheat Sheet Series][12])
* SHOULD avoid storing long-lived secrets/tokens where JavaScript can read them (like `localStorage`) unless threat model explicitly accepts “XSS == account takeover”.

---

## 4) Rules (generation + audit)

### JQ-SUPPLY-001: jQuery MUST be patched; do not run known vulnerable versions

Severity: Medium (High if internet-facing app AND version is known-vulnerable)

NOTE: Get user consent before upgrading; ask whether they have reasons to hold it back. Upgrades can break apps unexpectedly. Report and recommend upgrades instead of just performing them.

Required:

* MUST NOT use jQuery versions with known high-impact vulnerabilities when patched version exists.
* MUST upgrade past:

  * CVE-2019-11358 (prototype pollution in jQuery before 3.4.0). ([NVD][13])
  * CVE-2020-11022 / CVE-2020-11023 (XSS risks in DOM manipulation methods handling untrusted HTML; patched in 3.5.0). ([NVD][1])

Insecure patterns:

* Script tags or package manifests referencing old jQuery (e.g., `jquery-1.*`, `jquery-2.*`, `jquery-3.3.*`, `jquery-3.4.*`, `jquery-3.4.1`, etc.).
* Bundled vendor directories with old minified jQuery and no upgrade path.

Detection hints:

* Search HTML/templates for `jquery-`; parse version strings.
* Check `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`.
* Check `vendor/`, `public/`, `static/`, `assets/`, `wwwroot/` for `jquery*.js`.

Fix:

* Upgrade to current jQuery (prefer latest stable major; as of 2026-01-27, 4.0.0 is current). ([blog.jquery.com][7])
* If upgrade is constrained, at minimum go beyond CVE thresholds and add compensating controls (strong CSP, strict sanitization, remove risky APIs like JSONP, remove deep-extend of untrusted objects).

Notes:

* If product requirement forces old versions, report as “accepted risk requiring compensating controls”.

---

### JQ-SUPPLY-002: Third-party script loading SHOULD use integrity and trusted origins

Severity: High

Required:

* MUST load jQuery and plugins only from trusted origins.
* If loaded from CDN, SHOULD use SRI (`integrity`) and correct `crossorigin` handling. ([jquery.com][8])

Insecure patterns:

* `<script src="https://…/jquery.min.js"></script>` with no `integrity`.
* Loading jQuery from random third-party CDNs without explicit trust decision.

Detection hints:

* Scan HTML for `<script src=`; check for `integrity=` + `crossorigin=`.
* Find dynamic script insertion with untrusted URLs (see JQ-EXEC-001).

Fix:

* Prefer bundling via npm + lockfile.
* If using CDN, copy official script tag (jQuery CDN supports SRI). ([jquery.com][8])

Note: If correct SRI tag is unavailable, skip this step but tell user. Wrong SRI tag breaks the app; then remove it and inform user.

---

### JQ-XSS-001: Untrusted data MUST NOT be inserted as HTML via jQuery DOM-manipulation methods

Severity: High (if attacker-controlled content reaches these sinks)

Required:

* MUST treat any HTML string insertion as code execution boundary.
* MUST use safe alternatives for untrusted text:

  * `.text(untrusted)` (text, not HTML). ([jQuery API][14])
  * `.val(untrusted)` for form fields. ([jQuery API][15])
  * Create elements and set text/attributes safely instead of concatenating HTML strings.

Insecure patterns (examples):

* `$(selector).html(untrusted)`
* `$(selector).append(untrusted)`
* `$(selector).before(untrusted)` / `.after(untrusted)` / `.replaceWith(untrusted)` / `.wrap(untrusted)` (and similar)
* Building markup: `"<div>" + untrusted + "</div>"` then passing to jQuery

Detection hints:

* Grep for: `.html(`, `.append(`, `.prepend(`, `.before(`, `.after(`, `.replaceWith(`, `.wrap(`, `.wrapAll(`, `.wrapInner(`
* Trace dataflow from §2.1 sources into these calls.

Fix:

* Replace with `.text()` / `.val()` or node construction:

  * `const $el = $("<span>").text(untrusted); container.append($el);`
* If output needs limited markup, see JQ-XSS-002 (sanitization).

Notes:

* Older jQuery versions had extra edge cases even with attempted sanitization; patched in 3.5.0+. Still, never rely on “string sanitization” alone; prefer structured creation or proven sanitizers. ([GitHub][16])

---

### JQ-XSS-002: If rendering user-controlled HTML is required, it MUST be sanitized with a proven HTML sanitizer

Severity: Medium (High if rich HTML is attacker-controlled and sanitizer is weak/misconfigured)

Required:

* MUST NOT “roll your own” HTML sanitizer with regexes.
* If user-controlled HTML must be displayed (e.g., rich text comments), MUST sanitize with well-maintained HTML sanitizer and restrictive allowlist.

  * DOMPurify is common choice; configure conservatively, keep updated. ([GitHub][17])
  * Where available, MAY consider browser HTML Sanitizer API (limited browser availability). ([MDN Web Docs][18])
* SHOULD pair sanitization with CSP and, where feasible, Trusted Types (defense in depth). ([OWASP Cheat Sheet Series][9])

Insecure patterns:

* Regex-based “strip `<script>`” or “escape `<`” attempts followed by `.html()` insertion.
* DOMPurify (or similar) allowing overly broad tags/attributes, or unreviewed configuration.

Detection hints:

* Search for “sanitize” helpers, regex replacing `<`/`>` patterns, “allow all tags” configs.
* Find features rendering user-generated “rich text” or “custom HTML”.
* Check whether sanitizer output goes into `.html()` or equivalent sinks.

Fix:

* Add sanitizer with strict allowlist.
* Centralize “sanitize then inject” in one reviewed module.
* Add regression tests with representative malicious inputs (don’t store payloads in logs or telemetry).

False positive notes:

* If content is guaranteed trusted (e.g., compiled templates you ship), document trust boundary and why it is not attacker-controlled.

---

### JQ-XSS-003: `$(untrustedString)` and `jQuery.parseHTML` MUST NOT process attacker-controlled markup

Severity: High (if attacker-controlled)

Required:

* MUST NOT pass attacker-controlled strings to `$()` when they might be interpreted as HTML.
* MUST treat `jQuery.parseHTML(html, …, keepScripts)` as high-risk primitive; keepScripts MUST be `false` for any untrusted input. ([jQuery API][2])

Insecure patterns:

* `const $node = $(untrusted);`
* `$.parseHTML(untrusted, /* context */, true)` (scripts preserved)

Detection hints:

* Search for `$(` calls whose argument is not static selector or static markup.
* Search for `$.parseHTML(`; inspect `keepScripts` argument.

Fix:

* Build DOM with constant tag names; use `.text()` for untrusted values.
* If HTML parsing is necessary, sanitize first (JQ-XSS-002) and keep scripts disabled.

---

### JQ-XSS-004: `.load()` MUST be treated as an HTML+script injection surface

Severity: Medium (High if URL/content is attacker-controlled)

Required:

* MUST NOT use `.load()` with attacker-controlled URLs or attacker-controlled HTML fragments.
* MUST understand jQuery `.load()` script behavior:

  * Without selector in URL, content passes to `.html()` before scripts are removed, so scripts can execute. ([jQuery API][3])
* SHOULD prefer `fetch()`/XHR for data, then render with safe DOM creation or explicit sanitization.

Insecure patterns:

* `$("#target").load(untrustedUrl)`
* `$("#target").load("/path?param=" + untrusted)`

Detection hints:

* Search JS/TS files for `.load(`.
* Check whether URL has appended selector (behavior differs). ([jQuery API][3])
* Trace whether user input can influence URL.

Fix:

* Replace `.load()` with:

  * `fetch()` to retrieve JSON, then render via `.text()` / node construction, or
  * `fetch()` to retrieve HTML, sanitize it, then inject.
* If `.load()` must stay, ensure URL is constant or strictly allowlisted and returned content is trusted.

---

### JQ-EXEC-001: Dynamic script execution and script fetching MUST NOT be reachable from untrusted input

Severity: High

Required:

* MUST NOT fetch-and-execute scripts from untrusted or user-influenced URLs.
* MUST treat these as code execution primitives:

  * `$.getScript(url)` executes fetched script in global context. ([jQuery API][4])
  * `$.ajax({ dataType: "script" })` and other script-typed requests executing responses.
* SHOULD remove these patterns unless strong, reviewed justification exists.

Insecure patterns:

* `$.getScript(untrustedUrl)`
* `$.ajax({ url: untrustedUrl, dataType: "script" })`
* Dynamic `<script src=...>` injection with `src` derived from untrusted input.

Detection hints:

* Search for `getScript(`, `dataType: "script"`, `globalEval`, `eval`, `new Function`.
* Look for “plugin loader” or “theme loader” features accepting URLs.

Fix:

* Bundle scripts at build time.
* If runtime loading is required, restrict to allowlisted, versioned, integrity-checked assets (ideally still avoid runtime code loading).

---

### JQ-AJAX-001: JSONP MUST be disabled unless the endpoint is fully trusted (and even then, avoid)

Severity: Medium (High if attacker can influence URL/endpoint)

Required:

* MUST NOT use JSONP for untrusted endpoints: it executes JavaScript responses.
* With `$.ajax`, MUST explicitly disable JSONP for non-fully-trusted targets; jQuery docs recommend `jsonp: false` “for security reasons” if you don’t trust the target. ([jQuery API][5])
* SHOULD prefer CORS with JSON (`dataType: "json"`) plus explicit server-side origin allowlists.

Insecure patterns:

* `dataType: "jsonp"`
* URLs with `callback=?` or patterns triggering JSONP behavior. Callback arguments are historical XSS vectors.
* `$.get(untrustedUrl)` without pinning `dataType` and disabling JSONP (risk depends on options and jQuery behavior)

Detection hints:

* Search for `jsonp`, `dataType: "jsonp"`, `callback=?`.
* Search for cross-domain AJAX whose URL is not hard-coded or allowlisted.

Fix:

* Use JSON over HTTPS with server-side CORS.
* Set:

  * `dataType: "json"`
  * `jsonp: false` (defense in depth when URL might be ambiguous) ([jQuery API][5])

---

### JQ-AJAX-002: State-changing AJAX requests using cookie auth MUST be CSRF-protected

Severity: High

NOTE: Only matters with cookie-based auth. Requests using Authorization header have no CSRF potential.

Required:

* If auth uses cookies, MUST protect state-changing requests (POST/PUT/PATCH/DELETE) against CSRF.
* SHOULD use server-verified CSRF tokens; AJAX calls commonly send them in custom header. ([OWASP Cheat Sheet Series][19])
* MUST NOT treat “it’s an AJAX request” as CSRF protection by itself.

Insecure patterns:

* `$.post("/transfer", {...})` or `$.ajax({ method: "POST", ... })` with cookie auth and no CSRF token/header.
* “CSRF protection” that only checks for `X-Requested-With` (defense-in-depth only, not primary).

Detection hints:

* List state-changing AJAX calls; check whether they include CSRF tokens.
* Find how server expects CSRF validation (meta tag, cookie-to-header double submit, synchronizer token, etc.).

Fix:

* Add CSRF token centrally, e.g., `$.ajaxSetup({ headers: { "X-CSRF-Token": token } })`, and ensure server verifies.
* Follow OWASP CSRF guidance for token properties and validation. ([OWASP Cheat Sheet Series][19])

False positive notes:

* If auth is not cookie-based (e.g., Authorization header bearer token), CSRF risk differs; verify actual auth mechanism.

---

### JQ-ATTR-001: Untrusted values MUST NOT be written into dangerous attributes without validation/allowlisting

Severity: Low (High for events like onclick)

Required:

* MUST validate/allowlist URLs written into `href`, `src`, `action`, etc.
* MUST block dangerous schemes; `javascript:` URLs are discouraged since they can execute code. ([MDN Web Docs][6])
* MUST NOT set event-handler attributes (`onclick`, `onerror`, etc.) from strings.
* SHOULD avoid writing untrusted strings into `style` attributes; prefer toggling predefined CSS classes.

Insecure patterns:

* `$("a").attr("href", untrustedUrl)`
* `$("img").attr("src", untrustedUrl)`
* `$(el).attr("style", untrustedCss)`
* `$(el).attr("onclick", untrustedJs)`

Detection hints:

* Search for `.attr("href"`, `.attr("src"`, `.attr("style"`, `.prop("href"`, `.prop("src"`.
* Trace whether inputs come from URL params, server JSON, DOM, or storage.

Fix:

* Parse and validate URLs with `new URL(value, location.origin)`; allowlist protocols (`https:` etc.) and, when needed, hostnames.
* For navigation targets, prefer relative paths you build over full URLs.
* Replace `style` strings with `addClass/removeClass` and predefined class names.

---

### JQ-SELECTOR-001: User-controlled selector fragments MUST be escaped with `jQuery.escapeSelector`

Severity: Medium (can become High if it enables wrong-element selection in security-relevant UI)

Required:

* If selecting by ID/class that may contain special CSS characters, SHOULD use `jQuery.escapeSelector()` (jQuery 3.0+). ([jQuery API][20])
* MUST NOT concatenate raw attacker-controlled strings into selector expressions.

Insecure patterns:

* `$("#" + untrustedId)`
* `$("[data-id='" + untrusted + "']")` (especially without strict quoting/escaping)

Detection hints:

* Search for `"#" +`, `". " +`, or template strings in `$(` selectors.
* Look for “select by user-supplied id”.

Fix:

* `$("#" + $.escapeSelector(untrustedId))` ([jQuery API][20])
* Prefer stable internal IDs over user-derived selectors.

Notes:

* Often a “robustness” issue, but security-relevant if wrong selection makes UI reveal/modify wrong data or skip security-related prompts.

---

### JQ-PROTOTYPE-001: Do not deep-merge untrusted objects; prevent prototype pollution

Severity: Medium

Required:

* MUST NOT deep-merge (`$.extend(true, …)`) attacker-controlled objects into app objects without filtering dangerous keys.
* MUST ensure jQuery >= 3.4.0 to avoid CVE-2019-11358 prototype pollution. ([NVD][13])

Insecure patterns:

* `$.extend(true, target, untrustedObj)`
* `$.extend(true, {}, defaults, untrustedObj)` where untrustedObj comes from URL/JSON/storage

Detection hints:

* Search for `$.extend(true`; inspect where merged objects come from.
* Search for “merge options” / “apply config” patterns using untrusted JSON.

Fix:

* Prefer:

  * Shallow merges over allowlisted keys, or
  * Safe merge helper explicitly rejecting `__proto__`, `prototype`, `constructor`, and nested occurrences.

---

### JQ-CSP-001: CSP and Trusted Types SHOULD be used to make DOM XSS harder to introduce and exploit

Severity: Medium

Required:

* With jQuery 4, SHOULD use its Trusted Types support (TrustedHTML inputs). ([blog.jquery.com][7])

Insecure patterns:

* “Fixing” a jQuery feature by weakening CSP (`script-src 'unsafe-inline'` / `'unsafe-eval'`) without compensating plan.
* No CSP on apps that render user content or heavily manipulate DOM.

Detection hints:

* Look for CSP headers (server configs, framework middleware, meta tags).
* If not visible in repo, flag as “verify at edge/runtime”.

Fix:

* Add CSP incrementally: first remove inline scripts and inline event handlers, then tighten `script-src`.
* Add Trusted Types where supported and feasible.

---

## 5) Practical scanning heuristics (how to “hunt”)

Always confirm:

* data origin (untrusted vs trusted)
* sink type (HTML insertion / script execution / attribute / selector / object merge)
* protective controls present (sanitizer, allowlists, CSP, Trusted Types, CSRF validation)

---

## 6) Sources (accessed 2026-01-27)

Primary jQuery project docs and release notes:

* jQuery 4.0.0 release notes (Trusted Types/CSP changes; version info): `https://blog.jquery.com/2026/01/17/jquery-4-0-0/`. ([blog.jquery.com][7])
* Download jQuery (latest version info; CDN + SRI guidance): `https://jquery.com/download/`. ([jquery.com][8])
* jQuery API: `.html()`: `https://api.jquery.com/html/`. ([jQuery API][21])
* jQuery API: `.text()`: `https://api.jquery.com/text/`. ([jQuery API][14])
* jQuery API: `.append()`: `https://api.jquery.com/append/`. ([jQuery API][22])
* jQuery API: `.load()` (script execution behavior): `https://api.jquery.com/load/`. ([jQuery API][3])
* jQuery API: `jQuery.parseHTML(…, keepScripts)`: `https://api.jquery.com/jQuery.parseHTML/`. ([jQuery API][2])
* jQuery API: `$.ajax()` (`jsonp: false` security note): `https://api.jquery.com/jQuery.ajax/`. ([jQuery API][5])
* jQuery API: `$.getScript()` (executes script): `https://api.jquery.com/jQuery.getScript/`. ([jQuery API][4])
* jQuery API: `jQuery.escapeSelector()`: `https://api.jquery.com/jQuery.escapeSelector/`. ([jQuery API][20])

jQuery vulnerabilities / advisories:

* NVD CVE-2019-11358 (prototype pollution; jQuery < 3.4.0): `https://nvd.nist.gov/vuln/detail/CVE-2019-11358`. ([NVD][13])
* NVD CVE-2020-11022 (XSS risk in DOM manipulation methods; patched in 3.5.0): `https://nvd.nist.gov/vuln/detail/CVE-2020-11022`. ([NVD][1])
* NVD CVE-2020-11023 (XSS risk involving `<option>`; patched in 3.5.0): `https://nvd.nist.gov/vuln/detail/CVE-2020-11023`. ([NVD][23])
* GitHub Security Advisory GHSA-gxr4-xjj5-5px2 (jQuery htmlPrefilter XSS; patched in 3.5.0): `https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2`. ([GitHub][16])

OWASP Cheat Sheet Series (web app security foundations relevant to jQuery usage):

* XSS Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`. ([OWASP Cheat Sheet Series][24])
* DOM-based XSS Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html`. ([OWASP Cheat Sheet Series][25])
* CSRF Prevention: `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`. ([OWASP Cheat Sheet Series][19])
* HTTP Security Headers: `https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html`. ([OWASP Cheat Sheet Series][12])
* Content Security Policy Cheat Sheet: `https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html`. ([OWASP Cheat Sheet Series][9])

Browser/platform references (SRI, CSP, Trusted Types, dangerous URL schemes):

* MDN: Subresource Integrity (SRI): `https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity`. ([MDN Web Docs][26])
* W3C: SRI specification: `https://www.w3.org/TR/sri-2/`. ([W3C][27])
* MDN: CSP guide: `https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP`. ([MDN Web Docs][28])
* MDN: `require-trusted-types-for` directive: `https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for`. ([MDN Web Docs][11])
* MDN: Trusted Types API: `https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API`. ([MDN Web Docs][29])
* W3C: Trusted Types specification: `https://www.w3.org/TR/trusted-types/`. ([W3C][10])
* MDN: `javascript:` URL scheme warning: `https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript`. ([MDN Web Docs][6])
* DOMPurify project documentation: `https://github.com/cure53/DOMPurify`. ([GitHub][17])

[1]: https://nvd.nist.gov/vuln/detail/cve-2020-11022?utm_source=chatgpt.com "CVE-2020-11022 Detail - NVD"
[2]: https://api.jquery.com/jQuery.parseHTML/?utm_source=chatgpt.com "jQuery.parseHTML()"
[3]: https://api.jquery.com/load/?utm_source=chatgpt.com ".load() | jQuery API Documentation"
[4]: https://api.jquery.com/jQuery.getScript/?utm_source=chatgpt.com "jQuery.getScript()"
[5]: https://api.jquery.com/jQuery.ajax/?utm_source=chatgpt.com "jQuery.ajax()"
[6]: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript?utm_source=chatgpt.com "javascript: URLs - URIs - MDN Web Docs"
[7]: https://blog.jquery.com/2026/01/17/jquery-4-0-0/ "jQuery 4.0.0 | Official jQuery Blog"
[8]: https://jquery.com/download/ "Download jQuery | jQuery"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html?utm_source=chatgpt.com "Content Security Policy - OWASP Cheat Sheet Series"
[10]: https://www.w3.org/TR/trusted-types/?utm_source=chatgpt.com "Trusted Types"
[11]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for?utm_source=chatgpt.com "Content-Security-Policy: require-trusted-types-for directive"
[12]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html?utm_source=chatgpt.com "HTTP Security Response Headers Cheat Sheet"
[13]: https://nvd.nist.gov/vuln/detail/cve-2019-11358?utm_source=chatgpt.com "CVE-2019-11358 Detail - NVD"
[14]: https://api.jquery.com/text/?utm_source=chatgpt.com ".text() | jQuery API Documentation"
[15]: https://api.jquery.com/val/?utm_source=chatgpt.com ".val() | jQuery API Documentation"
[16]: https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2 "Potential XSS vulnerability in jQuery.htmlPrefilter and related methods · Advisory · jquery/jquery · GitHub"
[17]: https://github.com/cure53/DOMPurify?utm_source=chatgpt.com "DOMPurify - a DOM-only, super-fast, uber-tolerant XSS ..."
[18]: https://developer.mozilla.org/en-US/docs/Web/API/HTML_Sanitizer_API?utm_source=chatgpt.com "HTML Sanitizer API - MDN Web Docs"
[19]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "Cross-Site Request Forgery Prevention Cheat Sheet"
[20]: https://api.jquery.com/jQuery.escapeSelector/?utm_source=chatgpt.com "jQuery.escapeSelector()"
[21]: https://api.jquery.com/html/?utm_source=chatgpt.com ".html() | jQuery API Documentation"
[22]: https://api.jquery.com/append/?utm_source=chatgpt.com ".append() | jQuery API Documentation"
[23]: https://nvd.nist.gov/vuln/detail/cve-2020-11023?utm_source=chatgpt.com "CVE-2020-11023 Detail - NVD"
[24]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "Cross Site Scripting Prevention - OWASP Cheat Sheet Series"
[25]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "DOM based XSS Prevention Cheat Sheet"
[26]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity?utm_source=chatgpt.com "Subresource Integrity - Security - MDN Web Docs"
[27]: https://www.w3.org/TR/sri-2/?utm_source=chatgpt.com "Subresource Integrity"
[28]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP?utm_source=chatgpt.com "Content Security Policy (CSP) - HTTP - MDN Web Docs"
[29]: https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API?utm_source=chatgpt.com "Trusted Types API - MDN Web Docs"
