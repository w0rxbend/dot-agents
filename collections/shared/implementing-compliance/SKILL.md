---
name: implementing-compliance
description: "Implement SOC 2, HIPAA, PCI-DSS and GDPR technical controls with a unified control map, policy-as-code (OPA, Checkov) and automated evidence collection. Use when a system must pass an audit or meet a regulatory framework; use architecting-security for framework-agnostic security design."
---

# Compliance Frameworks

Implement continuous compliance with major regulatory frameworks through unified control mapping, policy-as-code enforcement, and automated evidence collection.

## Purpose

Modern compliance is a continuous engineering discipline requiring technical implementation of security controls. This skill provides patterns for SOC 2 Type II, HIPAA, PCI-DSS 4.0, and GDPR compliance using infrastructure-as-code, policy automation, and evidence collection. Focus on unified controls that satisfy multiple frameworks simultaneously to reduce implementation effort by 60-80%.

## When to Use

Invoke when:
- Building SaaS products requiring SOC 2 Type II for enterprise sales
- Handling healthcare data (PHI) requiring HIPAA compliance
- Processing payment cards requiring PCI-DSS validation
- Serving EU residents and processing personal data under GDPR
- Implementing security controls that satisfy multiple compliance frameworks
- Automating compliance evidence collection and audit preparation
- Enforcing compliance policies in CI/CD pipelines

## Framework Selection

### Tier 1: Trust & Security Certifications

**SOC 2 Type II**
- Audience: SaaS vendors, cloud service providers
- When required: Enterprise B2B sales, handling customer data
- Timeline: 6-12 month observation period
- No fixed testing cadence or breach-notification deadline in the Trust Services Criteria; auditors and customer contracts set those expectations (often a defined notification window such as 72 hours)

**ISO 27001**
- Audience: Global enterprises
- When required: International business, government contracts
- Timeline: 3-6 month certification, annual surveillance

### Tier 2: Industry-Specific Regulations

**HIPAA (Healthcare)**
- Audience: Healthcare providers, health tech handling PHI
- When required: Processing Protected Health Information
- Security Rule changes were proposed in 2025 (stricter MFA, encryption, asset inventory); check the current status before treating them as mandatory

**PCI-DSS 4.0 (Payment Card Industry)**
- Audience: Merchants, payment processors
- When required: Processing, storing, transmitting cardholder data
- Future-dated v4.0 requirements became mandatory after March 31, 2025
- Key changes: Client-side security, 12-char passwords, enhanced MFA

### Tier 3: Privacy Regulations

**GDPR (EU Privacy)**
- Audience: Organizations processing EU residents' data
- When required: EU customers/users (extraterritorial)
- Breach notice to the supervisory authority within 72 hours (Art. 33); fines up to EUR 20M or 4% of global annual turnover (Art. 83)

**CCPA/CPRA (California Privacy)**
- Audience: Businesses serving California residents
- When required: Revenue >$25M, or 100K+ CA residents, or 50%+ revenue from data sales

For detailed framework requirements, see [references/soc2-controls.md](references/soc2-controls.md), [references/hipaa-safeguards.md](references/hipaa-safeguards.md), [references/pci-dss-requirements.md](references/pci-dss-requirements.md), and [references/gdpr-articles.md](references/gdpr-articles.md).

## Universal Control Implementation

### Unified Control Strategy

Implement controls once, map to multiple frameworks. Reduces effort by 60-80%.

**Implementation Priority:**
1. **Encryption** (ENC-001, ENC-002): AES-256 at rest, TLS 1.3 in transit
2. **Access Control** (MFA-001, RBAC-001): MFA, RBAC, least privilege
3. **Audit Logging** (LOG-001): Centralized, immutable, retention set per framework (see below)
4. **Monitoring** (MON-001): SIEM, intrusion detection, alerting
5. **Incident Response** (IR-001): Detection, escalation, breach notification

### Control Categories

**Identity & Access:**
- Multi-factor authentication for privileged access
- Role-based access control with least privilege
- Quarterly access reviews
- Password policy: 12+ characters, complexity

**Data Protection:**
- Encryption: AES-256 (rest), TLS 1.3 (transit)
- Data classification and tagging
- Retention policies aligned with regulations
- Data minimization

**Logging & Monitoring:**
- Centralized audit logging (all auth and data access)
- Retention per framework minimum: PCI-DSS 12 months (3 months immediately available, Req 10.5.1); HIPAA keeps required documentation 6 years (§164.316(b)(2)); SOC 2 and ISO 27001 set no fixed period (your policy, covering the audit period); GDPR storage limitation (Art. 5(1)(e)) means minimizing or pseudonymizing personal data in long-lived logs. See the `audit-logging` skill, which is the authority on retention
- Immutable storage (S3 Object Lock)
- Real-time alerting

**Network Security:**
- Network segmentation and VPC isolation
- Firewalls with deny-by-default
- Intrusion detection/prevention
- Regular vulnerability scanning

**Incident Response:**
- Documented incident response plan
- Automated detection and alerting
- Breach notification: HIPAA without unreasonable delay and within 60 days; GDPR 72h to the supervisory authority; SOC 2 per contract/policy; PCI-DSS immediately to the acquirer and card brands

**Business Continuity:**
- Automated backups with defined RPO/RTO
- Multi-region disaster recovery
- Regular failover testing

For complete control implementations, see [references/control-mapping-matrix.md](references/control-mapping-matrix.md).

## Compliance as Code

### Policy Enforcement with OPA

Enforce compliance policies in CI/CD before infrastructure deployment.

**Architecture:**
```
Git Push → Terraform Plan → JSON → OPA Evaluation
                                    ├─► Pass → Deploy
                                    └─► Fail → Block
```

**Example: Encryption Policy**

Enforce encryption requirements (SOC 2 CC6.1, HIPAA §164.312(a)(2)(iv), PCI-DSS Req 3.4):

See examples/opa-policies/encryption.rego for complete implementation.

**CI/CD Integration:**
```bash
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json
# Fails the job (exit 1) if any compliance.* package produces a deny message
opa eval --data policies/ --input tfplan.json --fail-defined 'data.compliance[_].deny[_]'
# Print every message as a JSON array
opa eval --data policies/ --input tfplan.json --format raw '[m | m := data.compliance[_].deny[_]]'
```

The example policies use Rego v1 syntax (`deny contains msg if { ... }`), which OPA 1.0+ requires by default.

### Static Analysis with Checkov

Scan IaC with built-in compliance framework support:

```bash
# Run all built-in checks; keep machine-readable output as audit evidence
checkov -d ./terraform -o json > reports/checkov.json

# Restrict to the checks mapped to a control (check IDs, not framework names)
checkov -d ./terraform --check CKV_AWS_19,CKV_AWS_145
```

`--check` takes check IDs; maintain your own control-to-check-ID mapping (Checkov's framework mappings require the commercial platform). Write organization-specific rules as custom Checkov policies or as OPA policies (see `examples/opa-policies/`).

### Automated Testing

Integrate compliance validation into test suites:

```python
def test_s3_encrypted(terraform_plan):
    """SOC2:CC6.1, HIPAA:164.312(a)(2)(iv)"""
    buckets = get_resources(terraform_plan, "aws_s3_bucket")
    encrypted = get_encryption_configs(terraform_plan)
    assert all_buckets_encrypted(buckets, encrypted)

def test_opa_policies():
    result = subprocess.run(
        ["opa", "eval", "--data", "policies/", "--input", "tfplan.json",
         "--format", "raw", "[m | m := data.compliance[_].deny[_]]"],
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == []
```

## Technical Control Implementations

### Encryption at Rest

**Standards:** AES-256, managed KMS, automatic rotation

**AWS Example:**
```hcl
resource "aws_kms_key" "data" {
  enable_key_rotation = true
  tags = { Compliance = "ENC-001" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
  }
}

resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id       = aws_kms_key.data.arn
}
```

For complete encryption implementations including Azure and GCP, see [references/encryption-implementations.md](references/encryption-implementations.md).

### Encryption in Transit

**Standards:** TLS 1.3 (TLS 1.2 minimum), strong ciphers, HSTS

**ALB Example:**
```hcl
resource "aws_lb_listener" "https" {
  port       = 443
  protocol   = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}
```

### Multi-Factor Authentication

**Standards:** TOTP, hardware tokens, biometric for privileged access

**AWS IAM Enforcement:**
```hcl
resource "aws_iam_policy" "require_mfa" {
  policy = jsonencode({
    Statement = [{
      Effect = "Deny"
      NotAction = ["iam:CreateVirtualMFADevice", "iam:EnableMFADevice"]
      Resource = "*"
      Condition = {
        BoolIfExists = { "aws:MultiFactorAuthPresent" = "false" }
      }
    }]
  })
}
```

For application-level MFA (TOTP), see examples/mfa-implementation.py.

### Role-Based Access Control

**Standards:** Least privilege, job function-based roles, quarterly reviews

**Kubernetes Example:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: development
rules:
- apiGroups: ["", "apps"]
  resources: ["pods", "deployments", "services"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]  # Read-only
```

For OPA access-control policies, see examples/opa-policies/access_control.rego.

### Audit Logging

**Standards:** Structured JSON, retention set per framework, immutable storage

**Required Events:** Authentication, authorization, data access, administrative actions, security events

**Python Example:**
```python
class AuditLogger:
    def log_event(self, event_type, user_id, resource_type,
                  resource_id, action, result, ip_address):
        audit_event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "user_id": user_id,
            "action": action,
            "result": result,
            "resource": {"type": resource_type, "id": resource_id},
            "source": {"ip": ip_address}
        }
        self.logger.info(json.dumps(audit_event))
```

**Log Retention:**
```hcl
resource "aws_cloudwatch_log_group" "audit" {
  # Allowed values are fixed (..., 365, 731, 1096, 1827, 2192, 2557, ...).
  # 2192 = 6 years, a common policy for HIPAA scope; PCI-DSS alone needs 365.
  retention_in_days = 2192
  kms_key_id        = aws_kms_key.logs.arn
}

resource "aws_s3_bucket_object_lock_configuration" "audit" {
  bucket = aws_s3_bucket.audit_logs.id
  rule {
    default_retention {
      mode  = "COMPLIANCE"
      years = 6
    }
  }
}
```

For audit-event taxonomy, shipping, SIEM integration and per-framework retention, use the `audit-logging` skill.

## Evidence Collection Automation

### Continuous Monitoring

Automate evidence collection for continuous compliance validation.

**Architecture:**
```
AWS Config → EventBridge → Lambda → S3 (Evidence)
                                   → DynamoDB (Status)
```

**Evidence Collection:**
```python
class EvidenceCollector:
    def collect_encryption_evidence(self):
        evidence = {
            "control_id": "ENC-001",
            "frameworks": ["SOC2-CC6.1", "HIPAA-164.312(a)(2)(iv)"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PASS",
            "findings": []
        }
        # Check S3, RDS, EBS encryption status
        # Document findings
        return evidence
```

For complete evidence collector, see examples/evidence-collection/evidence_collector.py.

### Audit Report Generation

Generate compliance reports automatically:

```python
class AuditReportGenerator:
    def generate_soc2_report(self, start_date, end_date):
        controls = self.get_control_status("SOC2")
        return {
            "framework": "SOC 2 Type II",
            "compliance_score": self.calculate_score(controls),
            "trust_services_criteria": {...},
            "controls": self.format_controls(controls)
        }
```

For complete report generator, see examples/evidence-collection/report_generator.py.

## Control Mapping Matrix

Unified control mapping across frameworks:

| Control | SOC 2 | HIPAA | PCI-DSS | GDPR | ISO 27001 |
|---------|-------|-------|---------|------|-----------|
| MFA | CC6.1 | §164.312(d) | Req 8.3 | Art 32 | A.9.4.2 |
| Encryption at Rest | CC6.1 | §164.312(a)(2)(iv) | Req 3.4 | Art 32 | A.10.1.1 |
| Encryption in Transit | CC6.1 | §164.312(e)(1) | Req 4.1 | Art 32 | A.13.1.1 |
| Audit Logging | CC7.2 | §164.312(b) | Req 10.2 | Art 30 | A.12.4.1 |
| Access Reviews | CC6.1 | §164.308(a)(3)(ii)(C) | Req 8.2.4 | Art 32 | A.9.2.5 |
| Vulnerability Scanning | CC7.1 | §164.308(a)(8) | Req 11.2 | Art 32 | A.12.6.1 |
| Incident Response | CC7.3 | §164.308(a)(6) | Req 12.10 | Art 33 | A.16.1.1 |

**Strategy:** Implement once with proper tagging, map to all applicable frameworks.

For complete control mapping with 45+ controls, see [references/control-mapping-matrix.md](references/control-mapping-matrix.md).

## Breach Notification Requirements

**Framework-Specific Timelines:**
- HIPAA: affected individuals without unreasonable delay and no later than 60 days after discovery; HHS within 60 days if 500+ individuals are affected (smaller breaches: annual log to HHS)
- GDPR: 72 hours to the supervisory authority (Art. 33); affected individuals without undue delay when the risk is high (Art. 34)
- SOC 2: no regulatory deadline; follow customer contracts and your own policy
- PCI-DSS: immediately to the acquirer and card brands, per their rules
- US state breach laws and sector rules add their own deadlines; confirm with counsel

**Required Elements:**
- Description of incident and data involved
- Estimated number of affected individuals
- Steps taken to mitigate harm
- Contact information for questions
- Remediation actions and timeline

For incident response process and postmortems, use the `managing-incidents` skill.

## Vendor Management

**Business Associate Agreements (HIPAA):**
- Required for all vendors handling PHI
- Specify permitted uses and disclosures
- Require appropriate safeguards
- Annual review and renewal

**Data Processing Agreements (GDPR):**
- Required for all vendors processing personal data
- Process only on controller instructions
- Implement appropriate technical measures
- Sub-processor approval required

**Assessment Process:**
1. Risk classification by data access level
2. Security questionnaire evaluation
3. BAA/DPA execution
4. SOC 2 report collection (≤90 days old)
5. Annual re-assessment


## Tools & Libraries

**Policy as Code:**
- Open Policy Agent (OPA): General-purpose policy engine
- Checkov: IaC security scanning with compliance frameworks
- tfsec: Terraform security scanner
- Trivy: Container and IaC scanner

**Compliance Automation:**
- AWS Config: AWS resource compliance monitoring
- Cloud Custodian: Multi-cloud compliance automation
- Drata/Vanta/Secureframe: Continuous compliance platforms


## Integration with Other Skills

**Related Skills:**
- `security-hardening`: Technical security control implementation
- `hashicorp-vault`: Secrets handling per HIPAA/PCI-DSS
- `kubernetes-hardening`: K8s RBAC, network policies, admission control
- `building-ci-pipelines`: Policy enforcement in CI/CD
- `audit-logging`: Audit logging, retention and SIEM integration
- `managing-incidents`: Incident response procedures
- `architecting-security`: Control-framework mapping at design time

## Quick Reference

**Implementation Checklist:**
- [ ] Identify applicable frameworks
- [ ] Implement encryption (AES-256, TLS 1.3)
- [ ] Configure MFA for privileged access
- [ ] Implement RBAC with least privilege
- [ ] Set up audit logging (retention per framework minimums)
- [ ] Configure security monitoring/alerting
- [ ] Create incident response plan
- [ ] Execute vendor agreements (BAAs, DPAs)
- [ ] Implement policy-as-code (OPA, Checkov)
- [ ] Automate evidence collection
- [ ] Conduct quarterly access reviews
- [ ] Perform annual risk assessments

**Common Mistakes:**
- Treating compliance as one-time project vs continuous process
- Implementing per-framework vs unified controls
- Manual evidence collection vs automation
- Log retention below a framework minimum (e.g. under 12 months for PCI-DSS), or keeping personal data in logs longer than needed (GDPR)
- Missing MFA enforcement
- Not encrypting backups/logs
- Inadequate vendor due diligence

## References

**Framework Details:**
- [references/soc2-controls.md](references/soc2-controls.md) - SOC 2 TSC control catalog
- [references/hipaa-safeguards.md](references/hipaa-safeguards.md) - HIPAA safeguards
- [references/pci-dss-requirements.md](references/pci-dss-requirements.md) - PCI-DSS 4.0 requirements
- [references/gdpr-articles.md](references/gdpr-articles.md) - GDPR key articles

**Implementation Patterns:**
- [references/control-mapping-matrix.md](references/control-mapping-matrix.md) - Unified control mapping
- [references/encryption-implementations.md](references/encryption-implementations.md) - Encryption patterns

**Code Examples:**
- examples/opa-policies/ - OPA policy examples
- examples/evidence-collection/ - Evidence automation
- examples/mfa-implementation.py - TOTP MFA implementation

Consult qualified legal counsel and auditors for legal interpretation and audit preparation.
