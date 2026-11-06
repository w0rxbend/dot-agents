# Document Database Implementation Skill

Production-ready Claude Skill for NoSQL document database selection and implementation.

## Overview

This skill guides document database selection and implementation for flexible schema applications across Python, TypeScript, Rust, and Go.

**Primary databases covered:**
- **MongoDB** (general-purpose, rich queries, vector search)
- **DynamoDB** (AWS serverless, single-table design)
- **Firestore** (real-time sync, mobile-first)

## Skill Structure

```
using-document-databases/
├── SKILL.md                          # Main skill file (<500 lines)
├── references/
│   ├── mongodb.md                    # MongoDB collections, indexes, aggregation
│   ├── dynamodb.md                   # DynamoDB single-table, GSI patterns
│   ├── firestore.md                  # Firestore real-time, security rules
│   └── schema-design-patterns.md     # Embedding vs referencing framework
├── examples/
│   ├── mongodb-fastapi/              # Python FastAPI + MongoDB (Motor)
│   │   ├── main.py
│   │   └── requirements.txt
│   └── dynamodb-serverless/          # Python Lambda + DynamoDB
│       ├── handler.py
│       └── serverless.yml
└── scripts/
    └── validate_indexes.py           # MongoDB index validation tool
```

## Quick Start

### Using the Skill

The skill automatically triggers when building applications with:
- Content management systems
- User profiles with flexible attributes
- Product catalogs
- Event logging systems
- Mobile apps requiring offline sync

### Database Selection

**Use MongoDB when:**
- Complex aggregation queries needed
- Full-text or vector search required
- ACID multi-document transactions needed
- Self-hosted or multi-cloud deployment

**Use DynamoDB when:**
- AWS-native serverless architecture
- Predictable single-digit ms latency required
- Auto-scaling without capacity planning
- Event-driven workflows (Streams + Lambda)

**Use Firestore when:**
- Real-time sync across clients required
- Mobile-first with offline support
- Firebase ecosystem (Auth, Hosting, Analytics)
- Rapid prototyping with generous free tier

## Key Features

### Schema Design Patterns

Decision matrix for embedding vs referencing:
- **One-to-Few** (<10) → Embed
- **One-to-Many** (10-1000) → Hybrid
- **One-to-Millions** → Reference
- **Many-to-Many** → Reference

See `references/schema-design-patterns.md`

### Indexing Strategies

MongoDB index types:
- Single field, compound, multikey
- Text (full-text search)
- Geospatial (2dsphere)
- TTL (auto-expiring documents)
- Wildcard (dynamic schemas)

**Validate indexes:**
```bash
python scripts/validate_indexes.py --db myapp --collection orders
```

### Aggregation Pipelines

MongoDB's killer feature for complex transformations:
- `$match`, `$project`, `$group`, `$lookup`
- `$unwind`, `$sort`, `$limit`, `$facet`

See `references/mongodb.md` for aggregation cookbook.

### DynamoDB Single-Table Design

Access pattern-driven modeling:
```
PK: USER#12345,  SK: METADATA       # User data
PK: USER#12345,  SK: ORDER#001      # User's orders
PK: ORDER#001,   SK: METADATA       # Order details
PK: ORDER#001,   SK: ITEM#001       # Order items
```

See `references/dynamodb.md` for complete patterns.

## Examples

### MongoDB + FastAPI (Python)

Demo async API with Motor (no auth; add it before real use):
```bash
cd examples/mongodb-fastapi
pip install -r requirements.txt
export MONGODB_URI="mongodb://localhost:27017/"
python main.py
```

**Features:**
- Async MongoDB with connection pooling
- CRUD operations with validation
- Aggregation pipeline analytics
- Soft deletes
- Health checks

### DynamoDB + Lambda (Serverless)

AWS serverless demo API with single-table design (public endpoints; add an authorizer before real use):
```bash
cd examples/dynamodb-serverless
# v3 honors the telemetry opt-out; v4 always reports usage to Serverless Inc.
npm install -g serverless@3.40.0
export SLS_TELEMETRY_DISABLED=1
serverless deploy   # creates billed AWS resources; confirm account/stage with user first
```

**Features:**
- Single-table design pattern
- Batch writes for efficiency
- GSI for status queries
- Lambda + API Gateway
- Auto-scaling with pay-per-request

## Multi-Language Support

**Python:**
- `pymongo` (sync)
- `motor` (async with AsyncIO/FastAPI)
- `boto3` (DynamoDB)

**TypeScript:**
- `mongodb` (native driver)
- `@aws-sdk/client-dynamodb` (DynamoDB SDK v3)
- `firebase/firestore` (Firestore)

**Rust:**
- `mongodb` crate
- `aws-sdk-dynamodb`

**Go:**
- `mongo-go-driver`
- `aws-sdk-go-v2`

## Integration with Other Skills

**media/** - File metadata storage (MongoDB GridFS)
**ai-chat/** - Conversation history + vector search (Atlas Vector Search)
**feedback/** - Event logging (DynamoDB high-throughput writes)
**forms/** - Dynamic form submissions (Firestore real-time validation)
**search-filter/** - Product catalogs (MongoDB Atlas Search)

## Performance Best Practices

### MongoDB
- Use indexes for all query filters
- Covering indexes (query + projection in index)
- Connection pooling (reuse client)
- Projection (fetch only needed fields)

### DynamoDB
- Design for even partition distribution
- Batch operations (up to 100 items)
- GSI projections (KEYS_ONLY or INCLUDE)
- TTL for auto-expiring data

### Firestore
- Denormalize frequently accessed data
- Use subcollections for large arrays
- Offline persistence for mobile
- Security rules for access control

## Common Patterns

**Pagination (MongoDB):**
```javascript
// Cursor-based (recommended)
db.products.find({ _id: { $gt: lastId }}).limit(20)
```

**Soft Deletes:**
```javascript
// Mark as deleted instead of removing
{ deleted: true, deletedAt: ISODate("...") }
```

**Audit Logs:**
```javascript
// Versioned documents
{ documentId: "doc123", version: 3, history: [...] }
```

## Dependencies

**Python:**
```bash
pip install motor pymongo boto3 firebase-admin
```

**TypeScript:**
```bash
npm install mongodb @aws-sdk/client-dynamodb firebase
```

## Anti-Patterns to Avoid

❌ **Unbounded arrays** - Use references instead
❌ **Deep nesting** - Flatten with references
❌ **Over-indexing** - Index only queried fields
❌ **DynamoDB scans** - Always use query with partition key
❌ **Missing indexes** - Validate with `explain()`

## Testing

Run index validation:
```bash
python scripts/validate_indexes.py --db myapp --all
```

Expected output:
- ✓ Covered queries
- ✗ Missing indexes with suggestions
- 📈 Index usage statistics
- ⚠️ Unused indexes

## Additional Resources

- MongoDB documentation: `references/mongodb.md`
- DynamoDB patterns: `references/dynamodb.md`
- Firestore guide: `references/firestore.md`
- Schema design: `references/schema-design-patterns.md`

## Version

**v0.1.0** - Initial release (December 2025)

---

**Skill Author:** Claude Code
**Skill Type:** Database Implementation
**Languages:** Python, TypeScript, Rust, Go
**Databases:** MongoDB, DynamoDB, Firestore
