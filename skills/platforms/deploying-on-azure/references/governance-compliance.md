# Azure Governance and Compliance Reference

## Azure Policy

### Policy Effects

| Effect | Behavior | Use Case |
|--------|----------|----------|
| **Deny** | Block resource creation/update | Prevent non-compliant resources |
| **Audit** | Log compliance | Visibility without blocking |
| **AuditIfNotExists** | Check for related resources | Ensure diagnostics enabled |
| **DeployIfNotExists** | Auto-remediate | Deploy missing configurations |
| **Modify** | Change properties | Add missing tags |
| **Disabled** | Turn off policy | Testing |

### Common Policies

- Allowed resource types
- Allowed locations
- Required tags
- Storage account encryption
- Network security rules
- SQL Database TDE

---

## Repeatable Environments (Blueprints replacement)

Azure Blueprints deprecated (retirement announced for July 2026). Use Template Specs and Deployment Stacks instead for repeatable, governed environments.

### Components

1. **Template Specs:** Versioned, RBAC-shared Bicep/ARM templates (resource groups, policy assignments, role assignments)
2. **Deployment Stacks:** Deploy template as managed unit. Deny settings protect deployed resources; resources removed from template get cleaned up
3. **Parameters:** Environment-specific values per stack
4. **Versions:** Template Spec versions track changes

### Use Cases

- Regulatory compliance (ISO 27001, HIPAA, PCI-DSS)
- Landing zone deployment
- Multi-region rollouts

---

## Cost Management

### Cost Allocation Tags

Required tags for cost tracking:
- Environment (dev, staging, production)
- CostCenter (billing code)
- Owner (team responsible)
- Project (initiative)

### Azure Advisor Cost Recommendations

- Right-size underutilized VMs
- Delete unattached disks
- Purchase Reserved Instances
- Enable auto-pause for SQL serverless
- Optimize storage tiers

---

## Resource Tagging

### Tag Strategy

| Tag Name | Values | Purpose |
|----------|--------|---------|
| Environment | dev, staging, production | Lifecycle management |
| Owner | team@example.com | Accountability |
| CostCenter | CC-1234 | Chargeback |
| Project | project-alpha | Initiative tracking |
| Criticality | low, medium, high | SLA/support priority |
| Compliance | pci, hipaa, sox | Regulatory requirements |

### Tag Inheritance

Resource Group tags do NOT inherit to resources automatically. Enforce with Azure Policy.

---

## Azure Landing Zones

### Core Components

1. **Management Groups:** Hierarchical organization
2. **Subscriptions:** Billing and resource boundaries
3. **Policies:** Governance guardrails
4. **Networking:** Hub-spoke topology
5. **Identity:** Entra ID integration
6. **Security:** Microsoft Defender for Cloud

### Reference Architectures

- CAF (Cloud Adoption Framework) Landing Zones
- Azure Landing Zone Accelerator
- Industry-specific landing zones (FSI, healthcare)
