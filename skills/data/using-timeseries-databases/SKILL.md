---
name: using-timeseries-databases
description: Time-series database implementation for metrics, IoT, financial data, and observability backends. Use when building dashboards, monitoring systems, IoT platforms, or financial applications. Covers TimescaleDB (PostgreSQL), InfluxDB, ClickHouse, QuestDB, continuous aggregates, downsampling (LTTB), and retention policies.
---

# Time-Series Databases

## Database Selection

Pick by primary use case:

**TimescaleDB** - PostgreSQL extension
- Use when: already on PostgreSQL, need SQL + JOINs, hybrid workloads
- Query: Standard SQL
- Scale: 100K-1M inserts/sec

**InfluxDB** - Purpose-built TSDB
- Use when: DevOps metrics, Prometheus integration, Telegraf ecosystem
- Query: InfluxQL or Flux
- Scale: 500K-1M points/sec

**ClickHouse** - Columnar analytics
- Use when: fastest aggregations, analytics dashboards, log analysis
- Query: SQL
- Scale: 1M-10M inserts/sec, 100M-1B rows/sec queries

**QuestDB** - High-throughput IoT
- Use when: highest write performance, financial tick data
- Query: SQL + Line Protocol
- Scale: 4M+ inserts/sec

## Core Patterns

### 1. Hypertables (TimescaleDB)

Automatic time-based partitioning:

```sql
CREATE TABLE sensor_data (
  time        TIMESTAMPTZ NOT NULL,
  sensor_id   INTEGER NOT NULL,
  temperature DOUBLE PRECISION,
  humidity    DOUBLE PRECISION
);

SELECT create_hypertable('sensor_data', 'time');
```

Benefits:
- Cheap data expiration (drop old chunks)
- Parallel queries
- Compression on older chunks (10-20x savings)

### 2. Continuous Aggregates

Pre-computed rollups for fast dashboard queries:

```sql
-- TimescaleDB: hourly rollup
CREATE MATERIALIZED VIEW sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS hour,
       sensor_id,
       AVG(temperature) AS avg_temp,
       MAX(temperature) AS max_temp,
       MIN(temperature) AS min_temp
FROM sensor_data
GROUP BY hour, sensor_id;

-- Auto-refresh policy
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
  start_offset => INTERVAL '3 hours',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour');
```

Query strategy:
- Short range (last hour): raw data
- Medium (last day): 1-minute rollups
- Long (last month): 1-hour rollups
- Very long (last year): daily rollups

### 3. Retention Policies

Automatic data expiration:

```sql
-- TimescaleDB: delete data older than 90 days
SELECT add_retention_policy('sensor_data', INTERVAL '90 days');
```

Retention policies, `drop_chunks`, `DROP PARTITION` and TTL `DELETE` erase data permanently. Confirm with user before applying to a database holding real data.

Typical retention:
- Raw data: 7-90 days
- Hourly rollups: 1-2 years
- Daily rollups: forever

### 4. Downsampling for Visualization

Use LTTB (Largest-Triangle-Three-Buckets) to cut chart point count.

```sql
-- TimescaleDB toolkit LTTB
-- lttb(time, value, resolution) is an aggregate returning a timevector;
-- unnest() turns it back into (time, value) rows
SELECT time, value
FROM unnest((
  SELECT lttb(time, temperature, 1000)  -- 1000 = target number of points
  FROM sensor_data
  WHERE sensor_id = 1
));
```

Thresholds:
- < 1,000 points: no downsampling
- 1,000-10,000 points: LTTB to 1,000 points
- 10,000+ points: LTTB to 500 points or use pre-aggregated data

## Dashboard Integration

Query patterns by component:

| Component | Query Pattern | Example |
|-----------|---------------|---------|
| KPI Card | Latest value | `SELECT temperature FROM sensors ORDER BY time DESC LIMIT 1` |
| Trend Chart | Time-bucketed avg | `SELECT time_bucket('5m', time), AVG(cpu) GROUP BY 1` |
| Heatmap | Multi-metric window | `SELECT hour, AVG(cpu), AVG(memory) GROUP BY hour` |
| Alert | Threshold check | `SELECT COUNT(*) WHERE cpu > 80 AND time > NOW() - '5m'` |

Data flow:
1. Ingest metrics (Prometheus, MQTT, application events)
2. Store in time-series DB with continuous aggregates
3. Apply retention policies (raw: 30d, rollups: 1y)
4. Query layer downsamples to optimal point count (LTTB)
5. Frontend renders with Recharts/visx

Auto-refresh intervals:
- Critical alerts: 1-5 seconds (WebSocket)
- Operations dashboard: 10-30 seconds (polling)
- Analytics dashboard: 1-5 minutes (cached)
- Historical reports: on-demand only

## Security

- Never build SQL from request input: allowlist identifiers (metric, table, column), map ranges through a fixed dict, bind values as parameters.
- Passwords and tokens from env or secret store (`PGPASSWORD`, `INFLUX_TOKEN`), never literals or CLI args.
- Docker examples are local dev: ports bound to 127.0.0.1, default users. Pin image tags (or digests) to a reviewed version, never `:latest`. Anything reachable: strong passwords, auth, TLS.
- Servers send telemetry by default; turn it off: TimescaleDB `timescaledb.telemetry_level=off`, QuestDB `telemetry.enabled=false` (`QDB_TELEMETRY_ENABLED=false`), InfluxDB 2 `INFLUXD_REPORTING_DISABLED=true`, InfluxDB 3 `--disable-telemetry-upload`, newer ClickHouse `<send_crash_reports><enabled>false</enabled></send_crash_reports>`.

## Database-Specific Details

Implementation guides:
- `references/timescaledb.md` - Setup, tuning, compression
- `references/influxdb.md` - InfluxQL/Flux, retention policies
- `references/clickhouse.md` - MergeTree engines, clustering
- `references/questdb.md` - Line Protocol, SIMD optimization

Downsampling implementation:
- `references/downsampling-strategies.md` - LTTB algorithm, aggregation methods

Examples:
- `examples/metrics-dashboard-backend/` - TimescaleDB + FastAPI
- `examples/iot-data-pipeline/` - InfluxDB + Go for IoT

Scripts:
- `scripts/setup_hypertable.py` - Create TimescaleDB hypertables (password via `PGPASSWORD` or `~/.pgpass`)
- `scripts/generate_retention_policy.py` - Generate retention policies

## Performance Optimization

### Write Optimization

Batch inserts:

| Database | Batch Size | Expected Throughput |
|----------|------------|---------------------|
| TimescaleDB | 1,000-10,000 | 100K-1M rows/sec |
| InfluxDB | 5,000+ | 500K-1M points/sec |
| ClickHouse | 10,000-100,000 | 1M-10M rows/sec |
| QuestDB | 10,000+ | 4M+ rows/sec |

### Query Optimization

Rule 1: Always filter by time first (indexed)

```sql
-- BAD: Full table scan
SELECT * FROM metrics WHERE metric_name = 'cpu';

-- GOOD: Time index used
SELECT * FROM metrics
WHERE time > NOW() - INTERVAL '1 hour'
  AND metric_name = 'cpu';
```

Rule 2: Use continuous aggregates for dashboard queries

```sql
-- BAD: Aggregate 1B rows every dashboard load
SELECT time_bucket('1 hour', time), AVG(cpu)
FROM metrics
WHERE time > NOW() - INTERVAL '30 days'
GROUP BY 1;

-- GOOD: Query pre-computed rollup
SELECT hour, avg_cpu
FROM metrics_hourly
WHERE hour > NOW() - INTERVAL '30 days';
```

Rule 3: Downsample for visualization

```typescript
// Request optimal point count
const points = Math.min(1000, chartWidth);
const query = `/api/metrics?start=${start}&end=${end}&points=${points}`;
```

## Use Cases

**DevOps Monitoring** → InfluxDB or TimescaleDB
- Prometheus metrics, application traces, infrastructure

**IoT Sensor Data** → QuestDB or TimescaleDB
- Millions of devices, high write throughput

**Financial Tick Data** → QuestDB or ClickHouse
- Sub-millisecond queries, OHLC aggregates

**User Analytics** → ClickHouse
- Event tracking, daily active users, funnel analysis

**Real-time Dashboards** → Any TSDB + Continuous Aggregates
- Pre-computed rollups, WebSocket streaming, LTTB downsampling
