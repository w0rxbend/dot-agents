"""
Compliance Audit Report Generation
Frameworks: SOC 2, HIPAA, PCI-DSS, GDPR

Generates compliance reports from collected evidence.

Dependencies:
    pip install boto3

Usage:
    generator = AuditReportGenerator(start_date, end_date)
    report = generator.generate_soc2_report()
"""

import boto3
from boto3.dynamodb.conditions import Attr
import json
from datetime import datetime
from typing import Dict

dynamodb = boto3.resource('dynamodb')


class AuditReportGenerator:
    """Generate compliance audit reports"""

    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.table = dynamodb.Table('compliance-controls')

    def generate_soc2_report(self) -> Dict:
        """Generate SOC 2 Type II report from control records (evidence_collector shape)"""
        scan = {"FilterExpression": Attr("timestamp").between(
            self.start_date.isoformat(), self.end_date.isoformat())}
        items = []
        while True:
            page = self.table.scan(**scan)
            items += page["Items"]
            if "LastEvaluatedKey" not in page:
                break
            scan["ExclusiveStartKey"] = page["LastEvaluatedKey"]

        controls = [i for i in items
                    if any(f.startswith("SOC2") for f in i.get("frameworks", []))]
        if not controls:
            # Never report a score without evidence
            raise ValueError("No SOC 2 control records in report period")
        failed = [c.get("control_id") for c in controls if c.get("status") != "PASS"]
        return {
            "framework": "SOC 2 Type II",
            "report_period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "compliance_score": round(100.0 * (len(controls) - len(failed)) / len(controls), 1),
            "controls_evaluated": len(controls),
            "controls_not_passing": failed,
        }
