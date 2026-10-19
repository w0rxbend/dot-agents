---
name: aws-rds
description: "Operate Amazon RDS - provisioning, Multi-AZ, read replicas, parameter groups, backups, snapshots and point-in-time recovery, IAM auth, Performance Insights and connection troubleshooting. Use for hands-on RDS changes; use deploying-on-aws to choose a database service."
category: devops
risk: critical
source: https://github.com/BagelHole/DevOps-Security-Agent-Skills
source_repo: BagelHole/DevOps-Security-Agent-Skills
source_type: community
date_added: '2026-09-20'
license: MIT
license_source: https://github.com/BagelHole/DevOps-Security-Agent-Skills/blob/main/LICENSE
compatibility: Requires AWS CLI v2 with credentials for the target account; mutating commands need the corresponding IAM permissions.
metadata:
  author: devops-skills
  version: '1.0'
---

# AWS RDS

Deploy and manage Amazon RDS relational databases with production-grade backups, replication, monitoring, and security.

## When to Use This Skill

- Provisioning a managed PostgreSQL, MySQL, MariaDB, Oracle, or SQL Server database
- Setting up Multi-AZ deployments for high availability
- Creating read replicas for horizontal read scaling
- Configuring automated backups, snapshots, and point-in-time recovery
- Tuning database parameters for performance
- Migrating from self-managed databases to RDS
- Monitoring database performance and setting up alarms

## Prerequisites

- AWS CLI v2 installed and configured
- IAM permissions: `rds:*`, `ec2:DescribeSecurityGroups`, `ec2:DescribeSubnets`, `kms:*`, `cloudwatch:*`
- A VPC with at least two subnets in different AZs (for subnet group)
- Security group allowing database port access from application subnets only

## Create a DB Subnet Group

```bash
# Create a subnet group spanning two AZs
aws rds create-db-subnet-group \
  --db-subnet-group-name production-db-subnets \
  --db-subnet-group-description "Production database subnets" \
  --subnet-ids subnet-private-a subnet-private-b

# List subnet groups
aws rds describe-db-subnet-groups \
  --query "DBSubnetGroups[].{Name:DBSubnetGroupName,VPC:VpcId,Status:SubnetGroupStatus}" \
  --output table
```

## Create a Production Database

```bash
# Create a PostgreSQL 16 Multi-AZ instance
aws rds create-db-instance \
  --db-instance-identifier production-api-db \
  --db-instance-class db.r6g.large \
  --engine postgres \
  --engine-version 16.4 \
  --master-username appadmin \
  --manage-master-user-password \
  --allocated-storage 100 \
  --max-allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --kms-key-id alias/rds-key \
  --vpc-security-group-ids sg-db-access \
  --db-subnet-group-name production-db-subnets \
  --db-name appdb \
  --backup-retention-period 14 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:05:00-sun:06:00" \
  --multi-az \
  --auto-minor-version-upgrade \
  --deletion-protection \
  --copy-tags-to-snapshot \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --enable-cloudwatch-logs-exports '["postgresql","upgrade"]' \
  --tags '[
    {"Key":"Environment","Value":"production"},
    {"Key":"Team","Value":"backend"},
    {"Key":"Backup","Value":"daily"}
  ]'

# Wait for instance to become available
aws rds wait db-instance-available --db-instance-identifier production-api-db

# Get connection endpoint
aws rds describe-db-instances \
  --db-instance-identifier production-api-db \
  --query "DBInstances[0].Endpoint.{Address:Address,Port:Port}" \
  --output table
```

## Retrieve Master Password from Secrets Manager

```bash
# When using --manage-master-user-password, RDS stores the password in Secrets Manager
aws rds describe-db-instances \
  --db-instance-identifier production-api-db \
  --query "DBInstances[0].MasterUserSecret.SecretArn" \
  --output text

# Retrieve the secret value
aws secretsmanager get-secret-value \
  --secret-id arn:aws:secretsmanager:us-east-1:123456789012:secret:rds-db-secret-abc123 \
  --query SecretString --output text
```

## IAM Database Authentication

Supported for MySQL, MariaDB and PostgreSQL engines. Tokens are valid for 15 minutes and
the connection must use TLS.

```bash
# Enable on an existing instance
aws rds modify-db-instance \
  --db-instance-identifier production-api-db \
  --enable-iam-database-authentication \
  --apply-immediately

# PostgreSQL: create the DB user and grant the rds_iam role (run in psql as admin)
#   CREATE USER app_user; GRANT rds_iam TO app_user;
# MySQL: CREATE USER app_user IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';

# Generate a short-lived token and connect
TOKEN=$(aws rds generate-db-auth-token \
  --hostname production-api-db.xxxx.us-east-1.rds.amazonaws.com \
  --port 5432 --username app_user --region us-east-1)
PGPASSWORD="$TOKEN" psql "host=production-api-db.xxxx.us-east-1.rds.amazonaws.com \
  port=5432 user=app_user dbname=app sslmode=verify-full sslrootcert=global-bundle.pem"
```

The caller needs `rds-db:connect` on
`arn:aws:rds-db:<region>:<account>:dbuser:<DbiResourceId>/app_user` (see `aws-iam`).

## Parameter Groups

```bash
# Create a custom parameter group
aws rds create-db-parameter-group \
  --db-parameter-group-name production-pg16 \
  --db-parameter-group-family postgres16 \
  --description "Production PostgreSQL 16 parameters"

# Set performance parameters
aws rds modify-db-parameter-group \
  --db-parameter-group-name production-pg16 \
  --parameters \
    "ParameterName=max_connections,ParameterValue=200,ApplyMethod=pending-reboot" \
    "ParameterName=shared_buffers,ParameterValue={DBInstanceClassMemory/4},ApplyMethod=pending-reboot" \
    "ParameterName=effective_cache_size,ParameterValue={DBInstanceClassMemory*3/4},ApplyMethod=pending-reboot" \
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \
    "ParameterName=maintenance_work_mem,ParameterValue=524288,ApplyMethod=immediate" \
    "ParameterName=random_page_cost,ParameterValue=1.1,ApplyMethod=immediate" \
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \
    "ParameterName=log_statement,ParameterValue=ddl,ApplyMethod=immediate" \
    "ParameterName=idle_in_transaction_session_timeout,ParameterValue=60000,ApplyMethod=immediate"

# Apply parameter group to the instance
aws rds modify-db-instance \
  --db-instance-identifier production-api-db \
  --db-parameter-group-name production-pg16 \
  --apply-immediately
```

## Read Replicas

```bash
# Create a read replica in the same region
aws rds create-db-instance-read-replica \
  --db-instance-identifier production-api-db-read1 \
  --source-db-instance-identifier production-api-db \
  --db-instance-class db.r6g.large \
  --availability-zone us-east-1b \
  --enable-performance-insights \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role

# Create a cross-region read replica for DR
aws rds create-db-instance-read-replica \
  --db-instance-identifier dr-api-db-read \
  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:production-api-db \
  --db-instance-class db.r6g.large \
  --region us-west-2 \
  --source-region us-east-1 \
  --kms-key-id alias/rds-dr-key
# Encryption is inherited from the source; for an encrypted source in another region,
# --kms-key-id must be a key in the destination region and --source-region lets the
# CLI generate the required presigned URL.

# Promote a read replica to standalone (for DR failover)
aws rds promote-read-replica \
  --db-instance-identifier dr-api-db-read

# Check replication lag
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=production-api-db-read1 \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Average \
  --output table
```

## Snapshots and Point-in-Time Recovery

```bash
# Create a manual snapshot (reuse SNAP in the commands below)
SNAP="production-api-db-pre-migration-$(date +%Y%m%d)"
aws rds create-db-snapshot \
  --db-instance-identifier production-api-db \
  --db-snapshot-identifier "$SNAP"

# Wait for snapshot to complete
aws rds wait db-snapshot-available \
  --db-snapshot-identifier "$SNAP"

# Restore from snapshot (creates a new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier production-api-db-restored \
  --db-snapshot-identifier "$SNAP" \
  --db-instance-class db.r6g.large \
  --db-subnet-group-name production-db-subnets \
  --vpc-security-group-ids sg-db-access

# Point-in-time recovery (restore to a specific second)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier production-api-db \
  --target-db-instance-identifier production-api-db-pitr \
  --restore-time "2026-03-24T10:30:00Z" \
  --db-instance-class db.r6g.large \
  --db-subnet-group-name production-db-subnets

# Copy snapshot to another region (run against the destination region; --source-region
# makes the CLI generate the presigned URL needed for encrypted cross-region copies,
# and --kms-key-id must be a key in the destination region)
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier "arn:aws:rds:us-east-1:123456789012:snapshot:$SNAP" \
  --target-db-snapshot-identifier production-api-db-dr-copy \
  --region us-west-2 \
  --source-region us-east-1 \
  --kms-key-id alias/rds-dr-key

# Delete an old snapshot - irreversible. List and confirm the exact identifier with the
# user first:
aws rds describe-db-snapshots --db-instance-identifier production-api-db \
  --snapshot-type manual \
  --query "DBSnapshots[].{Id:DBSnapshotIdentifier,Created:SnapshotCreateTime}" --output table
aws rds delete-db-snapshot --db-snapshot-identifier old-snapshot-name
```

## Monitoring and Alarms

```bash
# Set CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name rds-production-cpu-high \
  --alarm-description "RDS CPU > 80% for 5 minutes" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --dimensions Name=DBInstanceIdentifier,Value=production-api-db \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:db-alerts

# Set free storage space alarm (alert below 10 GB)
aws cloudwatch put-metric-alarm \
  --alarm-name rds-production-storage-low \
  --alarm-description "RDS free storage < 10GB" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --dimensions Name=DBInstanceIdentifier,Value=production-api-db \
  --statistic Average \
  --period 300 \
  --threshold 10737418240 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:db-alerts

# Check current database connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=production-api-db \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Average Maximum \
  --output table
```

## Terraform RDS Example

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "production-db-subnets"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Environment = "production"
  }
}

resource "aws_db_parameter_group" "postgres16" {
  name   = "production-pg16"
  family = "postgres16"

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name         = "shared_buffers"
    value        = "{DBInstanceClassMemory/4}"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "production-api-db"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = "db.r6g.large"

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_name  = "appdb"
  username = "appadmin"
  manage_master_user_password = true

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name

  backup_retention_period   = 14
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:05:00-sun:06:00"
  copy_tags_to_snapshot     = true
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "production-api-db-final"

  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Environment = "production"
    Team        = "backend"
  }
}

resource "aws_db_instance" "read_replica" {
  identifier          = "production-api-db-read1"
  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = "db.r6g.large"

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn
}
```

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Cannot connect to RDS | Security group blocks traffic | Verify SG allows app subnet CIDR on DB port |
| Storage full | Auto-scaling not enabled or limit reached | Set `--max-allocated-storage`; increase manually |
| High replication lag | Write-heavy workload or replica undersized | Upgrade replica instance class; reduce write volume |
| Parameter change not applied | Requires reboot for static params | Reboot with `--force-failover` during maintenance window |
| Snapshot restore slow | Large database size | Use larger instance class for restore; consider PITR |
| Performance Insights empty | Not enabled or instance type unsupported | Enable PI; check instance class supports it |
| Multi-AZ failover happened | Hardware or AZ failure | Check RDS events; review failover logs |
| Connection count maxed out | Application connection leak | Implement connection pooling (PgBouncer/RDS Proxy) |
| Master password unknown | Using managed secret | Retrieve from Secrets Manager ARN in instance details |

## Related Skills

- `aws-iam` - RDS IAM authentication
- `aws-s3` - exporting snapshots to S3
- `architecting-networks` - subnet groups and security groups
- `deploying-on-aws` - choosing RDS versus Aurora or DynamoDB
- `database-design` - schema, indexing and migration planning

## Safety

- Run `aws sts get-caller-identity` and confirm the account, region and profile before any change.
- Use `describe-*` calls first (RDS has no `--dry-run`); take a manual snapshot before deleting or modifying a database, and confirm identifiers with the user before any delete.

