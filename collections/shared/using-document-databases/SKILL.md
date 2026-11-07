---
name: using-document-databases
description: Document database implementation for flexible schema applications. Use when building content management, user profiles, catalogs, or event logging. Covers MongoDB (primary), DynamoDB, Firestore, schema design patterns, indexing strategies, and aggregation pipelines.
---

# Document Database Implementation

## When to Use This Skill

Use document databases when apps need:
- **Flexible schemas** - Data models evolve fast without migrations
- **Nested structures** - JSON-like hierarchical data
- **Horizontal scaling** - Built-in sharding and replication
- **Developer velocity** - Object-to-database mapping without ORM complexity

## Database Selection

### Quick Decision Framework

```
DEPLOYMENT ENVIRONMENT?
├── AWS-Native Application → DynamoDB
│   ✓ Serverless, auto-scaling, single-digit ms latency
│   ✗ Limited query flexibility
│
├── Firebase/GCP Ecosystem → Firestore
│   ✓ Real-time sync, offline support, mobile-first
│   ✗ More expensive for heavy reads
│
└── General-Purpose/Complex Queries → MongoDB
    ✓ Rich aggregation, full-text search, vector search
    ✓ ACID transactions, self-hosted or managed
```

### Database Comparison

| Database | Best For | Latency | Max Item | Query Language |
|----------|----------|---------|----------|----------------|
| **MongoDB** | General-purpose, complex queries | 1-5ms | 16MB | MQL (rich) |
| **DynamoDB** | AWS serverless, predictable performance | <10ms | 400KB | PartiQL (limited) |
| **Firestore** | Real-time apps, mobile-first | 50-200ms | 1MB | Firebase queries |

MongoDB details: `references/mongodb.md`

## Schema Design Patterns

### Embedding vs Referencing

**Use decision matrix in `references/schema-design-patterns.md`**

Quick guide:

| Relationship | Pattern | Example |
|--------------|---------|---------|
| One-to-Few | Embed | User addresses (2-3 max) |
| One-to-Many | Hybrid | Blog posts → comments |
| One-to-Millions | Reference | User → events (logging) |
| Many-to-Many | Reference | Products ↔ Categories |

### Embedding Example (MongoDB)

```javascript
// User with embedded addresses
{
  _id: ObjectId("..."),
  email: "user@example.com",
  name: "Jane Doe",
  addresses: [
    {
      type: "home",
      street: "123 Main St",
      city: "Boston",
      default: true
    }
  ],
  preferences: {
    theme: "dark",
    notifications: { email: true, sms: false }
  }
}
```

### Referencing Example (E-commerce)

```javascript
// Orders reference products
{
  _id: ObjectId("..."),
  userId: ObjectId("..."),
  items: [
    {
      productId: ObjectId("..."),      // Reference
      priceAtPurchase: 49.99,          // Denormalize (historical)
      quantity: 2
    }
  ],
  totalAmount: 99.98
}
```

**Denormalize when:**
- Data is read together often
- Historical snapshots (prices, names)
- Read-heavy workloads

## Indexing Strategies

### MongoDB Index Types

```javascript
// 1. Single field (unique email)
db.users.createIndex({ email: 1 }, { unique: true })

// 2. Compound index (ORDER MATTERS!)
db.orders.createIndex({ status: 1, createdAt: -1 })

// 3. Partial index (index subset)
db.orders.createIndex(
  { userId: 1 },
  { partialFilterExpression: { status: { $eq: "pending" }}}
)

// 4. TTL index (auto-delete after 30 days)
db.sessions.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 2592000 }
)

// 5. Text index (full-text search)
db.articles.createIndex({
  title: "text",
  content: "text"
})
```

**Index Best Practices:**
- Index all query filters
- Compound index order: Equality → Sort → Range (MongoDB ESR rule)
- Use covering indexes (query + projection in index)
- Verify index usage with `explain()`
- Monitor with Performance Advisor (Atlas)

Full guide: `references/indexing-strategies.md`.

## MongoDB Aggregation Pipelines

**Key Operators:** `$match` (filter), `$group` (aggregate), `$lookup` (join), `$unwind` (arrays), `$project` (reshape)

**Full pipeline patterns and examples:** `references/aggregation-patterns.md`

## DynamoDB Single-Table Design

Design for access patterns with PK/SK patterns. Store multiple entity types in one table with composite keys.

**Full single-table design patterns and GSI strategies:** `references/dynamodb.md`

## Firestore Real-Time Patterns

Use `onSnapshot()` for real-time listeners. Use Firestore security rules for access control.

**Full real-time patterns and security rules:** `references/firestore.md`

## Multi-Language Examples

**Complete implementations in `examples/`:**
- `examples/mongodb-fastapi/` - Python FastAPI + MongoDB
- `examples/mongodb-nextjs/` - TypeScript Next.js + MongoDB
- `examples/dynamodb-serverless/` - Python Lambda + DynamoDB
- `examples/firestore-react/` - React + Firestore real-time

## Frontend Skill Integration

- **Media Skill** - MongoDB GridFS for large files with metadata
- **AI Chat Skill** - MongoDB Atlas Vector Search for semantic conversation retrieval
- **Feedback Skill** - DynamoDB for high-throughput event logging with TTL

**Integration examples:** `references/skill-integrations.md`

## Performance Optimization

**Key practices:**
- Use connection pooling (reuse clients across requests)
- Avoid collection scans in production

**Full optimization guide:** `references/performance.md`

## Common Patterns

**Pagination:** Cursor-based pagination for large datasets (preferred over offset)
**Soft Deletes:** Mark deleted with timestamp instead of removing
**Audit Logs:** Store version history in documents

**Implementation details:** `references/common-patterns.md`

## Validation and Scripts

### Validate Index Coverage

```bash
# MongoDB only; requires pymongo and the database profiler enabled
# (db.setProfilingLevel(1, { slowms: 100 })) so slow queries are recorded.
# Credentialed cluster: export MONGODB_URI instead of --uri (keeps password out of ps/history)
python scripts/validate_indexes.py --uri mongodb://localhost:27017/ --db myapp --collection orders
python scripts/validate_indexes.py --db myapp --all
```

Script lists existing indexes, reads slow queries from `system.profile`, and suggests missing or unused indexes. Treat suggestions as candidates. Confirm each with `explain("executionStats")` before creating an index.

### Schema Analysis

No bundled schema analyzer. Check document size and embedding balance by sampling the collection, e.g. in `mongosh` (sends usage telemetry by default; opt out once first: `mongosh --nodb --eval 'disableTelemetry()'`): `db.users.aggregate([{ $sample: { size: 1000 } }, { $project: { size: { $bsonSize: "$$ROOT" } } }, { $group: { _id: null, avg: { $avg: "$size" }, max: { $max: "$size" } } }])`. Look for unbounded arrays (see `references/anti-patterns.md`).

## Anti-Patterns to Avoid

**Unbounded Arrays:** Limit embedded arrays (use references for large collections)
**Over-Indexing:** Only index queried fields (indexes slow writes)
**DynamoDB Scans:** Always use Query with partition key (avoid Scan)

**Detailed anti-patterns:** `references/anti-patterns.md`

## Dependencies

### Python
```bash
# MongoDB
pip install motor pymongo

# DynamoDB
pip install boto3

# Firestore
pip install firebase-admin
```

### TypeScript
```bash
# MongoDB
npm install mongodb

# DynamoDB
npm install @aws-sdk/client-dynamodb @aws-sdk/util-dynamodb

# Firestore
npm install firebase firebase-admin
```

### Rust
```toml
# MongoDB
mongodb = "2.8"

# DynamoDB
aws-sdk-dynamodb = "1.0"
```

### Go
```bash
# MongoDB
go get go.mongodb.org/mongo-driver

# DynamoDB
go get github.com/aws/aws-sdk-go-v2/service/dynamodb
```
