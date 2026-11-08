---
name: implementing-gitops
description: "Set up GitOps continuous delivery for Kubernetes with Argo CD or Flux - bootstrap, Git-as-source-of-truth, pull-based sync, environment promotion, drift detection, multi-cluster and progressive rollouts. Use when wiring declarative delivery to clusters; use operating-kubernetes for workload operations and building-ci-pipelines for the CI that builds images."
---

# GitOps Workflows

## When to Use

- **Kubernetes Deployments:** Automate application and infrastructure deploys to clusters
- **Multi-Cluster Management:** Deploy across development, staging, production and edge clusters
- **Continuous Delivery:** Pull-based CD with automated reconciliation
- **Drift Detection:** Detect and correct drift from desired state automatically
- **Audit Requirements:** Full audit trail in Git commits for compliance
- **Progressive Delivery:** Canary, blue-green or rolling strategies
- **Disaster Recovery:** Fast cluster recovery via GitOps bootstrap

Trigger keywords: "deploy to Kubernetes", "ArgoCD setup", "Flux bootstrap", "GitOps pipeline", "environment promotion", "multi-cluster deployment", "automated reconciliation"

## Core GitOps Principles

### 1. Git as Single Source of Truth

All system configuration lives in Git. No manual kubectl apply or cluster edits. Declarative YAML manifests (not imperative scripts) define desired state for all Kubernetes resources, environment overlays, infrastructure and applications.

### 2. Pull-Based Deployment

In-cluster operators pull changes from Git and apply them automatically. Benefits: no cluster credentials in CI/CD, air-gapped support, self-healing via continuous reconciliation, simpler CI/CD.

### 3. Automated Reconciliation

Operators continuously reconcile actual cluster state against desired state in Git. Loop: watch Git, compare live state, apply differences, report status, repeat.

## Tool Selection

### ArgoCD vs Flux

| Decision Factor | Choose ArgoCD | Choose Flux |
|----------------|---------------|-------------|
| **Team Preference** | Web UI visual management | CLI/API-first workflows |
| **Learning Curve** | Easier onboarding via UI | Steeper, more flexible |
| **Architecture** | Monolithic, stateful controller | Modular, stateless controllers |
| **Multi-Tenancy** | Built-in RBAC and projects | Kubernetes-native RBAC |
| **Resource Usage** | Higher (UI components) | Lower (minimal controllers) |
| **Best For** | Transitioning to GitOps | Platform engineering |

**Hybrid Approach:** Some teams use Flux for infrastructure, ArgoCD for applications.

ArgoCD patterns: references/argocd-patterns.md
Flux patterns: references/flux-patterns.md
Kustomize overlay patterns: references/kustomize-overlays.md

## Quick Start

### ArgoCD Installation

```bash
# Pinned release (ARGOCD_VERSION, default v3.6.1), never the moving `stable` branch;
# downloads the manifest, shows the kube context, asks before applying
./scripts/install-argocd.sh
```

Pin install manifests, Helm charts and images to reviewed versions or digests, never `stable`/`latest`; review third-party manifests before applying.

**Basic Application:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    targetRevision: HEAD
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Flux Bootstrap

```bash
flux bootstrap github \
  --owner=myorg \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production
```

**Basic Kustomization:**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 10m
  path: "./k8s/prod"
  prune: true
  sourceRef:
    kind: GitRepository
    name: myapp
```

## Environment Promotion

**Branch-Based Strategy:** dev branch → staging branch → main branch (prod)
**Kustomize-Based Strategy:** k8s/base/ → k8s/overlays/{dev,staging,prod}/

**Promotion Process:**
1. Merge code to main branch
2. CI builds tagged container image
3. Commit new image tag to environment overlay
4. GitOps operator detects change and deploys
5. Test in environment
6. Promote by updating next environment in Git

Multi-environment ApplicationSet patterns: references/argocd-patterns.md

## Multi-Cluster Management

**ArgoCD:** Register external clusters with argocd CLI. ApplicationSets generate Applications per cluster. One ArgoCD instance manages all.

**Flux:** Bootstrap Flux per cluster. One Git repo, cluster-specific paths. Remote clusters via kubeConfig secrets.

Detailed multi-cluster patterns: references/multi-cluster.md

## Progressive Delivery

**Canary Deployments:** Shift traffic to new version gradually, watch metrics during rollout, automated rollback on failure.

**Blue-Green Deployments:** Run new version beside old, switch traffic atomically, roll back instantly on issues.

**ArgoCD:** Argo Rollouts for progressive delivery
**Flux:** Flagger for automated canary analysis

Progressive delivery strategies and Argo Rollouts examples: references/progressive-delivery.md

## Secret Management

Configuration lives in Git, but secrets must stay protected: commit only encrypted secrets (Sealed Secrets, SOPS) or references (ESO); never plaintext Secret manifests, generator inputs or decryption keys. Never print secrets or ask the user to paste them into chat.

| Tool | Approach | Security | Complexity |
|------|----------|----------|------------|
| **Sealed Secrets** | Encrypt secrets for Git | Medium | Low |
| **SOPS** | Encrypt files with KMS | High | Medium |
| **External Secrets** | Reference external vaults | High | Medium |
| **HashiCorp Vault** | Central secret management | Very High | High |

Secret management integration patterns: references/secret-management.md

## Drift Detection and Remediation

**ArgoCD Automatic Self-Healing:**
```yaml
syncPolicy:
  automated:
    prune: true      # Remove resources not in Git
    selfHeal: true   # Revert manual changes
```

**Flux Automatic Reconciliation:**
```yaml
spec:
  interval: 10m    # Check every 10 minutes
  prune: true      # Remove resources not in Git
  # force: true    # Opt-in only: recreates resources on immutable-field
                   # conflicts (downtime; data loss for some resources)
```

**Manual Operations:** confirm with user first before cluster-changing or destructive commands (install/bootstrap, sync with `--prune`/`--force`, `delete`, `cluster rm`, removing finalizers, `git push`).
```bash
# ArgoCD
argocd app get myapp           # View sync status
argocd app diff myapp          # Show differences
argocd app sync myapp          # Manually trigger sync

# Flux
flux get kustomizations              # View sync status
flux reconcile kustomization myapp   # Force immediate sync
```

Drift detection strategies and troubleshooting: references/drift-remediation.md

## Sync Hooks and Lifecycle

**PreSync Hook (Database Migration):**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
```

**PostSync Hook (Smoke Test):**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  annotations:
    argocd.argoproj.io/hook: PostSync
```

Complete sync hook examples: examples/argocd/sync-hooks.yaml

## Monitoring and Observability

### Key Metrics

- **Sync Status:** OutOfSync, Synced, Unknown
- **Sync Frequency:** How often reconciliation runs
- **Drift Detection:** Time to detect configuration drift
- **Sync Duration:** Time to apply changes
- **Failure Rate:** Failed syncs and causes

**ArgoCD Metrics:** `/metrics` endpoint (`argocd_app_sync_total`, `argocd_app_info`)
**Flux Metrics:** From controllers (`gotk_reconcile_condition`, `gotk_reconcile_duration_seconds`)

## Troubleshooting

### Common Issues

**Sync Stuck/OutOfSync:**
- Check Git repository access
- Validate manifest YAML
- Review sync logs for errors
- Check resource finalizers

**Self-Heal Not Working:**
- Verify selfHeal enabled in syncPolicy
- Check operator write permissions
- Review resource ownership labels

**Secrets Not Decrypting:**
- Verify SOPS/ESO controllers installed
- Check KMS/Vault credentials
- Review encryption key configuration

## CLI Quick Reference

### ArgoCD Commands

```bash
argocd app create <name>          # Create application
argocd app get <name>              # View status
argocd app sync <name>             # Trigger sync
argocd app diff <name>             # Show drift
argocd app list                    # List all applications
```

### Flux Commands

```bash
flux create source git <name>      # Create Git source
flux create kustomization <name>   # Create kustomization
flux get all                       # View all resources
flux reconcile <kind> <name>       # Force reconciliation
flux logs                          # View controller logs
```

### Kustomize Commands

```bash
kustomize build k8s/overlays/prod  # Preview generated YAML
kubectl apply -k k8s/overlays/prod # Apply directly
kubectl diff -k k8s/overlays/prod  # Show differences
```

## Installation Scripts

```bash
# Install ArgoCD (pinned ARGOCD_VERSION; asks before applying; never prints the admin password)
./scripts/install-argocd.sh

# Bootstrap Flux
export GITHUB_TOKEN=<token>
export GITHUB_OWNER=<org>
export GITHUB_REPO=fleet-infra
# export GITHUB_PERSONAL=true   # only when the owner is a user account
./scripts/install-flux.sh       # needs the flux CLI; asks before pushing to the repo

# Check for drift
./scripts/check-drift.sh

# Promote environment
./scripts/promote-env.sh dev staging
```

## Example Files

Working examples in examples/:

**ArgoCD Examples:**
- examples/argocd/application.yaml - Basic Application
- examples/argocd/applicationset.yaml - Multi-environment ApplicationSet
- examples/argocd/progressive-rollout.yaml - Progressive rollout strategy
- examples/argocd/sync-hooks.yaml - PreSync/PostSync hooks

**Flux Examples:**
- examples/flux/gitrepository.yaml - Git source configuration
- examples/flux/kustomization.yaml - Kustomization controller
- examples/flux/helmrelease.yaml - Helm release management
- examples/flux/ocirepository.yaml - OCI artifact source

**Kustomize Examples:**
- examples/kustomize/base/ - Base configuration
- examples/kustomize/overlays/{dev,staging,prod}/ - Environment overlays

**Rollout Examples:**
- examples/rollouts/canary.yaml - Canary deployment with Argo Rollouts
- examples/rollouts/blue-green.yaml - Blue-green deployment strategy

## Related Skills

- **operating-kubernetes:** Kubernetes fundamentals and resource management
- **pulumi-stacks** / **deploying-on-aws**, **deploying-on-gcp**, **deploying-on-azure:** Provision clusters GitOps deploys to
- **building-ci-pipelines:** CI builds images, GitOps deploys them
- **hashicorp-vault:** Vault/ESO integration with GitOps
- **deploying-applications:** GitOps as deployment mechanism
