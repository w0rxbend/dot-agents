# OWASP Top 10 Risk Mitigation Reference


## Table of Contents

- [Overview](#overview)
- [OWASP Top 10 (2021)](#owasp-top-10-2021)
  - [A01: Broken Access Control](#a01-broken-access-control)
  - [A02: Cryptographic Failures](#a02-cryptographic-failures)
  - [A03: Injection](#a03-injection)
  - [A04: Insecure Design](#a04-insecure-design)
  - [A05: Security Misconfiguration](#a05-security-misconfiguration)
  - [A06: Vulnerable and Outdated Components](#a06-vulnerable-and-outdated-components)
  - [A07: Identification and Authentication Failures](#a07-identification-and-authentication-failures)
  - [A08: Software and Data Integrity Failures](#a08-software-and-data-integrity-failures)
  - [A09: Security Logging and Monitoring Failures](#a09-security-logging-and-monitoring-failures)
  - [A10: Server-Side Request Forgery (SSRF)](#a10-server-side-request-forgery-ssrf)

## Overview

OWASP Top 10 lists most critical web application security risks. This reference gives mitigations per risk, mapped to security architecture controls.

## OWASP Top 10 (2021)

### A01: Broken Access Control

**Risk Description:** Authorization failures let users access unauthorized data or functions.

**Common Examples:**
- Insecure Direct Object References (IDOR): changing URL parameter to access other users' data
- Missing authorization checks on API endpoints
- Privilege escalation (standard user reaches admin functions)
- CORS misconfiguration allows unauthorized origins

**Architectural Mitigations:**
- Use RBAC (role-based access control) or ABAC (attribute-based access control)
- Deny access by default (explicit allow lists)
- Authorization check at every API endpoint
- Use indirect object references (map session → object, not expose IDs)
- Log all authorization failures for monitoring

**Code Example (Node.js/Express):**
```javascript
// Verify user owns resource before returning
app.get('/api/orders/:id', authenticateUser, async (req, res) => {
  const order = await Order.findById(req.params.id);

  // Authorization check: user owns this order
  if (order.userId !== req.user.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  res.json(order);
});
```

---

### A02: Cryptographic Failures

**Risk Description:** Cryptography failures expose sensitive data.

**Common Examples:**
- Cleartext transmission (HTTP instead of HTTPS)
- Weak encryption algorithms (DES, MD5, SHA-1)
- Passwords stored in plaintext or with weak hashing
- Hardcoded cryptographic keys

**Architectural Mitigations:**
- Enforce TLS 1.3 for all data in transit
- Encrypt all sensitive data at rest (AES-256)
- Use strong password hashing (Argon2, bcrypt, scrypt)
- Use key management system (AWS KMS, Azure Key Vault, HashiCorp Vault)
- Rotate encryption keys regularly

---

### A03: Injection

**Risk Description:** Injection flaws (SQL, NoSQL, OS command, LDAP) allow arbitrary code execution.

**Common Examples:**
- SQL injection via unsanitized user input
- NoSQL injection in MongoDB queries
- OS command injection, LDAP injection

**Architectural Mitigations:**
- Use parameterized queries or ORM frameworks
- Input validation (whitelist allowed characters, length limits)
- Least privilege database users (no DROP, CREATE permissions)
- WAF with injection detection rules
- Code scanning (SAST/DAST) in CI/CD

**Code Example (SQL Injection Prevention):**
```javascript
// BAD: String concatenation (vulnerable to SQLi)
const query = `SELECT * FROM users WHERE email = '${userInput}'`;

// GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE email = ?';
db.query(query, [userInput], (err, results) => { ... });
```

---

### A04: Insecure Design

**Risk Description:** Security controls missing or ineffective at design phase.

**Mitigations:**
- Threat model (STRIDE, PASTA) during design
- Apply secure design patterns
- Separation of concerns (business logic apart from presentation)
- Defense in depth architecture
- Security requirements in every user story

---

### A05: Security Misconfiguration

**Risk Description:** Insecure defaults, incomplete setups, verbose errors.

**Common Examples:**
- Default admin credentials unchanged
- Directory listing enabled
- Unnecessary services running
- Verbose error messages reveal system details
- Missing security headers

**Architectural Mitigations:**
- Configuration management (CIS Benchmarks, STIG)
- Remove default accounts and sample applications
- Minimal platform (disable unnecessary features)
- Custom error pages (generic messages)
- Security headers (CSP, HSTS, X-Frame-Options)

---

### A06: Vulnerable and Outdated Components

**Risk Description:** Components with known vulnerabilities in use.

**Architectural Mitigations:**
- Generate SBOM (Software Bill of Materials)
- Continuous dependency scanning (Snyk, Dependabot, Trivy)
- Automated security updates
- Remove unused dependencies
- Monitor security advisories

---

### A07: Identification and Authentication Failures

**Risk Description:** Weak authentication and session management.

**Architectural Mitigations:**
- Multi-factor authentication (MFA) for all users
- Strong password policies (length > complexity)
- Secure session management (HttpOnly, Secure, SameSite flags)
- Rate-limit authentication endpoints
- Lock accounts after failed attempts

---

### A08: Software and Data Integrity Failures

**Risk Description:** Code and infrastructure not protected from integrity violations.

**Architectural Mitigations:**
- Code signing and verification
- SLSA framework for build integrity
- Subresource Integrity (SRI) for CDN resources
- Integrity checks (checksums, digital signatures)

---

### A09: Security Logging and Monitoring Failures

**Risk Description:** Insufficient logging and monitoring delay breach detection.

**Architectural Mitigations:**
- Centralized logging (SIEM)
- Log all security events (authentication, authorization failures, input validation failures)
- Immutable logs (append-only)
- Real-time alerting
- UEBA for anomaly detection

---

### A10: Server-Side Request Forgery (SSRF)

**Risk Description:** Application fetches remote resource without validating URL.

**Architectural Mitigations:**
- Input validation (whitelist allowed domains)
- Network segmentation (deny outbound traffic from application tier)
- Disable unnecessary URL schemas (file://, gopher://)
