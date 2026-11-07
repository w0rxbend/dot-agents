---
name: architecting-data
description: "Choose a data platform architecture: lake vs warehouse vs lakehouse, medallion layers, modeling approach (dimensional, normalized, data vault, wide tables), table formats (Iceberg, Delta), centralized vs data mesh, and governance. Use for platform-level analytics architecture decisions; use data-engineering-data-pipeline to build pipelines and database-design for operational databases."
---

# Data Architecture

## When to Use This Skill

Use when:
- Designing new data platform or modernizing legacy systems
- Choosing data lake, data warehouse or data lakehouse
- Choosing data modeling approach (dimensional, normalized, data vault, wide tables)
- Evaluating centralized vs data mesh architecture
- Selecting open table formats (Apache Iceberg, Delta Lake, Apache Hudi)
- Designing medallion architecture (bronze, silver, gold layers)
- Implementing data governance and cataloging

## Core Concepts

### 1. Storage Paradigms

Three patterns for analytical storage:

**Data Lake:** Central repository for raw data at scale
- Schema-on-read, cost-optimized ($0.02-0.03/GB/month)
- Use when: diverse sources, exploratory analytics, ML/AI training data

**Data Warehouse:** Structured repository optimized for BI
- Schema-on-write, ACID transactions, fast queries
- Use when: known BI requirements, strong governance needed

**Data Lakehouse:** Hybrid of lake flexibility and warehouse reliability
- Open table formats (Iceberg, Delta Lake), ACID on object storage
- Use when: mixed BI + ML workloads, cost optimization (60-80% cheaper than warehouse)

**Step 1: Identify Primary Use Case**
- BI/Reporting only + Known queries → Data Warehouse
- ML/AI primary + Raw data needed → Data Lake or Lakehouse
- Mixed BI + ML + Cost optimization → Data Lakehouse (recommended)
- Exploratory/Unknown use cases → Data Lake

**Step 2: Evaluate Budget**
- High budget, known queries → Data Warehouse
- Cost-sensitive, flexible → Data Lakehouse

**By Org Size:**
- Startup (<50): Data Warehouse (simplicity)
- Growth (50-500): Data Lakehouse (balance)
- Enterprise (>500): Hybrid or unified Lakehouse

Comparison: [references/storage-paradigms.md](references/storage-paradigms.md). All 4 decision frameworks in detail: [references/decision-frameworks.md](references/decision-frameworks.md).

### 2. Data Modeling Approaches

Four modeling patterns:

**Dimensional (Kimball):** Star/snowflake schemas for BI
- Use when: known query patterns, BI dashboards, trend analysis

**Normalized (3NF):** Removes redundancy for transactional systems
- Use when: OLTP systems, frequent updates, strong consistency

**Data Vault 2.0:** Flexible model, complete audit trail
- Use when: compliance requirements, multiple sources, agile warehousing

**Wide Tables:** Denormalized, optimized for columnar storage
- Use when: ML feature stores, data science notebooks, high-performance dashboards

**Decision Framework:**
- Analytical (BI) + Known queries → Dimensional (Star Schema)
- Transactional (OLTP) → Normalized (3NF)
- Compliance/Audit → Data Vault 2.0
- Data Science/ML → Wide Tables

Patterns: [references/modeling-approaches.md](references/modeling-approaches.md).

### 3. Data Mesh Principles

Decentralized architecture for large organizations (>500 people).

**Four Core Principles:**
1. Domain-oriented decentralization
2. Data as product (SLAs, quality, documentation)
3. Self-serve data infrastructure
4. Federated computational governance

**Readiness Assessment (Score 1-5 each):**
1. Domain clarity
2. Team maturity
3. Platform capability
4. Governance maturity
5. Scale need
6. Organizational buy-in

**Scoring:** 24-30: Strong candidate | 18-23: Hybrid | 12-17: Build foundation first | 6-11: Centralized

**Red Flags:** Small org (<100 people), unclear domains, no platform team, weak governance

Full guide: [references/data-mesh-guide.md](references/data-mesh-guide.md).

### 4. Medallion Architecture

Standard lakehouse pattern: Bronze (raw) → Silver (cleaned) → Gold (business-level)

**Bronze Layer:** Exact source copy, immutable, append-only

**Silver Layer:** Validated, deduplicated, typed data

**Gold Layer:** Business logic, aggregates, dimensional models, ML features

**Data Quality by Layer:**
- Bronze → Silver: Schema validation, type checks, deduplication
- Silver → Gold: Business rule validation, referential integrity
- Gold: Anomaly detection, statistical checks

Patterns: [references/medallion-pattern.md](references/medallion-pattern.md).

### 5. Open Table Formats

Add ACID transactions to data lakes:

**Apache Iceberg:** Multi-engine, vendor-neutral (Context7: 79.7 score)
- Use when: avoiding vendor lock-in, multi-engine flexibility

**Delta Lake:** Databricks ecosystem, Spark-optimized
- Use when: committed to Databricks

**Apache Hudi:** Optimized for CDC and frequent upserts
- Use when: CDC-heavy workloads

**Recommendation:** Apache Iceberg for new projects (vendor-neutral, broadest support)

Comparison: [references/table-formats.md](references/table-formats.md).

### 6. Modern Data Stack

**Standard Layers:**
- Ingestion: Fivetran, Airbyte, Kafka
- Storage: Snowflake, Databricks, BigQuery
- Transformation: dbt (Context7: 87.0 score), Spark
- Orchestration: Airflow, Dagster, Prefect
- Visualization: Tableau, Looker, Power BI
- Governance: DataHub, Alation, Great Expectations

**Tool Selection:**
- Fivetran vs Airbyte: Pre-built connectors vs cost-sensitive
- Snowflake vs Databricks: BI-focused vs ML-focused
- dbt vs Spark: SQL-based vs large-scale processing

Details: [references/tool-recommendations.md](references/tool-recommendations.md), [references/modern-data-stack.md](references/modern-data-stack.md).

### 7. Data Governance

**Data Catalog:** Searchable inventory (DataHub, Alation, Collibra)

**Data Lineage:** Track data flow (OpenLineage, Marquez)

**Data Quality:** Validation and testing (Great Expectations, Soda, dbt tests)

**Access Control:**
- RBAC: Role-based (sales_analyst role)
- ABAC: Attribute-based (row-level security)
- Column-level: Dynamic data masking for PII

Patterns: [references/governance-patterns.md](references/governance-patterns.md).

## Common Scenarios

- **Startup** (50 people; PostgreSQL + MongoDB + Stripe): simple data warehouse. BigQuery or Snowflake, Airbyte or Fivetran, dbt, orchestration in dbt Cloud.
- **Enterprise modernization** (legacy Oracle warehouse, cloud migration): Data Lakehouse (Databricks or Snowflake with Iceberg), incremental migration with CDC, medallion (bronze, silver, gold). Cost savings: 60-80%.
- **Data mesh assessment** (200 people, 5-person central data team): NOT YET, build foundation first. Org too small (<500 recommended), central team not yet bottleneck; invest in self-serve platform and governance.

Details: [references/scenarios.md](references/scenarios.md).

## Tool Recommendations

**Research-validated (Context7, December 2025):**
- **dbt:** Score 87.0, 3,532+ code snippets. SQL-based transformations, version control, testing; industry standard for transformation.
- **Apache Iceberg:** Score 79.7, 832+ code snippets. Open table format, multi-engine, vendor-neutral; production-ready (Netflix, Apple, Adobe).

**Tool Stack by Use Case:**

**Startup:** BigQuery + Airbyte + dbt + Metabase (<$1K/month)

**Growth:** Snowflake + Fivetran + dbt + Airflow + Tableau ($10K-50K/month)

**Enterprise:** Snowflake + Databricks + Fivetran + Kafka + dbt + Airflow + Alation ($50K-500K/month)

See [references/tool-recommendations.md](references/tool-recommendations.md).

## Implementation Patterns

### Pattern 1: Medallion Architecture

```sql
-- Bronze: Raw ingestion
CREATE TABLE bronze.raw_customers (_ingested_at TIMESTAMP, _raw_data STRING);

-- Silver: Cleaned
CREATE TABLE silver.customers AS
SELECT json_extract(_raw_data, '$.id') AS customer_id, ...
FROM bronze.raw_customers
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY _ingested_at DESC) = 1;

-- Gold: Business-level
CREATE TABLE gold.fact_sales AS
SELECT s.order_id, d.date_key, c.customer_key, ...
FROM silver.sales s
JOIN gold.dim_date d ON s.order_date = d.date;
```

### Pattern 2: Apache Iceberg Table

```sql
CREATE TABLE catalog.db.sales (order_id BIGINT, amount DECIMAL(10,2))
USING iceberg
PARTITIONED BY (days(order_date));

-- Time travel
SELECT * FROM catalog.db.sales TIMESTAMP AS OF '2025-01-01';
```

### Pattern 3: dbt Transformation

```sql
-- models/staging/stg_customers.sql
WITH source AS (SELECT * FROM {{ source('raw', 'customers') }}),
cleaned AS (
  SELECT customer_id, UPPER(customer_name) AS customer_name
  FROM source WHERE customer_id IS NOT NULL
)
SELECT * FROM cleaned
```

Full examples: [examples/](examples/).

## Best Practices

1. **Start simple:** Avoid over-engineering; begin with warehouse or basic lakehouse
2. **Invest in governance early:** Catalog, lineage, quality from day one
3. **Assess mesh readiness:** Don't decentralize prematurely (<500 people)
4. **Automate quality:** Run tests (Great Expectations, dbt) in CI/CD
5. **Monitor pipelines:** Observability critical (freshness, quality, health)
6. **Document as code:** dbt docs, DataHub, YAML for self-service
7. **Incremental loading:** Only load new/changed data (watermark columns)

## Anti-Patterns

- ❌ Data swamp: Lake without governance or cataloging
- ❌ Tool sprawl: Too many tools without integration
- ❌ Centralized bottleneck: Single team in large org (>500 people)
- ❌ Vendor lock-in: Proprietary formats without migration path
- ❌ No lineage: Can't answer "where did this come from?"

## Integration with Other Skills

**Direct dependencies:**
- **ingesting-data:** ETL/ELT mechanics, Fivetran, Airbyte, dlt implementation
- **data-engineering-data-pipeline:** Orchestration (Airflow/Prefect), dbt transformations, data-quality gates, table maintenance
- **using-message-queues:** Kafka and other brokers for real-time pipelines

**Complementary:**
- **using-relational-databases:** PostgreSQL, MySQL as source systems
- **using-document-databases:** MongoDB, DynamoDB as sources
- **database-design:** Operational (OLTP) schema and HA/DR decisions
- **observability-and-instrumentation:** Pipeline health and data-quality monitoring

**Downstream:**
- **visualizing-data:** BI and dashboard patterns

**Common Workflows:**

**End-to-End Analytics:**
```
architecting-data (warehouse) -> ingesting-data (Fivetran/Airbyte) ->
data-engineering-data-pipeline (dbt, quality gates) -> visualizing-data
```

**Data Platform for AI/ML:**
```
architecting-data (lakehouse) -> ingesting-data (CDC/Kafka) ->
data-engineering-data-pipeline (dbt features, Iceberg/Delta maintenance)
```

## Further Reading

**Reference Files:**
- [decision-frameworks.md](references/decision-frameworks.md) - All 4 decision frameworks, detailed
- [storage-paradigms.md](references/storage-paradigms.md) - Lake vs warehouse vs lakehouse
- [modeling-approaches.md](references/modeling-approaches.md) - Dimensional, normalized, data vault, wide
- [data-mesh-guide.md](references/data-mesh-guide.md) - Data mesh principles and implementation
- [medallion-pattern.md](references/medallion-pattern.md) - Bronze, silver, gold layers
- [table-formats.md](references/table-formats.md) - Iceberg, Delta Lake, Hudi comparison
- [tool-recommendations.md](references/tool-recommendations.md) - Tool analysis and recommendations
- [modern-data-stack.md](references/modern-data-stack.md) - Tool categories and selection
- [governance-patterns.md](references/governance-patterns.md) - Catalog, lineage, quality, access control
- [scenarios.md](references/scenarios.md) - Startup, enterprise, data mesh scenarios

**Examples:**
- [examples/dbt-project/](examples/dbt-project/) - dbt project with medallion architecture

**External Resources:**
- Apache Iceberg: https://iceberg.apache.org/
- dbt Documentation: https://docs.getdbt.com/
- Data Mesh (Zhamak Dehghani): https://www.datamesh-architecture.com/
- Databricks Medallion: https://www.databricks.com/glossary/medallion-architecture
