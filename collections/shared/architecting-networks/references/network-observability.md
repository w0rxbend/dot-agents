# Network Observability

## VPC Flow Logs

### Enable Flow Logs

**Traffic Type:**
- ALL (recommended) - accepted and rejected traffic
- ACCEPT - only accepted traffic
- REJECT - only rejected traffic

**Aggregation Interval:**
- 1 minute - real-time monitoring (higher cost)
- 10 minutes - standard (balance cost/latency)

**Destination:**
- CloudWatch Logs - real-time analysis, alerting
- S3 - long-term storage, cost-effective

### Monitoring Patterns

**Key Metrics:**
- Rejected connections (security anomalies)
- Traffic volume spikes
- Cross-VPC communication patterns
- NAT Gateway utilization
- Data transfer costs

**Alert On:**
- Spike in rejected connections (> 100 in 5 minutes)
- Unusual traffic patterns
- High data transfer costs
- Network errors

### Common Flow Log Queries

**Top Talkers (Most Traffic):**
```sql
SELECT srcaddr, dstaddr, SUM(bytes) as total_bytes
FROM vpc_flow_logs
WHERE action = 'ACCEPT'
GROUP BY srcaddr, dstaddr
ORDER BY total_bytes DESC
LIMIT 20
```

**Rejected Connections by Source:**
```sql
SELECT srcaddr, COUNT(*) as rejected_count
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY srcaddr
ORDER BY rejected_count DESC
LIMIT 20
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check security group rules
   - Verify route tables
   - Check network ACLs
   - Verify NAT Gateway status

2. **Slow Performance**
   - Check NAT Gateway metrics
   - Review cross-region traffic
   - Find bottlenecks in flow logs

3. **High Costs**
   - Review data transfer patterns
   - Check NAT Gateway usage
   - Analyze cross-AZ traffic
   - Optimize VPC Endpoint usage
