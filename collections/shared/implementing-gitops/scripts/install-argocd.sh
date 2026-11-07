#!/bin/bash
# Install ArgoCD on the current kubectl context from a pinned release.
#
# Applies cluster-wide CRDs and RBAC, so this script asks for confirmation
# (skip with --yes).
#
# Env vars:
#   ARGOCD_VERSION  release tag to install (default: v3.6.1; never "stable")
#   ARGOCD_HA       "true" installs the HA manifest (manifests/ha/install.yaml)
#   ARGOCD_SHA256   optional sha256 of the manifest to verify
set -euo pipefail

ARGOCD_VERSION="${ARGOCD_VERSION:-v3.6.1}"
ASSUME_YES=false
[[ "${1:-}" == "--yes" ]] && ASSUME_YES=true

if [[ ! "$ARGOCD_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: ARGOCD_VERSION must be a release tag like v3.6.1, got: $ARGOCD_VERSION" >&2
  exit 1
fi

MANIFEST_PATH=manifests/install.yaml
[[ "${ARGOCD_HA:-false}" == "true" ]] && MANIFEST_PATH=manifests/ha/install.yaml
MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/${MANIFEST_PATH}"
MANIFEST=$(mktemp)
trap 'rm -f "$MANIFEST"' EXIT

curl -fsSL -o "$MANIFEST" "$MANIFEST_URL"
if [[ -n "${ARGOCD_SHA256:-}" ]]; then
  echo "${ARGOCD_SHA256}  ${MANIFEST}" | sha256sum -c -
fi

echo "About to install ArgoCD ${ARGOCD_VERSION}:"
echo "  Cluster context: $(kubectl config current-context 2>/dev/null || echo unknown)"
echo "  Manifest:        $MANIFEST_URL"
echo "This creates the argocd namespace plus cluster-wide CRDs and RBAC."

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Continue? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

# Create namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD from the downloaded, pinned manifest
kubectl apply -n argocd -f "$MANIFEST"

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

echo ""
echo "ArgoCD installed successfully!"
echo ""
echo "Access ArgoCD UI:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
# The admin password is not printed here so it never lands in logs or an agent transcript.
echo "Get the initial admin password in your own terminal (do not paste it into chat):"
echo "  argocd admin initial-password -n argocd"
echo "Log in as admin, change the password, then delete argocd-initial-admin-secret."
