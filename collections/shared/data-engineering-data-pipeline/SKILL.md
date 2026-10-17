---
name: data-engineering-data-pipeline
description: "Build or review batch and streaming data pipelines end to end: pattern choice (ETL/ELT, batch vs streaming), incremental and idempotent loads, Airflow/Prefect orchestration, dbt transformations, data-quality gates, Delta/Iceberg table maintenance, monitoring and cost. Use when implementing or fixing a pipeline's jobs and DAGs; use ingesting-data for source connectors and file/API loading, architecting-data for platform-level architecture."
risk: safe
source: community
date_added: "2026-02-27"
---

# Data Pipeline Engineering

Turn a data flow requirement into a pipeline that is incremental, idempotent, tested and observable.

## Use this skill when

- Implementing a new batch or streaming pipeline (extract -> transform -> load -> serve)
- Writing or fixing Airflow/Prefect DAGs, dbt models, Spark jobs, or streaming consumers
- Adding data-quality checks, backfills, late-data handling or monitoring to an existing pipeline
- Reducing pipeline cost or runtime

## Do not use this skill when

- Choosing lake vs warehouse vs lakehouse, data mesh, or modeling paradigm (use `architecting-data`)
- Only connecting a source and loading files/APIs/CDC (use `ingesting-data`)
- Broker setup and consumer patterns for application messaging (use `using-message-queues`)

## 1. Gather Requirements

Write down before designing:

| Question | Why it matters |
|----------|----------------|
| Sources, formats, volume per run, growth | Ingestion method, partitioning, compute size |
| Freshness SLA (minutes? daily?) | Batch vs micro-batch vs streaming |
| Consumers and their access patterns | Serving layer, table layout |
| Can sources change history (updates, deletes, late events)? | Full vs incremental, CDC, merge strategy |
| Correctness needs (exact counts? duplicates tolerable?) | Dedup and idempotency design |
| Backfill horizon | Partitioned, parameterized runs |

## 2. Choose the Pattern

| Pattern | Use when | Avoid when |
|---------|----------|------------|
| ELT (load raw, transform in warehouse with dbt) | Warehouse/lakehouse compute is available; SQL-friendly transforms | Sensitive data must be filtered before landing |
| ETL (transform before load) | Heavy cleansing, PII removal or format conversion before landing | Transform logic changes often (reprocessing is costly) |
| Scheduled batch | Freshness of hours/day, simple ops | Sub-minute SLA |
| Micro-batch (e.g. Spark Structured Streaming triggers) | Minutes of latency, reuse batch code | Per-event reactions |
| Streaming (Kafka/Flink/Kafka Streams) | Seconds of latency, event-driven consumers | Team lacks ops capacity; batch meets the SLA |

Prefer the simplest pattern meeting the SLA. A "Lambda" architecture (separate batch and speed paths) doubles logic; use it only when you cannot reprocess from a replayable log.

## 3. Build Rules That Make Pipelines Safe to Rerun

1. **Incremental by watermark or CDC.** Track the high-water mark (`updated_at`, log offset) in state, not in code; read with an overlap window to catch late commits.
2. **Idempotent writes.** Rerunning a run must produce the same result: `MERGE`/upsert on a business key, or overwrite a whole partition (`INSERT OVERWRITE ... PARTITION (ds = ...)`). Never blind-append in a retried task.
3. **Parameterize by logical date/interval,** not wall-clock time, so backfills reuse the same code path.
4. **Quarantine bad records** to a dead-letter table/location with the reason; fail the run when the reject rate exceeds a threshold.
5. **Add lineage metadata columns** (`_ingested_at`, `_source`, `_run_id`).
6. **Streaming:** commit offsets only after the sink write succeeds; make the sink idempotent or transactional. "Exactly-once" holds only end to end when source, processor and sink all participate (e.g. Kafka transactions with a transactional or idempotent sink); otherwise assume at-least-once and deduplicate.

### Minimal incremental, idempotent load (PostgreSQL target)

```sql
-- staging table loaded with rows where updated_at > :last_watermark - interval '10 minutes'
INSERT INTO analytics.orders AS t (order_id, customer_id, status, amount, updated_at, _ingested_at)
SELECT order_id, customer_id, status, amount, updated_at, now()
FROM staging.orders_batch
ON CONFLICT (order_id) DO UPDATE
SET customer_id = EXCLUDED.customer_id,
    status      = EXCLUDED.status,
    amount      = EXCLUDED.amount,
    updated_at  = EXCLUDED.updated_at,
    _ingested_at = EXCLUDED._ingested_at
WHERE t.updated_at < EXCLUDED.updated_at;   -- ignore stale replays
```

Then store `max(updated_at)` from the batch as the new watermark in the same transaction or after the merge commits.

## 4. Orchestration

- One task = one idempotent unit with its own retries (bounded, with backoff) and timeout.
- Pass references (table/partition names, paths) between tasks, not data. In Airflow keep XCom small.
- Set `catchup`/backfill behavior deliberately; cap `max_active_runs` for pipelines that write the same tables.
- Alert on failure and on SLA/freshness misses, not on every retry.

```python
# Airflow 2.x TaskFlow sketch; check the installed version for parameter names
from airflow.decorators import dag, task
import pendulum

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
     catchup=False, max_active_runs=1, default_args={"retries": 3})
def orders_daily():
    @task
    def extract(ds=None) -> str:
        return load_partition_to_staging("orders", ds)   # returns staging table name

    @task
    def merge(staging_table: str) -> None:
        run_merge_sql(staging_table)                      # idempotent MERGE as above

    @task
    def check(ds=None) -> None:
        assert_row_count_and_freshness("analytics.orders", ds)

    check_task = check()
    merge(extract()) >> check_task

orders_daily()
```

Prefect: use `@flow`/`@task` with `retries`, `retry_delay_seconds`, and cache keys only for tasks that are truly pure.

## 5. Transformation (dbt)

- Layers: `staging` (rename, cast, dedupe, one model per source table) -> `intermediate` -> `marts` (facts/dimensions for consumers).
- Large tables: `materialized='incremental'` with `unique_key` and an `is_incremental()` filter that includes a lookback window for late data; choose `incremental_strategy` (`merge`, `delete+insert`, `insert_overwrite`) supported by your adapter.
- Tests on every model key: `unique`, `not_null`, `relationships`, `accepted_values`; source `freshness` with `loaded_at_field`.
- Run `dbt build` (models + tests in DAG order) in CI on a sample or deferred state.

## 6. Data-Quality Gates

| Check | Example | Action on failure |
|-------|---------|-------------------|
| Volume | Row count within ±X% of trailing average | Block publish, alert |
| Freshness | Max event time within SLA | Alert |
| Schema | Expected columns/types present | Fail run |
| Validity | Not-null keys, accepted values, ranges | Quarantine rows or fail above threshold |
| Uniqueness | Business key unique after merge | Fail run |
| Reconciliation | Source vs target counts/sums per partition | Alert, investigate |

Use dbt tests, Great Expectations / Soda, or SQL assertions; the tool matters less than running them **before** consumers read the data (write-audit-publish: write to a staging table/branch, check, then swap or publish).

## 7. Table Maintenance and Cost

- **File sizes:** target roughly 128 MB-1 GB Parquet files; compact small files regularly (Delta `OPTIMIZE`, Iceberg `rewrite_data_files`).
- **Partitioning:** partition by a low-cardinality column used in filters (usually date); avoid tiny partitions; consider clustering (Z-order, liquid clustering, Iceberg sort order) for high-cardinality filters.
- **Retention:** expire old snapshots/versions (Delta `VACUUM`, Iceberg `expire_snapshots`) consistent with time-travel and recovery needs.
- **Compute:** spot/preemptible for retryable batch; right-size clusters from observed metrics; turn off idle warehouses.
- **Storage tiers:** lifecycle raw/landing data to cheaper storage after the reprocessing window.

## 8. Monitoring

Emit per run: records read/written/rejected, duration, bytes, watermark, data-quality results. Alert on failures, freshness SLA breach, volume anomalies and reject-rate spikes. Keep lineage (OpenLineage, dbt docs, or catalog) so consumers can trace a column to its source.

## Done When

- A rerun or backfill of any interval produces identical results (verified once)
- Late and duplicate records are handled by design, not by luck
- Quality gates run before publish and failures block or quarantine
- Freshness and failure alerts route to an owner
- Runbook covers rerun, backfill and recovery
