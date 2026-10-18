#!/usr/bin/env bash
# Bootstrap Flux CD on the current kubectl context.
#
# flux bootstrap installs controllers into the cluster AND pushes commits to
# the GitHub repository, so this script asks for confirmation (skip with --yes).
#
# Env vars:
#   GITHUB_TOKEN     token with repo access (required)
#   GITHUB_OWNER     GitHub user or organization (required)
#   GITHUB_REPO      repository name, e.g. fleet-infra (required)
#   GITHUB_PERSONAL  "true" when GITHUB_OWNER is a user account, not an org (default: false)
#   FLUX_BRANCH      branch to commit to (default: main)
#   FLUX_PATH        path in the repo for this cluster (default: clusters/production)
set -euo pipefail

ASSUME_YES=false
[[ "${1:-}" == "--yes" ]] && ASSUME_YES=true

for var in GITHUB_TOKEN GITHUB_OWNER GITHUB_REPO; do
  if [[ -z "${!var:-}" ]]; then
    echo "Error: $var environment variable not set" >&2
    exit 1
  fi
done

if ! command -v flux >/dev/null 2>&1; then
  cat >&2 <<'MSG'
Error: flux CLI not found. Install it with a package manager or a pinned release:
  brew install fluxcd/tap/flux                      # macOS / Linuxbrew
  # or download a pinned release and verify it:
  #   https://github.com/fluxcd/flux2/releases  (flux_<version>_linux_amd64.tar.gz
  #   plus flux_<version>_checksums.txt; check with sha256sum -c)
Then re-run this script.
MSG
  exit 1
fi

BRANCH="${FLUX_BRANCH:-main}"
CLUSTER_PATH="${FLUX_PATH:-clusters/production}"
PERSONAL_FLAG=()
[[ "${GITHUB_PERSONAL:-false}" == "true" ]] && PERSONAL_FLAG=(--personal)

echo "About to bootstrap Flux CD:"
echo "  Cluster context: $(kubectl config current-context 2>/dev/null || echo unknown)"
echo "  Repository:      $GITHUB_OWNER/$GITHUB_REPO (${PERSONAL_FLAG[*]:-organization})"
echo "  Branch / path:   $BRANCH / $CLUSTER_PATH"
echo "This installs Flux controllers in the cluster and pushes commits to the repository."

flux check --pre

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Continue? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

flux bootstrap github \
  --owner="$GITHUB_OWNER" \
  --repository="$GITHUB_REPO" \
  --branch="$BRANCH" \
  --path="$CLUSTER_PATH" \
  "${PERSONAL_FLAG[@]}"

echo ""
echo "Flux installed. Check status:"
echo "  flux check"
echo "  flux get all"
