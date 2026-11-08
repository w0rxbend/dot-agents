# VPC Design Patterns

## Table of Contents

1. [Pattern 1: Flat (Single VPC) Architecture](#pattern-1-flat-single-vpc-architecture)
2. [Pattern 2: Multi-VPC (Isolated) Architecture](#pattern-2-multi-vpc-isolated-architecture)
3. [Pattern 3: Hub-and-Spoke (Transit Gateway) Architecture](#pattern-3-hub-and-spoke-transit-gateway-architecture)
4. [Pattern 4: Full Mesh (VPC Peering) Architecture](#pattern-4-full-mesh-vpc-peering-architecture)
5. [Pattern 5: Hybrid (Multi-Pattern) Architecture](#pattern-5-hybrid-multi-pattern-architecture)
6. [Pattern Comparison Matrix](#pattern-comparison-matrix)
7. [Migration Paths](#migration-paths)

---

## Pattern 1: Flat (Single VPC) Architecture

### Description

All resources in one VPC, segmented by subnet. Simplest network architecture pattern.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    VPC 10.0.0.0/16                  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Public     │  │   Private    │  │ Database │ │
│  │   Subnet     │  │   Subnet     │  │  Subnet  │ │
│  │ 10.0.1.0/24  │  │ 10.0.10.0/24 │  │10.0.20./24│ │
│  │              │  │              │  │          │ │
│  │ ┌─────────┐ │  │ ┌─────────┐  │  │ ┌──────┐ │ │
│  │ │   ALB   │ │  │ │   ECS   │  │  │ │  RDS │ │ │
│  │ └─────────┘ │  │ └─────────┘  │  │ └──────┘ │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                     │
│  Internet Gateway          NAT Gateway             │
└─────────────────────────────────────────────────────┘
```

### Use Cases

**Ideal For:**
- Startups, small applications
- Single environment (dev OR staging OR prod, not multiple)
- Proofs of concept
- Teams < 10 engineers
- Simple security needs
- Low complexity tolerance

**Not Suitable For:**
- Multiple environments needing isolation
- Large teams with differing access needs
- Compliance requiring network-level separation
- Applications needing strong blast radius containment

### Pros and Cons

**Advantages:**
- ✓ Simplest to understand and manage
- ✓ No inter-VPC routing complexity
- ✓ Lowest cost (no Transit Gateway fees)
- ✓ Fastest to set up
- ✓ Easy network troubleshooting

**Disadvantages:**
- ✗ Poor isolation between workloads
- ✗ Hard to enforce least privilege
- ✗ CIDR exhaustion risks
- ✗ Hard to scale as organization grows
- ✗ Blast radius is entire VPC
- ✗ Security group rules grow complex at scale

### Implementation Example (AWS)

```hcl
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "app-vpc"
  cidr = "10.0.0.0/16"

  azs              = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false  # NAT per AZ for resilience
  enable_dns_hostnames = true

  tags = {
    Architecture = "flat"
    Environment  = "dev"
  }
}
```

---

## Pattern 2: Multi-VPC (Isolated) Architecture

### Description

Separate VPC per environment or workload, no direct connectivity. Each VPC fully isolated.

### Architecture Diagram

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Dev VPC       │  │  Staging VPC    │  │   Prod VPC      │
│  10.0.0.0/16    │  │  10.1.0.0/16    │  │  10.2.0.0/16    │
│                 │  │                 │  │                 │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │  Subnets  │  │  │  │  Subnets  │  │  │  │  Subnets  │  │
│  │  + Apps   │  │  │  │  + Apps   │  │  │  │  + Apps   │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│                 │  │                 │  │                 │
│  IGW + NAT      │  │  IGW + NAT      │  │  IGW + NAT      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                        Internet

No direct connectivity between VPCs
```

### Use Cases

**Ideal For:**
- Multiple environments (dev, staging, prod)
- Strong isolation needs
- Separate team per VPC
- Compliance requiring network-level separation
- Independent security boundaries
- Separate cost centers

**Not Suitable For:**
- Workloads needing frequent inter-VPC communication
- Shared services needed across environments
- Cost-sensitive environments (duplicate infrastructure)

### Pros and Cons

**Advantages:**
- ✓ Strong blast radius containment
- ✓ Independent CIDR ranges (no overlap concerns)

**Disadvantages:**
- ✗ No cross-VPC communication without explicit setup
- ✗ Management overhead (multiple VPCs)
- ✗ Duplicate infrastructure (NAT, endpoints)

---

## Pattern 3: Hub-and-Spoke (Transit Gateway) Architecture

### Description

Central hub VPC/Transit Gateway; spoke VPCs connect to it. All inter-VPC traffic routes through hub.

### Architecture Diagram

```
                         On-Premises
                              │
                          VPN / DX
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Transit Gateway   │
                   │   (Hub)            │
                   └─────────────────────┘
                     │      │       │
            ┌────────┘      │       └────────┐
            │               │                │
            ▼               ▼                ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │  Prod VPC │   │  Dev VPC  │   │ Shared    │
     │  (Spoke)  │   │  (Spoke)  │   │ Services  │
     │           │   │           │   │ (Spoke)   │
     └───────────┘   └───────────┘   └───────────┘
```

### Use Cases

**Ideal For:**
- 5+ VPCs communicating
- Centralized security inspection required
- Hybrid connectivity (on-premises to multiple VPCs)
- Multi-account AWS Organizations setup
- Network-level segmentation and policy
- Shared services VPC (Active Directory, monitoring, etc.)

**Not Suitable For:**
- Few VPCs (< 5) where peering suffices
- Ultra-low latency needs (hub hop adds latency)
- Cost-sensitive projects (Transit Gateway fees)

### Routing Patterns

**Spoke-to-Spoke:**
```
VPC-A → Transit Gateway → VPC-B
```

**Spoke-to-On-Premises:**
```
VPC-A → Transit Gateway → VPN/Direct Connect → On-Premises
```

**Centralized Egress:**
```
VPC-A → Transit Gateway → Egress VPC → Internet
```

### Pros and Cons

**Advantages:**
- ✓ Simplified routing (spokes only connect to hub)
- ✓ Centralized security inspection (firewall in hub)
- ✓ Scales easily (add spokes without redesign)
- ✓ Works with AWS Resource Access Manager (RAM) for multi-account
- ✓ Fewer VPN/Direct Connect connections

**Disadvantages:**
- ✗ Transit Gateway costs (~$0.05/hour + $0.02/GB)
- ✗ Hub can become bottleneck
- ✗ More complex than simple peering

### Implementation Example (AWS)

```hcl
# Transit Gateway
resource "aws_ec2_transit_gateway" "main" {
  description                     = "Main TGW for hub-spoke"
  amazon_side_asn                 = 64512
  default_route_table_association = "enable"
  default_route_table_propagation = "enable"
  dns_support                     = "enable"
  vpn_ecmp_support               = "enable"

  tags = {
    Name = "main-tgw"
  }
}

# Spoke VPC Attachment
resource "aws_ec2_transit_gateway_vpc_attachment" "spoke_prod" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = module.vpc_prod.vpc_id
  subnet_ids         = module.vpc_prod.private_subnets

  dns_support = "enable"

  tags = {
    Name = "prod-vpc-attachment"
  }
}

# Route: Spoke to Spoke
resource "aws_ec2_transit_gateway_route" "spoke_to_spoke" {
  destination_cidr_block         = "10.1.0.0/16"
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke_prod.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.main.id
}
```

### Advanced: Inspection VPC Pattern

```
                   ┌─────────────────────┐
                   │  Transit Gateway    │
                   └─────────────────────┘
                     │      │       │
            ┌────────┘      │       └────────┐
            │               │                │
            ▼               ▼                ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │  Prod VPC │   │Inspection │   │  Dev VPC  │
     │           │   │    VPC    │   │           │
     │           │   │  ┌──────┐ │   │           │
     │           │   │  │Firewall│   │           │
     │           │   │  └──────┘ │   │           │
     └───────────┘   └───────────┘   └───────────┘

All spoke-to-spoke traffic routed through Inspection VPC firewall
```

---

## Pattern 4: Full Mesh (VPC Peering) Architecture

### Description

Every VPC peered directly with every other VPC.

### Architecture Diagram

```
           ┌───────────┐
           │  VPC-A    │
           └───────────┘
              /  |  \
             /   |   \
            /    |    \
           /     |     \
    ┌─────┐  ┌─────┐  ┌─────┐
    │VPC-B│──│VPC-C│──│VPC-D│
    └─────┘  └─────┘  └─────┘
       │        │        │
       └────────┼────────┘
                │
           ┌─────────┐
           │  VPC-E  │
           └─────────┘

For 5 VPCs: 10 peering connections required
```

### Scaling Challenge

Management complexity scales as O(n²):

| Number of VPCs | Peering Connections Required |
|----------------|------------------------------|
| 3 VPCs | 3 connections |
| 5 VPCs | 10 connections |
| 10 VPCs | 45 connections |
| 20 VPCs | 190 connections |

### Use Cases

**Ideal For:**
- Few VPCs (2-5)
- Low latency needs (no hub hop)
- No centralized inspection needed
- Cost optimization (avoid Transit Gateway fees)
- Simple connectivity needs

**Not Suitable For:**
- More than ~10 VPCs
- Centralized security inspection required
- Frequent topology changes (adding/removing VPCs)

### Pros and Cons

**Advantages:**
- ✓ No single point of failure

**Disadvantages:**
- ✗ Route table management becomes unwieldy

### Implementation Example (AWS)

```hcl
# VPC Peering Connection
resource "aws_vpc_peering_connection" "prod_to_dev" {
  vpc_id      = module.vpc_prod.vpc_id
  peer_vpc_id = module.vpc_dev.vpc_id
  auto_accept = true

  tags = {
    Name = "prod-to-dev-peering"
  }
}

# Routes in Prod VPC to reach Dev VPC
resource "aws_route" "prod_to_dev" {
  count = length(module.vpc_prod.private_route_table_ids)

  route_table_id            = module.vpc_prod.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_dev.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.prod_to_dev.id
}

# Routes in Dev VPC to reach Prod VPC
resource "aws_route" "dev_to_prod" {
  count = length(module.vpc_dev.private_route_table_ids)

  route_table_id            = module.vpc_dev.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_prod.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.prod_to_dev.id
}
```

---

## Pattern 5: Hybrid (Multi-Pattern) Architecture

### Description

Patterns combined per workload needs. Most common: hub-spoke for most VPCs + direct peering for latency-sensitive pairs.

### Architecture Diagram

```
                   ┌─────────────────────┐
                   │  Transit Gateway    │
                   │      (Hub)          │
                   └─────────────────────┘
                     │      │       │
            ┌────────┘      │       └────────┐
            │               │                │
            ▼               ▼                ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │  Prod VPC │◄──┤  Dev VPC  │   │ Shared    │
     │           │   │           │   │ Services  │
     └───────────┘   └───────────┘   └───────────┘
          ▲                                 │
          │          VPC Peering            │
          └─────────────────────────────────┘
           (Low-latency path for specific traffic)
```

### Use Cases

**Ideal For:**
- Large enterprise, diverse needs
- Some workloads need low latency (direct peering)
- Others need centralized inspection (hub-spoke)
- Balancing cost, performance, security
- Complex multi-environment architectures

### Traffic Routing Examples

**Prod ↔ Shared Services:**
- Low-latency direct VPC peering
- No hub hop for time-sensitive operations

**Dev → Prod:**
- Through Transit Gateway for inspection
- Security team can audit cross-environment traffic

**All → On-Premises:**
- Through Transit Gateway
- Single hybrid connection point

---

## Pattern Comparison Matrix

| Criterion | Flat | Multi-VPC | Hub-Spoke | Mesh | Hybrid |
|-----------|------|-----------|-----------|------|--------|
| **Complexity** | Very Low | Low | Medium | High | High |
| **Isolation** | Low | High | Medium | Medium | High |
| **Scalability** | Poor | Medium | Excellent | Poor | Excellent |
| **Latency** | Lowest | N/A | Medium | Lowest | Mixed |
| **Cost** | Lowest | Medium | Medium-High | Low | Medium-High |
| **Management** | Easy | Medium | Medium | Difficult | Difficult |
| **Hybrid Connectivity** | Simple | Duplicate | Centralized | Duplicate | Centralized |
| **Security Inspection** | No | No | Yes | No | Yes |
| **Max VPCs** | 1 | Unlimited | 100+ | ~10 | 100+ |

---

## Migration Paths

### Migrating from Flat to Hub-Spoke

**Step 1:** Create Transit Gateway
**Step 2:** Create separate VPC per environment
**Step 3:** Migrate workloads incrementally
**Step 4:** Attach new VPCs to Transit Gateway
**Step 5:** Decommission flat VPC

**Downtime:** zero possible with proper planning

### Migrating from Mesh to Hub-Spoke

**Step 1:** Create Transit Gateway
**Step 2:** Attach all existing VPCs
**Step 3:** Update route tables to use TGW
**Step 4:** Remove VPC peering connections
**Step 5:** Validate connectivity

**Downtime:** Minimal (during route table updates)

### Migrating from Multi-VPC to Hub-Spoke

**Step 1:** Create Transit Gateway
**Step 2:** Attach VPCs that need communication
**Step 3:** Configure routing policies
**Step 4:** Test connectivity

**Downtime:** None (VPCs stay functional during migration)
