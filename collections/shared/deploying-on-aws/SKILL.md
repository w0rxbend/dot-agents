---
name: deploying-on-aws
description: "Select AWS services and reference architectures - compute (Lambda, Fargate, EKS, EC2), data, storage, networking, serverless and container patterns, Well-Architected trade-offs. Use when designing or migrating a workload on AWS; use aws-ec2/aws-iam/aws-rds/aws-s3 for hands-on operation of those services."
---

# AWS Patterns

## When to Use This Skill

Invoke when:

- Choosing compute: Lambda, Fargate, ECS, EKS or EC2
- Selecting databases (RDS, Aurora, DynamoDB) by access pattern
- Designing VPCs for multi-tier applications
- Implementing serverless patterns with API Gateway and Lambda
- Building container-based microservices on ECS or EKS
- Applying AWS Well-Architected Framework to designs
- Optimizing AWS costs while keeping performance
- Applying security best practices (IAM, KMS, encryption)

## Core Service Selection Frameworks

### Compute Service Selection

**Decision Flow:**

```
Execution Duration:
  <15 minutes → Evaluate Lambda
  >15 minutes → Evaluate containers or VMs

Event-Driven/Scheduled:
  YES → Lambda (serverless)
  NO → Consider traffic patterns

Containerized:
  YES → Need Kubernetes?
    YES → EKS
    NO → ECS (Fargate or EC2)
  NO → Evaluate EC2 or containerize first

Special Requirements:
  GPU/Windows/BYOL licensing → EC2
  Predictable high traffic → EC2 or ECS on EC2 (cost optimization)
  Variable traffic → Lambda or Fargate
```

**Quick Reference:**

| Workload | Primary Choice | Cost Model | Key Benefit |
|----------|---------------|------------|-------------|
| API Backend | Lambda + API Gateway | Pay per request | Auto-scale, no servers |
| Microservices | ECS on Fargate | Pay for runtime | Simple operations |
| Kubernetes Apps | EKS | $73/mo + compute | Portability, ecosystem |
| Batch Jobs | Lambda or Fargate Spot | Request/spot pricing | Cost efficiency |
| Long-Running | EC2 Reserved Instances | 30-60% savings | Predictable cost |

See `references/compute-services.md` for service comparisons, cost examples, performance characteristics and use-case guidance.

### Database Service Selection

**Decision Matrix by Access Pattern:**

| Access Pattern | Data Model | Primary Choice | Key Criteria |
|----------------|------------|----------------|--------------|
| Transactional (OLTP) | Relational | Aurora | Performance + HA |
| Simple CRUD | Relational | RDS PostgreSQL | Cost vs. features |
| Key-Value Lookups | NoSQL | DynamoDB | Serverless scale |
| Document Storage | JSON/BSON | DynamoDB | Flexibility vs. MongoDB compat |
| Caching | In-Memory | ElastiCache Redis | Speed + durability |
| Analytics (OLAP) | Columnar | Redshift/Athena | Dedicated vs. serverless |
| Time-Series | Timestamped | Timestream for InfluxDB | Purpose-built (Timestream for LiveAnalytics closed to new customers) |

**Query Complexity Guide:**

- **Simple Key-Value:** DynamoDB (single-digit ms latency)
- **Moderate Joins (2-3 tables):** Aurora or RDS (cost vs. performance)
- **Complex Analytics:** Redshift (dedicated) or Athena (serverless, query S3)
- **Real-Time Streams:** DynamoDB Streams + Lambda

See `references/database-services.md` for RDS, Aurora, DynamoDB and ElastiCache comparison, storage class selection, cost comparisons and migration patterns.

### Storage Service Selection

**Primary Decision Tree:**

```
Data Type:
  Objects (files, media) → S3 + lifecycle policies
  Blocks (databases, boot volumes) → EBS
  Shared Files (cross-instance) → Evaluate protocol

File Protocol Required:
  NFS (Linux) → EFS
  SMB (Windows) → FSx for Windows
  High-Performance HPC → FSx for Lustre
  Multi-Protocol + Enterprise → FSx for NetApp ONTAP
```

**Cost Comparison (1TB/month):**

| Service | Monthly Cost | Access Pattern |
|---------|--------------|----------------|
| S3 Standard | $23 | Frequent access |
| S3 Standard-IA | $12.50 | Infrequent (>30 days) |
| S3 Glacier Instant | $4 | Archive, instant retrieval |
| EBS gp3 | $80 | Block storage |
| EFS Standard | $300 | Shared files, frequent |
| EFS IA | $25 | Shared files, infrequent |

**Recommendation:** Use S3 for 80%+ of storage needs. Use EFS/FSx only when shared file access is required.

See `references/storage-services.md` for S3 storage classes, EBS volume types, EFS/FSx selection and lifecycle policy examples.

## Serverless Architecture Patterns

### Pattern 1: REST API (Lambda + API Gateway + DynamoDB)

**Architecture:**
```
Client → API Gateway (HTTP API) → Lambda → DynamoDB
                                        ↓
                                       S3 (file uploads)
```

**Use When:**
- RESTful APIs with CRUD operations
- Variable or unpredictable traffic
- Minimal operational overhead wanted
- Pay-per-request cost model acceptable

**Cost Estimate (1M requests/month):**
- API Gateway: $3.50
- Lambda: $3.53
- DynamoDB: ~$7.50
- **Total: ~$15/month** (vs. Fargate ~$35+, EC2 ~$50+)

**Key Components:**
- API Gateway HTTP API (cheaper than REST API)
- Lambda with right memory allocation (1024MB typically optimal)
- DynamoDB on-demand billing (for variable traffic)
- CloudWatch Logs for debugging

Minimal CloudFormation version: `examples/cloudformation/lambda-api.yaml`.

### Pattern 2: Event-Driven Processing (EventBridge + Lambda + SQS)

**Architecture:**
```
S3 Upload → EventBridge Rule → Lambda (process) → DynamoDB (metadata)
                                              ↓
                                            SQS (downstream tasks)
```

**Use When:**
- Asynchronous file processing
- Decoupled microservice communication
- Fan-out patterns (one event, multiple consumers)
- Retry logic and dead-letter queues needed

**Key Features (2025):**
- **Step Functions Distributed Map:** Process millions of items in parallel

See `references/serverless-patterns.md` for more patterns: Step Functions orchestration, API Gateway WebSockets, Lambda SnapStart configuration.

## Container Architecture Patterns

### Pattern 1: ECS on Fargate (Serverless Containers)

**Architecture:**
```
ALB → ECS Service (Fargate tasks) → RDS Aurora
                                 ↓
                           ElastiCache Redis
```

**Use When:**
- Containerized applications without cluster management
- Variable traffic with auto-scaling
- Avoid EC2 instance management
- Docker-based deployment

**Key Components:**
- Application Load Balancer (path-based routing)
- ECS Cluster with Fargate launch type
- Task definitions (CPU, memory, container image)
- Auto-scaling on CPU/memory or custom metrics
- Service Connect for built-in service mesh

**Cost Model (2 vCPU, 4GB RAM, 24/7):**
- Fargate: ~$70/month
- ALB: ~$20/month
- RDS Aurora db.t3.medium: ~$50/month
- **Total: ~$140/month**

### Pattern 2: EKS (Kubernetes on AWS)

**Use When:**
- Team has Kubernetes expertise
- Multi-cloud or hybrid cloud strategy
- Kubernetes ecosystem needed (Helm, Operators, Istio)
- Complex workload orchestration

**Key Features (2025):**
- **EKS Hybrid Nodes:** Run on-premises nodes

**Cost Considerations:**
- EKS control plane: $73/month per cluster
- Worker nodes: Fargate or EC2 pricing
- Use EKS on Fargate for simplicity, EC2 for cost optimization

See `references/container-patterns.md` for ECS task definitions, ECS Service Connect, EKS Pod Identities, EKS cluster setup with CDK/Terraform and service mesh patterns.

## Networking Essentials

### VPC Architecture

**Standard 3-Tier Pattern:**

```
VPC: 10.0.0.0/16

Per Availability Zone (deploy across 3 AZs):
  Public Subnet:    10.0.X.0/24   (ALB, NAT Gateway)
  Private Subnet:   10.0.1X.0/24  (ECS, Lambda, app tier)
  Database Subnet:  10.0.2X.0/24  (RDS, Aurora, isolated)
```

**Best Practices:**
- Use /16 for VPC CIDR (65,536 IPs for growth)
- Use /24 for subnet CIDRs (256 IPs, 251 usable)
- Deploy across minimum 2 AZs (3 recommended) for high availability
- Use Security Groups (stateful) as instance-level firewall
- Enable VPC Flow Logs for troubleshooting

### Load Balancing

**Service Selection:**

| Load Balancer | Protocol | Use Case | Key Feature |
|---------------|----------|----------|-------------|
| ALB | HTTP/HTTPS | Web apps, APIs | Path/host routing, Lambda targets |
| NLB | TCP/UDP | High performance | Static IP, ultra-low latency |
| GWLB | Layer 3 | Security appliances | Inline inspection |

**ALB Features:**
- Path-based routing: `/api` → backend, `/web` → frontend
- Host-based routing: `api.example.com`, `web.example.com`
- WebSocket and gRPC support
- Lambda integration (serverless backends)

See `references/networking.md` for VPC design, load balancing, CloudFront CDN patterns, Route 53 routing policies and VPC peering configurations.

## Security Best Practices

### IAM Principles

**Least Privilege Pattern:**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::my-bucket/uploads/*"
  }]
}
```

**Core Practices:**
- Use IAM roles (not users) for applications
- Apply least privilege (minimum permissions needed)
- Enable MFA for privileged users
- Validate policies with IAM Access Analyzer
- Use AWS Organizations SCPs for guardrails

### Data Protection

**Encryption Requirements:**

| Service | At-Rest Encryption | In-Transit Encryption |
|---------|-------------------|----------------------|
| S3 | SSE-S3 or SSE-KMS | HTTPS (TLS 1.2+) |
| EBS | KMS encryption | N/A (within instance) |
| RDS/Aurora | KMS encryption | TLS connections |
| DynamoDB | KMS encryption | HTTPS API |

**Secrets Management:**
- **Secrets Manager:** Database credentials with automatic rotation
- **Parameter Store:** Application configuration (free tier available)
- **KMS:** Encryption key management (customer-managed keys)

See `references/security.md` for IAM patterns, KMS, Secrets Manager, WAF rules, GuardDuty configuration and network security patterns.

## AWS Well-Architected Framework

Six pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability (added 2021). See `references/well-architected.md` for pillar implementation guides, architectural review checklists and Well-Architected Tool integration.

## Infrastructure as Code

### Tool Selection

**AWS CDK (Cloud Development Kit):**
- **Languages:** TypeScript, Python, Java, C#, Go
- **Best For:** AWS-native workloads, type-safe infrastructure
- **Key Benefit:** High-level constructs, synthesizes to CloudFormation

**Terraform:**
- **Language:** HCL (HashiCorp Configuration Language)
- **Best For:** Multi-cloud environments
- **Key Benefit:** Largest ecosystem, mature state management

**CloudFormation:**
- **Language:** YAML or JSON
- **Best For:** Native AWS integration, no extra tools
- **Key Benefit:** AWS service support on day 1
- **Example:** `examples/cloudformation/lambda-api.yaml`

### CDK Quick Start

```bash
# Install CDK CLI
npm install -g aws-cdk
export CDK_DISABLE_CLI_TELEMETRY=true  # CLI telemetry on by default since 2.1100.0

# Initialize new project
cdk init app --language=typescript
npm install
cdk cli-telemetry --disable  # persist opt-out for this app (env var is per shell)

# Deploy infrastructure
cdk bootstrap  # One-time setup
cdk diff       # Review changes
cdk deploy --no-version-reporting  # also drops CDK usage metadata
```

### Terraform Quick Start

```bash
# Install Terraform
brew install terraform  # macOS

# Initialize project
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

**Gate:** show `cdk diff` / `terraform plan` to the user and get explicit approval before `cdk bootstrap`, `cdk deploy` or `terraform apply`. Never use `-auto-approve` or `--require-approval never`.

See `examples/` for working examples: VPC networking, multi-tier applications, event-driven architectures.

## Cost Optimization Strategies

### Compute Cost Optimization

**Right-Sizing:**
- Use AWS Compute Optimizer for EC2/Lambda recommendations
- Monitor CloudWatch metrics (CPU, memory utilization)
- Start conservatively, scale on actual usage

**Pricing Models:**

| Model | Commitment | Savings | Best For |
|-------|------------|---------|----------|
| On-Demand | None | 0% | Variable workloads |
| Savings Plans | 1-3 years | 30-40% | Flexible compute |
| Reserved Instances | 1-3 years | 30-60% | Predictable workloads |
| Spot Instances | None | 60-90% | Fault-tolerant tasks |

**Graviton Advantage:**
- Graviton3 instances: 25% better performance vs. Graviton2
- 60% less energy consumption
- Available: EC2, Lambda, Fargate, RDS, ElastiCache

### Storage Cost Optimization

**S3 Lifecycle Policies:**
```
Day 0-30:    S3 Standard         ($0.023/GB)
Day 30-90:   S3 Standard-IA      ($0.0125/GB)
Day 90-365:  S3 Glacier Instant  ($0.004/GB)
Day 365+:    S3 Deep Archive     ($0.00099/GB)
```

**EBS Optimization:**
- Use gp3 volumes (20% cheaper than gp2, configurable IOPS)
- Delete unused snapshots
- Archive old snapshots (75% cheaper)

**Monitoring:**
- Enable AWS Cost Explorer (free)
- Set up AWS Budgets with alerts
- Use Cost Allocation Tags for attribution
- Review Trusted Advisor cost checks

## Common Patterns and Examples

### Serverless Three-Tier Application

```
CloudFront (CDN)
  → S3 (React frontend)
  → API Gateway (REST API)
    → Lambda (business logic)
      → DynamoDB (data)
      → S3 (file storage)
```

### Containerized Microservices

```
Route 53 (DNS)
  → CloudFront (CDN)
    → ALB (load balancer)
      → ECS Fargate (services)
        → RDS Aurora (database)
        → ElastiCache Redis (cache)
```

### Event-Driven Data Pipeline

```
S3 Upload
  → EventBridge Rule
    → Lambda (transform)
      → Kinesis Firehose
        → S3 Data Lake
          → Athena (query)
```

See `references/serverless-patterns.md` for EventBridge and Firehose patterns.

## Integration with Other Skills

### Related Skills

- **aws-ec2 / aws-iam / aws-rds / aws-s3** - hands-on operation of those services
- **pulumi-components / pulumi-stacks** - IaC in TypeScript/Python with per-environment stacks
- **operating-kubernetes** - EKS workload operations, kubectl, Helm
- **building-ci-pipelines** - GitHub Actions or CodePipeline to AWS with OIDC
- **hashicorp-vault** - secrets beyond Secrets Manager / Parameter Store
- **implementing-observability** - CloudWatch, X-Ray and OpenTelemetry backends
- **security-hardening** - account and workload hardening
- **architecting-networks** - VPC design

### Cross-Skill Patterns

**EKS + operating-kubernetes:**
- Use this skill for EKS cluster provisioning (CDK/Terraform)
- Use operating-kubernetes for kubectl, Helm, application deployment

**Secrets Management:**
- Use this skill for Secrets Manager/Parameter Store setup and rotation
- Use hashicorp-vault when cloud-agnostic secrets store is required

**CI/CD Integration:**
- Use this skill for CodePipeline infrastructure
- Use building-ci-pipelines for pipeline configuration

## Notable AWS Features (verify current status before relying on them)

**Recent Innovations to Consider:**

- **Lambda SnapStart:** Near-instant cold starts for Java functions
- **Lambda Response Streaming:** Stream responses beyond 6 MB buffered limit (check current Lambda quotas for streaming maximum)
- **EventBridge Pipes:** Simplified event processing (source → filter → enrichment → target)
- **S3 Express One Zone:** 10x faster S3, single-digit millisecond latency
- **ECS Service Connect:** Built-in service mesh for ECS
- **EKS Auto Mode:** Fully managed Kubernetes node lifecycle
- **EKS Pod Identities:** Simplified IAM for pods (replaces IRSA)
- **Aurora Limitless Database:** Horizontal write scaling beyond single-writer limit
- **DynamoDB Standard-IA:** Infrequent access tables at 60% cost savings
- **RDS Blue/Green Deployments:** Zero-downtime version upgrades

---

## Quick Decision Checklist

**Before choosing a service, answer:**

1. **Traffic Pattern:** Predictable or variable? (affects compute choice)
2. **Data Model:** Relational, key-value, document or graph? (affects database choice)
3. **Access Pattern:** Frequent, infrequent or archive? (affects storage class)
4. **Latency Requirements:** Milliseconds, seconds or minutes acceptable?
5. **Scaling Needs:** Vertical (bigger instances) or horizontal (more instances)?
6. **Operational Overhead:** Prefer managed services or need control?
7. **Cost Sensitivity:** Optimize for cost, performance or balance?
8. **Compliance Requirements:** Data residency, encryption, audit logging needed?

## Getting Started

**For New AWS Projects:**

1. Define architecture with Well-Architected Framework pillars
2. Choose compute service with decision tree (Lambda/Fargate/ECS/EKS/EC2)
3. Select database by access patterns and data model
4. Design VPC with 3-tier subnet architecture
5. Implement IaC with CDK or Terraform (see examples/)
6. Apply security best practices (IAM, encryption, logging)
7. Set up monitoring and cost tracking

**For Existing AWS Projects:**

1. Run AWS Trusted Advisor for recommendations
2. Review Well-Architected Framework pillars
3. Optimize costs (right-size, Reserved Instances, storage lifecycle)
4. Migrate to modern services (EC2 → Fargate, RDS → Aurora)
5. Improve security posture (enable GuardDuty, implement least privilege)
6. Automate with IaC (reverse-engineer to Terraform or CDK)
