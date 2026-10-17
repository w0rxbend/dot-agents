---
name: kubernetes-hardening
description: Harden Kubernetes clusters and workloads - Pod Security Admission, securityContext, service-account tokens, default-deny NetworkPolicy that keeps DNS, least-privilege RBAC, admission policy (ValidatingAdmissionPolicy/Kyverno), image digests and signature verification, secrets encryption, audit logging, CIS scanning and runtime detection. Use for a K8s security review or before exposing a cluster to production; use operating-kubernetes for day-to-day workload operations.
category: security
risk: critical
source: https://github.com/BagelHole/DevOps-Security-Agent-Skills
source_repo: BagelHole/DevOps-Security-Agent-Skills
source_type: community
date_added: '2026-09-20'
license: MIT
license_source: https://github.com/BagelHole/DevOps-Security-Agent-Skills/blob/main/LICENSE
compatibility: Requires kubectl access with permission to read cluster configuration; changing admission, audit or encryption settings requires control-plane access (self-managed) or the cloud provider's equivalent settings (EKS/GKE/AKS).
metadata:
  author: devops-skills
  version: '1.1'
---

# Kubernetes Hardening

Work in layers and verify each one. Apply changes in a non-production cluster first; `enforce` modes and default-deny policies break workloads that were relying on the gap.

## 0. Inventory first (read-only)

```bash
kubectl version
kubectl get ns --show-labels                         # current Pod Security labels
kubectl get networkpolicy -A
kubectl get clusterrolebindings -o wide | grep -E 'cluster-admin|system:anonymous|system:unauthenticated'
kubectl auth can-i --list --as=system:serviceaccount:<ns>:default -n <ns>
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep -v '@sha256'
```

Then run the scanners in section 9 to get a baseline.

## 1. Pod Security Admission

Label every workload namespace. Roll out with `warn`/`audit` first, then `enforce`.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

```bash
# Preview which existing pods would violate "restricted"
kubectl label --dry-run=server --overwrite ns production pod-security.kubernetes.io/enforce=restricted
```

Use `baseline` only for namespaces that genuinely need it (for example some CNI or monitoring agents), and keep `privileged` for system namespaces.

## 2. Workload securityContext

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      automountServiceAccountToken: false      # only mount when the pod calls the API server
      serviceAccountName: api
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: api
          image: registry.example.com/api@sha256:<digest>   # digest, not a mutable tag
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits: { memory: 256Mi }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - name: tmp
          emptyDir: {}
```

Also avoid `hostNetwork`, `hostPID`, `hostIPC`, `hostPath` volumes and `privileged: true`; PSA `restricted` rejects most of these.

## 3. Service accounts

- One service account per workload; never grant permissions to `default`.
- Set `automountServiceAccountToken: false` on the ServiceAccount or pod unless the pod calls the API. When it does, the projected token is short-lived and audience-bound; do not create legacy long-lived token Secrets.
- For cloud APIs, use workload identity (EKS Pod Identity/IRSA, GKE Workload Identity, AKS Workload ID) instead of static keys in Secrets.

## 4. NetworkPolicy: default deny that keeps DNS

NetworkPolicies only take effect if the CNI enforces them (Calico, Cilium, cloud-native policy engines); check before relying on them.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: production
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns          # check your DNS pods' labels
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-from-frontend
  namespace: production
spec:
  podSelector:
    matchLabels: { app: web }
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels: { app: frontend }
      ports:
        - { protocol: TCP, port: 8080 }
```

Without the DNS rule, a default-deny egress policy breaks every name lookup. Add explicit egress rules for databases, external APIs and the API server where needed.

## 5. RBAC least privilege

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: app-reader, namespace: production }
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config"]
    verbs: ["get", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: app-reader, namespace: production }
subjects:
  - kind: ServiceAccount
    name: api
    namespace: production
roleRef:
  kind: Role
  name: app-reader
  apiGroup: rbac.authorization.k8s.io
```

Treat these as privilege-escalation paths and grant them only to cluster administrators:

| Grant | Why it is dangerous |
|---|---|
| `*` verbs or resources | Includes everything, now and in future API versions |
| `escalate`, `bind` on roles | Lets a subject grant itself more permissions |
| `impersonate` | Act as any user, group or service account |
| `create` on `pods` / workloads | Can mount any service account token or hostPath in that namespace |
| `get`/`list` on `secrets` | Reads every credential in scope |
| `create` on `serviceaccounts/token` | Mints tokens for other identities |
| `nodes/proxy`, `pods/exec`, `pods/attach` | Code execution on nodes or in pods |

Audit with `kubectl auth can-i --list --as=<subject>` and a tool such as `rbac-tool` or `kubectl-who-can` if installed.

## 6. Admission policy

PSA covers pod-level controls only. Add policy for registries, digests, labels and resource limits.

Built-in ValidatingAdmissionPolicy (CEL; GA in recent Kubernetes versions, check yours):

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: require-image-digest }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "object.spec.template.spec.containers.all(c, c.image.contains('@sha256:'))"
      message: "images must be pinned by digest"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata: { name: require-image-digest }
spec:
  policyName: require-image-digest
  validationActions: ["Deny"]
  matchResources:
    namespaceSelector:
      matchLabels: { env: production }
```

Kyverno or OPA Gatekeeper add mutation, generation and image-signature checks. Start in audit mode (`validationActions: ["Audit"]`, Kyverno `Audit`) and switch to deny after reviewing reports.

## 7. Supply chain: digests and signatures

- Deploy by digest; resolve it in CI from the image you built and tested.
- Sign images in CI (for example `cosign sign --yes <image>@<digest>` with keyless OIDC) and verify at admission (Kyverno `verifyImages`, Sigstore policy-controller, or Connaisseur).
- Verify manually: `cosign verify <image>@<digest> --certificate-identity-regexp '<repo workflow>' --certificate-oidc-issuer https://token.actions.githubusercontent.com`.
- Scan images in CI and continuously in-cluster (see `dockerfile-optimise` rule `sec-scan-images`).

## 8. Secrets

- Enable encryption at rest for Secrets: an `EncryptionConfiguration` with a KMS provider (self-managed), or the provider's envelope-encryption option (EKS/GKE/AKS). Re-encrypt existing Secrets after enabling it.
- Prefer an external store synced in at runtime (External Secrets Operator, Secrets Store CSI Driver, Vault Agent; see `hashicorp-vault`) over Secrets committed to Git; if they must be in Git, encrypt them (Sealed Secrets, SOPS).
- Restrict `get/list/watch` on `secrets` to the workloads that need specific names (`resourceNames`).

## 9. Audit logging, scanning and runtime detection

- **Audit policy** (self-managed API server: `--audit-policy-file`, `--audit-log-path`; managed clusters: enable control-plane audit logs in the provider). Minimal policy:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: ["RequestReceived"]
rules:
  - level: Metadata                       # never log Secret bodies
    resources: [{ group: "", resources: ["secrets", "configmaps"] }]
  - level: RequestResponse
    resources: [{ group: "rbac.authorization.k8s.io" }]
  - level: Metadata
    verbs: ["create", "update", "patch", "delete"]
  - level: None
```

- **CIS benchmark**: `kube-bench` (run as a Job on nodes; use the managed-service profile on EKS/GKE/AKS).
- **Posture scan**: `kubescape scan` (NSA/CISA and MITRE frameworks) or `trivy k8s --report summary`.
- **Runtime detection**: Falco (or Tetragon) for shells in containers, unexpected outbound connections, writes below `/etc`, and token reads; route alerts to on-call.
- **Control plane and nodes**: keep the cluster on a supported minor version, restrict API server access (private endpoint or authorized networks), disable anonymous auth, restrict kubelet (`--anonymous-auth=false`, webhook authorization), and keep etcd unreachable from workloads with client TLS.

## Done when

- Every workload namespace enforces PSA `restricted` (or has a documented `baseline` exception).
- Each namespace has default-deny ingress and egress plus explicit allows, and DNS still resolves (`kubectl exec <pod> -- getent hosts kubernetes.default`).
- No non-admin subject holds the escalation grants above; workloads use dedicated service accounts with tokens mounted only where needed.
- Production admission rejects unpinned or unsigned images (test with a deliberately bad Deployment).
- Secrets are encrypted at rest, audit logs are flowing, and kube-bench/kubescape findings are triaged with owners.

## Related skills

- `operating-kubernetes` - resources, scheduling, autoscaling and troubleshooting.
- `security-hardening` - host, container runtime and cloud account hardening.
- `implementing-gitops` - delivering these policies declaratively.
- `hashicorp-vault` - external secrets source.

> Adapted from [BagelHole/DevOps-Security-Agent-Skills](https://github.com/BagelHole/DevOps-Security-Agent-Skills) (MIT) and substantially expanded.
