---
name: code-audit
description: "Authorized white-box source-code security review - Semgrep/CodeQL/Bandit/gosec pattern hunting plus manual triage of each hit for reachability and exploitability, with fix verification. Use for a SAST review or PR/diff security audit of first-party code; use dependency-scanning for third-party CVEs."
risk: safe
source: "https://github.com/zhaoxuya520/reverse-skill"
source_repo: "zhaoxuya520/reverse-skill"
source_type: community
date_added: "2026-08-25"
license: "MIT"
license_source: "https://github.com/zhaoxuya520/reverse-skill/blob/main/LICENSE"
---
# Source Code Security Audit

White-box review of first-party code: run static analysis, then manually verify each hit. A scanner dump is not an audit. This skill covers your own code logic; use `dependency-scanning` for third-party dependencies and the supply chain.

## When to use

- Reviewing a codebase for security defects with static analysis.
- Security review of a pull request or diff.
- Verifying that a vulnerability fix actually removes the flawed pattern.

## Workflow

### 1. Scope and threat model

```text
[ ] Trust boundaries: user input, files, deserialization, SSRF sinks, auth middleware
[ ] High-value assets: authentication, payments, admin surfaces, secret handling
```

### 2. Automated scan

```bash
semgrep --config auto .
# or a focused ruleset
semgrep --config p/owasp-top-ten .
```

### 3. Manual verification (required)

```text
[ ] For each SAST hit: reachable? exploitable? false positive?
[ ] AuthZ: IDOR / broken object-level access, missing checks, wrong multi-tenant isolation
[ ] Injection: SQL / command / template / LDAP
[ ] Crypto: hardcoded keys, ECB mode, home-grown crypto
```

### 4. Output

```text
Finding: location + data flow + proof of concept + remediation
Optional: CWE and/or MITRE ATT&CK references
```

## Tooling

| Tool | Language / scope |
|------|------------------|
| Semgrep | Multi-language, fast rules |
| CodeQL | Deep data-flow (GitHub) |
| Bandit | Python |
| gosec / staticcheck | Go |
| SpotBugs / FindSecBugs | Java |

## References

- `references/sast-review-checklist.md`

## Done when

- Each finding was manually verified, not just copied from scanner output.
- Each finding includes a remediation recommendation.
- Work stayed within the authorized repository scope.
- A fix verification confirms the flawed pattern is gone and no equivalent remains.

## Limitations

- Static analysis produces false positives; manual triage is required.
- Coverage depends on the chosen engine's language support.

> Adapted from [zhaoxuya520/reverse-skill](https://github.com/zhaoxuya520/reverse-skill) (MIT); body translated to English and repository-foreign references removed.
