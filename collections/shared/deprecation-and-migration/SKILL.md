---
name: deprecation-and-migration
description: Manages deprecation and migration. Use when removing old systems, APIs, or features. Use when migrating users from one implementation to another. Use when migrating a database schema in production, such as renaming or dropping a column without downtime (expand/contract). Use when deciding whether to maintain or sunset existing code.
---

# Deprecation and Migration

## When to Use

- Replacing old system, API, or library
- Sunsetting unneeded feature
- Consolidating duplicate implementations
- Removing dead code nobody owns but everybody depends on
- Planning new system lifecycle (deprecation planning starts at design time)
- Choosing: maintain legacy system or invest in migration

## Core Principles

### Code Is a Liability

Every line needs tests, documentation, security patches, dependency updates, and mental overhead for anyone working nearby. Value is functionality, not code. If less code, less complexity, or better abstractions can deliver same functionality, remove old code.

### Hyrum's Law Makes Removal Hard

With enough users, every observable behavior gets depended on: bugs, timing quirks, undocumented side effects. So deprecation needs active migration, not only announcement. Users can't "just switch" if replacement misses behaviors they rely on.

### Deprecation Planning Starts at Design Time

When building something new, ask: "How would we remove this in 3 years?" Clean interfaces, feature flags, and minimal surface area ease deprecation. Leaked implementation details make it harder.

## The Deprecation Decision

Before deprecating anything, answer:

```
1. Does this system still provide unique value?
   → If yes, maintain it. If no, proceed.

2. How many users/consumers depend on it?
   → Quantify the migration scope.

3. Does a replacement exist?
   → If no, build the replacement first. Don't deprecate without an alternative.

4. What's the migration cost for each consumer?
   → If trivially automated, do it. If manual and high-effort, weigh against maintenance cost.

5. What's the ongoing maintenance cost of NOT deprecating?
   → Security risk, engineer time, opportunity cost of complexity.
```

## Compulsory vs Advisory Deprecation

| Type | When to Use | Mechanism |
|------|-------------|-----------|
| **Advisory** | Migration optional, old system stable | Warnings, documentation, nudges. Users migrate on own timeline. |
| **Compulsory** | Old system has security issues, blocks progress, or costs too much to maintain | Hard deadline: old system removed by date X. Provide migration tooling. |

**Default to advisory.** Use compulsory only when maintenance cost or risk justifies forcing migration. Compulsory requires migration tooling, documentation, and support, not only a deadline.

## The Migration Process

### Step 1: Build the Replacement

Don't deprecate without a working alternative. Replacement must:

- Cover all critical use cases of old system
- Have documentation and migration guides
- Be proven in production (not just "theoretically better")

### Step 2: Announce and Document

```markdown
## Deprecation Notice: OldService

**Status:** Deprecated as of 2025-03-01
**Replacement:** NewService (see migration guide below)
**Removal date:** Advisory — no hard deadline yet
**Reason:** OldService requires manual scaling and lacks observability.
            NewService handles both automatically.

### Migration Guide
1. Replace `import { client } from 'old-service'` with `import { client } from 'new-service'`
2. Update configuration (see examples below)
3. Run the project's migration check: `npm run migrate-check`
```

### Step 3: Migrate Incrementally

Migrate consumers one at a time, not all at once. Per consumer:

```
1. Identify all touchpoints with the deprecated system
2. Update to use the replacement
3. Verify behavior matches (tests, integration checks)
4. Remove references to the old system
5. Confirm no regressions
```

**The Churn Rule:** If you own deprecated infrastructure, you migrate your users or ship backward-compatible updates needing no migration. Don't announce deprecation and leave users to figure it out.

### Step 4: Remove the Old System

Only after all consumers have migrated:

```
1. Verify zero active usage (metrics, logs, dependency analysis)
2. Remove the code
3. Remove associated tests, documentation, and configuration
4. Remove the deprecation notices
5. Celebrate — removing code is an achievement
```

## Migration Patterns

### Strangler Pattern

Run old and new in parallel. Shift traffic to new incrementally. Remove old once it handles 0% of traffic.

```
Phase 1: New system handles 0%, old handles 100%
Phase 2: New system handles 10% (canary)
Phase 3: New system handles 50%
Phase 4: New system handles 100%, old system idle
Phase 5: Remove old system
```

### Adapter Pattern

Adapter maps old-interface calls to new implementation. Consumers keep old interface while you migrate backend.

```typescript
// Adapter: old interface, new implementation
class LegacyTaskService implements OldTaskAPI {
  constructor(private newService: NewTaskService) {}

  // Old method signature, delegates to new implementation
  getTask(id: number): OldTask {
    const task = this.newService.findById(String(id));
    return this.toOldFormat(task);
  }
}
```

### Feature Flag Migration

Switch consumers from old to new system one at a time via feature flags:

```typescript
function getTaskService(userId: string): TaskService {
  if (featureFlags.isEnabled('new-task-service', { userId })) {
    return new NewTaskService();
  }
  return new LegacyTaskService(new NewTaskService());
}
```

### Database Schema Migrations (Expand/Contract)

Schema change is riskiest migration: reverting a deploy cannot roll back data. Main failure: coupling schema change to code change. Example: one release renames a column and uses new name. During rollout, old and new code run together; one queries a missing column. Fix: **never change a column in place**. Migrate in additive phases so old and new code stay valid at every step.

```
EXPAND ──────────────→ MIGRATE ──────────────→ CONTRACT
add the new column,    backfill existing rows,  once no code reads the
nullable, alongside    dual-write old+new from  old column, drop it in
the old one            the app                  a later, separate deploy
```

**Worked example — renaming `name` to `full_name`:**

1. **Expand.** Add `full_name` as nullable. Deploy. (Old code ignores it; nothing breaks.)
2. **Dual-write.** App writes `name` and `full_name` on every insert/update. Deploy.
3. **Backfill.** Copy `name → full_name` for existing rows in batches, to avoid locking table.
4. **Switch reads.** Point app at `full_name`; keep writing both. Deploy and bake.
5. **Contract.** Stop writing `name`. Then drop column in a *separate, later* deploy; confirm with user before the drop.

Each step deploys and reverts independently. If step 4 misbehaves, roll code back; `full_name` stays populated. Treat each phase as thin vertical slice (see `incremental-implementation` skill).

**Rules:**
- **Additive first, destructive last and alone.** Adds (new nullable column, table, index) are safe in any deploy. Drops and renames get own deploy *after* no code references old shape.
- **Every migration has a tested down path.** Irreversible migration blocks deploy rollback. Write and run `down` before merging.
- **Backfill in batches, off the hot path.** Single `UPDATE` over millions of rows locks table; chunk and throttle.
- **Build large indexes without blocking writes** (e.g. Postgres `CREATE INDEX CONCURRENTLY`).
- **Decouple from code by feature flag** when cutover is risky (see Feature Flag Migration above).

## Zombie Code

Zombie code: nobody owns it, everybody depends on it. Unmaintained and ownerless, it accumulates security vulnerabilities and compatibility issues. Signs:

- No commits in 6+ months but active consumers exist
- No assigned maintainer or team
- Failing tests nobody fixes
- Known-vulnerable dependencies nobody updates
- Documentation referencing systems that no longer exist

**Response:** Assign owner and maintain properly, or deprecate with concrete migration plan. Zombie code cannot stay in limbo: invest or remove.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It still works, why remove it?" | Unmaintained working code accrues security debt and complexity. Cost grows silently. |
| "Someone might need it later" | Rebuild it if needed. Keeping unused code "just in case" costs more than rebuilding. |
| "The migration is too expensive" | Compare migration cost to 2-3 years of maintenance. Migration usually costs less long-term. |
| "Users will migrate on their own" | They won't. Provide tooling, documentation, and incentives, or do the migration yourself (the Churn Rule). |
| "We can maintain both systems indefinitely" | Two systems doing same thing double maintenance, testing, documentation, and onboarding cost. |

## Red Flags

- "Soft" deprecation, advisory for years, no progress
- New features added to deprecated system (invest in replacement instead)

## Verification

After a deprecation:

- [ ] Replacement production-proven, covers all critical use cases
- [ ] Migration guide has concrete steps and examples
- [ ] All active consumers migrated (verified by metrics/logs)
- [ ] Old code, tests, documentation, and configuration fully removed
- [ ] No references to deprecated system remain in codebase
- [ ] Deprecation notices removed (they served their purpose)

After database schema migration:

- [ ] Change ships in additive phases (expand, backfill, contract), not one in-place edit
- [ ] Old and new code valid against schema at every deploy step
- [ ] Each migration has tested down path; backfills run in throttled batches
- [ ] Destructive steps (drop/rename) get own deploy after no code references old shape
