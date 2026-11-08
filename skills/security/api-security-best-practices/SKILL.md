---
name: api-security-best-practices
description: "Design and implement API request-boundary controls - token validation, object- and function-level authorization, schema validation, rate limiting and safe logging. Use when building or reviewing API endpoints; use api-security for authorized penetration testing of an API."
risk: critical
source: community
date_added: "2026-02-27"
---

# API Security Best Practices

Review request boundary: caller identity, authorization, validated input, storage,
observable response. Keep app's actual identity provider and data model; do not add
second authentication system.

## When to Use

Use when adding protected endpoint, reviewing object access, replacing permissive
request parsing, or investigating API abuse path. For concrete defect, start at failing
route and its callers. Do not deploy unrelated security infrastructure.

## Inputs and prerequisites

Record routes, caller/tenant model, identity provider, token contract, runtime, locked
dependency versions, database schema, proxy topology, authorized test scope. Use
synthetic identities in test environment. Existing task authorization carries forward.
Production scans, account writes and message sends need own authority. Node examples
below are integration sketches for Express, jsonwebtoken and Zod, not full runnable
service: app/database adapters are only named. Confirm APIs against installed versions
before integrating.

## 1. Authenticate the exact token contract

Prefer established provider/session middleware. If service owns HMAC JWT contract,
require strong server-owned key, fixed algorithm, exact issuer and audience, required
runtime claims. Do not infer permissions from decoded token before signature
verification. Never accept caller-selected verification algorithm.

```javascript
const jwt = require('jsonwebtoken');

// Illustrative first-party access-token contract; not a third-party OAuth adapter.
const ACCESS_POLICY = {
  algorithms: ['HS256'], issuer: 'example-auth', audience: 'example-api'
};
function verifyAccessToken(token, signingKey) {
  const claims = jwt.verify(token, signingKey, ACCESS_POLICY);
  if (!claims || typeof claims !== 'object' ||
      typeof claims.sub !== 'string' || !claims.sub ||
      typeof claims.tenantId !== 'string' || !claims.tenantId ||
      !Number.isSafeInteger(claims.exp) || !Number.isSafeInteger(claims.iat) ||
      claims.exp <= claims.iat) {
    throw new Error('Invalid access claims');
  }
  return { subject: claims.sub, tenantId: claims.tenantId };
}
function readBearer(header) {
  if (typeof header !== 'string' || header.length > 8192) return null;
  const match = /^Bearer ([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/i.exec(header);
  return match ? match[1] : null;
}
```

Issue access tokens with same issuer/audience/algorithm and short app-approved
expiration. On verification failure, return generic 401 without echoing token or
exception. Expiration alone does not revoke token: define revocation or short-lived
sessions per actual threat model. Asymmetric provider keys need provider's
discovery/JWKS validation and key-rotation policy, not this HMAC example. Never reuse
access token as refresh token.

### Refresh sessions

Use provider's supported session flow or server-side opaque refresh design. Store only
digest, expiry, user/session family, revocation state. One atomic transaction consumes
old active token and creates replacement. Concurrent reuse must not issue two
successors; defined reuse handling revokes affected family. Recheck user status and
permissions when issuing new access tokens. Bind refresh to intended client/session.
Protect cookie-based requests against CSRF. Do not log tokens, store them plaintext in
database, or return refresh token through URL. Before calling flow complete, test
simultaneous refresh, expiry, replay, revocation and transaction failure. No database
transaction adapter is bundled here.

## 2. Authorize the resource and operation

Authentication identifies caller; authorization decides exact operation on object and
tenant. Role name does not automatically grant cross-tenant access. Put owner/tenant
predicate in database mutation to avoid check-then-write race. Allowlist writable
properties. Use 404/403 consistently per product's resource-disclosure policy.

```javascript
// Prisma-style sketch; id and tenant types must match your actual schema.
async function deleteOwnedPost(prisma, postId, principal) {
  const result = await prisma.post.deleteMany({
    where: { id: postId, userId: principal.subject, tenantId: principal.tenantId }
  });
  return result.count === 1;
}
```

Admin path needs explicit separate policy and audit event. Do not add implicit admin
bypass to every owner check. Test: valid user on another user's object, same ID in
another tenant, deleted memberships, bulk endpoints.

## 3. Parse once, then use the validated value

Reject partial numeric parses (`12abc` is not ID 12), unsafe integers, unexpected
properties, oversized requests. Use parameterized database queries. ORM gives no
business authorization and does not make unsafe raw SQL safe.

```javascript
function parsePositiveId(raw) {
  if (typeof raw !== 'string' || !/^[1-9][0-9]{0,15}$/.test(raw)) return null;
  const value = Number(raw);
  return Number.isSafeInteger(value) && value > 0 ? value : null;
}

const { z } = require('zod');
const profileUpdate = z.object({
  displayName: z.string().trim().min(1).max(100)
}).strict();
function validateBody(schema) {
  return (req, res, next) => {
    const parsed = schema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid request' });
    }
    req.validatedBody = parsed.data; // Defaults/transforms must reach the handler.
    next();
  };
}
// Handler uses req.validatedBody, never the original body or an arbitrary spread.
```

Set body limits before parsing. Zod shape validation is only one layer: check current
ownership, allowed transitions and uniqueness in transaction. For HTML, allow only
needed tags/attributes via maintained sanitizer, then render with destination's safe
output API. Prefer plain text for plain comments. Sanitizing a string does not make it
safe in every JavaScript, URL or HTML context. Validate upstream API responses as
untrusted input too.

For outbound URLs, define allowed scheme/hosts, redirect behavior, resolved IP ranges,
credentials policy, timeout, response size. Regex or URL parser alone does not prevent
SSRF or DNS rebinding. File uploads need type/content checks, size limits, isolated
storage, authorization on reads.

## 4. Control abuse without claiming DDoS protection

Use existing gateway and maintained rate-limit store. Authenticate before deriving
authenticated-user key. Never trust user-supplied tier. For anonymous traffic, use
library's supported IPv6-aware IP key handling. Set Express trust proxy to actual
trusted hops; do not blindly enable it for all callers.

For distributed quota, use atomic counter-plus-expiration with defined store-outage
behavior. Avoid handwritten `INCR` then `EXPIRE`: crash between them can leave
permanent key. Separate per-user quotas, per-IP abuse controls, concurrency limits,
upstream service budgets. Record actual window/reset semantics. Send accurate
Retry-After, not hardcoded full-window value. In-memory limiter is per-process unless
shared store is configured.

Test concurrent requests, IPv4/IPv6, forged forwarding headers, unknown tiers, absent
identity, Redis failure, expiration. App rate limits cannot absorb network saturation.
Helmet sets HTTP response headers. It is not DDoS protection, access control or
substitute for upstream capacity controls. Roll out CSP/HSTS against actual deployment
and subdomain policy. Do not copy preload settings blindly.

## 5. Passwords, secrets and logging

Use established identity provider where possible. Store passwords with maintained
password-hashing scheme and calibrated parameters (prefer Argon2id for new designs).
Check breached/common passwords; support passphrases. Do not impose arbitrary
uppercase/symbol composition rules or silently truncate long passwords. Legacy bcrypt
has input-byte limit: handle it explicitly during migration. Character length differs
from UTF-8 byte length.

Keep secrets in approved secret mechanism. Check required configuration at startup
without printing values. Rotate exposed credentials. Never put raw tokens, passwords,
request bodies or complete database exceptions in routine logs. Log bounded event
names, request correlation, safe status/error classes under appropriate
retention/access policy. Sanitized errors should not return mass-assigned user objects.
CORS controls browser cross-origin access; not API authentication or CSRF protection.

## Worked example: a profile update boundary

Given `PATCH /users/:id` with string ID and editable display name:

1. Record authorized caller/tenant and current endpoint behavior in fixtures.
2. Check missing/expired/wrong-audience tokens return 401 before storage access.
3. Send `12abc`, unsafe integer, empty name, extra `role` field. Expect 400 and no
   database mutation. Send padded valid name. Confirm only parsed trimmed value reaches
   owner-and-tenant-scoped update.
4. Try different user's valid ID and cross-tenant ID. Expect documented denial and no
   mutation. Valid owner request updates only allowed property.
5. Exercise quota/store failure. Confirm logs contain no request token or name.

Return route policy, reproduced failure cases, exact test command/output, remaining
gaps. These are checks to execute in target application, not claims that this
repository has tested a deployed API.

## Limitations

Not full identity service, certified security audit or penetration test. Snippets omit
app adapters and integration error middleware. Parser unit tests do not verify database
transactions, proxy behavior or provider sessions. Report any untested route, tenant
path and failure mode explicitly. Do not infer clean security posture from passing
structural checks or risk metadata label.

## References

- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [JWT best current practices, RFC 8725](https://www.rfc-editor.org/rfc/rfc8725)
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Express production security](https://expressjs.com/en/advanced/best-practice-security.html)
- [Zod basic parsing](https://zod.dev/basics)
- Related skills: `designing-apis` (contract design), `api-security` (authorized API testing), `security-and-hardening` (general app hardening).
