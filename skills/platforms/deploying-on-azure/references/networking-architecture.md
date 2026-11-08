# Azure Networking Architecture Reference

## Hub-and-Spoke Topology

### Hub VNet Components

- Azure Firewall (centralized traffic filtering)
- VPN Gateway (hybrid connectivity)
- Azure Bastion (secure VM access)
- Private Endpoints (shared PaaS services)
- DNS forwarders

### Spoke VNet Components

- Application workloads
- Environment isolation (dev, staging, prod)
- Team isolation

### VNet Peering

- Low-latency, high-bandwidth connectivity
- No data egress charges between peered VNets in same region
- Hub-spoke peering: Enable "Allow Gateway Transit" in hub, "Use Remote Gateway" in spoke

---

## Private Endpoints

Network interface connecting privately and securely to a service powered by Azure Private Link.

### Supported Services

100+ Azure services support Private Endpoints, including:
- Storage (Blob, Files, Queue, Table)
- Databases (SQL, Cosmos DB, PostgreSQL, MySQL)
- Azure OpenAI, Cognitive Services
- Key Vault, App Configuration
- Container Registry, Event Hub, Service Bus

### Private DNS Zones

Required for automatic DNS resolution of privatelink FQDNs.

---

## Network Security Groups

Stateful firewall rules for subnet- and NIC-level filtering.

### Rule Priority

- Lower number means higher priority
- Default rules (65000-65500) allow VNet traffic, deny internet
- Custom rules (100-4096) take precedence

---

## Load Balancing

### Service Comparison

| Service | Layer | Scope | Use Case |
|---------|-------|-------|----------|
| **Azure Front Door** | L7 (HTTP/S) | Global | Global routing, WAF |
| **Application Gateway** | L7 (HTTP/S) | Regional | Regional load balancing, WAF |
| **Load Balancer** | L4 (TCP/UDP) | Regional | Non-HTTP traffic |
| **Traffic Manager** | DNS | Global | DNS-based routing |

---

## DNS Configuration

### Azure Private DNS Zones

Link private DNS zones to VNets so Private Endpoints resolve automatically.

### DNS Forwarding

Conditional forwarders for hybrid DNS resolution, both ways between on-premises and Azure.
