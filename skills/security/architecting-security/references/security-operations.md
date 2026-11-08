# Security Operations Reference

## SIEM (Security Information & Event Management)

**Purpose:** Centralize log aggregation, correlation, alerting

**Leading Platforms:**
- Splunk Enterprise Security
- Elastic Security
- Microsoft Sentinel
- Google Chronicle

**Architecture:**
1. Log Collection: Ingest from all sources
2. Normalization: Standardize log formats
3. Correlation: Rules detect patterns
4. Alerting: Notify SOC team
5. Investigation: Search, visualization

## SOAR (Security Orchestration, Automation & Response)

**Purpose:** Automate incident response workflows

**Capabilities:**
- Playbooks: Automated response workflows
- Orchestration: Integrate security tools
- Case Management: Track incidents

**Leading Platforms:**
- Splunk SOAR
- Palo Alto Cortex XSOAR
- IBM Resilient

## Detection Strategies

### UEBA (User & Entity Behavior Analytics)

**Purpose:** ML-based anomaly detection

**Detects:**
- Account compromise
- Insider threats
- Data exfiltration
- Lateral movement

### Threat Intelligence

**Sources:**
- MISP (Malware Information Sharing Platform)
- ThreatConnect
- ISACs (Information Sharing and Analysis Centers)

**Integration:**
- Enrich SIEM alerts with threat context
- Block known malicious IPs/domains
- Proactive threat hunting
