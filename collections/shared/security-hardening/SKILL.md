---
name: security-hardening
description: "Harden hosts, containers, cloud accounts, networks and databases against CIS Benchmarks and least-privilege defaults, with scanning to verify. Use for infrastructure hardening or a pre-production infrastructure review; use security-and-hardening for application code and kubernetes-hardening for cluster-specific controls."
---

# Security Hardening

## When to Use This Skill

Use when:
- Hardening production infrastructure before deployment
- Meeting compliance requirements (SOC 2, PCI-DSS, HIPAA, FedRAMP)
- Building zero-trust security architecture
- Reducing container or cloud misconfiguration risk
- Preparing for security audits or penetration tests
- Automating security baseline enforcement
- Responding to vulnerability scan findings

## Hardening Layers

### Layer 1: Operating System (Linux)
- Kernel parameter tuning (sysctl)
- SSH hardening
- User and group management
- File system permissions and mount options
- Service minimization
- SELinux/AppArmor enforcement

### Layer 2: Container
- Minimal base images (Chainguard, Distroless, Alpine)
- Non-root execution
- Read-only root filesystems
- Seccomp and AppArmor profiles
- Resource limits, dropped capabilities
- Pod Security Standards enforcement

### Layer 3: Cloud Configuration
- IAM least privilege and MFA enforcement
- Network security groups and NACLs
- Encryption at rest and in transit
- Public access blocking
- Logging and monitoring enabled
- CSPM (Cloud Security Posture Management) integration

### Layer 4: Network
- Default-deny network policies
- Network segmentation and micro-segmentation
- TLS/mTLS enforcement
- Firewall rule minimization
- DNS security (DNSSEC, DNS filtering)

### Layer 5: Database
- Authentication and authorization hardening
- Connection encryption (SSL/TLS)
- Audit logging enabled
- Network isolation and access control
- Role-based permissions with least privilege

## Core Hardening Principles

### 1. Default Deny, Explicit Allow
Deny all access by default. Permit only required operations. Apply default-deny firewall rules and network policies, then allow specific traffic.

### 2. Least Privilege Access
Grant minimum permissions needed. Use RBAC, IAM policies scoped to specific resources, and database roles with limited permissions (no DELETE or DDL unless required).

### 3. Defense in Depth
Layer overlapping controls: network firewalls, authentication, authorization, audit logging, encryption.

### 4. Minimal Attack Surface
Remove unneeded components, services and permissions. Use minimal container base images, disable unused services, drop all Linux capabilities unless required.

### 5. Fail Securely
On error or misconfiguration, default to secure state. Authentication failures deny access. Missing configuration uses restrictive defaults. Monitoring failures trigger immediate alerts.

## Hardening Priority Framework

Prioritize by exposure and data sensitivity:

### Critical Priority: Internet-Facing Systems
**Apply immediately:**
- Container hardening (minimal images, non-root, read-only)
- Network segmentation (DMZ, WAF, DDoS protection)
- TLS termination and certificate management
- Rate limiting and authentication
- Real-time monitoring and alerting

**Tools:** Trivy, Falco, ModSecurity, Cloudflare

### High Priority: Systems with Sensitive Data
**Apply before production:**
- Encryption at rest (AES-256, KMS-managed keys)
- Strict access controls (RBAC, least privilege)
- Comprehensive audit logging
- Database connection encryption
- Regular vulnerability scanning

**Tools:** Checkov, Prowler, Lynis, OpenSCAP

### Standard Priority: Internal Systems
**Apply systematically:**
- OS hardening (CIS Benchmarks)
- Service minimization
- Patch management automation
- Configuration management
- Basic monitoring

**Tools:** Ansible, Puppet, kube-bench, docker-bench-security

## CIS Benchmark Integration

### Automated CIS Scanning

**Docker CIS Benchmark:**
```bash
# Hub image docker/docker-bench-security is stale (2019) and gets host net/pid + Docker socket
# (root on host): never pull it. Run a reviewed release tag on the host instead.
GH_TELEMETRY=false gh repo clone docker/docker-bench-security -- --depth 1 --branch v1.6.1   # gh sends usage telemetry unless off
cd docker-bench-security && less docker-bench-security.sh   # review before running as root
sudo sh docker-bench-security.sh
```

**Kubernetes CIS Benchmark:**
```bash
# Pin a release tag (never main), read the manifest, then apply your reviewed copy
curl -fsSLo kube-bench-job.yaml https://raw.githubusercontent.com/aquasecurity/kube-bench/v0.16.0/job.yaml
less kube-bench-job.yaml   # check image tag, hostPath mounts, namespace
kubectl apply -f kube-bench-job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=300s
kubectl logs job/kube-bench
kubectl delete -f kube-bench-job.yaml
```

**Linux CIS Benchmark:**
```bash
# Using Lynis
lynis audit system --quick

# Using OpenSCAP: list the profile ids your datastream actually ships first
oscap info /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
# Ubuntu datastreams use cis_level1_server / cis_level2_server (no plain "cis")
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
```

### Key CIS Controls Mapping

| CIS Control | Hardening Action | Layer |
|-------------|------------------|-------|
| 4.1 Secure Configuration | Apply hardening baselines | All layers |
| 5.1 Account Management | Enforce least privilege, MFA | OS, Cloud |
| 6.1 Access Control | RBAC, network policies | All layers |
| 8.1 Audit Log Management | Enable comprehensive logging | All layers |
| 13.1 Network Monitoring | Deploy IDS/IPS, flow logs | Network |
| 3.1 Data Protection | Enable encryption at rest/transit | Cloud, Database |

Detailed CIS control mapping: `references/cis-benchmark-mapping.md`.

## Container Base Image Selection

| Use Case | Recommended Base | Size | CVEs | Trade-off |
|----------|------------------|------|------|-----------|
| **Production apps** | Chainguard Images | ~10MB | 0 | Minimal, zero CVEs |
| **Minimal Linux** | Alpine | ~5MB | Few | Small, auditable |
| **Compatibility** | Distroless | ~20MB | Few | No shell, harder debug |
| **Debugging** | Debian slim | ~80MB | More | Has debugging tools |
| **Legacy apps** | Ubuntu | ~100MB | Many | Full compatibility |

**Production recommendation:** Chainguard Images or Distroless in production, Alpine for development.

## Verification and Auditing

Verify hardening continuously, not only at implementation.

### Automated Security Scanning

**Container vulnerability scanning:**
```bash
# Trivy: Comprehensive vulnerability and misconfiguration scanner.
# Sends usage telemetry to Aqua by default: opt out wherever it runs (CI env too)
export TRIVY_DISABLE_TELEMETRY=true TRIVY_SKIP_VERSION_CHECK=true
trivy image --severity HIGH,CRITICAL myapp:latest

# Grype: Fast vulnerability scanner
grype myapp:latest
```

**Infrastructure as Code scanning:**
```bash
# Checkov: Multi-cloud IaC scanner
checkov -d terraform/ --framework terraform

# Terrascan: Policy-as-code scanner
terrascan scan -t terraform -d terraform/
```

**Kubernetes security scanning:**
```bash
# Kubesec: Security risk analysis
kubesec scan k8s/deployment.yaml

# Polaris: Configuration validation
polaris audit --format=pretty

# Trivy K8s scanning
trivy k8s --report summary cluster
```

**Cloud security posture:**
```bash
# Prowler: AWS security assessment
prowler aws --services s3 iam ec2

# ScoutSuite: Multi-cloud security audit
scout aws --services s3 iam ec2
```

### Continuous Verification Pipeline

```yaml
# GitHub Actions example
name: Security Hardening Verification

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily scan

jobs:
  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:test .

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@<pinned-sha> # vX.Y.Z - never a branch ref
        with:
          image-ref: 'myapp:test'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on findings

  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan IaC with Checkov
        uses: bridgecrewio/checkov-action@<pinned-sha> # vX.Y.Z - never a branch ref
        with:
          directory: terraform/
          framework: terraform
          soft_fail: false
```

### Compliance Reporting

```bash
# Generate CIS compliance report
kube-bench run --json > cis-report.json

# Generate vulnerability report for the exact image you ship
trivy image --format json --output vuln-report.json myapp@sha256:<digest>
```

Store JSON reports as build artifacts or evidence. Aggregate them in compliance tooling (see `implementing-compliance` skill).

## Automation Tools

### Hardening Automation
- **Ansible/Puppet/Chef:** Configuration management for OS hardening
- **Terraform/Pulumi:** Infrastructure as Code with security modules
- **Cloud Custodian:** Cloud resource policy enforcement
- **OPA/Gatekeeper:** Kubernetes policy enforcement
- **Kyverno:** Kubernetes-native policy management

### Monitoring Tools
- **Falco:** Runtime threat detection for containers
- **Sysdig:** Container security and monitoring
- **Wazuh:** Host and endpoint security monitoring
- **OSSEC:** Host-based intrusion detection

## Quick Reference: Common Hardening Tasks

### Harden SSH Access
Lockout guard for remote hosts: first confirm key login from a **second** terminal
(`ssh -o PreferredAuthentications=publickey -o PasswordAuthentication=no user@host`).
Keep current session open until a fresh login works with new config.

```bash
# /etc/ssh/sshd_config.d/00-hardening.conf
# (00- sorts before 50-cloud-init.conf; sshd keeps the FIRST value it reads, so a
#  later cloud-init "PasswordAuthentication yes" cannot override this file)
PermitRootLogin no
PasswordAuthentication no
PermitEmptyPasswords no
MaxAuthTries 3
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
```

```bash
sshd -t || exit 1                                   # validate before touching the daemon
systemctl reload ssh 2>/dev/null || systemctl reload sshd   # ssh on Debian/Ubuntu, sshd elsewhere
sshd -T | grep -E '^(passwordauthentication|permitrootlogin) '  # effective values
```

`scripts/harden-linux.py` automates this with same checks. Only previews unless given `--apply`.

### Harden Container Image
```dockerfile
# Minimal base, pinned by digest (Renovate/Dependabot bumps it)
FROM cgr.dev/chainguard/python:latest@sha256:<digest>

# App files owned by root and not writable by the runtime user
COPY app /app
WORKDIR /app

# Non-root user
USER nonroot
ENTRYPOINT ["python", "-m", "app"]
```

Dockerfile cannot make root filesystem read-only or drop capabilities. Set those at
runtime (`docker run --read-only --cap-drop=ALL --security-opt no-new-privileges`, or
Kubernetes `securityContext` below).

### Harden Kubernetes Pod
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  seccompProfile:
    type: RuntimeDefault
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

### Harden AWS S3 Bucket
```hcl
resource "aws_s3_bucket_public_access_block" "secure" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

### Harden Network with Default Deny
```yaml
# Kubernetes NetworkPolicy: deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### Harden Database Access
```sql
-- PostgreSQL hardening
REVOKE ALL ON DATABASE app FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE ROLE app_user WITH LOGIN;
GRANT CONNECT ON DATABASE app TO app_user;
GRANT SELECT, INSERT, UPDATE ON app.orders TO app_user;

-- Force SSL connections
ALTER SYSTEM SET ssl = on;
-- In pg_hba.conf, only the application subnet, TLS only:
--   hostssl app app_user 10.0.1.0/24 scram-sha-256
```

## Detailed Hardening Guides

Layer-specific guides:
- **OS hardening:** `references/linux-hardening.md`
- **Container hardening:** `references/container-hardening.md`
- **Cloud hardening:** `references/cloud-hardening.md`
- **Network hardening:** `references/network-hardening.md`
- **Database hardening:** `references/database-hardening.md`

Automation scripts:
- **Python automation:** `scripts/harden-linux.py` (dry run by default; `--apply` to change host, `--confirm-key-login` before it touches sshd, `--disable-ip-forward` only on non-container, non-router hosts)
- **Infrastructure scanning:** `scripts/scan-infrastructure.sh`

Working examples:
- **Linux configurations:** `examples/linux/`
- **Kubernetes manifests:** `examples/kubernetes/`

## Integration with Related Skills

- **security-and-hardening:** Application-code controls (input, authn/authz, secrets in code)
- **hashicorp-vault:** Secrets storage and rotation
- **kubernetes-hardening:** Pod security, RBAC, admission and network policy in Kubernetes
- **dockerfile-optimise:** Hardened, minimal container images
- **building-ci-pipelines:** Automated security scanning stages
- **audit-logging:** Security monitoring and SIEM integration
- **implementing-compliance:** Mapping hardening to compliance requirements

## Anti-Patterns to Avoid

**❌ Security through obscurity**
- Obscurity is not security. Use proven controls.

**❌ Hardening without testing**
- Test that hardening changes don't break functionality

## Getting Started

1. **Assess current posture:** Run CIS benchmark scans
2. **Prioritize:** Internet-facing → sensitive data → internal
3. **Apply baseline hardening:** OS, container, cloud basics
4. **Automate:** Scripts and IaC for consistency
5. **Verify continuously:** Add scanning to CI/CD
6. **Monitor:** Deploy runtime security monitoring
7. **Iterate:** Review and improve hardening regularly

Step-by-step: start with `references/linux-hardening.md` or `references/container-hardening.md`, by infrastructure type.

