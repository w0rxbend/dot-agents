# Drift Detection and Remediation

## Table of Contents

- [Drift Detection Concepts](#drift-detection-concepts)
- [ArgoCD Drift Detection](#argocd-drift-detection)
  - [View Sync Status](#view-sync-status)
  - [Automatic Self-Healing](#automatic-self-healing)
  - [Manual Sync Operations](#manual-sync-operations)
- [Flux Drift Detection](#flux-drift-detection)
  - [View Kustomization Status](#view-kustomization-status)
  - [Force Reconciliation](#force-reconciliation)
  - [Automatic Drift Correction](#automatic-drift-correction)
- [Disaster Recovery](#disaster-recovery)
  - [ArgoCD Recovery](#argocd-recovery)
  - [Flux Recovery](#flux-recovery)
- [Troubleshooting](#troubleshooting)
  - [OutOfSync Issues](#outofsync-issues)
  - [Resource Finalizers](#resource-finalizers)

## Drift Detection Concepts

**Drift:** actual state (cluster) diverges from desired state (Git).

**Common Causes:**
- Manual kubectl apply
- Cluster operators modifying resources
- External controllers changing state
- Finalizers blocking deletion
- CRD updates needing migration

## ArgoCD Drift Detection

### View Sync Status

```bash
# Check application sync status
argocd app get myapp

# View detailed diff
argocd app diff myapp

# Hard refresh (fetch latest Git)
argocd app get myapp --hard-refresh
```

### Automatic Self-Healing

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
spec:
  syncPolicy:
    automated:
      prune: true      # Remove resources not in Git
      selfHeal: true   # Revert manual changes
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Manual Sync Operations

```bash
# Sync specific resource
argocd app sync myapp --resource apps:Deployment:myapp

# Force sync (may delete and recreate resources; confirm with user first)
argocd app sync myapp --force

# Sync with prune
argocd app sync myapp --prune

# Dry-run sync
argocd app sync myapp --dry-run
```

## Flux Drift Detection

### View Kustomization Status

```bash
# Check all kustomizations
flux get kustomizations

# Check specific kustomization
flux get kustomization myapp

# View events
flux events --for Kustomization/myapp
```

### Force Reconciliation

```bash
# Reconcile immediately
flux reconcile kustomization myapp

# Reconcile with source update
flux reconcile kustomization myapp --with-source

# Suspend reconciliation
flux suspend kustomization myapp

# Resume reconciliation
flux resume kustomization myapp
```

### Automatic Drift Correction

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp
spec:
  interval: 10m       # Check every 10 minutes
  prune: true         # Remove resources not in Git
  # force: true       # Opt-in only: recreates resources on immutable-field
                      # conflicts (downtime; data loss for some resources)
  wait: true          # Wait for resources to be ready
  timeout: 5m
  sourceRef:
    kind: GitRepository
    name: myapp
  path: ./k8s/prod
```

## Disaster Recovery

### ArgoCD Recovery

```bash
# 1. Reinstall ArgoCD at the same pinned release the cluster ran (not `stable`)
ARGOCD_VERSION=v3.6.1 scripts/install-argocd.sh   # set to your release tag

# 2. Re-register clusters
argocd cluster add prod-cluster

# 3. Restore applications from Git
kubectl apply -f git-repo/argocd/applications/

# 4. Sync all applications
argocd app sync --all
```

### Flux Recovery

```bash
# Bootstrap Flux (idempotent operation)
flux bootstrap github \
  --owner=myorg \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production

# Flux automatically reconciles all resources from Git
```

## Troubleshooting

### OutOfSync Issues

**Check Git connectivity:**
```bash
argocd repo get https://github.com/myorg/myapp
flux get sources git
```

**Validate manifests:**
```bash
kubectl apply --dry-run=server -f manifest.yaml
kustomize build overlays/prod | kubectl apply --dry-run=server -f -
```

**Review sync logs:**
```bash
argocd app logs myapp
flux logs --kind=Kustomization --name=myapp
```

### Resource Finalizers

```bash
# View finalizers
kubectl get deployment myapp -o yaml | grep finalizers -A 5

# Remove finalizer (if stuck)
kubectl patch deployment myapp -p '{"metadata":{"finalizers":[]}}' --type=merge
```
