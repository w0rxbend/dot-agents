# Azure Messaging Patterns Reference

## Azure Service Bus

Enterprise messaging: queues and publish-subscribe topics.

### Queue vs. Topic

| Feature | Queue | Topic/Subscription |
|---------|-------|-------------------|
| **Pattern** | Point-to-point | Publish-subscribe |
| **Receivers** | Single consumer | Multiple subscribers |
| **Filtering** | No | Yes (SQL filters) |
| **Use Case** | Task distribution | Event broadcasting |

### Sessions for Ordered Processing

Enable sessions for FIFO (first-in-first-out) processing within a session.

---

## Azure Event Grid

Event routing for reactive programming.

### Event Domains

Group related topics for multi-tenant scenarios.

### Advanced Filtering

Filter events by subject, data fields and event type before delivery.

---

## Azure Event Hubs

Big data streaming platform for telemetry and event ingestion.

### Partitioning Strategy

Partition by key (e.g., device ID) for ordered processing within partition.

### Capture Feature

Archives events to Blob Storage or Data Lake automatically.

---

## Storage Queues

Simple queue for async messaging.

**When to Use:**
- Simple task queues
- Cost-sensitive (<500k messages/sec)
- No advanced features needed (transactions, sessions)
