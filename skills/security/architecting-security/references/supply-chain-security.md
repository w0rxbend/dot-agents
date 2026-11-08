# Supply Chain Security Reference

## Table of Contents

- [Overview](#overview)
- [SLSA Framework](#slsa-framework)
  - [4 SLSA Levels](#4-slsa-levels)
  - [SLSA Requirements Matrix](#slsa-requirements-matrix)
  - [SLSA Implementation Steps](#slsa-implementation-steps)
- [SBOM (Software Bill of Materials)](#sbom-software-bill-of-materials)
  - [SBOM Standards](#sbom-standards)
  - [CycloneDX SBOM Structure](#cyclonedx-sbom-structure)
  - [Generating SBOMs](#generating-sboms)
  - [SBOM Use Cases](#sbom-use-cases)
- [Dependency Scanning Tools](#dependency-scanning-tools)
- [Dependency Management Best Practices](#dependency-management-best-practices)
  - [1. Minimize Dependencies](#1-minimize-dependencies)
  - [2. Pin Dependency Versions](#2-pin-dependency-versions)
  - [3. Continuous Dependency Scanning](#3-continuous-dependency-scanning)
  - [4. Automated Security Updates](#4-automated-security-updates)
  - [5. Vendor and Maintainer Monitoring](#5-vendor-and-maintainer-monitoring)
  - [6. Private Dependency Mirrors](#6-private-dependency-mirrors)
- [Supply Chain Attack Vectors](#supply-chain-attack-vectors)
  - [1. Compromised Dependencies](#1-compromised-dependencies)
  - [2. Typosquatting](#2-typosquatting)
  - [3. Dependency Confusion](#3-dependency-confusion)
  - [4. Compromised Build Pipeline](#4-compromised-build-pipeline)
- [Summary](#summary)

## Overview

**Key Frameworks:**
- **SLSA (Supply-chain Levels for Software Artifacts):** Build integrity framework
- **SBOM (Software Bill of Materials):** Dependency transparency
- **SSDF (Secure Software Development Framework):** NIST SP 800-218

## SLSA Framework

**Purpose:** Protect artifacts from tampering, ensure build integrity

### 4 SLSA Levels

**SLSA Level 1: Provenance**
- Provenance generated automatically, documents how artifact was built
- NOT tamper-proof (can be forged)

**Example:** GitHub Actions basic workflow with attestation

**SLSA Level 2: Hosted Build Platform**
- Hosted build service (GitHub Actions, Cloud Build, GitLab CI)
- Platform generates provenance (more trustworthy than Level 1)
- Source and build logs available

**Example:** GitHub Actions with signed attestations

**SLSA Level 3: Hardened Build Platform**
- Build service hardened against admin tampering
- Provenance non-falsifiable
- Isolated build execution
- Audit logs retained

**Example:** Google Cloud Build with Binary Authorization

**SLSA Level 4: Hermetic, Reproducible Builds**
- Hermetic builds (no network access or external dependencies during build)
- Reproducible (same inputs = same output)
- Two-person review (pull request approval) for all changes
- Immutable build history

**Example:** Debian reproducible builds, Bazel hermetic builds

### SLSA Requirements Matrix

| Requirement | L1 | L2 | L3 | L4 |
|-------------|----|----|----|----|
| Provenance exists | ✓ | ✓ | ✓ | ✓ |
| Hosted build platform | | ✓ | ✓ | ✓ |
| Build service hardened | | | ✓ | ✓ |
| Provenance non-falsifiable | | | ✓ | ✓ |
| Isolated build process | | | | ✓ |
| Hermetic builds | | | | ✓ |
| Reproducible builds | | | | ✓ |
| Two-party review | | | | ✓ |

### SLSA Implementation Steps

**Step 1: Generate Provenance (SLSA L1)**

Generate attestations with GitHub Actions:

```yaml
name: Build with Provenance
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      attestations: write
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: make build
      - name: Generate attestation
        uses: actions/attest-build-provenance@<pinned-sha> # current major
        with:
          subject-path: 'dist/myapp'
```

**Step 2: Use Hosted Build Service (SLSA L2)**

Migrate to GitHub Actions, GitLab CI or Cloud Build (already hosted).

**Step 3: Harden Build Platform (SLSA L3)**

- Require reviews on protected branches
- Use GitHub Environment protection rules
- Enable audit logging
- Restrict admin access to build pipelines

**Step 4: Implement Hermetic Builds (SLSA L4)**

- Container-based builds with pinned images
- No network access during build (cache dependencies)
- Reproducible builds with Bazel or Nix

## SBOM (Software Bill of Materials)

### SBOM Standards

**1. CycloneDX (OWASP)**
- JSON or XML format
- Comprehensive (components, services, vulnerabilities)
- Strong tooling ecosystem

**2. SPDX (Linux Foundation)**
- ISO/IEC 5962:2021 standard
- Extensive license information
- Wide industry adoption

**3. SWID (Software Identification Tags)**
- ISO/IEC 19770-2 standard
- XML format
- Software asset management focus

### CycloneDX SBOM Structure

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "metadata": {
    "component": {
      "type": "application",
      "name": "my-app",
      "version": "1.0.0"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "express",
      "version": "4.18.2",
      "purl": "pkg:npm/express@4.18.2",
      "licenses": [{"license": {"id": "MIT"}}],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "abc123..."
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:npm/my-app@1.0.0",
      "dependsOn": ["pkg:npm/express@4.18.2"]
    }
  ],
  "vulnerabilities": [
    {
      "id": "CVE-2024-1234",
      "source": {"name": "NVD"},
      "ratings": [{"severity": "high"}],
      "affects": [{"ref": "pkg:npm/express@4.18.2"}]
    }
  ]
}
```

### Generating SBOMs

**Node.js (NPM):**
```bash
# Using CycloneDX
npx @cyclonedx/cyclonedx-npm@6.0.1 --output-file sbom.json

# Using Syft
syft dir:. -o cyclonedx-json > sbom.json
```

**Python:**
```bash
# Using CycloneDX
pip install cyclonedx-bom
cyclonedx-py -o sbom.json

# Using Syft
syft dir:. -o cyclonedx-json > sbom.json
```

**Java (Maven):**
```bash
# Using CycloneDX Maven Plugin
mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom
```

**Container Images:**
```bash
# Using Syft
syft nginx:latest -o cyclonedx-json > sbom.json

# Using Trivy (sends usage telemetry by default: opt out)
export TRIVY_DISABLE_TELEMETRY=true TRIVY_SKIP_VERSION_CHECK=true
trivy image --format cyclonedx nginx:latest > sbom.json
```

### SBOM Use Cases

**1. Vulnerability Management**

When CVE disclosed (e.g., Log4Shell):
```bash
# Search SBOM for affected component
cat sbom.json | jq '.components[] | select(.name == "log4j-core")'

# Output: All instances of log4j-core and versions
# Action: Identify affected applications and prioritize patches
```

**2. License Compliance**

```bash
# Extract all licenses from SBOM
cat sbom.json | jq '.components[].licenses[].license.id' | sort | uniq

# Flag non-approved licenses
cat sbom.json | jq '.components[] | select(.licenses[].license.id == "GPL-3.0")'
```

**3. Supply Chain Risk Assessment**

```bash
# Identify all components from specific maintainer
cat sbom.json | jq '.components[] | select(.supplier.name == "Compromised Vendor")'

# Identify components without hash verification
cat sbom.json | jq '.components[] | select(.hashes == null)'
```

**4. Incident Response**

During security incident:
- Quickly find every application using vulnerable component
- Assess blast radius across organization
- Prioritize remediation from SBOM data

## Dependency Scanning Tools

| Tool | Languages | Features | Best For |
|------|-----------|----------|----------|
| **Dependabot** | Multi-language | Automated PRs, GitHub native | GitHub users |
| **Snyk** | Multi-language | Vuln scanning, license compliance, fix PRs | Developers, CI/CD |
| **OWASP Dependency-Check** | Java, .NET, Python, Ruby, Node.js | CVE scanning, CLI/CI | Open-source projects |
| **Renovate** | Multi-language | Automated updates, flexible config | Advanced automation |
| **Trivy** | Multi-language, containers, IaC | CVE scanning, misconfiguration | Containers, cloud-native |
| **Grype** | Multi-language, containers | Fast CVE scanning | CI/CD pipelines |
| **JFrog Xray** | Multi-language, artifacts | Artifact scanning, policy enforcement | Enterprise, JFrog users |

## Dependency Management Best Practices

### 1. Minimize Dependencies

- Remove unused dependencies
- Justify each new dependency before adding it
- For simple functionality, weigh in-house code vs. new dependency
- Use tree-shaking and dead code elimination

**Example:**
```bash
# Analyze dependency tree
npm ls --all

# Find unused dependencies (Node.js)
npx depcheck@1.4.7

# Remove unused
npm uninstall <unused-package>
```

### 2. Pin Dependency Versions

- Commit lock files (package-lock.json, Pipfile.lock, go.sum)
- Exact versions in production (avoid `^` or `~` ranges)
- Pin Docker base image versions with SHA digests

**Example:**
```dockerfile
# Bad: Uses mutable tag
FROM node:18

# Better: Use specific version
FROM node:18.19.0

# Best: Pin to specific SHA digest (immutable)
FROM node:18.19.0@sha256:abc123...
```

### 3. Continuous Dependency Scanning

- Scan every commit (CI/CD integration)
- Scheduled scans (nightly) even without code changes
- Monitor security advisories (GitHub Security Advisories, NVD)

**Example (GitHub Actions):**
```yaml
name: Dependency Scan
on:
  push:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy
        uses: aquasecurity/trivy-action@<pinned-sha> # vX.Y.Z - never a branch ref
        env:
          TRIVY_DISABLE_TELEMETRY: 'true'
          TRIVY_SKIP_VERSION_CHECK: 'true'
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
```

### 4. Automated Security Updates

- Enable Dependabot security updates
- Auto-merge only patch security updates, via a workflow (SHA-pinned `dependabot/fetch-metadata`) gated on required checks and branch protection
- Test updates automatically (CI/CD)

**Example (Dependabot config):**
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    # Dependabot has no auto-merge key; see workflow note above
```

### 5. Vendor and Maintainer Monitoring

- Monitor maintainer activity (last release, commit frequency)
- Check maintainer count (single maintainer = risk)
- Subscribe to vendor security advisories
- Weigh package reputation and trust scores

**Red Flags:**
- No updates in > 1 year
- Single maintainer with no activity
- Recent ownership transfer
- Unusual dependency additions
- Obfuscated code

### 6. Private Dependency Mirrors

- Host private package registry (JFrog Artifactory, Nexus, npm Enterprise)
- Proxy public registries through private mirror
- Scan and approve packages before internal use
- Audit all package downloads

**Architecture:**
```
Developer → Private Registry → Public Registry (npm, PyPI)
              (scan, approve)      (upstream source)
```

## Supply Chain Attack Vectors

### 1. Compromised Dependencies

**Attack:** Attacker publishes malicious package or compromises existing one

**Examples:**
- event-stream (npm): Malicious code injected to steal cryptocurrency
- ua-parser-js (npm): Compromised package downloaded cryptocurrency miner
- codecov (Bash uploader): Compromised to steal credentials

**Mitigations:**
- Dependency scanning (detect known malicious packages)
- SBOM generation (visibility into all dependencies)
- Subresource Integrity (SRI) for CDN-hosted scripts
- Private package mirrors with approval workflow

### 2. Typosquatting

**Attack:** Attacker creates package named like popular package

**Examples:**
- `requessts` (typo of `requests` in Python)
- `electorn` (typo of `electron` in npm)

**Mitigations:**
- Review dependency additions
- Use package manager lockfiles (prevent unexpected installs)
- Namespace verification (official org/maintainer)
- IDE/linter warnings for common typos

### 3. Dependency Confusion

**Attack:** Attacker publishes public package with same name as internal package. Package manager installs public (malicious) version.

**Examples:**
- Alex Birsan's research (2021): Compromised Apple, Microsoft, Tesla via dependency confusion

**Mitigations:**
- Use scoped packages (@mycompany/package-name)
- Configure package manager to prefer private registry
- Reserve namespaces on public registries

**Example (npm config):**
```ini
# .npmrc
@mycompany:registry=https://npm.internal.company.com
registry=https://registry.npmjs.org
```

### 4. Compromised Build Pipeline

**Attack:** Attacker gains CI/CD pipeline access, injects malicious code during build

**Examples:**
- SolarWinds Orion (2020): Build pipeline compromised to inject backdoor
- CodeCov (2021): Compromised Bash uploader script

**Mitigations:**
- SLSA Level 3+ (hardened build platform)
- Least privilege for CI/CD service accounts
- Audit logging for all build pipeline changes
- Two-party review for pipeline modifications
- Hermetic builds (no network access during build)

## Summary

**Priority Actions:**
- Generate SBOM for all applications (CycloneDX)
- Add dependency scanning to CI/CD (Trivy, Snyk)
- Reach SLSA Level 2 (GitHub Actions with attestations)
- Enable automated security updates (Dependabot, Renovate)
- Establish incident response plan for supply chain incidents
