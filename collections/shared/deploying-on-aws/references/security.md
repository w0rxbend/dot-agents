# AWS Security Best Practices


## Table of Contents

- [IAM (Identity and Access Management)](#iam-identity-and-access-management)
  - [Least Privilege Policy Example](#least-privilege-policy-example)
  - [IAM Best Practices](#iam-best-practices)
  - [IAM Roles for Common Services](#iam-roles-for-common-services)
- [KMS (Key Management Service)](#kms-key-management-service)
  - [Key Types](#key-types)
  - [Encryption Patterns](#encryption-patterns)
  - [KMS API Costs](#kms-api-costs)
- [Secrets Manager](#secrets-manager)
  - [Cost Comparison](#cost-comparison)
  - [When to Use Each](#when-to-use-each)
  - [Automatic Rotation Example](#automatic-rotation-example)
- [WAF (Web Application Firewall)](#waf-web-application-firewall)
  - [Managed Rule Groups](#managed-rule-groups)
  - [Custom Rules](#custom-rules)
  - [Cost Model](#cost-model)
- [GuardDuty (Threat Detection)](#guardduty-threat-detection)
- [Security Hub](#security-hub)
- [Network Security](#network-security)
  - [Security Group Strategy](#security-group-strategy)
  - [VPC Flow Logs](#vpc-flow-logs)
- [Encryption Checklist](#encryption-checklist)
  - [Data at Rest](#data-at-rest)
  - [Data in Transit](#data-in-transit)
  - [Key Management](#key-management)
- [Compliance Frameworks](#compliance-frameworks)
  - [AWS Artifact](#aws-artifact)
  - [AWS Config](#aws-config)
- [Incident Response](#incident-response)
  - [CloudTrail](#cloudtrail)
  - [Security Automation](#security-automation)

## IAM (Identity and Access Management)

### Least Privilege Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject"
    ],
    "Resource": "arn:aws:s3:::my-bucket/uploads/*",
    "Condition": {
      "IpAddress": {
        "aws:SourceIp": "203.0.113.0/24"
      }
    }
  }]
}
```

### IAM Best Practices

1. **Use Roles, Not Users** for applications
2. **Enable MFA** for privileged users
3. **Use IAM Access Analyzer** to validate policies
4. **Use Permission Boundaries** to cap maximum permissions
5. **Rotate Credentials** every 90 days
6. **Use AWS Organizations SCPs** as guardrails

### IAM Roles for Common Services

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

**ECS Task Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

---

## KMS (Key Management Service)

### Key Types

| Type | Cost | Rotation | Use Case |
|------|------|----------|----------|
| **AWS Managed** | Free | Automatic (3 years) | S3, EBS, RDS default |
| **Customer Managed** | $1/month | Manual or automatic | Custom policies |
| **Custom Key Store** | $1/month + CloudHSM | Manual | FIPS 140-2 Level 3 |

### Encryption Patterns

**Server-Side Encryption (SSE):**
- S3: SSE-S3 (free), SSE-KMS ($1/month key + API costs)

**Client-Side Encryption:**
- Encrypt before sending to AWS
- Application manages keys
- Use KMS Encrypt API or encryption SDK

### KMS API Costs

- $0.03 per 10,000 requests
- Free tier: AWS managed keys

---

## Secrets Manager

### Cost Comparison

| Service | Cost/Secret | Rotation | Secret Size |
|---------|-------------|----------|-------------|
| **Secrets Manager** | $0.40/month | Automatic (Lambda) | 64KB |
| **Parameter Store (Standard)** | Free | Manual | 4KB |
| **Parameter Store (Advanced)** | $0.05/month | Manual | 8KB |

### When to Use Each

**Secrets Manager:**
- Database credentials with rotation
- API keys requiring rotation
- Multi-region replication needed

**Parameter Store:**
- Application configuration
- Non-rotating secrets
- Cost-sensitive cases

### Automatic Rotation Example

**RDS MySQL Credentials:**
1. Secrets Manager invokes Lambda every 30 days
2. Lambda creates new user with same permissions
3. Tests new credentials
4. Updates secret
5. Deletes old user

---

## WAF (Web Application Firewall)

### Managed Rule Groups

| Rule Group | Purpose | Cost |
|------------|---------|------|
| **Core Rule Set** | OWASP Top 10 | $10/month |
| **SQL Injection** | Database attacks | $10/month |
| **Known Bad Inputs** | CVE signatures | $10/month |
| **IP Reputation** | Block malicious IPs | $10/month |

### Custom Rules

**Rate Limiting:**
```json
{
  "Name": "RateLimitRule",
  "Priority": 1,
  "Statement": {
    "RateBasedStatement": {
      "Limit": 2000,
      "AggregateKeyType": "IP"
    }
  },
  "Action": {"Block": {}}
}
```

**Geo-Blocking:**
```json
{
  "Name": "BlockCountries",
  "Priority": 2,
  "Statement": {
    "GeoMatchStatement": {
      "CountryCodes": ["CN", "RU"]
    }
  },
  "Action": {"Block": {}}
}
```

### Cost Model

- Web ACL: $5/month
- Rules: $1/month per rule
- Requests: $0.60 per million
- Example: 1 ACL + 5 rules + 10M requests = $5 + $5 + $6 = $16/month

---

## GuardDuty (Threat Detection)

**Purpose:** ML-based threat detection

**Data Sources:**
- VPC Flow Logs
- CloudTrail event logs
- DNS logs

**Cost:**
- CloudTrail: $4.50 per million events
- VPC Flow Logs: $0.50 per million events analyzed
- DNS logs: $0.40 per million queries

**Use Cases:**
- Detect compromised instances
- Spot reconnaissance attempts
- Find unauthorized access

---

## Security Hub

**Purpose:** Central security dashboard, compliance checks

**Features:**
- CIS AWS Foundations Benchmark
- PCI DSS compliance
- Integrates with GuardDuty, Inspector, Macie

**Cost:**
- Security checks: $0.001 per check
- Findings ingestion: $0.00003 per finding

---

## Network Security

### Security Group Strategy

**Principle:** Default deny, explicit allow

**Example: Web Tier**
```
Inbound:
  - Port 443 (HTTPS) from 0.0.0.0/0
  - Port 80 (HTTP) from 0.0.0.0/0

Outbound:
  - All traffic (stateful return traffic automatic)
```

**Example: App Tier**
```
Inbound:
  - Port 8080 from web-tier-sg
  - Port 3000 from web-tier-sg

Outbound:
  - Port 5432 to database-tier-sg (PostgreSQL)
  - Port 443 to 0.0.0.0/0 (API calls)
```

### VPC Flow Logs

**Purpose:** Network traffic analysis, troubleshooting, security monitoring

**Cost:**
- $0.50 per GB ingested to CloudWatch Logs
- Send to S3 for cheaper storage ($0.023/GB)

**Analysis Tools:**
- CloudWatch Insights for queries
- Athena for S3-stored logs
- Third-party tools (Splunk, Datadog)

---

## Encryption Checklist

### Data at Rest

- [ ] S3: SSE-S3 or SSE-KMS enabled
- [ ] EBS: encryption by default enabled
- [ ] RDS: encryption enabled at creation
- [ ] DynamoDB: encryption enabled (free)
- [ ] EFS: encryption enabled
- [ ] ElastiCache: at-rest encryption (Redis only)

### Data in Transit

- [ ] ALB/NLB: HTTPS listeners with TLS 1.2+
- [ ] CloudFront: HTTPS required
- [ ] RDS: force SSL connections
- [ ] DynamoDB: HTTPS API calls
- [ ] S3: bucket policies require HTTPS

### Key Management

- [ ] Use AWS KMS for customer-managed keys
- [ ] Enable automatic key rotation (365 days)
- [ ] Control access with key policies
- [ ] Monitor KMS API usage (CloudTrail)

---

## Compliance Frameworks

### AWS Artifact

**Purpose:** Compliance reports (SOC, PCI, ISO, HIPAA)

**Available Reports:**
- SOC 1, 2, 3
- PCI DSS
- ISO 27001, 27017, 27018
- HIPAA BAA

### AWS Config

**Purpose:** Resource inventory, configuration compliance

**Rules Examples:**
- encrypted-volumes: all EBS volumes encrypted
- s3-bucket-public-read-prohibited: no public S3 buckets
- rds-multi-az-enabled: RDS instances Multi-AZ
- iam-password-policy: strong password requirements

**Cost:**
- $0.003 per configuration item
- $0.001 per rule evaluation

---

## Incident Response

### CloudTrail

**Purpose:** API audit logs for all AWS actions

**Features:**
- 90-day event history (free)
- Longer retention via S3 trail
- Multi-region trails
- Log file integrity validation

**Cost:**
- First copy of management events: free
- S3 storage: standard S3 rates
- CloudWatch Logs integration: $0.50/GB

### Security Automation

**Example: Auto-Remediation with Lambda**

1. Config Rule detects non-compliant resource
2. EventBridge triggers Lambda
3. Lambda remediates (e.g., enables encryption)
4. SNS sends notification

**Common Automations:**
- Revoke overly permissive security groups
- Enable encryption on new resources
- Enable S3 Block Public Access on public buckets (alert; never auto-delete data)
- Rotate IAM access keys >90 days old
