---
name: architecting-security
description: "Design a security architecture - threat modeling (STRIDE/PASTA), defense in depth, zero trust, cloud account structure and control-framework mapping (NIST CSF, CIS Controls, ISO 27001). Use when designing security for a new system or reviewing an existing architecture; use security-hardening to implement infrastructure controls and security-and-hardening for application code."
---

# Security Architecture

## Purpose

Covers strategic planning, defense strategies and governance frameworks, not tactical security work (configuring firewalls, implementing authentication, scanning vulnerabilities).

Start with risk assessment to understand threats. Pick architecture approach (zero trust for greenfield, hybrid for brownfield). Implement layered controls. Monitor and improve security posture continuously.

## When to Use This Skill

Use when:

- Designing security for greenfield systems (new applications, cloud migrations)
- Running security audits or risk assessments of existing systems
- Implementing zero trust across enterprise environments
- Establishing security governance programs and compliance frameworks
- Threat modeling applications, APIs or microservices architectures
- Selecting and mapping controls to regulatory requirements (SOC 2, HIPAA, PCI DSS)
- Designing cloud security architectures (AWS, GCP, Azure multi-account strategies)
- Addressing supply chain security (SLSA framework, SBOM implementation)

## Core Security Architecture Principles

### 1. Defense in Depth

**9 Defense Layers (2025 Model):**

1. **Physical Security:** Data center access, environmental controls, hardware security modules (HSMs)
2. **Network Perimeter:** Next-gen firewalls (NGFW), DDoS protection, web application firewalls (WAF)
3. **Network Segmentation:** VLANs, VPCs, security groups, micro-segmentation
4. **Endpoint Protection:** EDR, antivirus, device encryption, patch management
5. **Application Layer:** Secure coding, WAF, API security, SAST/DAST scanning
6. **Data Layer:** Encryption (at-rest, in-transit, in-use), DLP, backup/recovery
7. **Identity & Access Management:** MFA, SSO, RBAC/ABAC, privileged access management (PAM)
8. **Behavioral Analytics:** UEBA, ML-based anomaly detection, threat intelligence
9. **Security Operations:** SIEM, SOAR, incident response, continuous monitoring

**Key Principle:** Each layer protects independently. Failure of one layer does not compromise whole system.

See `references/defense-in-depth.md` for layer-by-layer implementation patterns.

### 2. Zero Trust Architecture

**Core Zero Trust Principles:**

1. **Continuous Verification:** Authenticate and authorize every access request (no implicit trust)
2. **Least Privilege Access:** Grant minimal required permissions, use just-in-time (JIT) access
3. **Assume Breach:** Design expecting compromise, limit blast radius
4. **Explicit Verification:** Verify user identity (MFA), device health, application integrity, context (location, time, behavior)
5. **Micro-Segmentation:** Split networks into small isolated zones, control east-west traffic

**Zero Trust Architecture Components:**

- **Policy Engine:** Central authorization decision point (allow/deny)
- **Identity Provider (IdP):** User/machine identity verification (Azure AD, Okta)
- **Device Posture Service:** Device health checks (MDM, EDR integration)
- **Context/Risk Engine:** Behavioral analytics, location, time, threat intelligence
- **Policy Enforcement Points:** Gateways enforcing decisions (ZTNA, API gateways)

See `references/zero-trust-architecture.md` for implementation roadmap and reference architecture.

### 3. Threat Modeling

**Primary Methodologies:**

| Methodology | Purpose | Complexity | Best For |
|-------------|---------|------------|----------|
| **STRIDE** | Threat identification | Low | Development teams, quick threat analysis |
| **PASTA** | Risk-centric analysis | High | Enterprise risk management |
| **DREAD** | Risk scoring | Low | Prioritizing existing threats |
| **Attack Trees** | Visual threat analysis | Medium | Security architecture reviews |

**STRIDE Threat Categories:**

- **S**poofing: Impersonating another user/system (Mitigation: MFA, certificate validation)
- **T**ampering: Unauthorized data modification (Mitigation: Encryption, digital signatures)
- **R**epudiation: User denies action, no proof exists (Mitigation: Audit logs, non-repudiation)
- **I**nformation Disclosure: Confidential data exposure (Mitigation: Encryption, access controls, DLP)
- **D**enial of Service: System unavailability (Mitigation: Rate limiting, DDoS protection, redundancy)
- **E**levation of Privilege: Gaining higher privileges (Mitigation: Least privilege, input validation, patching)

**STRIDE Application Process:**

1. Model system with data flow diagrams (DFDs)
2. Apply STRIDE to each component/data flow to identify threats
3. Document threats with STRIDE categories
4. Prioritize threats by DREAD scoring or business impact
5. Design mitigation controls

See `references/threat-modeling.md` for methodologies, PASTA process, DREAD scoring and attack trees. See `examples/threat-models/` for threat modeling examples.

## Security Control Frameworks

Map controls to industry frameworks for full coverage and compliance.

### NIST Cybersecurity Framework (CSF) 2.0

**6 Core Functions:**

1. **GOVERN (GV):** Risk management strategy, policies, supply chain risk management
2. **IDENTIFY (ID):** Asset inventory, risk assessment, continuous improvement
3. **PROTECT (PR):** Access control, data security, platform security, infrastructure resilience
4. **DETECT (DE):** Continuous monitoring, anomaly detection, security event analysis
5. **RESPOND (RS):** Incident management, analysis, communication, mitigation
6. **RECOVER (RC):** Recovery planning, execution, post-incident improvement

**Usage:** Map controls to NIST CSF categories to cover all security functions. Risk-based, flexible framework for security programs.

See `references/nist-csf-mapping.md` for category mapping and subcategories.

### CIS Critical Security Controls v8

**18 Controls organized in 3 Implementation Groups:**

- **IG1 (Basic):** 56 safeguards for small organizations (asset inventory, access control, logging, backups)
- **IG2 (Intermediate):** +74 safeguards for mid-sized organizations with IT security staff
- **IG3 (Advanced):** +23 safeguards for large enterprises with dedicated security teams

**Top Priority Controls (IG1):**
1. Inventory and Control of Enterprise Assets
2. Inventory and Control of Software Assets
3. Data Protection
4. Secure Configuration of Enterprise Assets
5. Account Management
6. Access Control Management
7. Continuous Vulnerability Management
8. Audit Log Management

**Usage:** CIS Controls give prescriptive, measurable security baseline. Start with IG1. Move to IG2/IG3 as security maturity grows.

See `references/cis-controls.md` for implementation guidance.

### OWASP Top 10 Risk Mitigation

Map OWASP Top 10 application risks to architectural controls:

| OWASP Risk | Primary Control | Framework Mapping |
|------------|-----------------|-------------------|
| **Injection** | Parameterized queries, input validation | NIST PR.DS, CIS 16 |
| **Broken Authentication** | MFA, secure session management | NIST PR.AC, CIS 5, 6 |
| **Sensitive Data Exposure** | Encryption, key management | NIST PR.DS, CIS 3 |
| **XXE** | Disable external entities, use JSON | NIST PR.DS, CIS 16 |
| **Broken Access Control** | Authorization checks, RBAC | NIST PR.AC, CIS 6 |
| **Security Misconfiguration** | Hardening, minimal configs | NIST PR.IP, CIS 4 |
| **XSS** | Output encoding, CSP | NIST PR.DS, CIS 16 |
| **Insecure Deserialization** | Validate objects, safe formats | NIST PR.DS, CIS 16 |
| **Known Vulnerabilities** | Patch management, SBOM | NIST ID.RA, CIS 7 |
| **Logging & Monitoring** | SIEM, centralized logging | NIST DE.CM, CIS 8 |

See `references/owasp-top10-mitigation.md` for mitigation strategies and code examples.

## Architecture Selection Decision Framework

Pick architecture approach by system characteristics:

**Greenfield (New System):**
- Implement Zero Trust from Day 1
- Identity-first architecture (MFA, SSO, RBAC/ABAC)
- Micro-segmentation by default
- Assume breach (limit blast radius)
- Continuous verification and monitoring

**Brownfield (Existing System):**
- Hybrid: maintain Defense in Depth, add Zero Trust overlay
- Keep existing perimeter controls (firewalls, VPN)
- Layer in Zero Trust controls progressively
- Segment critical assets first (data, admin access)
- Modernize identity and access management

**Compliance-Driven:**
- Map to control frameworks per requirements:
  - **General Security:** NIST CSF for risk-based approach
  - **Baseline Hardening:** CIS Controls for prescriptive guidance
  - **Comprehensive ISMS:** ISO 27001 for certification
  - **Industry-Specific:** PCI DSS (payments), HIPAA Security Rule (healthcare), FedRAMP (government)

**Cloud-Native:**
- Use cloud provider reference architectures:
  - **AWS:** Well-Architected Framework (Security Pillar)
  - **GCP:** Security Best Practices, Security Command Center
  - **Azure:** Security Benchmark, Defender for Cloud
- Implement cloud-native security services (CSPM, CWPP)

**Hybrid/Multi-Cloud:**
- Cloud Security Posture Management (CSPM) for unified policy enforcement
- Cross-cloud visibility and monitoring
- Cloud-agnostic IAM (Okta, Azure AD)

See `references/defense-in-depth.md` and `references/zero-trust-architecture.md` for architecture selection decision trees.

## Supply Chain Security

### SLSA Framework

**Supply-chain Levels for Software Artifacts (4 levels):**

1. **SLSA Level 1 - Provenance:** Build generates provenance metadata (not tamper-proof)
2. **SLSA Level 2 - Hosted Build:** Build on trusted platform (GitHub Actions, Cloud Build)
3. **SLSA Level 3 - Hardened Build:** Build platform prevents tampering, audit logs
4. **SLSA Level 4 - Hermetic, Reproducible:** Fully hermetic builds, reproducible, two-party review

**Implementation:** Start with Level 1 provenance generation. Move to Level 2 (GitHub Actions), then Level 3 (hardened CI/CD with audit logs).

### SBOM (Software Bill of Materials)

**SBOM Standards:**
- **CycloneDX:** OWASP standard (JSON/XML format)
- **SPDX:** Linux Foundation standard
- **SWID:** ISO/IEC 19770-2 standard

**Dependency Management Best Practices:**
1. Generate SBOM automatically in CI/CD pipeline
2. Scan continuously with tools (Dependabot, Snyk, Trivy, Grype)
3. Automate security patch updates
4. Track license compliance, run approval workflows
5. Pin dependency versions with lock files
6. Minimize dependencies to shrink attack surface

See `references/supply-chain-security.md` for SLSA implementation guide, SBOM generation examples and dependency scanning automation.

## Cloud Security Architecture Patterns

### AWS Security Architecture

**Well-Architected Framework - Security Pillar Principles:**

1. **Strong identity foundation:** Centralize IAM, least privilege, IAM Identity Center (SSO)
2. **Enable traceability:** CloudTrail, GuardDuty, Security Hub for full logging
3. **Apply security at all layers:** Defense in depth across VPC, instances, applications, data
4. **Automate security best practices:** Infrastructure as Code (Terraform, CloudFormation)
5. **Protect data in transit and at rest:** TLS 1.3, AWS KMS, encryption everywhere

**Key AWS Security Services:**

- **IAM:** AWS IAM, IAM Identity Center (SSO), Cognito (customer identity)
- **Detection:** GuardDuty (threat detection), Security Hub (centralized findings), Detective (investigation)
- **Network:** AWS WAF, Shield (DDoS), Network Firewall
- **Data:** KMS (key management), Secrets Manager, Macie (data classification)
- **Compute:** Systems Manager (patch management), Inspector (vulnerability scanning)

**Multi-Account Strategy:** Use AWS Organizations with Security OU (Security Account, Logging Account, Audit Account) and Workload OUs (Production, Non-Production). Apply Service Control Policies (SCPs) as guardrails.

See `references/aws-security-architecture.md` and `examples/architectures/aws-multi-account-security.md` for AWS reference architectures and multi-account setup.

### GCP Security Architecture

**Key GCP Security Services:**

- **IAM:** Cloud IAM, Identity Platform (customer identity), Cloud Identity (workforce)
- **Detection:** Security Command Center (unified dashboard), Chronicle (SIEM), Event Threat Detection
- **Network:** Cloud Armor (DDoS/WAF), VPC Service Controls (data exfiltration prevention), Cloud Firewall
- **Data:** Cloud KMS, Secret Manager, Cloud DLP (data loss prevention)
- **Compute:** Binary Authorization (image signing), Confidential Computing (encryption in use)

**Organization Hierarchy:** Structure as Organization → Folders (Production, Non-Production, Security) → Projects. Apply IAM policies at folder level for inheritance.

See `references/gcp-security-architecture.md` and `examples/architectures/gcp-security-hierarchy.md` for GCP architecture patterns and organization setup.

### Azure Security Architecture

**Key Azure Security Services:**

- **IAM:** Azure AD (Entra ID), Privileged Identity Management (JIT access), Conditional Access
- **Detection:** Microsoft Defender for Cloud (CSPM/CWPP), Sentinel (SIEM/SOAR), Azure Monitor
- **Network:** Azure Firewall, Front Door + WAF, DDoS Protection
- **Data:** Key Vault (secrets, keys, certificates), Information Protection (DLP), Storage encryption
- **Compute:** Just-in-Time VM Access, Azure Policy (compliance enforcement)

**Hub-Spoke Landing Zone:** Build hub VNet (shared services: firewall, VPN, Azure Bastion) with spoke VNets (workloads). Use Management Groups for policy hierarchy.

See `references/azure-security-architecture.md` and `examples/architectures/azure-landing-zone.md` for Azure architecture and hub-spoke design.

## Identity & Access Management Patterns

### Authentication Controls

**Multi-Factor Authentication (MFA):**
- **Types:** TOTP (time-based one-time passwords), push notifications, biometrics, hardware tokens (YubiKey, FIDO2)
- **Enforcement:** Require MFA for all users (workforce and customers), especially privileged accounts
- **Passwordless:** Move to WebAuthn, FIDO2, passkeys to eliminate password-based attacks

**Single Sign-On (SSO):**
- **Protocols:** SAML 2.0, OAuth 2.0, OpenID Connect (OIDC)
- **Implementation:** Azure AD, Okta, Auth0, Ping Identity

### Authorization Controls

**Role-Based Access Control (RBAC):**
- Users get roles, roles have permissions
- Coarse-grained, simple to implement
- Best for: Organizations with stable role structures

**Attribute-Based Access Control (ABAC):**
- Fine-grained access by attributes (user department, resource classification, time, location)
- More flexible than RBAC
- Best for: Complex, dynamic access requirements

**Policy-Based Access Control (PBAC):**
- Central policy engines (Open Policy Agent - OPA, AWS Cedar)
- Policies declarative and versioned
- Best for: Microservices, API gateways, cloud-native architectures

### Privileged Access Management (PAM)

**Just-in-Time (JIT) Access:**
- Temporary elevated privileges for specific tasks
- Time-bound access grants (e.g., 4 hours)
- Reduces standing privileged access

**Credential Vaulting:**
- Central storage of privileged credentials (CyberArk, HashiCorp Vault, Azure Key Vault)
- Automatic password rotation
- Session recording and auditing

See `references/iam-patterns.md` for IAM implementation patterns, MFA configuration and PAM setup.

## Security Monitoring & Operations

### SIEM (Security Information & Event Management)

**Leading SIEM Platforms:**
- Splunk, Elastic Security, Microsoft Sentinel, Chronicle

**SIEM Architecture:**
1. **Log Collection:** Ingest logs from all layers (network, endpoints, applications, cloud)
2. **Normalization:** Standardize log formats for correlation
3. **Correlation:** Apply rules to detect patterns (failed logins signal brute force attack)
4. **Alerting:** Notify SOC team of high-priority events
5. **Investigation:** Search and visualization for incident analysis

### SOAR (Security Orchestration, Automation & Response)

**SOAR Capabilities:**
- **Playbooks:** Automated response workflows (block IP, quarantine endpoint, revoke credentials)
- **Orchestration:** Integrate with security tools (SIEM, EDR, firewall, IAM)
- **Case Management:** Track incidents, assign to analysts, document resolution

**Leading SOAR Platforms:**
- Splunk SOAR, Palo Alto Cortex XSOAR, IBM Resilient

### Detection Strategies

**UEBA (User & Entity Behavior Analytics):**
- Machine learning-based anomaly detection
- Detects: Account compromise, insider threats, data exfiltration
- Baseline normal behavior, alert on deviations

**Threat Intelligence:**
- Integrate threat feeds (MISP, ThreatConnect, ISACs)
- Enrich alerts with threat context (known malicious IPs, IOCs)
- Proactive threat hunting with TTPs (MITRE ATT&CK framework)

See `references/security-operations.md` for SIEM architecture, SOAR playbook examples and detection strategies.

## Quick Reference: Control Framework Mapping

| Risk/Requirement | Framework | Key Controls |
|------------------|-----------|--------------|
| General security program | NIST CSF 2.0 | All 6 functions (GV, ID, PR, DE, RS, RC) |
| Compliance baseline | CIS Controls v8 | IG1: Controls 1-18 (56 safeguards) |
| ISO certification | ISO 27001/27002 | 114 controls across 14 domains |
| Application security | OWASP ASVS | 286 security requirements (3 levels) |
| Cloud security (AWS) | AWS Well-Architected | Security Pillar: 10 design principles |
| Cloud security (GCP) | GCP Security Best Practices | Security Command Center architecture |
| Cloud security (Azure) | Azure Security Benchmark | Defender for Cloud controls |
| Supply chain security | SLSA + SBOM | Level 2+ SLSA, CycloneDX SBOM |
| Zero trust architecture | NIST SP 800-207 | ZTA tenets, deployment models |
| Privacy/GDPR | NIST Privacy Framework | Privacy engineering objectives |

## Integration with Related Skills

- **`security-hardening`:** Implement infrastructure layers (OS, container, cloud, network, database)
- **`security-and-hardening`:** Application-code controls at trust boundaries
- **`kubernetes-hardening`:** Apply K8s security architecture (PSA, RBAC, NetworkPolicy, admission)
- **`hashicorp-vault`:** Secrets management (dynamic secrets, PKI, rotation)
- **`architecting-networks`:** Network segmentation and perimeter design
- **`building-ci-pipelines`:** Secure CI/CD architecture (scanning stages, artifact signing, SLSA)
- **`dependency-scanning`:** Vulnerability and SBOM scanning
- **`audit-logging`:** Security monitoring and SIEM integration
- **`implementing-compliance`:** Map security architecture to compliance requirements

## Common Security Architecture Patterns

### Pattern 1: Zero Trust Network Access (ZTNA)

Replace VPN with identity-based access to applications.

**Architecture:**
1. User authenticates to identity provider (Azure AD, Okta)
2. Device posture check validates device health
3. Policy engine evaluates access request (user, device, context)
4. Access granted through secure connector (no network access)

### Pattern 2: Defense in Depth for Web Applications

Layer multiple controls to protect web applications.

**Layers:**
1. DDoS Protection (Cloudflare, AWS Shield)
2. WAF (application firewall, OWASP Top 10 rules)
3. API Gateway (authentication, rate limiting)
4. Application Security (SAST/DAST, secure coding)
5. Database Security (encryption, least privilege)
6. Logging & Monitoring (SIEM, anomaly detection)

### Pattern 3: Cloud Security Posture Management (CSPM)

Continuously monitor and enforce security configurations across cloud environments.

**Architecture:**
1. Asset Discovery: Inventory all cloud resources
2. Configuration Assessment: Compare against security baselines (CIS Benchmarks)
3. Compliance Monitoring: Track regulatory compliance (SOC 2, ISO 27001)
4. Remediation: Automated fixes or guided workflows
5. Drift Detection: Alert on configuration changes

**Leading CSPM Tools:** Wiz, Orca Security, Prisma Cloud, Microsoft Defender for Cloud

## Resources and References

**Defense in Depth:**
- `references/defense-in-depth.md` - 9-layer defense model, implementation patterns, failure impact analysis

**Zero Trust Architecture:**
- `references/zero-trust-architecture.md` - ZTA principles, reference architecture, implementation roadmap

**Threat Modeling:**
- `references/threat-modeling.md` - STRIDE, PASTA, DREAD, Attack Trees methodologies
- `examples/threat-models/web-app-stride.md` - Web application STRIDE analysis example
- `examples/threat-models/api-threat-model.md` - REST API threat model example
- `examples/threat-models/microservices-threat-model.md` - Microservices threat model example

**Control Frameworks:**
- `references/nist-csf-mapping.md` - NIST CSF 2.0 functions, categories, subcategories
- `references/cis-controls.md` - CIS Controls v8, implementation groups, safeguards
- `references/owasp-top10-mitigation.md` - OWASP Top 10 risks and mitigation strategies

**Supply Chain Security:**
- `references/supply-chain-security.md` - SLSA framework, SBOM generation, dependency scanning

**Cloud Security:**
- `references/aws-security-architecture.md` - AWS Well-Architected Security Pillar, services, patterns
- `references/gcp-security-architecture.md` - GCP Security Best Practices, services, organization design
- `references/azure-security-architecture.md` - Azure Security Benchmark, Defender for Cloud, landing zones

**IAM & Operations:**
- `references/iam-patterns.md` - Authentication, authorization, MFA, RBAC/ABAC, PAM
- `references/security-operations.md` - SIEM, SOAR, UEBA, threat intelligence, incident response

**Architecture Examples:**
- `examples/architectures/aws-multi-account-security.md` - AWS Organizations security setup
- `examples/architectures/gcp-security-hierarchy.md` - GCP folder/project security hierarchy
- `examples/architectures/azure-landing-zone.md` - Azure hub-spoke landing zone
- `examples/architectures/zero-trust-network.md` - Zero trust network design

**Scripts:**
- `scripts/security-checklist.sh` - Automated security architecture checklist
