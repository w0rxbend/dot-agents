# Multi-Cloud Networking

## Unified Concepts

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

## Provider Best Practices

### AWS
- Multi-AZ baseline for production
- Prefer Transit Gateway for 5+ VPCs
- VPC Endpoints to avoid NAT charges

### GCP
- Custom mode VPC (not auto-mode)
- Start with one VPC; Shared VPC for multi-project
- Grant network user role at subnet level

### Azure
- Hub-and-spoke topology as standard
- Prefer few large VNets over many small VNets
- Private endpoints for Azure services

AWS implementation examples: `../examples/aws/`.
