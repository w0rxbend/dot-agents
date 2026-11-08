# Security Review Checklist

Severity: Critical, High, Medium, Low

## Input Handling

- [ ] **High** All user input validated at system boundaries — internal code trusts boundary
- [ ] **High** Allowlists, not blocklists — blocklists always miss something
- [ ] **High** Output escaped per context (HTML, SQL, shell)
- [ ] **Medium** Length limits enforced — blocks buffer abuse and DoS

## Database

- [ ] **Critical** SQL uses parameterized placeholders — separates data from code
- [ ] **Critical** ORM/library guards against SQL injection
- [ ] **Critical** No SQL built from user input

## Code Execution

- [ ] **Critical** No `exec.Command()` with shell arguments — metacharacters enable injection
- [ ] **Critical** No eval, reflection on untrusted input — arbitrary code execution risk
- [ ] **Critical** No deserialization of untrusted data — can trigger arbitrary constructors

## Cryptography

- [ ] **High** `crypto/rand` for security-critical randomness — `math/rand` is predictable
- [ ] **High** Vetted algorithms (AES-GCM, Argon2id, bcrypt) — custom crypto unanalyzed
- [ ] **Critical** Proper key management — hardcoded secrets leak via VCS, logs, backups
- [ ] **Medium** HMAC for message authentication — prevents tampering

## Web Security

- [ ] **High** TLS 1.2+ configured correctly — older versions have known attacks
- [ ] **Medium** CSRF protection on state-changing requests — blocks cross-origin action forgery
- [ ] **Medium** Open redirects validated — attackers use your domain to redirect to phishing
- [ ] **High** XSS protected via `html/template` auto-escaping

## Authentication/Authorization

- [ ] **High** Passwords hashed with Argon2id (preferred) or bcrypt — deliberately slow, resists brute-force
- [ ] **High** Sessions use secure tokens from `crypto/rand`
- [ ] **High** Authorization checked on every privileged action — not just at login
- [ ] **High** JWT tokens validated (algorithm, claims, expiry) — unsigned JWTs bypass auth
- [ ] **High** Expired/invalid sessions invalidated server-side

## Error Handling

- [ ] **Medium** Generic error messages to users — detailed errors help attackers map system
- [ ] **Medium** Detailed errors logged server-side only
- [ ] **Medium** Stack traces not leaked to clients
- [ ] **Medium** Database errors hidden — they reveal schema and query structure

## Dependency Security

- [ ] **High** `govulncheck` passes — catches known CVEs in dependency tree
- [ ] **High** Dependencies updated regularly — unpatched deps are #1 attack vector
- [ ] **Medium** Third-party libraries reviewed for security posture

## HTTP Security Headers

- [ ] **Medium** `Content-Security-Policy` set — restricts resource sources, blocks XSS
- [ ] **Medium** `X-Frame-Options: DENY` — blocks clickjacking via iframe embedding
- [ ] **Medium** `X-Content-Type-Options: nosniff` — blocks MIME-type sniffing
- [ ] **Medium** `Strict-Transport-Security` with `includeSubDomains` — forces HTTPS, blocks downgrade
- [ ] **Low** `Referrer-Policy` set — limits referrer leakage to external sites
- [ ] **Low** `Permissions-Policy` set — restricts browser features (camera, mic, geolocation)

## Rate Limiting & DoS Prevention

- [ ] **Medium** HTTP server has `ReadTimeout`, `WriteTimeout`, `IdleTimeout` — prevents Slowloris
- [ ] **Medium** Request body capped with `http.MaxBytesReader` — blocks memory exhaustion
- [ ] **Medium** Rate limits on authentication endpoints — block brute-force and credential stuffing
- [ ] **Medium** Rate limits on expensive operations (search, export, file upload)

## Concurrency

- [ ] **High** `-race` detector passes — races cause data corruption and can bypass auth checks
- [ ] **High** Shared state synchronized
- [ ] **High** No data races on global variables
