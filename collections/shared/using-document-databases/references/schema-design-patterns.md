# Schema Design Patterns

## Table of Contents

- [Core Decision Matrix](#core-decision-matrix)
- [Embedding Pattern](#embedding-pattern)
- [Referencing Pattern](#referencing-pattern)
- [Hybrid Pattern](#hybrid-pattern)
- [Denormalization Strategies](#denormalization-strategies)
- [Anti-Patterns](#anti-patterns)

## Core Decision Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│          EMBEDDING VS REFERENCING DECISION TREE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RELATIONSHIP TYPE?                                              │
│  ├── ONE-TO-FEW (1 to <10)                                      │
│  │   → EMBED                                                     │
│  │   Example: User → Addresses (2-3 max)                        │
│  │   {                                                           │
│  │     userId: "123",                                           │
│  │     addresses: [                                              │
│  │       { type: "home", street: "123 Main" },                  │
│  │       { type: "work", street: "456 Office" }                 │
│  │     ]                                                         │
│  │   }                                                           │
│  │                                                              │
│  ├── ONE-TO-MANY (10 to 1000)                                   │
│  │   → HYBRID (embed summary, reference details)                │
│  │   Example: Blog Post → Comments                              │
│  │   {                                                           │
│  │     postId: "post123",                                       │
│  │     recentComments: [/* last 10 */],                         │
│  │     commentCount: 245  // Reference rest in comments coll    │
│  │   }                                                           │
│  │                                                              │
│  ├── ONE-TO-MILLIONS                                             │
│  │   → REFERENCE                                                │
│  │   Example: User → Events (logging)                           │
│  │   Users: { userId: "123" }                                   │
│  │   Events: { userId: "123", timestamp: "...", type: "..." }   │
│  │                                                              │
│  └── MANY-TO-MANY                                                │
│      → REFERENCE                                                │
│      Example: Products ↔ Categories                             │
│      Products: { productId: "p1", categoryIds: ["c1", "c2"] }   │
│      Categories: { categoryId: "c1", name: "Electronics" }      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Decision Factors

| Factor | Embed | Reference |
|--------|-------|-----------|
| **Relationship Size** | Few (<10) | Many (>100) |
| **Access Pattern** | Always together | Sometimes separate |
| **Update Frequency** | Child rarely changes | Child changes often |
| **Data Growth** | Bounded | Unbounded |
| **Query Pattern** | Parent + children | Children queried independently |
| **Consistency** | Always in sync | May be stale |

## Embedding Pattern

### Example 1: User Profile

```javascript
// Good: Embed addresses (bounded, always accessed together)
{
  _id: ObjectId("..."),
  email: "user@example.com",
  name: "Jane Doe",
  // Embed addresses (few, fixed size)
  addresses: [
    {
      type: "home",
      street: "123 Main St",
      city: "Boston",
      state: "MA",
      zip: "02101",
      default: true
    },
    {
      type: "work",
      street: "456 Business Ave",
      city: "Boston",
      state: "MA",
      zip: "02102",
      default: false
    }
  ],
  // Embed preferences (key-value pairs)
  preferences: {
    theme: "dark",
    language: "en-US",
    notifications: {
      email: true,
      sms: false,
      push: true
    }
  },
  metadata: {
    createdAt: ISODate("2025-01-15"),
    lastLogin: ISODate("2025-11-28"),
    loginCount: 42
  }
}
```

**Benefits:**
- One query gets everything
- Atomic updates (user and addresses together)
- No joins
- Strong consistency

**Query:**
```javascript
// Single query gets user with all addresses
const user = await db.users.findOne({ email: "user@example.com" })
console.log(user.addresses)  // Immediately available
```

## Referencing Pattern

Also reference large subdocuments (approaching 16MB limit).

### Example 1: Blog Posts and Comments

```javascript
// Posts collection
{
  _id: ObjectId("..."),
  title: "MongoDB Schema Design",
  slug: "mongodb-schema-design",
  content: "...",
  authorId: ObjectId("..."),  // Reference to users collection
  tags: ["mongodb", "database", "schema"],
  publishedAt: ISODate("2025-11-15"),
  // Summary stats (denormalized)
  stats: {
    views: 1247,
    likes: 89,
    commentCount: 23  // Count, not actual comments
  }
}

// Comments collection (separate)
{
  _id: ObjectId("..."),
  postId: ObjectId("..."),     // Reference to posts
  authorId: ObjectId("..."),   // Reference to users
  content: "Great article!",
  createdAt: ISODate("2025-11-16")
}

// Users collection (separate)
{
  _id: ObjectId("..."),
  username: "janedoe",
  email: "jane@example.com",
  avatar: "/avatars/jane.jpg"
}
```

**Query Pattern:**
```javascript
// Get post
const post = await db.posts.findOne({ slug: "mongodb-schema-design" })

// Get comments for post (separate query)
const comments = await db.comments.find({ postId: post._id }).toArray()

// Join with aggregation pipeline
const postsWithComments = await db.posts.aggregate([
  { $match: { slug: "mongodb-schema-design" }},
  { $lookup: {
      from: "comments",
      localField: "_id",
      foreignField: "postId",
      as: "comments"
  }}
])
```

## Hybrid Pattern

### Strategy: Embed Summary, Reference Details

Best for one-to-many relationships needing both summary and detail access.

### Example 1: Blog Post with Comment Preview

```javascript
// Post with embedded recent comments
{
  _id: ObjectId("..."),
  title: "MongoDB Schema Design",
  content: "...",
  // Embed recent comments for preview
  recentComments: [
    {
      commentId: ObjectId("..."),
      authorName: "John Smith",
      content: "Great article!",
      createdAt: ISODate("2025-11-28")
    },
    {
      commentId: ObjectId("..."),
      authorName: "Alice Johnson",
      content: "Very helpful, thanks!",
      createdAt: ISODate("2025-11-27")
    }
    // Last 5-10 comments embedded
  ],
  commentCount: 245,  // Total count
  // Full comments in separate collection
}

// Comments collection (all comments)
{
  _id: ObjectId("..."),
  postId: ObjectId("..."),
  authorId: ObjectId("..."),
  authorName: "John Smith",  // Denormalized for performance
  content: "Great article!",
  createdAt: ISODate("2025-11-28")
}
```

**Update Pattern:**
```javascript
// When new comment added:
// 1. Insert into comments collection
const commentId = await db.comments.insertOne({
  postId: postId,
  authorId: userId,
  authorName: "New User",
  content: "New comment"
})

// 2. Update post with recent comments + count
await db.posts.updateOne(
  { _id: postId },
  {
    $push: {
      recentComments: {
        $each: [{
          commentId: commentId.insertedId,
          authorName: "New User",
          content: "New comment",
          createdAt: new Date()
        }],
        $position: 0,  // Add to beginning
        $slice: 10     // Keep only 10 most recent
      }
    },
    $inc: { commentCount: 1 }
  }
)
```

## Denormalization Strategies

### When to Denormalize

1. **Read-heavy workloads** (optimize reads over writes)
2. **Frequently accessed together**
3. **Historical snapshots** (prices, names at transaction time)
4. **Reduce query complexity** (avoid aggregation lookups)

### Example 1: Social Media Post

```javascript
{
  _id: ObjectId("..."),
  content: "Check out this amazing feature!",
  authorId: ObjectId("..."),        // Reference
  // Denormalize author info (avoid join on every post read)
  authorName: "Jane Doe",           // Duplicated from users
  authorAvatar: "/avatars/jane.jpg", // Duplicated from users
  authorVerified: true,              // Duplicated from users
  createdAt: ISODate("2025-11-28"),
  likes: 42,
  comments: 17,
  shares: 8
}
```

**Update Pattern:**
```javascript
// When user updates profile, update all their posts
await db.users.updateOne(
  { _id: userId },
  { $set: { name: "Jane Smith", avatar: "/avatars/jane-new.jpg" }}
)

// Propagate to posts (eventual consistency acceptable)
await db.posts.updateMany(
  { authorId: userId },
  { $set: {
      authorName: "Jane Smith",
      authorAvatar: "/avatars/jane-new.jpg"
  }}
)
```

### Example 2: Order Historical Data

```javascript
{
  _id: ObjectId("..."),
  orderNumber: "ORD-2025-001234",
  items: [
    {
      productId: ObjectId("..."),
      // Denormalize product info (snapshot at purchase time)
      name: "Widget Pro",           // May change in products collection
      sku: "WGT-PRO-001",
      priceAtPurchase: 49.99,       // Current price may differ
      category: "widgets",
      imageUrl: "/images/wgt.jpg"
    }
  ],
  totalAmount: 249.97
}
```

**Why?** Order shows what customer bought. If product name or price changes, order should still show historical data.

## Anti-Patterns

### ❌ Unbounded Arrays

```javascript
// BAD: Array grows indefinitely
{
  userId: "user123",
  events: [/* 10,000+ events */]  // Document too large! (>16MB limit)
}

// GOOD: Use references
{
  userId: "user123",
  recentEvents: [/* Last 10 events */]  // Embed recent
}
// Store full history in separate collection
db.events.find({ userId: "user123" })
```

### ❌ Deep Nesting

```javascript
// BAD: Too many levels (hard to query, update)
{
  company: {
    departments: [
      {
        name: "Engineering",
        teams: [
          {
            name: "Backend",
            members: [
              {
                name: "Jane",
                projects: [
                  { name: "API", tasks: [...] }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}

// GOOD: Flatten with references
// Companies collection
{ _id: "comp1", name: "Acme Corp" }

// Departments collection
{ _id: "dept1", companyId: "comp1", name: "Engineering" }

// Teams collection
{ _id: "team1", departmentId: "dept1", name: "Backend" }

// Members collection
{ _id: "mem1", teamId: "team1", name: "Jane" }
```

### ❌ Massive Documents

```javascript
// BAD: Single document with all user data
{
  userId: "user123",
  profile: {...},
  orders: [/* 1000s of orders */],
  messages: [/* 10000s of messages */],
  events: [/* 100000s of events */]
}
// Document size: >16MB (MongoDB limit!)

// GOOD: Separate collections
// Users: { userId: "user123", profile: {...} }
// Orders: { userId: "user123", ... }
// Messages: { userId: "user123", ... }
// Events: { userId: "user123", ... }
```

### ❌ Premature Referencing

```javascript
// BAD: Reference for small, bounded data
{
  userId: "user123",
  addressId: ObjectId("...")  // Reference to addresses collection
}
// Requires join for every user fetch!

// GOOD: Embed small, bounded data
{
  userId: "user123",
  addresses: [
    { type: "home", street: "123 Main" }  // Max 2-3 addresses
  ]
}
```

## Schema Evolution

### Adding Fields (Schema-less Advantage)

```javascript
// Old documents
{ userId: "user123", name: "Jane" }

// New documents (with new field)
{ userId: "user456", name: "John", phoneNumber: "555-1234" }

// Handle in application code
const user = await db.users.findOne({ userId: "user123" })
const phone = user.phoneNumber || null  // Graceful handling
```

### Migrating Schema

```javascript
// Gradual migration (no downtime)
// 1. Application handles both old and new formats
// 2. Migrate documents over time

// Migration script
await db.users.updateMany(
  { version: { $exists: false }},  // Old documents
  [
    {
      $set: {
        fullName: { $concat: ["$firstName", " ", "$lastName"] },
        version: 2
      }
    },
    { $unset: ["firstName", "lastName"] }
  ]
)
```

## Performance Considerations

### Document Size Limits

| Database | Max Document Size |
|----------|-------------------|
| **MongoDB** | 16 MB |
| **DynamoDB** | 400 KB |
| **Firestore** | 1 MB |

**Rule of thumb:** Keep documents < 1 MB for best performance.

### Read vs Write Optimization

| Pattern | Read Performance | Write Performance | Use Case |
|---------|------------------|-------------------|----------|
| **Embed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Read-heavy |
| **Reference** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Write-heavy |
| **Denormalize** | ⭐⭐⭐⭐⭐ | ⭐⭐ | Read >> Writes |

Database-specific patterns: `mongodb.md`, `dynamodb.md`, `firestore.md`.
