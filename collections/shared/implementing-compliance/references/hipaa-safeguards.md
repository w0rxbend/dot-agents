# HIPAA Safeguards Reference

Quick reference to the HIPAA Security Rule (45 CFR Part 164, Subpart C). Code examples live in this skill's `examples/` directory.

## Quick Reference

**Technical Safeguards (§164.312):**
- Access Control with MFA
- Audit Controls (§164.312(b); the rule sets no log-retention period, while required documentation is kept 6 years under §164.316(b)(2))
- Integrity Controls
- Person/Entity Authentication
- Transmission Security (TLS 1.2+)

**Physical Safeguards (§164.310):**
- Facility Access Controls
- Workstation Use and Security
- Device and Media Controls

**Administrative Safeguards (§164.308):**
- Security Management Process (Risk Analysis required)
- Assigned Security Responsibility
- Workforce Security
- Information Access Management
- Security Awareness Training
- Security Incident Procedures (Breach Notification Rule: individuals without unreasonable delay, no later than 60 days after discovery)
- Contingency Plan (Backup and DR)
- Business Associate Agreements

See [control-mapping-matrix.md](control-mapping-matrix.md) for unified control implementations satisfying multiple frameworks.
