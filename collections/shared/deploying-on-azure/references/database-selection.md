# Azure Database Selection Reference

## Azure SQL Database

### Service Tiers

| Tier | vCores | RAM | Max Storage | Use Case |
|------|--------|-----|-------------|----------|
| **Serverless** | 0.5-40 | Auto | 4 TB | Variable workloads |
| **Provisioned (General Purpose)** | 2-80 | 5-415 GB | 4 TB | Most workloads |
| **Hyperscale** | 2-80 | 5-415 GB | 100 TB | Large databases |
| **Business Critical** | 2-80 | 5-415 GB | 4 TB | Low latency, HA |

---

## Cosmos DB

Globally distributed, multi-model NoSQL database. Multiple consistency models and APIs.

### API Selection

| API | Data Model | Use Case |
|-----|------------|----------|
| **NoSQL** | Document (JSON) | General purpose, new apps |
| **MongoDB** | Document (BSON) | MongoDB compatibility |
| **Cassandra** | Wide-column | Time-series, IoT |
| **Gremlin** | Graph | Social networks, recommendations |
| **Table** | Key-value | Simple key-value storage |

---

## PostgreSQL Flexible Server

**Advantages:**
- Zone-redundant HA
- Flexible maintenance windows
- Built-in connection pooling (PgBouncer)
- Point-in-time restore

---

## MySQL Flexible Server

**Advantages:**
- Zone-redundant HA
- Read replicas
- Automatic backups
- Burstable tier for dev/test

---

## Azure Cache for Redis

In-memory cache for session state, caching and real-time analytics.

### Tiers

| Tier | Clustering | Persistence | Use Case |
|------|------------|-------------|----------|
| **Basic** | No | No | Dev/test |
| **Standard** | No | No | Production cache |
| **Premium** | Yes | Yes | Enterprise, HA |
| **Enterprise** | Yes | Yes | Active geo-replication |
