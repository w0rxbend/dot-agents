# Multi-Region Networking

## Use Cases

1. **Disaster Recovery**
   - Failover to secondary region
   - Cross-region data replication

2. **Global Applications**
   - Low latency for users worldwide
   - Geo-distributed workloads

3. **Data Residency**
   - Regional data-law compliance
   - Data sovereignty requirements

## Cross-Region VPC Peering

### AWS

**Setup:**
```hcl
# Peering connection between regions
resource "aws_vpc_peering_connection" "us_to_eu" {
  vpc_id        = aws_vpc.us_east.id
  peer_vpc_id   = aws_vpc.eu_west.id
  peer_region   = "eu-west-1"
  auto_accept   = false  # Requires acceptance in peer region

  tags = {
    Name = "us-east-to-eu-west-peering"
  }
}

# Accept peering in peer region
resource "aws_vpc_peering_connection_accepter" "eu_accept" {
  provider                  = aws.eu_west
  vpc_peering_connection_id = aws_vpc_peering_connection.us_to_eu.id
  auto_accept               = true
}
```

**Data Transfer Costs:**
- Cross-region: $0.02/GB

### GCP

**VPC global by default**
- Subnets regional
- No cross-region peering needed within one VPC
- Multi-region by design

### Azure

**VNet Peering:**
- Cross-region peering supported
- Data transfer: $0.01/GB

## Global Load Balancing

### AWS Global Accelerator

**Use When:**
- Static anycast IPs needed
- Better global availability and performance
- Instant regional failover

**Cost:** $0.025/hour + $0.015/GB

### GCP Cloud Load Balancing

**Use When:**
- Global HTTP(S) load balancing
- Anycast IP addresses
- Cross-region failover

### Azure Traffic Manager

**Use When:**
- DNS-based global load balancing
- Geographic routing
- Priority-based failover

**Cost:** $0.54/million queries

## Multi-Region Architecture Pattern

```
        Global Load Balancer
               │
       ┌───────┴────────┐
       │                │
   us-east-1        eu-west-1
   (Primary)        (DR/Active)
       │                │
   ┌───────┐        ┌───────┐
   │  VPC  │◄───────┤  VPC  │
   │       │ Peering│       │
   └───────┘        └───────┘
```
