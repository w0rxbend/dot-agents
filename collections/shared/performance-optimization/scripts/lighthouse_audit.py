#!/usr/bin/env python3
"""Run a Lighthouse lab audit on one URL and print a compact JSON summary.

Usage:   python3 scripts/lighthouse_audit.py https://example.com
Needs:   the Lighthouse CLI on PATH (npm install -g lighthouse) and a local Chrome/Chromium.
Output:  category scores (0-100, or null if Lighthouse could not score a category)
         plus lab metrics in milliseconds (CLS is unitless).

Lab data only. INP cannot be measured in a lab run; Total Blocking Time is its
closest lab proxy. Confirm improvements with field data (RUM / CrUX).
"""
import json
import os
import subprocess
import sys
import tempfile

CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]
METRICS = {
    "first-contentful-paint": "fcp_ms",
    "largest-contentful-paint": "lcp_ms",
    "total-blocking-time": "tbt_ms",
    "cumulative-layout-shift": "cls",
    "speed-index": "speed_index_ms",
}


def _score(categories: dict, key: str):
    score = categories.get(key, {}).get("score")
    return None if score is None else round(score * 100)


def run_lighthouse(url: str, timeout_s: int = 180) -> dict:
    fd, output_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        result = subprocess.run(
            [
                "lighthouse",
                url,
                "--output=json",
                f"--output-path={output_path}",
                "--chrome-flags=--headless",
                "--only-categories=" + ",".join(CATEGORIES),
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if result.returncode != 0 or os.path.getsize(output_path) == 0:
            return {"url": url, "error": "Lighthouse failed", "stderr": result.stderr[-1000:]}

        with open(output_path, encoding="utf-8") as f:
            report = json.load(f)
    except subprocess.TimeoutExpired:
        return {"url": url, "error": f"Lighthouse timed out after {timeout_s}s"}
    except FileNotFoundError:
        return {"url": url, "error": "Lighthouse CLI not found; install with: npm install -g lighthouse"}
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

    categories = report.get("categories", {})
    audits = report.get("audits", {})
    return {
        "url": url,
        "lighthouse_version": report.get("lighthouseVersion"),
        "scores": {key.replace("-", "_"): _score(categories, key) for key in CATEGORIES},
        "metrics": {
            name: audits.get(audit_id, {}).get("numericValue") for audit_id, name in METRICS.items()
        },
        "runtime_error": (report.get("runtimeError") or {}).get("message"),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python3 lighthouse_audit.py <url>"}))
        sys.exit(2)
    summary = run_lighthouse(sys.argv[1])
    print(json.dumps(summary, indent=2))
    sys.exit(1 if "error" in summary else 0)
