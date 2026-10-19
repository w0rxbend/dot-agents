---
name: deploying-applications
description: "Choose where and how to deploy an application - Kubernetes, managed containers, serverless, edge or PaaS - plus the IaC tool and rollout strategy, then route to the platform-specific skill. Use at the start of a deployment decision or migration; use deploying-on-aws/azure/gcp, operating-kubernetes or implementing-gitops for the implementation itself."
---

# Deploying Applications

Pick the deployment target, IaC tool and rollout strategy for a workload, record the decision, then hand off to the skill that implements it.

## 1. Gather the inputs

Answer these before choosing; ask when they are unknown.

| Question | Why it matters |
|---|---|
| Number of services, and is there a team to run a cluster? | Kubernetes pays off with many services and platform staff, rarely before |
| Traffic shape: steady, spiky, near zero at night? | Spiky or idle favors scale-to-zero (serverless, Cloud Run) |
| Latency target and user geography | Global sub-50ms reads favor edge runtimes and replicated data |
| Long-running work, WebSockets, background workers? | Rules out short-timeout function platforms |
| State: which database, and where must data live? | Data residency and connection limits constrain compute placement |
| Existing cloud account, compliance scope, budget | Usually decides the provider before any technical argument |
| Who operates it at 03:00? | Managed platforms trade control for less on-call load |

## 2. Choose the target

| Workload | Default target | Implement with |
|---|---|---|
| Many services, platform team, need for custom networking/operators | Kubernetes (EKS/GKE/AKS) with GitOps | `operating-kubernetes`, `implementing-gitops`, `kubernetes-hardening` |
| A few containerized services, steady load | Managed containers (ECS Fargate, Cloud Run, Azure Container Apps) | `deploying-on-aws`, `deploying-on-gcp`, `deploying-on-azure` |
| Spiky or low traffic, stateless request/response | Functions (Lambda, Cloud Run functions, Azure Functions) | the cloud skill for that provider |
| Global low-latency reads, light compute | Edge runtimes (Cloudflare Workers, Deno Deploy) | [references/edge-functions.md](references/edge-functions.md) |
| Frontend or full-stack framework app (Next.js etc.), small team | PaaS (Vercel, Netlify, Render, Railway, Fly.io) | the platform's docs; Render has its own skills collection |
| Single host, small internal tool | Docker Compose on a VM | `docker-compose-production` |

Prefer the simplest target that meets the requirements; move up to Kubernetes when concrete needs (many services, custom scheduling, operators, multi-tenant platform) appear.

## 3. Choose the IaC tool

| Situation | Tool |
|---|---|
| Team writes TypeScript/Python/Go and wants real languages | Pulumi (`pulumi-components`, `pulumi-stacks`, [references/pulumi-guide.md](references/pulumi-guide.md)) |
| HCL ecosystem, existing Terraform modules | OpenTofu or Terraform ([references/opentofu-guide.md](references/opentofu-guide.md)) |
| AWS-only, CloudFormation-native shops | AWS CDK / CloudFormation (`deploying-on-aws`) |
| Azure-only | Bicep (`deploying-on-azure`) |
| Kubernetes application manifests | Helm or Kustomize, delivered by Argo CD/Flux (`implementing-gitops`) |

Keep application deploys (image version changes) separate from infrastructure changes; they have different cadence and blast radius.

## 4. Choose the rollout strategy

| Strategy | Use when | Needs |
|---|---|---|
| Rolling | Default for stateless services | Health checks; backward-compatible changes |
| Blue-green | Instant rollback required | Double capacity during switch; shared DB must work with both versions |
| Canary | Risky changes, large traffic | Traffic splitting and metrics-based promotion (Argo Rollouts, Flagger, ALB weights) |
| Recreate | Singleton or schema-incompatible versions | Accepted downtime window |
| Feature flags | Decouple deploy from release | Flag service and cleanup discipline (`shipping-and-launch`) |

Details and manifests: [references/deployment-strategies.md](references/deployment-strategies.md). Database schema changes use expand-and-contract so old and new versions run side by side.

## 5. Record and hand off

Write a short decision record (target, IaC tool, rollout strategy, rejected options and why) with `documentation-and-adrs`, then continue with the implementation skill from the tables above. CI that builds and tests the artifact belongs to `building-ci-pipelines`; the pre-launch checklist to `shipping-and-launch`.

## Reference material in this skill

- [references/kubernetes-patterns.md](references/kubernetes-patterns.md) - Helm packaging, service mesh trade-offs, autoscaling
- [references/gitops-argocd.md](references/gitops-argocd.md) - Argo CD and Flux workflows
- [references/serverless-dbs.md](references/serverless-dbs.md) - scale-to-zero databases (Neon, Turso and similar) for serverless/edge compute
- [references/edge-functions.md](references/edge-functions.md) - Cloudflare Workers, Deno Deploy, Hono
- [references/pulumi-guide.md](references/pulumi-guide.md), [references/opentofu-guide.md](references/opentofu-guide.md) - IaC patterns and Terraform-to-OpenTofu migration
- [examples/pulumi-aws/](examples/pulumi-aws/) - ECS Fargate service with Pulumi
- [examples/k8s-argocd/](examples/k8s-argocd/) - Kubernetes base manifests with an Argo CD application
- `scripts/generate_k8s_manifests.py --app-name my-app --image <registry>/<image>@sha256:<digest> --enable-hpa` - starter Deployment/Service/HPA manifests (review before use; pass a pinned image, the default is a placeholder)
- `scripts/validate_deployment.py --config deployment.yaml [--strict]` - check a manifest for missing probes, limits and similar issues

## Done when

- The target, IaC tool and rollout strategy are chosen with the inputs from step 1 written down.
- Rejected alternatives and the conditions that would change the decision are recorded.
- The next skill (cloud, Kubernetes, GitOps or Compose) and the owner for operating the result are named.
