#!/usr/bin/env python3
"""
TimescaleDB Hypertable Setup Script

Creates a hypertable with best practices:
- Automatic partitioning by time
- Compression on old chunks
- Continuous aggregates (1min, 1hour, 1day)
- Retention policies
- Appropriate indexes

Usage:
    python setup_hypertable.py --table metrics --time-column time --partition-interval 7d

Password comes from PGPASSWORD or ~/.pgpass (never a CLI arg).
"""

import psycopg2
import argparse
import re
from typing import List, Optional


# Values below are spliced into DDL; restrict them so CLI input cannot inject SQL.
def _ident(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise argparse.ArgumentTypeError(f"invalid identifier: {value!r}")
    return value


def _ident_list(value: str) -> str:
    return ",".join(_ident(v.strip()) for v in value.split(","))


def _interval(value: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z ]+", value):
        raise argparse.ArgumentTypeError(f"invalid interval: {value!r}")
    return value


def create_hypertable(
    conn,
    table_name: str,
    time_column: str = "time",
    partition_interval: str = "7 days",
    compress_after: str = "7 days",
    retention: Optional[str] = None,
    segment_by: Optional[List[str]] = None,
    create_rollups: bool = True,
):
    """
    Create and configure a TimescaleDB hypertable.

    Args:
        conn: psycopg2 connection
        table_name: Name of table to convert to hypertable
        time_column: Name of time column
        partition_interval: Chunk interval (e.g., "1 day", "7 days")
        compress_after: Compress chunks older than this (e.g., "7 days")
        retention: Delete data older than this (e.g., "90 days", None = keep forever)
        segment_by: Columns to segment by for compression (e.g., ["device_id", "metric_name"])
        create_rollups: Whether to create continuous aggregates
    """
    cur = conn.cursor()

    # 1. Convert to hypertable
    print(f"Creating hypertable '{table_name}' with time column '{time_column}'...")
    cur.execute(f"""
        SELECT create_hypertable(
            '{table_name}',
            '{time_column}',
            chunk_time_interval => INTERVAL '{partition_interval}',
            if_not_exists => TRUE
        );
    """)
    print("  ✓ Hypertable created")

    # 2. Enable compression
    print(f"Enabling compression (segment_by: {segment_by or 'none'})...")
    compress_config = f"timescaledb.compress"
    if segment_by:
        compress_config += f", timescaledb.compress_segmentby = '{', '.join(segment_by)}'"

    cur.execute(f"""
        ALTER TABLE {table_name} SET (
            {compress_config}
        );
    """)
    print("  ✓ Compression enabled")

    # 3. Add compression policy
    print(f"Adding compression policy (compress after {compress_after})...")
    cur.execute(f"""
        SELECT add_compression_policy('{table_name}', INTERVAL '{compress_after}');
    """)
    print("  ✓ Compression policy added")

    # 4. Add retention policy (if specified)
    if retention:
        print(f"Adding retention policy (delete after {retention})...")
        cur.execute(f"""
            SELECT add_retention_policy('{table_name}', INTERVAL '{retention}');
        """)
        print("  ✓ Retention policy added")
    else:
        print("  ⊗ No retention policy (data kept forever)")

    # 5. Create continuous aggregates (if requested)
    if create_rollups:
        print("Creating continuous aggregates...")

        # Detect numeric columns for aggregation
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
              AND data_type IN ('double precision', 'real', 'integer', 'bigint', 'numeric')
              AND column_name != '{time_column}'
            LIMIT 1;
        """)
        result = cur.fetchone()

        if result:
            value_column = result[0]
            segment_cols = ", ".join(segment_by) if segment_by else ""
            group_clause = f", {segment_cols}" if segment_by else ""

            # 1-minute rollup
            print(f"  Creating 1-minute rollup...")
            cur.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {table_name}_1min
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 minute', {time_column}) AS bucket
                       {f', {segment_cols}' if segment_cols else ''}
                       , AVG({value_column}) AS avg_value
                       , MAX({value_column}) AS max_value
                       , MIN({value_column}) AS min_value
                       , COUNT(*) AS sample_count
                FROM {table_name}
                GROUP BY bucket{group_clause};
            """)

            cur.execute(f"""
                SELECT add_continuous_aggregate_policy('{table_name}_1min',
                    start_offset => INTERVAL '3 hours',
                    end_offset => INTERVAL '1 minute',
                    schedule_interval => INTERVAL '1 minute');
            """)
            print("    ✓ 1-minute rollup created")

            # 1-hour rollup
            print(f"  Creating 1-hour rollup...")
            cur.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {table_name}_1hour
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 hour', {time_column}) AS bucket
                       {f', {segment_cols}' if segment_cols else ''}
                       , AVG({value_column}) AS avg_value
                       , MAX({value_column}) AS max_value
                       , MIN({value_column}) AS min_value
                       , STDDEV({value_column}) AS stddev_value
                FROM {table_name}
                GROUP BY bucket{group_clause};
            """)

            cur.execute(f"""
                SELECT add_continuous_aggregate_policy('{table_name}_1hour',
                    start_offset => INTERVAL '7 days',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour');
            """)
            print("    ✓ 1-hour rollup created")

            # Daily rollup
            print(f"  Creating daily rollup...")
            cur.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {table_name}_daily
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 day', {time_column}) AS bucket
                       {f', {segment_cols}' if segment_cols else ''}
                       , AVG({value_column}) AS avg_value
                       , MAX({value_column}) AS max_value
                       , MIN({value_column}) AS min_value
                       , STDDEV({value_column}) AS stddev_value
                FROM {table_name}
                GROUP BY bucket{group_clause};
            """)

            cur.execute(f"""
                SELECT add_continuous_aggregate_policy('{table_name}_daily',
                    start_offset => INTERVAL '90 days',
                    end_offset => INTERVAL '1 day',
                    schedule_interval => INTERVAL '1 day');
            """)
            print("    ✓ Daily rollup created")

            # Add retention policies for rollups
            if retention:
                rollup_retention_days = int(retention.split()[0]) * 3  # Keep rollups 3x longer
                cur.execute(f"""
                    SELECT add_retention_policy('{table_name}_1min', INTERVAL '{rollup_retention_days} days');
                """)
                print(f"    ✓ 1-minute rollup retention: {rollup_retention_days} days")
        else:
            print("  ⊗ No numeric columns found, skipping rollups")

    conn.commit()
    cur.close()

    print(f"\n✅ Hypertable '{table_name}' configured successfully!")


def print_summary(conn, table_name: str):
    """Print configuration summary."""
    cur = conn.cursor()

    print(f"\n📊 Summary for '{table_name}':")
    print("=" * 60)

    # Chunk info
    cur.execute(f"""
        SELECT COUNT(*) FROM timescaledb_information.chunks
        WHERE hypertable_name = '{table_name}';
    """)
    chunk_count = cur.fetchone()[0]
    print(f"  Chunks: {chunk_count}")

    # Compression info
    cur.execute(f"""
        SELECT
            pg_size_pretty(before_compression_total_bytes) AS before,
            pg_size_pretty(after_compression_total_bytes) AS after,
            ROUND(before_compression_total_bytes::numeric / NULLIF(after_compression_total_bytes, 0), 2) AS ratio
        FROM timescaledb_information.compression_settings
        WHERE hypertable_name = '{table_name}';
    """)
    result = cur.fetchone()
    if result:
        print(f"  Compression: {result[0]} → {result[1]} (ratio: {result[2]}x)")

    # Policies
    cur.execute(f"""
        SELECT
            proc_name,
            config
        FROM timescaledb_information.jobs j
        JOIN timescaledb_information.hypertables h ON h.hypertable_name = '{table_name}'
        WHERE j.hypertable_name = '{table_name}';
    """)
    print(f"  Policies:")
    for row in cur.fetchall():
        print(f"    - {row[0]}")

    # Continuous aggregates
    cur.execute(f"""
        SELECT view_name
        FROM timescaledb_information.continuous_aggregates
        WHERE hypertable_name = '{table_name}';
    """)
    print(f"  Continuous Aggregates:")
    for row in cur.fetchall():
        print(f"    - {row[0]}")

    cur.close()


def main():
    parser = argparse.ArgumentParser(
        description="Setup TimescaleDB hypertable with best practices"
    )
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--database", default="postgres", help="Database name")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--table", required=True, type=_ident, help="Table name to convert")
    parser.add_argument("--time-column", default="time", type=_ident, help="Time column name")
    parser.add_argument(
        "--partition-interval",
        default="7 days",
        type=_interval,
        help="Chunk interval (e.g., '1 day', '7 days')",
    )
    parser.add_argument(
        "--compress-after",
        default="7 days",
        type=_interval,
        help="Compress chunks after (e.g., '7 days')",
    )
    parser.add_argument(
        "--retention", type=_interval, help="Delete data after (e.g., '90 days', omit to keep forever)"
    )
    parser.add_argument(
        "--segment-by",
        type=_ident_list,
        help="Columns to segment by for compression (comma-separated)",
    )
    parser.add_argument(
        "--no-rollups", action="store_true", help="Skip creating continuous aggregates"
    )

    args = parser.parse_args()

    # Connect to database
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
    )

    segment_by = args.segment_by.split(",") if args.segment_by else None

    # Setup hypertable
    create_hypertable(
        conn,
        table_name=args.table,
        time_column=args.time_column,
        partition_interval=args.partition_interval,
        compress_after=args.compress_after,
        retention=args.retention,
        segment_by=segment_by,
        create_rollups=not args.no_rollups,
    )

    # Print summary
    print_summary(conn, args.table)

    conn.close()


if __name__ == "__main__":
    main()
