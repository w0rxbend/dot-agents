# Open Table Formats Comparison

## Feature Matrix

| Feature | Apache Iceberg | Delta Lake | Apache Hudi |
|---------|---------------|------------|-------------|
| **ACID Transactions** | Yes (serializable) | Yes | Yes |
| **Time Travel** | Yes (snapshot ID) | Yes (version number) | Yes (commit time) |
| **Schema Evolution** | Excellent | Good | Good |
| **Partition Evolution** | Yes (no rewrite) | No | Limited |
| **Hidden Partitioning** | Yes | No | No |
| **Multi-Engine Support** | Spark, Trino, Flink, Presto, Dremio | Spark (primary), Trino (limited) | Spark, Flink |
| **Governance** | Apache Foundation | Databricks/Linux Foundation | Apache Foundation |
| **CDC Support** | Good | Excellent | Excellent |
| **Streaming** | Good | Excellent | Excellent |

## Decision Matrix

**Use Apache Iceberg when:**
- Multi-engine flexibility needed (Spark, Trino, Flink)
- Vendor neutrality wanted (Apache Foundation)
- Partition evolution required
- Future-proof architecture (broadest adoption)

**Use Delta Lake when:**
- Committed to Databricks ecosystem
- Mostly Spark-based workflows
- Excellent streaming + CDC support needed
- Unity Catalog integration wanted

**Use Apache Hudi when:**
- CDC and upserts are main workload
- Streaming ingestion dominant
- Record-level updates needed (Merge-on-Read)
- Cost-optimized incremental processing

## Recommendation

**Default:** Apache Iceberg (vendor-neutral, multi-engine, best long-term)
