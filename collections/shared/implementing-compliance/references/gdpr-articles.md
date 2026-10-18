# GDPR Key Articles Reference

Engineering-relevant articles of Regulation (EU) 2016/679. This is an orientation aid, not legal advice; confirm interpretations with counsel and your DPO.

## Principles and Lawful Basis

| Article | Requirement | Engineering implication |
|---------|-------------|-------------------------|
| Art. 5 | Principles: lawfulness, purpose limitation, data minimisation, accuracy, storage limitation (5(1)(e)), integrity and confidentiality (5(1)(f)), accountability (5(2)) | Collect only needed fields; define retention per data category; delete or anonymise on expiry; keep evidence of compliance |
| Art. 6 | Lawful basis for processing (consent, contract, legal obligation, vital interests, public task, legitimate interests) | Record the basis per processing purpose |
| Art. 7 | Conditions for consent (demonstrable, withdrawable as easily as given) | Store consent records with timestamp and version; support withdrawal |
| Art. 9 | Special categories (health, biometrics, etc.) are prohibited unless an exception applies | Separate storage, stricter access control and encryption |

## Data Subject Rights (Art. 12-22)

Respond within one month (extendable by two months for complex requests, Art. 12(3)).

| Article | Right | Implementation |
|---------|-------|----------------|
| Art. 15 | Access | Export all personal data for a subject |
| Art. 16 | Rectification | Editable profile data, propagated to copies |
| Art. 17 | Erasure ("right to be forgotten") | Deletion across primary stores, replicas, caches and search indexes; document backup handling |
| Art. 18 | Restriction of processing | Flag that blocks processing while keeping the data |
| Art. 20 | Data portability | Machine-readable export (JSON, CSV) |
| Art. 21 | Objection | Opt-out of processing based on legitimate interests and of direct marketing |
| Art. 22 | Automated decision-making | Human review path for decisions with legal or similar effects |

## Controller and Processor Obligations

| Article | Requirement | Implementation |
|---------|-------------|----------------|
| Art. 25 | Data protection by design and by default | Privacy-preserving defaults; pseudonymisation; minimal default visibility |
| Art. 28 | Processor contracts (DPA) | DPA with every vendor that processes personal data; sub-processor approval |
| Art. 30 | Records of processing activities | Maintained inventory of purposes, categories, recipients, transfers and retention |
| Art. 32 | Security of processing (appropriate technical and organisational measures) | Encryption at rest and in transit, access control, MFA, backups, regular testing |
| Art. 33 | Breach notification to the supervisory authority within 72 hours of becoming aware, unless unlikely to result in risk | Incident runbook with a 72-hour clock; breach register for all breaches |
| Art. 34 | Communication to data subjects without undue delay when the breach is likely to result in high risk | Notification templates and contact channels |
| Art. 35 | Data Protection Impact Assessment for high-risk processing | DPIA before launching high-risk features (large-scale profiling, special categories, systematic monitoring) |
| Art. 37-39 | Data Protection Officer where required | Designate and involve the DPO |

## International Transfers (Art. 44-49)

Transfers outside the EEA need an adequacy decision (Art. 45, e.g. the EU-US Data Privacy Framework for certified US companies), appropriate safeguards such as Standard Contractual Clauses (Art. 46), or a specific derogation (Art. 49). Document a transfer impact assessment where SCCs are used.

## Fines (Art. 83)

Up to EUR 10 million or 2% of worldwide annual turnover for obligations such as Art. 25-39, and up to EUR 20 million or 4% for breaches of the principles, lawful basis, data subject rights and transfer rules, whichever is higher.

## Logging and Retention

Audit logs that contain personal data are themselves subject to storage limitation (Art. 5(1)(e)): set a retention period justified by the security purpose, pseudonymise identifiers where possible, and restrict access. See the `audit-logging` skill for retention guidance across frameworks.

See [control-mapping-matrix.md](control-mapping-matrix.md) for how these articles map to unified controls.
