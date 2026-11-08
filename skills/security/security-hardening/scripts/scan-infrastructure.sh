#!/bin/bash
# Infrastructure Security Scanning Script
# Runs multiple security scanners and generates reports

set -euo pipefail

# Configuration
REPORT_DIR="${REPORT_DIR:-./security-reports}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Trivy sends usage telemetry and a version check to Aqua by default: opt out
export TRIVY_DISABLE_TELEMETRY=true TRIVY_SKIP_VERSION_CHECK=true

echo "=== Infrastructure Security Scanning ==="
echo "Report directory: $REPORT_DIR"
echo "Timestamp: $TIMESTAMP"
echo

# Create report directory
mkdir -p "$REPORT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run scanner if available: run_scanner NAME CMD [ARG...]
# (argv, not an eval'd string, so paths and env values are never parsed as shell code)
run_scanner() {
    local name=$1
    shift

    if command_exists "$1"; then
        echo "[✓] Running $name..."
        "$@" || echo "[!] $name completed with warnings"
    else
        echo "[✗] $name not installed, skipping"
    fi
}

# Docker CIS Benchmark
# The Hub image docker/docker-bench-security is stale (2019) and would run with host
# net/pid and the Docker socket (root on host), so this only runs a checkout you cloned
# at a release tag and reviewed:
#   git clone --depth 1 --branch v1.6.1 https://github.com/docker/docker-bench-security
#   less docker-bench-security/docker-bench-security.sh
#   DOCKER_BENCH_DIR=./docker-bench-security ./scan-infrastructure.sh
docker_bench() {
    (cd "$DOCKER_BENCH_DIR" && sudo sh docker-bench-security.sh) \
        > "$REPORT_DIR/docker-bench-$TIMESTAMP.txt"
}
if command_exists docker; then
    echo
    echo "=== Docker Security Scan ==="
    if [ -n "${DOCKER_BENCH_DIR:-}" ] && [ -f "$DOCKER_BENCH_DIR/docker-bench-security.sh" ]; then
        run_scanner "docker-bench-security" docker_bench
    else
        echo "[-] docker-bench-security skipped: set DOCKER_BENCH_DIR to a reviewed release checkout (see comment above)"
    fi
fi

# Kubernetes CIS Benchmark
# Creates a Job in the current kubectl context, so it only runs when you point
# KUBE_BENCH_JOB at a manifest you downloaded from a pinned release and reviewed:
#   curl -fsSLo kube-bench-job.yaml \
#     https://raw.githubusercontent.com/aquasecurity/kube-bench/v0.16.0/job.yaml
#   less kube-bench-job.yaml
#   KUBE_BENCH_JOB=./kube-bench-job.yaml ./scan-infrastructure.sh
kube_bench() {
    kubectl apply -f "$KUBE_BENCH_JOB" &&
        kubectl wait --for=condition=complete job/kube-bench --timeout=300s &&
        kubectl logs job/kube-bench > "$REPORT_DIR/kube-bench-$TIMESTAMP.txt"
    kubectl delete -f "$KUBE_BENCH_JOB"
}
if command_exists kubectl; then
    echo
    echo "=== Kubernetes Security Scan ==="
    if [ -n "${KUBE_BENCH_JOB:-}" ] && [ -f "$KUBE_BENCH_JOB" ]; then
        echo "kubectl context: $(kubectl config current-context)"
        run_scanner "kube-bench" kube_bench
    else
        echo "[-] kube-bench skipped: set KUBE_BENCH_JOB to a reviewed, pinned job.yaml (see comment above)"
    fi
fi

# Container Image Scanning with Trivy
if command_exists trivy; then
    echo
    echo "=== Container Image Scanning ==="

    # Scan images (replace with your images)
    IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")

    for image in $IMAGES; do
        echo "Scanning $image..."
        run_scanner "trivy image scan" \
            trivy image --severity HIGH,CRITICAL --format json \
            --output "$REPORT_DIR/trivy-${image//[:\/]/_}-$TIMESTAMP.json" \
            "$image"
    done
fi

# Linux System Audit with Lynis
if command_exists lynis; then
    echo
    echo "=== Linux System Audit ==="
    run_scanner "lynis" \
        sudo lynis audit system --quick --report-file "$REPORT_DIR/lynis-$TIMESTAMP.txt"
fi

# AWS Security Scan with Prowler
if command_exists prowler; then
    echo
    echo "=== AWS Security Scan ==="
    run_scanner "prowler" \
        prowler aws --output-modes json html \
        --output-directory "$REPORT_DIR/prowler-$TIMESTAMP/"
fi

# Infrastructure as Code Scanning with Checkov
if [ -d "terraform" ] && command_exists checkov; then
    echo
    echo "=== Terraform Security Scan ==="
    run_scanner "checkov" \
        checkov -d terraform/ --framework terraform \
        --output json --output-file "$REPORT_DIR/checkov-terraform-$TIMESTAMP.json"
fi

if [ -d "kubernetes" ] && command_exists checkov; then
    echo
    echo "=== Kubernetes Manifest Scan ==="
    run_scanner "checkov" \
        checkov -d kubernetes/ --framework kubernetes \
        --output json --output-file "$REPORT_DIR/checkov-k8s-$TIMESTAMP.json"
fi

# Generate summary report
echo
echo "=== Generating Summary Report ==="

cat > "$REPORT_DIR/summary-$TIMESTAMP.md" <<EOF
# Security Scan Summary

**Date:** $(date)
**Scans Performed:**

EOF

for report in "$REPORT_DIR"/*-$TIMESTAMP.*; do
    if [ -f "$report" ]; then
        filename=$(basename "$report")
        echo "- $filename" >> "$REPORT_DIR/summary-$TIMESTAMP.md"
    fi
done

echo
echo "=== Scan Complete ==="
echo "Reports saved to: $REPORT_DIR"
echo "Summary: $REPORT_DIR/summary-$TIMESTAMP.md"
echo

# Check for critical findings
echo "=== Critical Findings Check ==="
CRITICAL_FOUND=0

# Check Trivy reports for CRITICAL vulnerabilities
for report in "$REPORT_DIR"/trivy-*-$TIMESTAMP.json; do
    # trivy pretty-prints JSON ("Severity": "CRITICAL"), so allow the space
    if [ -f "$report" ] && grep -Eq '"Severity": ?"CRITICAL"' "$report"; then
        echo "[!] CRITICAL vulnerabilities found in $(basename "$report")"
        CRITICAL_FOUND=1
    fi
done

if [ $CRITICAL_FOUND -eq 1 ]; then
    echo
    echo "[!] CRITICAL issues detected - review reports immediately"
    exit 1
else
    echo "[✓] No critical issues detected"
    exit 0
fi
