---
name: api-security
description: "Authorized security assessment of REST, GraphQL, WebSocket and SOAP APIs - discovery, authentication and authorization flaws (BOLA/IDOR/BFLA, JWT/OAuth), input validation, rate-limit and data-exposure testing, in a structured multi-phase workflow. Use for permitted testing of an API; use api-security-best-practices to build secure endpoints."
risk: offensive
source: "https://github.com/zhaoxuya520/reverse-skill"
source_repo: "zhaoxuya520/reverse-skill"
source_type: community
date_added: "2026-08-25"
license: "MIT"
license_source: "https://github.com/zhaoxuya520/reverse-skill/blob/main/LICENSE"
---
> **AUTHORIZED USE ONLY.** Use this skill only against systems you own or have explicit written permission to test. Unauthorized testing is illegal.

> **Confirmation gate.** Before running any command that probes, exploits, modifies, persists on, extracts data from, or attempts credential access against a target:
> 1. Have the user state the exact target URL, IP, account or resource.
> 2. Have the user confirm written authorization and the permitted scope.
> 3. Show the exact command(s) and their expected effect.
> 4. Wait for explicit confirmation in this conversation.
>
> Without that confirmation, stay read-only and give defensive guidance only. Prefer a sandbox, disposable VM or controlled lab.

# API Security Testing

A discovery-to-report workflow for authorized API assessments. Work the phases in order, confirm the scope at the gate above, and keep reproducible evidence for every finding.

## When to use

- An authorized assessment covers API endpoints and you need a structured workflow.
- You are testing API authentication, authorization or rate-limiting behavior within an approved scope.

Covers: REST (OpenAPI/Swagger-driven or blind), GraphQL (introspection, batching, alias overload), WebSocket, JWT and OAuth 2.0 auth, BOLA/IDOR/BFLA authorization flaws, and rate-limit bypass / DoS.

## Phase 1: Discovery and reconnaissance

- Crawl for an API surface and generate an OpenAPI 3.0 / GraphQL SDL spec from observed traffic.
- Extract endpoints from `robots.txt` and JavaScript files; brute-force undocumented paths with a tool like ffuf or kiterunner.
- Check common paths: `/swagger.json`, `/openapi.json`, `/graphql`, `/api-docs`.
- GraphQL introspection, three escalating attempts: full introspection query; a reduced query to bypass WAFs that block the full one; and a minimal `__schema { types { name } }` probe.

## Phase 2: Authentication testing

JWT (with jwt_tool or Burp):
- `alg:none`: set header `"alg":"none"` and strip the signature.
- Algorithm confusion: RS256 public key reused as an HS256 symmetric key.
- Weak HMAC secret: dictionary attack (`jwt_tool -C -d wordlist.txt`).
- Expiry / claim tampering: modify `exp`, `iat`, `sub`, `role`.
- `kid` injection (path traversal or SQL in the `kid` header) to subvert signature verification.

OAuth 2.0:
- `redirect_uri` manipulation leaking the authorization code.
- CSRF from a missing `state` parameter.
- Token leaking via the `Referer` header.
- Missing PKCE.

GraphQL auth:
- Mutation via GET request to bypass auth (CSRF).
- Auth bypass through batched queries.

## Phase 3: Authorization (BOLA/IDOR/BFLA)

BOLA (object-level):
- Enumerate numeric IDs (`/user/1` to `/user/2`), UUIDs, usernames/emails.
- Replay the same request across two sessions and diff (for example Burp Autorize).

BFLA (function-level):
- A normal user calling an admin API.
- HTTP method switching: GET to PUT/PATCH/DELETE.
- API version downgrade: `/v2/admin` to `/v1/admin`.
- Mass-operation injection: add another tenant's id to a batch (`{"users":[1,2,3]}` to `{"users":[1,2,3,<admin_id>]}`).

## Phase 4: GraphQL-specific

Introspection leakage, alias overload (100+ aliases) and batched-query DoS, field duplication (`__typename` x500), directive overload (recursive `@skip`/`@include`), deeply nested/circular queries, field-suggestion leakage in error messages, exposed GraphiQL/Playground, GET mutations (CSRF), and debug/trace mode metadata leakage.

## Phase 5: REST input validation

- HTTP method switching across GET/POST/PUT/DELETE/OPTIONS/PATCH.
- Content-Type tampering: JSON to XML to multipart.
- NoSQL injection: `{"username": {"$gt": ""}}`.
- SSRF via URL parameters (webhook, avatar, import URLs).
- XXE in XML endpoints.
- Parameter pollution: `/api?role=user&role=admin`.
- Mass assignment: add `is_admin: true` to the body.

## Phase 6: Business logic and differential testing

- Diff v1 vs v2 of an API: status-code changes, dropped fields, latency regressions.
- Multi-role workflow and permission-matrix testing (admin/user/readonly).
- Coupon, points and price manipulation.
- Race conditions: concurrent requests to hit TOCTOU windows.

## Phase 7: WebSocket

Endpoint discovery, message injection (payloads, prototype pollution), oversized-message handling, type confusion, and cross-site WebSocket hijacking (CSWH).

## Phase 8: Rate limiting and DoS

- Bypass via headers: `X-Forwarded-For`, `X-Real-IP`.
- Path variants: `/api/`, `/api`, `/Api/`, `/API/`.
- Slowloris low-bandwidth exhaustion.
- GraphQL batched / deeply nested query DoS.
- IP rotation testing.

Keep DoS testing to approved non-production targets, and stop at proof of concept rather than sustained disruption.

## Phase 9: Data exposure

- Over-exposure: compare the API response against what the UI actually uses.
- Pagination enumeration: `?page=1&limit=10000`.
- Error-message leakage: stack traces, internal paths, SQL errors.
- Nested GraphQL traversal reaching unauthorized data.
- OpenAPI spec exposing sensitive endpoints.

## Phase 10: CI/CD integration

- Re-run the assessment automatically when the API spec changes.
- Gate builds on a DAST severity threshold.
- Persist findings as regression tests.

## Tooling

| Tool | Use |
|------|-----|
| ffuf / kiterunner | Endpoint path brute-forcing |
| jwt_tool | JWT attacks (alg:none, confusion, secret cracking) |
| Burp Autorize / AuthMatrix | Two-session authorization comparison |
| OWASP ZAP / StackHawk | DAST, CI integration |
| traffic-to-spec generators | Build OpenAPI/GraphQL specs from observed traffic |

Confirm each tool is installed and authorized before use; substitute equivalents as available.

## References

- `references/rest-graphql-testing.md` - REST and GraphQL in depth.
- `references/jwt-oauth-testing.md` - JWT and OAuth testing.

## Done when

- Every step was executed (not just read), against an authorized target.
- Each finding has reproducible evidence: the command, request/response, and impact.
- Each finding has a remediation recommendation, optionally with a CWE reference.
- Out-of-scope and untested areas are stated explicitly.

## Limitations

- Only run against APIs you are explicitly authorized to test.
- Many checks are intrusive; prefer non-production mirrors.
- Results depend on which tools are available and on scope; absence of findings is not proof of a secure API.

> Adapted from [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill) (MIT); body translated to English and repository-foreign references removed.
