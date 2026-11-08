---
name: platform-engineering
description: "Design an internal developer platform - platform-as-product strategy, golden paths, developer portals (Backstage, Port), infrastructure orchestration (Crossplane), GitOps integration, maturity assessment and adoption. Use when planning or evolving an IDP or platform team; use implementing-gitops or operating-kubernetes for the underlying delivery and cluster work."
---

# Platform Engineering

## When to Use This Skill

Use when:
- Building or improving IDP
- Designing developer portal (Backstage, Port, or commercial IDP)
- Implementing golden paths and software templates
- Forming or restructuring platform engineering team
- Measuring and improving developer experience (DevEx)
- Integrating IDP with infrastructure, CI/CD, observability, or security tools
- Driving platform adoption across engineering organization
- Assessing platform maturity and capability gaps

## Core Concepts

### Platform as Product

Treat internal platforms with same rigor as customer-facing products:

**Product Management Approach:**
- Define platform vision, strategy, roadmap
- Identify developer "customers" and their pain points
- Measure success via adoption metrics, satisfaction surveys, business impact
- Iterate on feedback loops and usage analytics
- Balance new capabilities against reliability and support

**Key Differences from Traditional DevOps:**
- DevOps focuses on delivery pipelines; platform engineering builds full developer experiences
- Platform teams are product teams (product managers, UX designers, engineers)
- Success measured by developer productivity and satisfaction, not just infrastructure metrics
- Self-service is primary interface, not ticket queues

### Internal Developer Platform (IDP) Architecture

**Three-Layer Architecture:**

**1. Developer Portal (Frontend)**
- Service catalog: services with ownership, dependencies, health status
- Software templates: scaffolding with best practices baked in
- Documentation hub: centralized, searchable, version-controlled docs
- Self-service workflows: environment provisioning, deployments, access requests

**2. Platform Orchestration (Backend)**
- Infrastructure provisioning: multi-cloud resources
- Environment management: dev, staging, production lifecycle
- Deployment automation: GitOps continuous delivery
- Configuration management: app and infrastructure concerns kept separate

**3. Integration Layer (Glue)**
- CI/CD integration: pipeline visibility and triggering
- Observability: metrics, logs, traces in portal
- Security: vulnerability scanning, policy enforcement, secrets management
- FinOps: cost visibility, budgets, optimization recommendations

Architecture patterns, component breakdowns: see `references/idp-architecture.md`.

### Golden Paths and Scaffolding

**Golden Path Principle:**
Opinionated templates cover 80% of use cases. Escape hatches handle remaining 20%.

**Template Components:**
- Repository structure, boilerplate code
- Infrastructure as code (Kubernetes manifests, Terraform)
- CI/CD pipeline configuration
- Observability instrumentation (metrics, logging, tracing)
- Security configuration (RBAC, network policies, secrets)
- Documentation templates (README, runbooks, architecture diagrams)

**Constraint Mechanisms:**
- Policy-as-code enforcement (OPA, Kyverno) for security, compliance
- Resource limits and quotas against over-provisioning
- Required health checks and observability instrumentation
- Approved base images, dependency scanning

Template design patterns, examples: see `references/golden-paths.md`.

### Developer Experience (DevEx) Optimization

**Cognitive Load Reduction:**
- Abstract infrastructure complexity without hiding necessary details
- Sensible defaults, clear override mechanisms
- Progressive disclosure (simple for common cases, advanced options available)
- Consolidate tooling (one developer portal vs. 15+ separate tools)

**Key Metrics:**

**DORA Metrics:**
- Deployment frequency (how often code reaches production)
- Lead time for changes (commit to production)
- Mean time to recovery (MTTR for incidents)
- Change failure rate (share of deployments causing incidents)

**SPACE Framework:**
- Satisfaction: developer happiness via surveys, NPS
- Performance: throughput, efficiency of completed work
- Activity: commits, PRs, deployments (context, not raw counts)
- Communication: collaboration quality, discoverability
- Efficiency: fewer interruptions, less toil

**Platform-Specific Metrics:**
- Platform adoption rate (share of teams on platform)
- Self-service rate (actions done without platform team tickets)
- Onboarding time (new developer to first production deployment)
- Template usage (which golden paths get adopted)
- Support ticket volume, resolution time

## Platform Maturity Assessment

Assess current capabilities on 5-level maturity model:

**Level 0: Ad-Hoc** - Manual provisioning, no standardization
**Level 1: Basic Automation** - Some IaC and CI/CD, limited self-service
**Level 2: Paved Paths** - Golden path templates, early portal, limited coverage
**Level 3: Self-Service Platform** - Full portal, 80%+ self-service
**Level 4: Product-Driven Platform** - Data-driven, product team structure, FinOps integration
**Level 5: AI-Augmented Platform** - AI-assisted troubleshooting, predictive optimization

Assessment framework, gap analysis, improvement roadmap: see `references/maturity-model.md`.

## Decision Frameworks

### Build vs. Buy IDP

**Choose Open Source (Backstage) when:**
- Large enterprise (1000+ engineers)
- Dedicated platform team (5-10 engineers)
- Deep customization needed
- Open-source ecosystem preferred
- Long-term investment (3+ year horizon)

**Choose Commercial IDP (Port, Humanitec, Cortex) when:**
- Mid-size organization (100-1000 engineers)
- Faster time-to-value needed (3-6 months vs. 6-12 months)
- Managed solution with vendor support preferred
- Small platform engineering team (<5 engineers)
- Standard use cases (web apps, microservices, CI/CD)

**Choose Hybrid Approach when:**
- Large organization needs both flexibility and speed
- Complex infrastructure needs orchestration backend
- Best-in-class portal + orchestration components wanted
- Willing to integrate multiple systems (e.g., Backstage + Humanitec)

Decision tree, selection criteria, ROI calculations: see `references/decision-frameworks.md`.

### Golden Path Design: Flexibility vs. Standardization

**Spectrum of Control:**

**High Standardization (Regulated Industries):**
- Limited technology choices, mandatory templates
- Policy enforcement via admission controllers (OPA, Kyverno)
- Escape hatches require approval

**Balanced Approach (Recommended for Most):**
- Recommended golden paths (easy, well-documented, supported)
- Alternatives allowed with documentation
- Soft enforcement (defaults + education, not hard blocks)
- Clear ownership for deviations ("deviate and own")

**High Flexibility (Innovative Organizations):**
- Golden paths as suggestions (not requirements)
- Minimal policy enforcement (only critical security)
- "Build it, run it" ownership model

Choosing balance and enforcement strategies: see `references/decision-frameworks.md`.

### Platform Team Structure

**Centralized Model:**
- Single platform team (5-20 engineers) serving whole organization
- Best for: small to mid-size orgs (100-500 engineers)

**Federated Model:**
- Central team (5-10 engineers) + embedded engineers (1-2 per business unit)
- Best for: large orgs (500-2000+ engineers), multiple business units

**Hub-and-Spoke Model:**
- Central "hub" team (3-5 engineers) + "spoke" teams contributing plugins
- Best for: organizations with strong open-source culture

Team sizing, roles, responsibilities, governance models: see `references/decision-frameworks.md`.

## Tool Recommendations

### Developer Portals

**Backstage** (Open Source, CNCF)
- Software catalog, scaffolder, TechDocs, plugin ecosystem
- Recommended for: enterprises with platform teams

**Port** (Commercial)
- Managed platform, modern UI/UX, faster time-to-value
- Recommended for: mid-size orgs (100-1000 engineers)

**Cortex** (Commercial SaaS)
- Enterprise IDP, compliance focus, engineering standards enforcement
- Recommended for: regulated industries

### Platform Orchestration

**Crossplane** (Open Source, CNCF)
- Universal control plane for multi-cloud
- Kubernetes-native declarative infrastructure
- Recommended for: multi-cloud abstractions

**Humanitec** (Commercial)
- Platform Orchestrator backend, environment and deployment management
- Recommended for: complex infrastructure, complements portals

**HCP Terraform** (Commercial, formerly Terraform Cloud)
- Mature IaC orchestration, workspace management
- Recommended for: Terraform-heavy organizations

### GitOps Continuous Delivery

**Argo CD** (Open Source, CNCF) - **RECOMMENDED**
- Declarative GitOps for Kubernetes, multi-cluster management
- Large community, thorough documentation

**Flux** (Open Source, CNCF)
- Toolkit approach, Kubernetes-native
- Good for: GitOps-native operations

Tool comparisons, integration patterns, selection criteria: see `references/tool-recommendations.md`.

## Implementation Guides

### Bootstrapping a Platform

**Foundation Phase (Months 1-3):**
1. Define platform vision; form platform team (3-5 members)
2. Interview developers to find pain points
3. Set up developer portal (Backstage or commercial)
4. Create initial service catalog and first golden path template

**Pilot Phase (Months 4-6):**
1. Pick 2-3 pilot teams for white-glove onboarding
2. Iterate fast on feedback
3. Expand to 3-5 golden path templates
4. Integrate key tools (CI/CD, monitoring, secrets)

**Expansion Phase (Months 7-12):**
1. Scale to 20-50% of engineering teams
2. Build self-service documentation and training
3. Set platform SLOs and on-call rotation
4. Internal evangelization (demos, champions program)

**Maturity Phase (Year 2+):**
1. 80%+ adoption across organization
2. Platform team runs as product team
3. Continuous improvement via metrics and feedback
4. AI-assisted capabilities, policy-as-code expansion

Implementation steps, bootstrapping code: see `references/implementation-backstage.md`.

### Creating Golden Path Templates

**Template Design Process:**
1. Identify most common use case (web app, API, data pipeline)
2. Define opinionated choices (language, framework, deployment pattern)
3. Create repository structure and infrastructure manifests
4. Configure CI/CD pipeline with security scanning
5. Instrument observability; document usage
6. Test with pilot team before broad rollout

**Template Categories:**
- Full-stack web application (backend API + frontend + database)
- Data pipeline (ETL/ELT with orchestration)
- Machine learning service (model serving, monitoring)
- Event-driven microservice (message broker integration)
- Scheduled job (cron jobs, batch processing)

Template examples, scaffolding code, customization patterns: see `references/golden-paths.md` and `examples/` directory.

### Driving Platform Adoption

**Evangelization Strategies:**
- Showcase pilot team successes (internal blog posts, demos)
- Lunch-and-learns on platform capabilities
- Internal champions program (power users help peers)
- Office hours, Slack/Teams support channels

**Incentive Alignment:**
- Make platform easier than alternatives (golden paths are "paved roads")
- Integrate with workflows developers already use
- Deliver immediate value (faster onboarding, better visibility)

Adoption metrics, tracking dashboards, success patterns: see `references/maturity-model.md`.

## Quick Reference

### Platform Engineering Checklist

**Strategy and Vision:**
- [ ] Platform vision and charter documented
- [ ] Platform team formed with clear roles
- [ ] Developer pain points identified via interviews
- [ ] Success metrics defined (DORA, SPACE, adoption)

**IDP Foundation:**
- [ ] Developer portal deployed (Backstage, Port, or commercial)
- [ ] Service catalog established (ownership, dependencies, health)
- [ ] First golden path template created and validated
- [ ] Documentation hub open to all engineers

**Self-Service Capabilities:**
- [ ] Environment provisioning (dev, staging, production)
- [ ] Deployment automation (GitOps with Argo CD or Flux)
- [ ] CI/CD integration visible in portal
- [ ] Per-service observability dashboards

**Security and Compliance:**
- [ ] Policy-as-code enforcement (OPA, Kyverno)
- [ ] Secrets management integrated (Vault, cloud providers)
- [ ] Vulnerability scanning in pipelines
- [ ] RBAC and access controls configured

**Operations and Support:**
- [ ] Platform SLOs defined and monitored
- [ ] Support channels established (Slack, office hours)
- [ ] Incident response playbooks documented
- [ ] Feedback loops and usage analytics in place

### Common Pitfalls

- **Building too much upfront:** start small (1 golden path, pilot team), iterate; avoid "boil the ocean" syndrome
- **Ignoring developer feedback:** continuous feedback loops, not just quarterly surveys
- **Over-standardization:** clear escape hatches for advanced use cases
- **Under-measuring success:** track DORA metrics, satisfaction surveys, self-service rates
- **Treating platform as IT project:** platform engineering is product development, not infrastructure provisioning; needs product managers, UX designers, customer focus

## Integration with Other Skills

**Related Skills:**

- `operating-kubernetes`: cluster operations, namespace management, RBAC, network policies
- `pulumi-components` / `pulumi-stacks`: infrastructure provisioning integrated with platform
- `implementing-gitops`: Argo CD / Flux implementation patterns
- `building-ci-pipelines`: CI/CD pipeline design for platform templates
- `security-hardening` / `kubernetes-hardening`: security defaults enforced through golden paths
- `hashicorp-vault`: secrets management integrated into platform
- `implementing-observability`: monitoring, logging, tracing in developer portal

**Cross-Skill Workflows:**

**Platform Bootstrapping:**
1. Provision platform infrastructure with `pulumi-stacks` (or your IaC tool)
2. Configure clusters with `operating-kubernetes`
3. Deploy developer portal (Backstage) on platform infrastructure
4. Integrate `implementing-gitops` (Argo CD) for continuous delivery
5. Add `implementing-observability` integrations (Prometheus, Grafana plugins)

**Golden Path Creation:**
1. Design template around common use case
2. Use `building-ci-pipelines` patterns for CI/CD configuration
3. Apply `security-hardening` best practices (SAST, container scanning)
4. Integrate `hashicorp-vault` (or cloud secret manager)
5. Add `observability-and-instrumentation` defaults (metrics, logging, tracing)

## Example Use Cases

Illustrative scenarios, not measured case studies. "Target outcomes" show goals to set, not results to promise.

### Use Case 1: E-Commerce Platform Team

**Context:** 300-engineer e-commerce company, microservices architecture, manual provisioning causes bottlenecks.

**Approach:** Deploy Backstage, create 3 golden paths, integrate Argo CD, pilot with 3 teams, expand to 20 teams over 6 months.

**Target outcomes:** Onboarding time 2 days → 2 hours, deployment frequency 2x/week → 10x/day, developer NPS +35.

### Use Case 2: Financial Services Platform

**Context:** 1500-engineer bank, strict compliance, legacy infrastructure, fragmented tooling.

**Approach:** Adopt Port (commercial), high standardization golden paths, OPA Gatekeeper, federated model, HCP Terraform.

**Target outcomes:** Compliance audit prep 3 weeks → 3 days, infrastructure drift incidents 90% reduction, per-service cost attribution.

### Use Case 3: Startup Platform

**Context:** 50-engineer startup, rapid growth, needs fast developer onboarding.

**Approach:** No self-hosted portal yet (README-based service catalog or managed portal), 2 golden paths as repo templates, GitHub Actions, PaaS infrastructure (Fly.io), documentation focus.

**Target outcomes:** New engineer to production 1 day (vs. 2 weeks), 100% self-service, 2 engineers supporting 50 developers. Revisit full Backstage deployment only once organization nears Build vs. Buy scale above.
