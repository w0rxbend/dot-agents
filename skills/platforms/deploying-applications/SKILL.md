---
name: deploying-applications
description: "Choose where and how to deploy an application - Kubernetes, managed containers, serverless, edge or PaaS - plus the IaC tool and rollout strategy, then route to the platform-specific skill. Use at the start of a deployment decision or migration; use deploying-on-aws/azure/gcp, operating-kubernetes or implementing-gitops for the implementation itself."
---

# Deploying Applications

## 1. Gather the inputs

Answer before choosing. Ask when unknown.

| Question | Why it matters |
|---|---|
| Number of services; team to run a cluster? | Kubernetes pays off with many services and platform staff, rarely before |
| Traffic shape: steady, spiky, near zero at night? | Spiky or idle favors scale-to-zero (serverless, Cloud Run) |
| Latency target and user geography | Global sub-50ms reads favor edge runtimes and replicated data |
| Long-running work, WebSockets, background workers? | Rules out short-timeout function platforms |
| State: which database, where must data live? | Data residency and connection limits constrain compute placement |
| Existing cloud account, compliance scope, budget | Usually decides provider before any technical argument |
| Who operates it at 03:00? | Managed platforms trade control for less on-call load |

## 2. Choose the target

| Workload | Default target | Implement with |
|---|---|---|
| Many services, platform team, custom networking/operators needed | Kubernetes (EKS/GKE/AKS) with GitOps | `operating-kubernetes`, `implementing-gitops`, `kubernetes-hardening` |
| A few containerized services, steady load | Managed containers (ECS Fargate, Cloud Run, Azure Container Apps) | `deploying-on-aws`, `deploying-on-gcp`, `deploying-on-azure` |
| Spiky or low traffic, stateless request/response | Functions (Lambda, Cloud Run functions, Azure Functions) | cloud skill for that provider |
| Global low-latency reads, light compute | Edge runtimes (Cloudflare Workers, Deno Deploy) | [references/edge-functions.md](references/edge-functions.md) |
| Frontend or full-stack framework app (Next.js etc.), small team | PaaS (Vercel, Netlify, Render, Railway, Fly.io) | platform's docs; Render has own skills collection |
| Single host, small internal tool | Docker Compose on a VM | `docker-compose-production` |

Prefer simplest target that meets requirements. Move up to Kubernetes when concrete needs appear (many services, custom scheduling, operators, multi-tenant platform).

## 3. Choose the IaC tool

| Situation | Tool |
|---|---|
| Team writes TypeScript/Python/Go, wants real languages | Pulumi (`pulumi-components`, `pulumi-stacks`, [references/pulumi-guide.md](references/pulumi-guide.md)) |
| HCL ecosystem, existing Terraform modules | OpenTofu or Terraform ([references/opentofu-guide.md](references/opentofu-guide.md)) |
| AWS-only, CloudFormation-native shops | AWS CDK / CloudFormation (`deploying-on-aws`) |
| Azure-only | Bicep (`deploying-on-azure`) |
| Kubernetes application manifests | Helm or Kustomize, delivered by Argo CD/Flux (`implementing-gitops`) |

Keep application deploys (image version changes) separate from infrastructure changes. Different cadence and blast radius.

## 4. Choose the rollout strategy

| Strategy | Use when | Needs |
|---|---|---|
| Rolling | Default for stateless services | Health checks; backward-compatible changes |
| Blue-green | Instant rollback required | Double capacity during switch; shared DB must work with both versions |
| Canary | Risky changes, large traffic | Traffic splitting, metrics-based promotion (Argo Rollouts, Flagger, ALB weights) |
| Recreate | Singleton or schema-incompatible versions | Accepted downtime window |
| Feature flags | Decouple deploy from release | Flag service, cleanup discipline (`shipping-and-launch`) |

Details and manifests: [references/deployment-strategies.md](references/deployment-strategies.md). DB schema changes use expand-and-contract, so old and new versions run side by side.

## 5. Record and hand off

Write short decision record with `documentation-and-adrs`: target, IaC tool, rollout strategy, rejected options and why. Then continue with implementation skill from tables above. CI that builds and tests artifact: `building-ci-pipelines`. Pre-launch checklist: `shipping-and-launch`.

## Safety

- State-changing commands (`kubectl apply/delete`, `argocd app sync`, `pulumi up/destroy`, `tofu apply/destroy`, `wrangler deploy`, `pscale deploy-request deploy`, DB branch deletes): show diff/plan, confirm with user first. Never production without approval.
- Secrets: never print, echo or commit. Capture into env vars or pipe into secret store; user runs commands that reveal passwords/tokens.
- Install CLIs via package manager; apply manifests only from pinned release tags, reviewed before apply.
- Some CLIs send telemetry by default; opt out first: `WRANGLER_SEND_METRICS=false`, `neonctl --no-analytics`, Terraform `CHECKPOINT_DISABLE=1`, Linkerd `--set disableHeartBeat=true`.

## Reference material in this skill

- [references/kubernetes-patterns.md](references/kubernetes-patterns.md) - Helm packaging, service mesh trade-offs, autoscaling
- [references/gitops-argocd.md](references/gitops-argocd.md) - Argo CD and Flux workflows
- [references/serverless-dbs.md](references/serverless-dbs.md) - scale-to-zero databases (Neon, Turso and similar) for serverless/edge compute
- [references/edge-functions.md](references/edge-functions.md) - Cloudflare Workers, Deno Deploy, Hono
- [references/pulumi-guide.md](references/pulumi-guide.md), [references/opentofu-guide.md](references/opentofu-guide.md) - IaC patterns, Terraform-to-OpenTofu migration
- [examples/pulumi-aws/](examples/pulumi-aws/) - ECS Fargate service with Pulumi
- [examples/k8s-argocd/](examples/k8s-argocd/) - Kubernetes base manifests with Argo CD application
- `scripts/generate_k8s_manifests.py --app-name my-app --image <registry>/<image>@sha256:<digest> --enable-hpa` - starter Deployment/Service/HPA manifests, non-root restricted securityContext (review before use; `--image` required, pin by digest)
- `scripts/validate_deployment.py --config deployment.yaml [--strict]` - check manifest for missing probes, limits and similar issues

## Done when

- Target, IaC tool and rollout strategy chosen, with step 1 inputs written down.
- Rejected alternatives and conditions that would change decision recorded.
- Next skill (cloud, Kubernetes, GitOps or Compose) and owner operating the result named.
