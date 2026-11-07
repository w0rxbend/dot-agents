# Serverless Databases Guide


## Table of Contents

- [Comparison Overview](#comparison-overview)
- [Neon PostgreSQL](#neon-postgresql)
  - [Key Features](#key-features)
  - [Setup](#setup)
  - [Connection String](#connection-string)
  - [Database Branching Workflow](#database-branching-workflow)
  - [Autoscaling Configuration](#autoscaling-configuration)
  - [Time-Travel Queries](#time-travel-queries)
- [PlanetScale MySQL](#planetscale-mysql)
  - [Key Features](#key-features)
  - [Setup](#setup)
  - [Connection String](#connection-string)
  - [Non-Blocking Schema Changes](#non-blocking-schema-changes)
  - [Prisma Integration](#prisma-integration)
  - [Read Replicas](#read-replicas)
- [Turso SQLite](#turso-sqlite)
  - [Key Features](#key-features)
  - [Setup](#setup)
  - [Connection](#connection)
  - [Embedded Replicas (Local-First)](#embedded-replicas-local-first)
  - [Edge Deployment](#edge-deployment)
- [Cost Comparison](#cost-comparison)
  - [Neon (PostgreSQL)](#neon-postgresql)
  - [PlanetScale (MySQL)](#planetscale-mysql)
  - [Turso (SQLite)](#turso-sqlite)
- [Decision Framework](#decision-framework)
  - [Choose Neon if:](#choose-neon-if)
  - [Choose PlanetScale if:](#choose-planetscale-if)
  - [Choose Turso if:](#choose-turso-if)
- [Integration Examples](#integration-examples)
  - [Next.js + Neon (Vercel)](#nextjs-neon-vercel)
  - [Cloudflare Workers + Turso](#cloudflare-workers-turso)
  - [Prisma + PlanetScale](#prisma-planetscale)
- [Best Practices](#best-practices)
  - [Neon](#neon)
  - [PlanetScale](#planetscale)
  - [Turso](#turso)
- [Resources](#resources)

## Comparison Overview

| Feature | Neon (PostgreSQL) | PlanetScale (MySQL) | Turso (SQLite) |
|---------|-------------------|---------------------|----------------|
| **Database Type** | PostgreSQL | MySQL (Vitess) | SQLite (libSQL) |
| **Scale-to-Zero** | ✓✓✓ (Compute) | ✗ | ✓✓ (Replicas) |
| **Branching** | ✓✓✓ (Git-like) | ✓✓✓ (Non-blocking deploys) | ✓ (Embedded replicas) |
| **Cold Start** | <500ms | N/A | <10ms |
| **Autoscaling** | ✓✓✓ (0-8 CPU) | ✓ (Connection pooling) | ✓ (Replica distribution) |
| **Read Replicas** | ✓ (Manual) | ✓✓✓ (Built-in) | ✓✓✓ (Edge replicas) |
| **Write Latency** | ~10-50ms | ~10-50ms | ~5-20ms (edge) |

## Neon PostgreSQL

### Key Features

- **Instant database branches** - Copy production in <1 second
- **Scale-to-zero compute** - Pauses automatically after inactivity
- **Time-travel queries** - Query database state at any point in time
- **Autoscaling** - Compute scales from 0.25 to 8 vCPU automatically
- **Point-in-time restore** - Restore to any second in last 30 days

### Setup

```bash
# Install Neon CLI (analytics on by default: pass --no-analytics on every call)
npm install -g neonctl

# Create project
neonctl --no-analytics projects create --name myapp

# Create branch
neonctl --no-analytics branches create --name dev --parent main

# Get connection string (contains password: capture, don't print)
export DATABASE_URL=$(neonctl --no-analytics connection-string main)
```

### Connection String

```bash
# Pooled connection (recommended for serverless)
postgresql://user:password@ep-cool-darkness-123456-pooler.us-east-2.aws.neon.tech/mydb?sslmode=require

# Direct connection (for migrations)
postgresql://user:password@ep-cool-darkness-123456.us-east-2.aws.neon.tech/mydb?sslmode=require
```

### Database Branching Workflow

**Feature development:**
```bash
# 1. Create branch from main
neonctl --no-analytics branches create --name feature-auth

# 2. Get branch connection string (capture, don't print)
export DATABASE_URL=$(neonctl --no-analytics connection-string feature-auth)

# 3. Run migrations on branch (Prisma telemetry off)
CHECKPOINT_DISABLE=1 PRISMA_DISABLE_TELEMETRY=1 npx prisma migrate dev

# 4. Test feature with real data (copy of production)
# 5. Delete branch when done (confirm with user first)
neonctl --no-analytics branches delete feature-auth
```

**Preview deployments (Vercel integration):**
```bash
# Each PR gets a database branch automatically
# vercel.json
{
  "build": {
    "env": {
      "DATABASE_URL": "@neon-preview-branch"
    }
  }
}
```

### Autoscaling Configuration

```typescript
// Neon automatically scales compute based on load
// Configure via dashboard or API:
// - Min: 0.25 vCPU (scale-to-zero)
// - Max: 8 vCPU
// - Autosuspend: 5 minutes of inactivity
```

### Time-Travel Queries

```sql
-- Query database state from 2 hours ago
SELECT * FROM users AS OF SYSTEM TIME '2025-12-03 10:00:00';

-- Point-in-time restore via dashboard or CLI (overwrites branch; confirm with user first)
neonctl --no-analytics branches restore main --timestamp '2025-12-03 10:00:00'
```

## PlanetScale MySQL

### Key Features

- **Non-blocking schema changes** - Deploy schema changes with zero downtime
- **Database branching** - Development branches with production schema
- **Built-in read replicas** - Automatic geographic distribution
- **Online DDL** - ALTER TABLE without locking
- **No foreign key constraints** - Application enforces referential integrity

### Setup

```bash
# Install PlanetScale CLI
brew install planetscale/tap/pscale

# Authenticate
pscale auth login

# Create database
pscale database create myapp --region us-east

# Create branch
pscale branch create myapp dev
```

### Connection String

```bash
# Get connection string (includes SSL certificate)
pscale connect myapp main --port 3309

# Connection string format
mysql://username:password@aws.connect.psdb.cloud/myapp?ssl={"rejectUnauthorized":true}
```

### Non-Blocking Schema Changes

**Deploy request workflow:**
```bash
# 1. Create development branch
pscale branch create myapp add-user-phone

# 2. Connect to branch
pscale shell myapp add-user-phone

# 3. Make schema changes
mysql> ALTER TABLE users ADD COLUMN phone VARCHAR(20);

# 4. Create deploy request
pscale deploy-request create myapp add-user-phone

# 5. Review diff
pscale deploy-request diff myapp 1

# 6. Deploy to production (zero downtime; confirm with user first)
pscale deploy-request deploy myapp 1

# 7. Auto-merge to main after deploy
```

### Prisma Integration

```prisma
// schema.prisma
datasource db {
  provider = "mysql"
  url = env("DATABASE_URL")
  relationMode = "prisma"  // Required: No FK constraints
}

model User {
  id    Int    @id @default(autoincrement())
  email String @unique
  posts Post[]
}

model Post {
  id     Int    @id @default(autoincrement())
  userId Int
  user   User   @relation(fields: [userId], references: [id])

  @@index([userId])  // Manual index (replaces FK)
}
```

### Read Replicas

```javascript
// Automatically routed to nearest replica
const users = await prisma.user.findMany();  // Read from replica

// Force primary for consistency
const user = await prisma.user.create({ data: { email: 'test@example.com' } });  // Write to primary
```

## Turso SQLite

### Key Features

- **Edge replicas** - Deploy to 200+ locations globally
- **Embedded replicas** - Local SQLite + cloud sync
- **Sub-10ms reads** - Query from nearest edge location
- **LibSQL** - SQLite fork with extensions
- **Multi-region writes** - Eventually consistent replication

### Setup

```bash
# Install Turso CLI via a package manager (macOS/Linux with Homebrew)
brew install tursodatabase/tap/turso
# Without Homebrew: download the vendor installer, read it, then run it
#   curl -sSfLo turso-install.sh https://get.tur.so/install.sh && less turso-install.sh && bash turso-install.sh

# Create database
turso db create myapp

# Create replica in multiple regions
turso db replicate myapp --region ams  # Amsterdam
turso db replicate myapp --region sin  # Singapore

# Get connection URL
turso db show myapp --url
```

### Connection

```typescript
import { createClient } from '@libsql/client';

const db = createClient({
  url: process.env.TURSO_URL,
  authToken: process.env.TURSO_AUTH_TOKEN,
});

const users = await db.execute('SELECT * FROM users');
```

### Embedded Replicas (Local-First)

```typescript
import { createClient } from '@libsql/client';

const db = createClient({
  url: 'file:local.db',  // Local SQLite file
  syncUrl: process.env.TURSO_URL,  // Turso cloud
  authToken: process.env.TURSO_AUTH_TOKEN,
});

// Read from local (instant)
const users = await db.execute('SELECT * FROM users');

// Sync to cloud (background)
await db.sync();
```

### Edge Deployment

```typescript
// Cloudflare Worker + Turso
export default {
  async fetch(request, env) {
    const db = createClient({
      url: env.TURSO_URL,
      authToken: env.TURSO_AUTH_TOKEN,
    });

    const users = await db.execute('SELECT * FROM users');
    return Response.json(users.rows);
  },
};
```

## Cost Comparison

### Neon (PostgreSQL)

**Free Tier:**
- 0.5 GB storage
- 3 compute branches
- Shared compute (0.25 vCPU)

**Launch ($19/month):**
- 10 GB storage
- 10 branches
- 2 vCPU autoscaling (0.25-2)
- Point-in-time restore (7 days)

**Scale ($69/month):**
- 50 GB storage
- Unlimited branches
- 8 vCPU autoscaling (0.25-8)
- Point-in-time restore (30 days)

**Break-even:** 24/7 usage vs managed PostgreSQL (~$50/month)

### PlanetScale (MySQL)

**Hobby (Free):**
- 5 GB storage
- 1 billion row reads/month
- 10 million row writes/month
- 1 production branch

**Scaler ($29/month):**
- 10 GB storage
- 100 billion row reads/month
- 50 million row writes/month
- 2 production branches
- Deploy requests

**Business ($39/month per branch):**
- Unlimited reads/writes
- Multiple production branches
- SSO/SAML

**Break-even:** High read volume vs managed MySQL

### Turso (SQLite)

**Starter (Free):**
- 8 GB storage
- 500 database locations (replicas)
- 1 billion row reads/month

**Scaler ($29/month):**
- 50 GB storage
- 1,000 locations
- 100 billion row reads/month

**Enterprise (Custom):**
- Unlimited
- SLA guarantees
- Dedicated support

**Break-even:** Edge use cases with global distribution

## Decision Framework

### Choose Neon if:
- Need PostgreSQL features (JSONB, arrays, extensions)
- Want scale-to-zero compute
- Database branching for preview environments critical
- Team needs isolated database copies

### Choose PlanetScale if:
- MySQL compatibility required
- Non-blocking schema changes critical
- High read volume with geographic distribution
- Want automated read replicas

### Choose Turso if:
- Building edge apps (Cloudflare Workers, Deno Deploy)
- Need sub-10ms global reads
- Local-first architecture (offline-capable apps)
- SQLite compatibility required

## Integration Examples

### Next.js + Neon (Vercel)

```bash
# 1. Create Neon database
neonctl --no-analytics projects create

# 2. Add to Vercel (telemetry off)
VERCEL_TELEMETRY_DISABLED=1 vercel env add DATABASE_URL

# 3. Automatic branching (preview deployments)
# Each PR gets a Neon branch automatically
```

### Cloudflare Workers + Turso

```typescript
export default {
  async fetch(request, env) {
    const db = createClient({
      url: env.TURSO_URL,
      authToken: env.TURSO_AUTH_TOKEN,
    });

    const result = await db.execute({
      sql: 'SELECT * FROM users WHERE id = ?',
      args: [1],
    });

    return Response.json(result.rows[0]);
  },
};
```

### Prisma + PlanetScale

```typescript
// prisma/schema.prisma
datasource db {
  provider = "mysql"
  url = env("DATABASE_URL")
  relationMode = "prisma"
}

// Deploy schema changes
pscale branch create myapp migration
pscale connect myapp migration --port 3309
DATABASE_URL="mysql://127.0.0.1:3309/myapp" CHECKPOINT_DISABLE=1 PRISMA_DISABLE_TELEMETRY=1 npx prisma db push
pscale deploy-request create myapp migration
```

## Best Practices

### Neon

1. Use **pooled connections** for serverless functions
2. **Branch per feature** for isolated development
3. Enable **autoscaling** for variable workloads
4. Use **time-travel** to debug production issues

### PlanetScale

1. Use **deploy requests** for all schema changes
2. **Index all foreign key columns** (no FK constraints)
3. Test schema changes on **development branches**
4. Monitor **row read/write quotas** on dashboard

### Turso

1. Deploy **replicas near users** for low latency
2. Use **embedded replicas** for offline-first apps
3. **Sync periodically** in background (embedded mode)
4. Monitor **replication lag** in multi-region setups

## Resources

- Neon Docs: https://neon.tech/docs
- PlanetScale Docs: https://planetscale.com/docs
- Turso Docs: https://docs.turso.tech
