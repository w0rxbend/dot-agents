# Azure Security Architecture Reference

## Defense-in-Depth

### Security Layers

1. **Physical:** Azure datacenter security
2. **Identity:** Entra ID, MFA, Conditional Access
3. **Perimeter:** Azure Firewall, DDoS Protection
4. **Network:** NSGs, Private Endpoints, WAF
5. **Compute:** Disk encryption, secure boot
6. **Application:** Code scanning, secrets management
7. **Data:** Encryption at rest, TLS 1.2+

---

## Zero Trust Architecture

"Never trust, always verify"

### Principles

- Verify explicitly (MFA, Conditional Access)
- Use least privilege (RBAC)
- Assume breach (segmentation, monitoring)

---

## Microsoft Defender for Cloud

### Key Features

- Security posture management (Secure Score)
- Vulnerability assessment
- Just-In-Time VM access
- Adaptive application controls
- File integrity monitoring
- Threat detection and alerts
