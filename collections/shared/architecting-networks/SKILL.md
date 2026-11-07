---
name: architecting-networks
description: "Design cloud network architecture - VPC/VNet topology, subnet and CIDR strategy, segmentation and zero-trust microsegmentation, hybrid and multi-cloud connectivity. Use when planning network layout for cloud workloads; use docker-compose-networking for single-host Docker networks and operating-kubernetes for in-cluster networking."
---

# Network Architecture

## When to Use This Skill

Invoke when:
- Designing VPC/VNet topology for new cloud environments
- Adding network segmentation and security controls
- Planning multi-VPC or multi-cloud connectivity
- Setting up hybrid connectivity (on-premises to cloud)
- Migrating flat network to sophisticated architecture
- Applying zero trust network principles
- Optimizing network cost and performance

## Core Network Architecture Patterns

### Pattern 1: Flat (Single VPC) Architecture

**Use When:** Small apps, single environment, simple security needs, team < 10 engineers

**Characteristics:**
- All resources in one VPC, subnet-level segmentation
- Public, private and database subnet tiers
- Simplest to understand and manage
- No inter-VPC routing complexity

**Tradeoffs:**
- ✓ Lowest cost, fastest setup
- ✗ Poor isolation, hard to scale, whole VPC is blast radius

### Pattern 2: Multi-VPC (Isolated) Architecture

**Use When:** Multiple environments (dev/staging/prod), strong isolation needs, compliance mandates separation

**Characteristics:**
- Separate VPCs per environment or workload
- No direct connectivity without explicit setup
- Independent CIDR ranges

**Tradeoffs:**
- ✓ Strong blast radius containment, clear security boundaries
- ✗ Management overhead, duplicate infrastructure, higher cost

### Pattern 3: Hub-and-Spoke (Transit Gateway) Architecture

**Use When:** 5+ VPCs must communicate, centralized security inspection required, hybrid connectivity, multi-account setup

**Characteristics:**
- Central hub VPC/Transit Gateway
- Spoke VPCs connect to hub
- All inter-VPC traffic routes through hub

**Tradeoffs:**
- ✓ Simpler routing, centralized security, scales easily (100+ VPCs)
- ✗ Transit Gateway costs (~$0.05/hour + $0.02/GB), added latency (hub hop)

### Pattern 4: Full Mesh (VPC Peering) Architecture

**Use When:** Few VPCs (< 5), low latency critical, no centralized inspection needed

**Characteristics:**
- Every VPC peered directly

**Tradeoffs:**
- ✓ Lowest latency, no Transit Gateway costs
- ✗ Management complexity grows O(n²), does not scale past ~10 VPCs

### Pattern 5: Hybrid (Multi-Pattern) Architecture

**Use When:** Large enterprise, diverse requirements, balancing cost/performance/security

**Characteristics:**
- Hub-spoke for most VPCs + direct peering for latency-sensitive pairs

**Tradeoffs:**
- ✓ Tuned to specific needs
- ✗ More complex to design and manage

## Pattern Selection Framework

```
Number of VPCs?
│
├─► 1 VPC → Flat (Single VPC)
├─► 2-4 VPCs + No inter-VPC communication → Multi-VPC (Isolated)
├─► 2-5 VPCs + Low latency critical → Full Mesh (VPC Peering)
├─► 5+ VPCs + Centralized inspection → Hub-and-Spoke (Transit Gateway)
└─► 10+ VPCs + Mixed requirements → Hybrid (Multi-Pattern)

Additional Considerations:
├─► Hybrid connectivity required? → Hub-and-Spoke preferred
├─► Centralized egress/inspection? → Hub-and-Spoke with Inspection VPC
├─► Multi-account environment? → Hub-and-Spoke with AWS RAM sharing
└─► Cost optimization priority? → Flat or Multi-VPC (avoid TGW fees)
```

## Subnet Strategy

### Standard Three-Tier Design

**Public Subnets:**
- Route to Internet Gateway
- For load balancers, bastion hosts, NAT Gateways
- CIDR: /24 to /27 (256 to 32 IPs)

**Private Subnets:**
- Route to NAT Gateway for outbound
- For app servers, containers, compute workloads
- CIDR: /20 to /22 (4,096 to 1,024 IPs)

**Database Subnets:**
- No direct internet route
- For RDS, ElastiCache, managed databases
- CIDR: /24 to /26 (256 to 64 IPs)

### Multi-AZ Distribution

**Production:** Spread each tier across 3 Availability Zones minimum
**Dev/Test:** 1-2 AZs acceptable to save cost

### CIDR Block Planning

**VPC Sizing:**
- /16 (65,536 IPs) - Large production environments
- /20 (4,096 IPs) - Medium environments
- /24 (256 IPs) - Small/dev environments

**Critical Rules:**
- Non-overlapping CIDR ranges across VPCs
- Coordinate with on-premises network team for hybrid connectivity
- Reserve address space for growth

Detailed subnet planning: `references/subnet-strategy.md`

## NAT Gateway Strategy

### Decision Framework

```
Cost vs Resilience?
│
├─► Cost Priority (Dev/Test)
│   └─► Single NAT Gateway (~$32/month)
│       └─► Risk: Single point of failure
│
├─► Balanced (Most Production)
│   └─► One NAT Gateway per AZ (~$96/month for 3 AZs)
│       └─► Resilience: AZ failure doesn't break connectivity
│
└─► Maximum Resilience
    └─► Multiple NAT Gateways per AZ + monitoring
        └─► Critical workloads, SLA-dependent

Alternative: Centralized Egress Pattern
└─► Hub-and-Spoke: Single egress VPC with NAT
    └─► Reduces NAT Gateway count, centralized logging
```

**No Outbound Internet Needed?**
- Skip NAT Gateway entirely (saves cost)
- Use VPC Endpoints for AWS service access

## Security Controls

### Security Groups (Recommended)

**Characteristics:**
- Stateful (return traffic auto-allowed)
- Instance-level control
- Allow rules only (implicit deny)
- Can reference other security groups

**Use For:**
- Service-to-service communication
- Most common case

**Best Practices:**
- Descriptive names (app-alb-sg, app-backend-sg)
- Reference other security groups, not CIDR blocks
- Keep rules minimal and specific

### Network ACLs (Optional)

**Characteristics:**
- Stateless (must allow both request and response)
- Subnet-level control
- Allow and deny rules
- Rules processed in order (lowest number first)

**Use For:**
- Explicit deny rules (block specific IPs)
- Compliance requirements (defense in depth)
- Extra layer beyond security groups

**Best Practices:**
- Use sparingly (complex to manage)
- Allow ephemeral ports (1024-65535)
- Test thoroughly (stateless behavior causes issues)

Security group architecture patterns: `references/security-controls.md`

## Zero Trust Principles

### Core Tenets

1. **Never Trust, Always Verify**
   - Authenticate every request regardless of source
   - No implicit trust from network location

2. **Least Privilege Access**
   - Grant minimum needed permissions
   - Time-bound access (just-in-time)

3. **Assume Breach**
   - Segment network aggressively
   - Monitor all traffic
   - Detect and respond fast

### Implementation Patterns

**Microsegmentation:**
- Isolate every workload with granular security group rules
- Allow service-to-service traffic only between specific services

**Identity-Based Access:**
- Authorize by IAM roles, not IP addresses
- VPC Endpoints with IAM policies
- Service-to-service identity verification

**Continuous Verification:**
- VPC Flow Logs for traffic analysis
- Monitor rejected connections
- Alert on anomalies

Zero trust architecture patterns: `references/zero-trust-networking.md`

## Hybrid Connectivity

### VPN (Virtual Private Network)

**Use When:** Dev/test, backup connectivity, temporary connections

**Characteristics:**
- Encrypted tunnel over public internet
- Throughput: ~1.25 Gbps per tunnel
- Latency: Variable (internet-dependent)
- Cost: Low (~$0.05/hour + data transfer)
- Setup: Quick (no contracts)

### Direct Connect / ExpressRoute / Cloud Interconnect

**Use When:** Production workloads, large data transfers, real-time apps

**Characteristics:**
- Dedicated connection (bypasses public internet)
- Throughput: Up to 100 Gbps
- Latency: Low and consistent
- Cost: Higher (port fees + data transfer)
- Setup: Slower (contracts, coordination)

### Transit Gateway + Direct Connect

**Use When:** Multiple VPCs need on-premises connectivity

**Benefits:**
- Single Direct Connect connection → Transit Gateway → Multiple VPCs
- Centralized hybrid connectivity

Hybrid connectivity patterns and examples: `references/hybrid-connectivity.md`

## Multi-Cloud Networking

### Unified Concepts Across Providers

| Concept | AWS | GCP | Azure |
|---------|-----|-----|-------|
| Virtual Network | VPC | VPC | Virtual Network (VNet) |
| Subnets | Subnets (AZ-scoped) | Subnets (Regional) | Subnets |
| NAT | NAT Gateway | Cloud NAT | NAT Gateway |
| Peering | VPC Peering | VPC Peering | VNet Peering |
| Hub-Spoke | Transit Gateway | Cloud Router | Virtual WAN |
| Private Endpoints | PrivateLink | Private Service Connect | Private Link |
| Hybrid VPN | VPN | Cloud VPN | VPN Gateway |
| Hybrid Dedicated | Direct Connect | Cloud Interconnect | ExpressRoute |

### Provider-Specific Best Practices

**AWS:**
- Multi-AZ baseline for production
- Prefer Transit Gateway for 5+ VPCs
- Use VPC Endpoints to avoid NAT charges

**GCP:**
- Custom mode VPC (not auto-mode)
- Start with single VPC; use Shared VPC for multi-project
- Grant network user role at subnet level

**Azure:**
- Hub-and-spoke topology as standard
- Few large VNets over many small VNets
- Private endpoints for Azure services

Multi-cloud implementations: `references/multi-cloud-networking.md`

## Network Observability

### VPC Flow Logs

**Enable Flow Logs for:**
- Traffic analysis and troubleshooting
- Security monitoring (detect unauthorized access)
- Cost attribution by network path
- Compliance requirements

**Configuration:**
- Traffic type: ALL (capture accepted and rejected)
- Aggregation interval: 1-10 minutes
- Destination: CloudWatch Logs or S3

### Monitoring Patterns

**Monitor:**
- Rejected connections (security anomalies)
- Traffic volume spikes
- Cross-VPC communication patterns
- NAT Gateway utilization

**Alert On:**
- Spike in rejected connections
- Unusual traffic patterns
- High data transfer costs
- Network errors

Observability patterns and flow log analysis: `references/network-observability.md`

## Cost Optimization

### Common Cost Drivers

1. **NAT Gateway:** $0.045/hour + $0.045/GB data processed
2. **Transit Gateway:** $0.05/hour/attachment + $0.02/GB
3. **Data Transfer:** Egress charges vary by destination
4. **VPN/Direct Connect:** Port fees + data transfer

### Optimization Strategies

**Reduce NAT Gateway Costs:**
- VPC Endpoints for AWS services (S3, DynamoDB)
- Centralized egress VPC pattern
- Single NAT Gateway for dev/test (accept availability risk)

**Reduce Data Transfer Costs:**
- Keep traffic in same region
- VPC Endpoints instead of public internet
- Private connectivity for high-volume transfers

Detailed cost optimization: `references/cost-optimization.md`

## Implementation Workflow

### Step 1: Analyze Requirements

- How many VPCs/environments?
- Hybrid connectivity required?
- Latency requirements?
- Security/compliance requirements?
- Budget constraints?

### Step 2: Select Pattern

Pick with pattern selection framework above:
- Flat, Multi-VPC, Hub-Spoke, Mesh, or Hybrid

### Step 3: Design Subnets

- Calculate CIDR blocks (non-overlapping)
- Plan multi-AZ distribution
- Set public/private/database tiers

### Step 4: Configure Security

- Design security group architecture
- Plan microsegmentation
- Configure Network ACLs if needed

### Step 5: Implement with IaC

Use IaC: Terraform/OpenTofu, or Pulumi via `pulumi-components` and `pulumi-stacks` skills.

### Step 6: Enable Observability

- Configure VPC Flow Logs
- Set up monitoring and alerting
- Track cost

## Quick Reference

### NAT Gateway Configuration

| Scenario | Configuration | Monthly Cost (3 AZs) |
|----------|---------------|----------------------|
| Dev/Test | Single NAT | ~$32 |
| Production | NAT per AZ | ~$96 |
| Centralized Egress | Hub VPC NAT | ~$32-96 |

## Reference Documentation

**Detailed Guides:**
- `references/vpc-design-patterns.md` - Full pattern descriptions with diagrams
- `references/subnet-strategy.md` - CIDR planning, IPAM, multi-AZ best practices
- `references/zero-trust-networking.md` - Microsegmentation, IAM integration, continuous verification
- `references/hybrid-connectivity.md` - VPN, Direct Connect, Transit Gateway patterns
- `references/multi-cloud-networking.md` - AWS, GCP, Azure implementations
- `references/security-controls.md` - Security groups, NACLs, firewall patterns
- `references/private-networking.md` - VPC Endpoints, PrivateLink, Private Service Connect
- `references/multi-region-networking.md` - Cross-region peering, global load balancing
- `references/network-observability.md` - Flow logs, monitoring, troubleshooting
- `references/cost-optimization.md` - Egress reduction, NAT strategies

**Code Examples:**
- `examples/aws/` - AWS VPC patterns (flat, hub-spoke, peering, VPN, Direct Connect). GCP and Azure equivalents in `references/multi-cloud-networking.md`.

**Utility Scripts:**
- `scripts/cidr-calculator.py` - Calculate CIDR blocks, plan IP addressing

## Integration with Other Skills

**Use `pulumi-components` / `pulumi-stacks` to:**
- Build network architectures as reusable, per-environment IaC

**Use `operating-kubernetes` skill to:**
- Configure Kubernetes networking (CNI) on top of VPC design
- Set up pod networking and service meshes

**Use `security-hardening` skill to:**
- Build firewall rules and WAF configurations
- Configure network-level DDoS protection
- Set up intrusion detection systems

**Use `implementing-observability` skill to:**
- Build full network monitoring
- Set up distributed tracing across network boundaries
- Configure performance dashboards
