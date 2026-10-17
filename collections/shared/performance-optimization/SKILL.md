---
name: performance-optimization
description: Find and fix a measured bottleneck in a web app, API, query or algorithm (Core Web Vitals, bundle size, N+1, missing indexes, caching, memory leaks), proving it with before/after numbers. Use when something is slow or regressed; for load/stress testing, capacity planning and perf SLOs use performance-engineering.
risk: safe
source: https://github.com/addyosmani/agent-skills/tree/main/skills/performance-optimization
source_repo: addyosmani/agent-skills
source_type: community
date_added: 2026-07-01
license: MIT
license_source: https://github.com/addyosmani/agent-skills/blob/main/LICENSE
---

# Performance Optimization

## Overview

Measure before optimizing. Performance work without measurement is guessing — and guessing leads to premature optimization that adds complexity without improving what matters. Profile first, identify the actual bottleneck, fix it, measure again. Optimize only what measurements prove matters.

## When to Use

- Performance requirements exist in the spec (load time budgets, response time SLAs)
- Users or monitoring report slow behavior
- Core Web Vitals scores are below thresholds
- You suspect a change introduced a regression
- Building features that handle large datasets or high traffic

**When NOT to use:** Don't optimize before you have evidence of a problem. Premature optimization adds complexity that costs more than the performance it gains.

## Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## The Optimization Workflow

```
1. MEASURE  → Establish baseline with real data
2. IDENTIFY → Find the actual bottleneck (not assumed)
3. FIX      → Address the specific bottleneck
4. VERIFY   → Measure again, confirm improvement
5. GUARD    → Add monitoring or tests to prevent regression
```

### Step 1: Measure

Two complementary approaches — use both:

- **Synthetic (Lighthouse, DevTools Performance tab):** Controlled conditions, reproducible. Best for CI regression detection and isolating specific issues.
- **RUM (web-vitals library, CrUX):** Real user data in real conditions. Required to validate that a fix actually improved user experience.

**Frontend (synthetic):** Chrome DevTools → Performance tab → Record, or a Lighthouse run. For a scripted lab audit with scores and LCP/CLS/TBT in JSON:

```bash
python3 scripts/lighthouse_audit.py https://staging.example.com   # needs the lighthouse CLI + Chrome
```

Lab runs cannot measure INP; Total Blocking Time is the closest lab proxy.

**Frontend (RUM):**
```typescript
import { onLCP, onINP, onCLS } from 'web-vitals';

onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

**Backend:** APM traces, database slow-query logs with timing, or a quick local timing:
```typescript
console.time('db-query');
const result = await db.query(sql, params);
console.timeEnd('db-query');
```

Record the baseline numbers (p50/p95, sizes, query counts) before changing anything; you need them for Step 4.

### Where to Start Measuring

Use the symptom to decide what to measure first:

```
What is slow?
├── First page load
│   ├── Large bundle? --> Measure bundle size, check code splitting
│   ├── Slow server response? --> Measure TTFB in DevTools Network waterfall
│   │   ├── DNS long? --> Add dns-prefetch / preconnect for known origins
│   │   ├── TCP/TLS long? --> Enable HTTP/2, check edge deployment, keep-alive
│   │   └── Waiting (server) long? --> Profile backend, check queries and caching
│   └── Render-blocking resources? --> Check network waterfall for CSS/JS blocking
├── Interaction feels sluggish
│   ├── UI freezes on click? --> Profile main thread, look for long tasks (>50ms)
│   ├── Form input lag? --> Check re-renders, controlled component overhead
│   └── Animation jank? --> Check layout thrashing, forced reflows
├── Page after navigation
│   ├── Data loading? --> Measure API response times, check for waterfalls
│   └── Client rendering? --> Profile component render time, check for N+1 fetches
└── Backend / API
    ├── Single endpoint slow? --> Profile database queries, check indexes
    ├── All endpoints slow? --> Check connection pool, memory, CPU
    └── Intermittent slowness? --> Check for lock contention, GC pauses, external deps
```

### Step 2: Identify the Bottleneck

Common bottlenecks by category:

**Frontend:**

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| Slow LCP | Large images, render-blocking resources, slow server | Check network waterfall, image sizes |
| High CLS | Images without dimensions, late-loading content, font shifts | Check layout shift attribution |
| Poor INP | Heavy JavaScript on main thread, large DOM updates | Check long tasks in Performance trace |
| Slow initial load | Large bundle, many network requests | Check bundle size, code splitting |

**Backend:**

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| Slow API responses | N+1 queries, missing indexes, unoptimized queries | Check database query log |
| Memory growth | Leaked references, unbounded caches, large payloads | Heap snapshot analysis |
| CPU spikes | Synchronous heavy computation, regex backtracking | CPU profiling |
| High latency | Missing caching, redundant computation, network hops | Trace requests through the stack |

**Choosing a profiling tool:**

| Problem | Tool |
|---|---|
| Page load | Lighthouse, DevTools Network waterfall |
| Bundle size | Bundle analyzer for your bundler (e.g. `rollup-plugin-visualizer`, `webpack-bundle-analyzer`, `source-map-explorer`) |
| Main-thread work | DevTools Performance panel |
| Memory | DevTools Memory panel (heap snapshots, allocation timeline) |
| Node.js CPU | `node --cpu-prof app.js` (open the `.cpuprofile` in DevTools) or `node --inspect` + Performance panel |
| SQL | `EXPLAIN ANALYZE` (PostgreSQL) / `EXPLAIN ANALYZE` or `EXPLAIN FORMAT=TREE` (MySQL 8) |

**Reading a bundle analysis:**

| Finding | Indicator | Action |
|---|---|---|
| Large dependency | Dominates the treemap | Lighter alternative, per-module import, or lazy load |
| Duplicate code | Same package in several chunks or versions | Dedupe versions, shared chunk |
| Unused code | Low DevTools Coverage | Remove or split |
| Missing split | One large initial chunk with route code | Route-level code splitting |

**Reading a DevTools Memory profile:**

| Pattern | Meaning |
|---|---|
| Heap keeps growing across repeated identical actions | Likely leak; compare two snapshots |
| Large retained size on one object | Follow its retainers to the reference keeping it alive |
| Detached DOM nodes | Removed elements still referenced (listeners, caches, closures) |

### Step 3: Fix Common Anti-Patterns

#### N+1 Queries (Backend)

```typescript
// BAD: N+1 — one query per task for the owner
const tasks = await db.tasks.findMany();
for (const task of tasks) {
  task.owner = await db.users.findUnique({ where: { id: task.ownerId } });
}

// GOOD: Single query with join/include
const tasks = await db.tasks.findMany({
  include: { owner: true },
});
```

#### Missing Index (verify with the query plan)

```sql
-- PostgreSQL: look at the plan and actual timings
EXPLAIN ANALYZE SELECT id, name FROM users WHERE email = 'test@example.com';
-- "Seq Scan on users ... rows=1 ... actual time=... " on a large table → missing index

CREATE INDEX CONCURRENTLY idx_users_email ON users (email);  -- avoids long write locks

EXPLAIN ANALYZE SELECT id, name FROM users WHERE email = 'test@example.com';
-- expect "Index Scan using idx_users_email"
```

An index only helps predicates it can serve: `LIKE '%term%'` (leading wildcard) or `lower(email) = ...` will not use a plain btree index on `email`. A sequential scan on a tiny table is fine. Every index costs write time and storage, so add it for a measured query, then re-run the plan.

#### Over-fetching Columns and Payloads

```typescript
// BAD: every column, every field serialized
const users = await db.query('SELECT * FROM users');
res.json(users);

// GOOD: only what the caller renders
const users = await db.query('SELECT id, name, email FROM users');
res.json(users);
```

`SELECT *` also defeats index-only scans and silently grows responses when columns are added.

#### Sequential Independent Awaits

```typescript
// BAD: 300ms + 200ms + 150ms
const user = await getUser(id);
const posts = await getPosts(id);
const comments = await getComments(id);

// GOOD: ~max(300, 200, 150)ms when the calls are independent
const [user, posts, comments] = await Promise.all([getUser(id), getPosts(id), getComments(id)]);
```

#### Unbounded Data Fetching

```typescript
// BAD: Fetching all records
const allTasks = await db.tasks.findMany();

// GOOD: Paginated with limits
const tasks = await db.tasks.findMany({
  take: 20,
  skip: (page - 1) * 20,
  orderBy: { createdAt: 'desc' },
});
```

#### Missing Image Optimization (Frontend)

```html
<!-- BAD: No dimensions, no format optimization -->
<img src="/hero.jpg" />

<!-- GOOD: Hero / LCP image — art direction + resolution switching, high priority -->
<!--
  Two techniques combined:
  - Art direction (media): different crop/composition per breakpoint
  - Resolution switching (srcset + sizes): right file size per screen density
-->
<picture>
  <!-- Mobile: portrait crop (8:10) -->
  <source
    media="(max-width: 767px)"
    srcset="/hero-mobile-400.avif 400w, /hero-mobile-800.avif 800w"
    sizes="100vw"
    width="800"
    height="1000"
    type="image/avif"
  />
  <source
    media="(max-width: 767px)"
    srcset="/hero-mobile-400.webp 400w, /hero-mobile-800.webp 800w"
    sizes="100vw"
    width="800"
    height="1000"
    type="image/webp"
  />
  <!-- Desktop: landscape crop (2:1) -->
  <source
    srcset="/hero-800.avif 800w, /hero-1200.avif 1200w, /hero-1600.avif 1600w"
    sizes="(max-width: 1200px) 100vw, 1200px"
    width="1200"
    height="600"
    type="image/avif"
  />
  <source
    srcset="/hero-800.webp 800w, /hero-1200.webp 1200w, /hero-1600.webp 1600w"
    sizes="(max-width: 1200px) 100vw, 1200px"
    width="1200"
    height="600"
    type="image/webp"
  />
  <img
    src="/hero-desktop.jpg"
    width="1200"
    height="600"
    fetchpriority="high"
    alt="Hero image description"
  />
</picture>

<!-- GOOD: Below-the-fold image — lazy loaded + async decoding -->
<img
  src="/content.webp"
  width="800"
  height="400"
  loading="lazy"
  decoding="async"
  alt="Content image description"
/>
```

#### Unnecessary Re-renders (React)

```tsx
// BAD: Creates new object on every render, causing children to re-render
function TaskList() {
  return <TaskFilters options={{ sortBy: 'date', order: 'desc' }} />;
}

// GOOD: Stable reference
const DEFAULT_OPTIONS = { sortBy: 'date', order: 'desc' } as const;
function TaskList() {
  return <TaskFilters options={DEFAULT_OPTIONS} />;
}

// Use React.memo for expensive components
const TaskItem = React.memo(function TaskItem({ task }: Props) {
  return <div>{/* expensive render */}</div>;
});

// Use useMemo for expensive computations
function TaskStats({ tasks }: Props) {
  const stats = useMemo(() => calculateStats(tasks), [tasks]);
  return <div>{stats.completed} / {stats.total}</div>;
}
```

#### Large Bundle Size

```typescript
// Modern bundlers (Vite, webpack 5+) handle named imports with tree-shaking automatically,
// provided the dependency ships ESM and is marked `sideEffects: false` in package.json.
// Profile before changing import styles — the real gains come from splitting and lazy loading.

// GOOD: Dynamic import for heavy, rarely-used features
const ChartLibrary = lazy(() => import('./ChartLibrary'));

// GOOD: Route-level code splitting wrapped in Suspense
const SettingsPage = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <SettingsPage />
    </Suspense>
  );
}
```

#### Missing Caching (Backend)

```typescript
// Cache frequently-read, rarely-changed data
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
let cachedConfig: AppConfig | null = null;
let cacheExpiry = 0;

async function getAppConfig(): Promise<AppConfig> {
  if (cachedConfig && Date.now() < cacheExpiry) {
    return cachedConfig;
  }
  cachedConfig = await db.config.findFirst();
  cacheExpiry = Date.now() + CACHE_TTL;
  return cachedConfig;
}

// HTTP caching headers for static assets
app.use('/static', express.static('public', {
  maxAge: '1y',           // Cache for 1 year
  immutable: true,        // Never revalidate (use content hashing in filenames)
}));

// Cache-Control for API responses
res.set('Cache-Control', 'public, max-age=300'); // 5 minutes
```

Only cache responses that are safe to share: per-user data needs `private` (or no shared cache), and every cache needs an invalidation story.

#### Algorithmic Complexity

When a CPU profile points at your own code, check complexity before micro-tuning:

```typescript
// BAD: O(n²) nested scan
function findDuplicates<T>(items: T[]): T[] {
  const dupes: T[] = [];
  for (let i = 0; i < items.length; i++)
    for (let j = i + 1; j < items.length; j++)
      if (items[i] === items[j]) dupes.push(items[i]);
  return dupes;
}

// GOOD: O(n) with a Set
function findDuplicates<T>(items: T[]): T[] {
  const seen = new Set<T>();
  const dupes = new Set<T>();
  for (const item of items) {
    if (seen.has(item)) dupes.add(item);
    seen.add(item);
  }
  return [...dupes];
}
```

Other common wins: replace repeated `array.find`/`includes` inside loops with a `Map`/`Set` lookup, hoist invariant work out of loops, and avoid catastrophic regex backtracking on untrusted input.

#### Memory Leaks and Large Data

```typescript
// BAD: listener never removed → component and its closure stay alive
useEffect(() => {
  window.addEventListener('scroll', handleScroll);
}, []);

// GOOD: cleanup
useEffect(() => {
  window.addEventListener('scroll', handleScroll);
  return () => window.removeEventListener('scroll', handleScroll);
}, [handleScroll]);
```

```typescript
// BAD: whole file in memory
const data = await fs.promises.readFile('huge.log');

// GOOD: stream it
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';
for await (const line of createInterface({ input: createReadStream('huge.log') })) {
  handle(line);
}
```

Also look for unbounded caches/maps keyed by request data (add a size limit or TTL) and timers/intervals that are never cleared.

## Performance Budget

Set budgets and enforce them:

```
JavaScript bundle: < 200KB gzipped (initial load)
CSS: < 50KB gzipped
Images: < 200KB per image (above the fold)
Fonts: < 100KB total
API response time: < 200ms (p95)
Time to Interactive: < 3.5s on 4G
Lighthouse Performance score: ≥ 90
```

**Enforce in CI:**
```bash
# Bundle size check
npx bundlesize --config bundlesize.config.json

# Lighthouse CI
npx lhci autorun
```

Treat these numbers as starting points; derive real budgets from your baseline and user expectations.

## Related Skills

- `performance-engineering`: load/stress/soak tests, backend profilers (py-spy, pprof, clinic.js), performance SLOs and CI perf gates.
- `observability-and-instrumentation`: latency histograms and traces that keep regressions visible after the fix.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll optimize later" | Performance debt compounds. Fix obvious anti-patterns now, defer micro-optimizations. |
| "It's fast on my machine" | Your machine isn't the user's. Profile on representative hardware and networks. |
| "This optimization is obvious" | If you didn't measure, you don't know. Profile first. |
| "Users won't notice 100ms" | Research shows 100ms delays impact conversion rates. Users notice more than you think. |
| "The framework handles performance" | Frameworks prevent some issues but can't fix N+1 queries or oversized bundles. |

## Red Flags

- Optimization without profiling data to justify it
- N+1 query patterns in data fetching
- List endpoints without pagination
- Images without dimensions, lazy loading, or responsive sizes
- Bundle size growing without review
- No performance monitoring in production
- `React.memo` and `useMemo` everywhere (overusing is as bad as underusing)

## Verification

After any performance-related change:

- [ ] Before and after measurements exist (specific numbers)
- [ ] The specific bottleneck is identified and addressed
- [ ] Core Web Vitals are within "Good" thresholds
- [ ] Bundle size hasn't increased significantly
- [ ] No N+1 queries in new data fetching code
- [ ] Performance budget passes in CI (if configured)
- [ ] Existing tests still pass (optimization didn't break behavior)

## Limitations

- Lab numbers (Lighthouse, local timing) can disagree with field data; confirm user-facing wins with RUM or production percentiles.
- Index creation, cache changes and load against shared environments affect other users: get approval and use non-blocking variants (e.g. `CREATE INDEX CONCURRENTLY`) where the database supports them.
