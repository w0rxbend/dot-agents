"""
Automated Evidence Collection for Compliance Frameworks
Control IDs: All controls
Frameworks: SOC 2, HIPAA, PCI-DSS, GDPR

Collects compliance evidence automatically for continuous monitoring.

Dependencies:
    pip install boto3

Usage:
    collector = EvidenceCollector()
    evidence = collector.collect_encryption_evidence()
    collector.store_evidence(evidence)
"""

import boto3
from botocore.exceptions import ClientError
import json
from datetime import datetime
from typing import Dict, List, Any

s3 = boto3.client('s3')
config = boto3.client('config')


class EvidenceCollector:
    """Automated evidence collection for compliance"""

    def collect_encryption_evidence(self) -> Dict[str, Any]:
        """
        Collect evidence for encryption controls
        Control ID: ENC-001
        """
        evidence = {
            "control_id": "ENC-001",
            "control_name": "Encryption at Rest",
            "frameworks": ["SOC2-CC6.1", "HIPAA-164.312(a)(2)(iv)"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PASS",
            "findings": []
        }

        # Check S3 bucket encryption
        try:
            paginator = s3.get_paginator('list_buckets')
            for page in paginator.paginate():
                for bucket in page.get('Buckets', []):
                    bucket_name = bucket['Name']
                    # Since Jan 2023 every bucket has SSE-S3 by default, so
                    # "encryption present" proves little; record the algorithm
                    # and require SSE-KMS when your controls call for managed keys.
                    try:
                        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
                        rules = encryption["ServerSideEncryptionConfiguration"]["Rules"]
                        algorithm = rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
                        compliant = algorithm in ("aws:kms", "aws:kms:dsse")
                        evidence["findings"].append({
                            "resource": f"s3://{bucket_name}",
                            "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
                            "encryption": algorithm,
                            **({} if compliant else {"issue": "Not using SSE-KMS"}),
                        })
                        if not compliant:
                            evidence["status"] = "FAIL"
                    except ClientError as e:
                        if e.response["Error"]["Code"] != "ServerSideEncryptionConfigurationNotFoundError":
                            raise
                        evidence["findings"].append({
                            "resource": f"s3://{bucket_name}",
                            "status": "NON_COMPLIANT",
                            "issue": "No encryption configured"
                        })
                        evidence["status"] = "FAIL"
        except Exception as e:
            evidence["error"] = str(e)

        return evidence

    def store_evidence(self, evidence: Dict[str, Any]):
        """Store evidence in S3"""
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"evidence/{date_path}/{evidence['control_id']}-{evidence['timestamp']}.json"

        s3.put_object(
            Bucket="compliance-evidence",
            Key=key,
            Body=json.dumps(evidence, indent=2),
            ServerSideEncryption='aws:kms'
        )
