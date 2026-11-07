---
name: migration
description: Implement reversible compatibility-safe transitions. Use for schema, data, API, protocol, configuration, or dependency migrations requiring rollback and preservation proof.
---

# Migration

Before editing, map current readers, writers, data shape, compatibility window, ownership.

- Define forward and rollback paths.
- Preserve existing data. Make destructive steps explicit and separately authorized.
- Keep mixed-version operation safe where rollouts can overlap.
- Order, when applicable: expand, migrate, verify, then contract.
- Make retries idempotent and partial failure observable.
- Verify old and new paths at required transition stages.

Stop after requested stage passes. Do not run later destructive contraction implicitly.
