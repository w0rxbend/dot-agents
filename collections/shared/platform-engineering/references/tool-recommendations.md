# Platform Engineering Tool Recommendations

## Table of Contents

1. [Developer Portals](#developer-portals)
2. [Platform Orchestration](#platform-orchestration)
3. [GitOps Continuous Delivery](#gitops-continuous-delivery)
4. [Tool Selection Matrix](#tool-selection-matrix)

## Developer Portals

### Backstage (Open Source, CNCF)

**Core Features:**
- Software Catalog: YAML metadata, API for programmatic access
- Scaffolder: Cookiecutter-style templates, custom actions
- TechDocs: Markdown to static site (MkDocs)
- Plugin ecosystem: 100+ community plugins
- Search: full-text across catalog and docs

**Strengths:**
- Deep customization and control (open source)
- Large community, big plugin ecosystem
- No vendor lock-in
- Integrates any tooling via plugins
- Active development, frequent releases

**Challenges:**
- Complex setup, ongoing maintenance
- Needs dedicated platform engineering team
- Self-hosted infrastructure required
- Plugin development learning curve

**Estimated Costs:**
- Licensing: Free (open source)
- Infrastructure: $500-2000/month (Kubernetes cluster, databases)
- Team: 5-10 platform engineers ($1M-2M/year)
- Total: ~$1.5M-2.5M/year for 1000-engineer org

### Port (Commercial)

**Core Features:**
- Service catalogs with custom entity modeling
- Blueprints for entity types
- Self-service actions and workflows
- Workflows and automation
- Dashboards and visualizations
- Developer-facing APIs
- Scorecards for service quality

**Strengths:**
- Faster time-to-value than Backstage (3-6 months)
- Managed infrastructure (no ops burden)
- Modern UI/UX
- Good workflow automation
- Strong support and docs

**Challenges:**
- Commercial licensing costs
- Some vendor lock-in
- Smaller ecosystem than Backstage

**Estimated Costs:**
- Licensing: $50-150 per developer/month
- For 500 engineers: $25K-75K/month ($300K-900K/year)
- Small platform team: 2-3 engineers ($400K-600K/year)
- Total: ~$700K-1.5M/year

### Cortex (Commercial SaaS)

**Core Features:**
- Service catalog with compliance scoring
- Engineering best-practice enforcement
- Scorecards (service quality metrics)
- Leadership dashboards (org-wide insights)
- Incident management integration (PagerDuty, Opsgenie)

**Strengths:**
- Compliance focus (SOC2, GDPR, HIPAA)
- Service health scoring and tracking
- Fits regulated industries
- Leadership visibility

**Estimated Costs:**
- Enterprise pricing (contact for quote)
- Typically $100-200 per developer/month

## Platform Orchestration

### Crossplane (Open Source, CNCF)

**Overview:**
- Manages cloud infrastructure via Kubernetes APIs
- Composition functions for reusable abstractions

**Core Features:**
- Providers for AWS, Azure, GCP, GitHub, Datadog, more
- Compositions: reusable infrastructure abstractions
- Kubernetes-native (CRDs and controllers)
- GitOps-friendly (declarative YAML)
- Multi-cloud resources from one control plane

**Strengths:**
- Cloud-agnostic infrastructure management
- Kubernetes-native (familiar to K8s users)
- Open source, no vendor lock-in
- Strong community and ecosystem
- Works with existing GitOps tools (Argo CD, Flux)

**Challenges:**
- Learning curve (needs Kubernetes expertise)
- Provider maturity varies (AWS mature, others catching up)
- Too complex for simple use cases

**Estimated Costs:**
- Licensing: Free (open source)
- Infrastructure: runs on existing Kubernetes clusters
- Learning investment: 2-4 weeks team ramp-up

### Humanitec (Commercial)

**Overview:**
- Platform Orchestrator for infrastructure standardization
- Complements developer portals (Backstage + Humanitec common)

**Core Features:**
- Live Resource Graph: single source of truth for infrastructure
- Resource management (databases, caches, message queues)
- Environment management (dev, staging, prod with inheritance)
- Deployment pipelines with approval workflows
- Resource matching (dev uses in-cluster, prod uses managed cloud)

**Strengths:**
- Strong environment management
- Infrastructure abstraction across clouds
- Deployment standardization
- Good docs and support
- Integrates with Backstage and Port

**Challenges:**
- Commercial licensing
- Needs developer portal integration
- Learning curve for platform orchestrator concepts

**Estimated Costs:**
- Contact for pricing
- Typically $50-100 per developer/month

### HCP Terraform (Commercial, formerly Terraform Cloud)

**Overview:**
- Managed Terraform with workspace orchestration
- Remote state management

**Core Features:**
- Workspace management (separate state per environment)
- Remote execution (consistent environment, audit trail)
- Policy as code (Sentinel policies for compliance)
- Cost estimation before apply
- VCS integration (GitOps workflow)

**Strengths:**
- Mature IaC platform (Terraform ecosystem)
- Strong multi-cloud support

**Estimated Costs:**
- Free tier available
- Team tier: $20 per user/month
- Plus tier: custom enterprise pricing

## GitOps Continuous Delivery

### Argo CD (Open Source, CNCF) - RECOMMENDED

**Core Features:**
- Declarative GitOps (Git as single source of truth)
- Automated sync (Git to cluster)
- Multi-cluster application management
- ApplicationSets (template apps across clusters/environments)
- Progressive delivery (canary, blue-green via Argo Rollouts)
- Sync waves (ordered deployment steps)
- Health assessment (checks app health, not just deployment)
- RBAC and SSO integration

**Strengths:**
- Highest trust score (91.8/100), industry-proven
- Excellent docs and community
- Strong RBAC and security
- Active development, frequent releases
- Integrates with Backstage and other portals

**Challenges:**
- Kubernetes-only (no other platforms)
- Complex for very simple deployments

**Estimated Costs:**
- Licensing: Free (open source)
- Infrastructure: runs on Kubernetes (minimal overhead)
- Team: works with existing platform team

### Flux (Open Source, CNCF)

**Core Features:**
- Toolkit approach (composable controllers)
- Source Controller (Git, Helm, Bucket sources)
- Kustomize Controller (Kustomize builds)
- Helm Controller (Helm releases)
- Image automation (auto-updates image tags in Git)
- Notifications (alerts to Slack, GitHub)

**Strengths:**
- Kubernetes-native (minimal CRDs)
- Toolkit approach (use what you need)
- Strong Kustomize integration

**Challenges:**
- Less complete UI than Argo CD
- Toolkit needs more assembly

## Tool Selection Matrix

### Quick Selection Guide

**Choose Backstage when:**
- Large enterprise (1000+ engineers)
- Dedicated platform team (5-10 engineers)
- Deep customization required
- Open-source ecosystem preferred
- Long-term investment (3+ years)

**Choose Port when:**
- Mid-size org (100-1000 engineers)
- Faster time-to-value needed (3-6 months)
- Managed solution preferred
- Limited platform resources (<5 engineers)

**Choose Cortex when:**
- Regulated industry (finance, healthcare)
- Compliance focus (SOC2, HIPAA)
- Engineering standards enforcement needed

**Choose Crossplane when:**
- Multi-cloud infrastructure abstraction needed
- Kubernetes expertise available
- GitOps-native operations preferred

**Choose Humanitec when:**
- Complex environment management needed
- Platform orchestrator backend wanted
- Budget covers commercial tool

**Choose HCP Terraform when:**
- Already using Terraform heavily
- Policy enforcement needed (Sentinel)
- Multi-cloud IaC management

**Choose Argo CD when:**
- Kubernetes continuous delivery needed
- Multi-cluster management required
- Highest trust score tool wanted (91.8/100)
- GitOps best practices desired

**Choose Flux when:**
- Kubernetes-native GitOps preferred
- Toolkit/composable approach wanted
- Image automation needed

### Comparison Matrix

| Feature | Backstage | Port | Crossplane | Humanitec | Argo CD | Flux |
|---------|-----------|------|------------|-----------|---------|------|
| **Type** | Portal | Portal | Orchestration | Orchestration | GitOps | GitOps |
| **License** | Open Source | Commercial | Open Source | Commercial | Open Source | Open Source |
| **Best For** | Large orgs | Mid-size | Multi-cloud | Complex infra | K8s CD | K8s GitOps |
| **Time to Value** | 6-12 months | 3-6 months | 3-6 months | 3-6 months | 1-3 months | 1-3 months |
| **Customization** | Maximum | Good | High | Medium | Good | Good |
| **Vendor Lock-In** | None | Medium | None | High | None | None |
| **Team Size Needed** | 5-10 | 2-3 | 2-5 | 2-3 | 1-2 | 1-2 |

### Common Tool Combinations

**Combination 1: Open Source Stack**
- Portal: Backstage
- Orchestration: Crossplane
- GitOps: Argo CD
- Best for: large enterprises, maximum control, no vendor lock-in
- Total cost: $1.5M-2.5M/year (mostly team costs)

**Combination 2: Hybrid (Commercial Portal + Open Source Backend)**
- Portal: Port
- Orchestration: Crossplane
- GitOps: Argo CD
- Best for: mid-size orgs, faster portal time-to-value, open source backend
- Total cost: $700K-1.5M/year

**Combination 3: Hybrid (Open Source Portal + Commercial Orchestration)**
- Portal: Backstage
- Orchestration: Humanitec
- GitOps: Argo CD
- Best for: large orgs needing advanced environment management
- Total cost: $1.8M-3M/year

**Combination 4: Full Commercial Stack**
- Portal: Port
- Orchestration: Humanitec
- Best for: mid-size orgs, fastest time-to-value, vendor support
- Total cost: $1M-2M/year

### ROI Considerations

**Developer Productivity Gains:**
- Onboarding time cut from 2 weeks to 2 hours: 78 hours saved per developer
- 100 new hires/year: 7,800 hours = $400K saved (at $50/hour)

**Deployment Velocity:**
- Deployment frequency up from 1x/week to 10x/day: 50x increase
- Lead time down from 2 days to 2 hours: 12x faster

**Cost Optimization:**
- Infrastructure right-sizing: 20-40% cloud cost savings
- $1M/month cloud spend: $200K-400K/month saved = $2.4M-4.8M/year

**Total ROI:**
- Platform cost: $1M-2.5M/year
- Productivity gains: $400K/year (conservative)
- Cost optimization: $2.4M-4.8M/year
- Net ROI: $1.8M-3.7M/year positive

**Breakeven:**
- Typically 6-18 months, depending on org size and platform costs
