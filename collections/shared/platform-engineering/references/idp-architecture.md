# Internal Developer Platform (IDP) Architecture

## Table of Contents

1. [Three-Layer Architecture](#three-layer-architecture)
2. [Developer Portal Layer](#developer-portal-layer)
3. [Platform Orchestration Layer](#platform-orchestration-layer)
4. [Integration Layer](#integration-layer)
5. [Reference Architecture Diagrams](#reference-architecture-diagrams)

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Developer Portal (Frontend Layer)              │
│  - Service Catalog    - Software Templates             │
│  - Documentation Hub  - Workflow Automation             │
└─────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────┐
│         Integration Layer (Glue)                        │
│  - API Gateway      - CI/CD Integration                 │
│  - Observability    - Security Integration              │
│  - FinOps           - Secrets Management                │
└─────────────────────────────────────────────────────────┘
                          ↓ ↑
┌─────────────────────────────────────────────────────────┐
│         Platform Orchestration (Backend Layer)          │
│  - Infrastructure Provisioning                          │
│  - Environment Management                               │
│  - Deployment Automation (GitOps)                       │
└─────────────────────────────────────────────────────────┘
```

## Developer Portal Layer

### Purpose

One interface for developers to discover, create and manage services without knowing underlying infrastructure.

### Core Components

#### 1. Service Catalog

**Features:**
- Software inventory (services, APIs, libraries, data pipelines, ML models)
- Ownership tracking (teams, individuals, on-call rotation)
- Dependency mapping (upstream/downstream, service mesh topology)
- Health and SLO status (real-time metrics, historical trends)
- Documentation links (architecture diagrams, runbooks, API specs)
- Metadata (tech stack, cloud provider, cost attribution)

**Examples:**

**Backstage Software Catalog:**
- YAML metadata files in service repositories
- API for programmatic access
- Plugins for enrichment (pull deployment status, cost data)
- Discovery: automatic repository scanning

**Port Service Catalog:**
- Entity modeling (custom entities beyond services)
- Blueprints for entity types
- Scorecards (track service quality, compliance)

**Cortex Service Catalog:**
- Compliance scoring against best practices
- Incident management integration (PagerDuty, Opsgenie)
- Service health scoring

#### 2. Software Templates / Scaffolders

**Function:** Initialize projects with best practices, infrastructure and CI/CD config baked in.

**Template Components:**
- Repository structure (monorepo vs. polyrepo, directory layout)
- App boilerplate (framework setup, starter files)
- Infrastructure as code (Kubernetes manifests, Terraform modules)
- CI/CD pipeline config (GitHub Actions workflows, GitLab CI YAML)
- Observability instrumentation (Prometheus metrics, structured logging, OpenTelemetry tracing)
- Security config (RBAC, network policies, secrets references)
- Doc templates (README, runbooks, architecture diagrams, API docs)

**Examples:**

**Backstage Scaffolder:**
- Cookiecutter/Yeoman-style templates
- Template inputs (service name, tech stack, deployment environment)
- Actions: create repository, scaffold code, configure CI/CD, register in catalog
- Template composition (base template + mixins)

**Humanitec Resource Packs:**
- Infrastructure abstractions (database, cache, message queue)
- Cloud-agnostic resource definitions
- Auto-provisioning on deployment

**Template Versioning:**
- Version templates (v1.0, v2.0)
- Migration guides when templates change
- Deprecation notices for old templates

#### 3. Documentation Hub

**Features:**
- Central docs (architecture, tutorials, runbooks, API specs)
- Version-controlled (docs-as-code, Git-backed, PR workflow)
- Search and discovery (full-text, tags, categories)
- Auto-generated docs (API specs from OpenAPI, dependency graphs)
- Metrics (doc views, staleness detection)

**Examples:**

**Backstage TechDocs:**
- Markdown + MkDocs
- Docs live next to code in repositories
- Auto build and publish on commit
- Search across all docs

**GitBook / Confluence Integrations:**
- Embed external docs in portal
- Single pane of glass for all docs

**Swagger/OpenAPI Integrations:**
- Auto-generate API docs from specs
- Interactive API exploration

#### 4. Workflow Automation

**Capabilities:**
- Self-service actions (create environment, deploy service, request database access)
- Approval workflows (production access needs manager approval)
- Ticketing integration (Jira, ServiceNow for non-self-service requests)
- ChatOps integrations (Slack, Microsoft Teams for bot-driven workflows)

**Examples:**

**Port Self-Service Actions:**
- Define actions in UI
- Trigger via API, portal or Slack
- Configurable approval steps

**Backstage Custom Plugins:**
- React components for custom actions
- API calls to platform services (Kubernetes API, HCP Terraform)
- Feedback to user (action status, logs)

**Humanitec Deployment Pipelines:**
- One-click deploy to environment
- Environment diff before deploy
- Auto rollback on failure

## Platform Orchestration Layer

### Purpose

Manage infrastructure provisioning, environment lifecycle and deployment automation without exposing raw cloud APIs to developers.

### Core Components

#### 1. Infrastructure Orchestration

**Capabilities:**
- Multi-cloud resource provisioning (AWS, Azure, GCP, on-prem)
- Kubernetes cluster management (namespaces, RBAC, network policies, resource quotas)
- Resource abstraction (developer requests "database", platform provisions RDS/Cloud SQL/etc.)
- Configuration management (app config separate from infrastructure config)

**Examples:**

**Crossplane:**
- Universal control plane for Kubernetes
- Providers for clouds (AWS, Azure, GCP), services (GitHub, Datadog)
- Compositions: reusable infrastructure abstractions
- Kubernetes-native (CRDs, controllers)

**Humanitec Platform Orchestrator:**
- Resource management (databases, caches, message queues)
- Resource matching (dev uses in-cluster Postgres, prod uses managed RDS)
- Live Resource Graph: single source of truth for all resources

**HCP Terraform:**
- Workspace orchestration (separate state per environment/service)
- Remote execution (consistent environment, audit trail)
- Policy as code (Sentinel policies for compliance)

**Pulumi Automation API:**
- Programmatic infrastructure management
- Multi-language (TypeScript, Python, Go)
- State management and diffs

#### 2. Environment Management

**Environment Types:**
- Development: developer-owned, permissive policies, frequent deployments, auto-cleanup
- Staging: pre-production testing, production-like config, automated integration tests
- Production: strict policies, approval workflows, automated rollback, immutable infrastructure

**Capabilities:**
- Ephemeral environments (per-PR preview deployments, on-demand test environments)
- Environment promotion pipelines (dev → staging → prod, automated or manual)
- Config drift detection (actual vs. desired state)
- Config drift remediation (auto-fix or alert)

**Examples:**

**Humanitec Environment Manager:**
- Environment types with inheritance (base config + overrides)
- Automatic environment creation
- Environment diff (what changes between dev and prod)

**Kubernetes Namespaces + GitOps:**
- Namespace per environment
- Argo CD ApplicationSets (template environments)
- Kustomize overlays (base + environment-specific overrides)

**Cloud Provider Environments:**
- AWS Environments (isolated accounts)
- Azure Management Groups (subscription hierarchy)
- GCP Folders (project organization)

#### 3. Deployment Automation

**Principles:**
- GitOps-based continuous delivery (Git as source of truth)
- Progressive delivery (canary, blue-green, rolling updates)
- Deployment policies (require approval, automated testing, gradual rollout)
- Rollback (automatic on failure, manual trigger, keep last N versions)

**Examples:**

**Argo CD:**
- GitOps for Kubernetes (declarative desired state in Git)
- Multi-cluster app management
- ApplicationSets for templated deployments
- Sync waves for ordered rollouts
- Health assessment (checks app works, not just deployed)

**Flux:**
- Toolkit approach (composable controllers)
- Image automation (auto-update image tags in Git)
- Notifications (alerts to Slack, GitHub, etc.)

**Humanitec Deployment Pipelines:**
- Environment-aware deployments
- Approval gates (manual approval before prod)
- Automated testing integration (deploy → run tests → promote)

**Spinnaker:**
- Advanced deployment strategies (canary analysis, blue-green, rolling)
- Multi-cloud
- Pipeline as code (JSON/YAML)

## Integration Layer

### Purpose

Connect developer portal with underlying infrastructure, CI/CD, observability, security and FinOps tools.

### Core Components

#### 1. API Gateway / Abstraction Layer

**Features:**
- Unified API for platform capabilities (hides underlying tool complexity)
- Authentication and authorization (SSO, RBAC, API keys)
- Rate limiting and quotas (prevent abuse, fair usage)
- API versioning and deprecation (backward compatibility, migration paths)

**Examples:**

**Kubernetes API Server:**
- Platform-native for Kubernetes resources
- RBAC for fine-grained permissions
- Admission controllers for policy enforcement

**Backstage Backend API:**
- REST API for catalog, scaffolder, auth
- Plugin backend APIs

**Custom API Gateways:**
- Kong, Tyk, AWS API Gateway
- Aggregate multiple backends
- Transform requests/responses

#### 2. CI/CD Integration

**Features:**
- Pipeline status (in-progress, failed, succeeded)
- Trigger builds/deployments from portal
- Artifact management (container registry, package repositories)
- Test results and quality gates (unit tests, integration tests, security scans)

**Examples:**

**Backstage CI/CD Plugins:**
- GitHub Actions plugin (workflow runs)
- GitLab CI plugin (pipeline status)
- Jenkins plugin (job history)
- CircleCI plugin

**Argo Workflows:**
- Kubernetes-native CI
- DAG-based workflows
- Artifact passing between steps

**Tekton:**
- Cloud-native CI/CD (Kubernetes CRDs)
- Reusable tasks and pipelines

#### 3. Observability Integration

**Features:**
- Metrics dashboards in portal (per-service, per-team, per-environment)
- Log aggregation and search (centralized logging, grep/filter)
- Distributed tracing (request path visualization, latency breakdown)
- Alerting and on-call management (PagerDuty, Opsgenie integration)

**Examples:**

**Backstage Prometheus/Grafana Plugins:**
- Embed Grafana dashboards
- Prometheus metrics per service

**Commercial Observability:**
- Datadog plugin (APM, logs, metrics in one place)
- New Relic plugin
- Splunk integration

**OpenTelemetry:**
- Standard instrumentation across languages
- Vendor-agnostic telemetry collection
- Auto-instrumentation in golden paths

#### 4. Security Integration

**Features:**
- Vulnerability scanning (container images, dependencies, IaC)
- Policy enforcement (OPA, Kyverno for Kubernetes)
- Secrets management (Vault integration, encrypted configs, rotation)
- Compliance reporting (SOC2, GDPR, HIPAA dashboards)

**Examples:**

**Backstage Security Insights Plugins:**
- Vulnerability scan results
- Dependency security scores
- Compliance status per service

**Scanning Tools:**
- Snyk (container and dependency scanning)
- Trivy (comprehensive vulnerability scanner)
- Aqua, Twistlock (runtime security)

**Policy Engines:**
- OPA Gatekeeper (Kubernetes admission control)
- Kyverno (policy as Kubernetes resources)
- Cloud Custodian (cloud resource policies)

**Secrets Management:**
- HashiCorp Vault (dynamic secrets, encryption as a service)
- AWS Secrets Manager, Azure Key Vault, GCP Secret Manager
- External Secrets Operator (sync cloud secrets to Kubernetes)

#### 5. FinOps Integration

**Features:**
- Cost visibility (per-service, per-team, per-environment, per-deployment)
- Budget alerts (spending thresholds, trend analysis)
- Right-sizing recommendations (over-provisioned or unused resources)
- Resource lifecycle management (auto-delete unused resources, hibernation)

**Examples:**

**Backstage Cost Insights Plugin:**
- Cost per service
- Compare cost across teams
- Trend analysis

**Cloud Provider Cost Tools:**
- AWS Cost Explorer (detailed cost breakdown)
- Azure Cost Management (budgets, recommendations)
- GCP Cost Management (cost attribution, forecasting)

**Kubernetes Cost Tools:**
- Kubecost (cost allocation per namespace, pod, label)
- OpenCost (open-source Kubernetes cost monitoring)

**Infrastructure Cost Estimation:**
- Infracost (IaC cost estimation before deployment)
- Terraform cost estimation modules

## Reference Architecture Diagrams

### Full-Stack IDP Architecture (Backstage + Crossplane + Argo CD)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Portal (Backstage)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Service    │  │   Software   │  │  TechDocs    │          │
│  │   Catalog    │  │   Templates  │  │  (Markdown)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CI/CD      │  │ Observability│  │  Cost        │          │
│  │   Status     │  │  Dashboards  │  │  Insights    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓ API Calls
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Clusters                          │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Crossplane (Infrastructure Orchestration)          │        │
│  │  - Providers: AWS, Azure, GCP                       │        │
│  │  - Compositions: Reusable resource abstractions     │        │
│  └─────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Argo CD (GitOps Continuous Delivery)              │        │
│  │  - Sync Git → Cluster                               │        │
│  │  - ApplicationSets for multi-env                    │        │
│  └─────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Application Workloads                              │        │
│  │  - Deployments, Services, Ingresses                 │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Cloud Providers                              │
│  AWS (RDS, S3, EKS)  │  Azure (CosmosDB, AKS)  │  GCP (GKE)     │
└─────────────────────────────────────────────────────────────────┘
```

### Hybrid Architecture (Backstage + Humanitec)

```
┌─────────────────────────────────────────────────────────────────┐
│             Developer Portal (Backstage or Port)                │
│  - Service Catalog    - Documentation    - Self-Service UI     │
└─────────────────────────────────────────────────────────────────┘
                            ↓ API
┌─────────────────────────────────────────────────────────────────┐
│             Platform Orchestrator (Humanitec)                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Live Resource Graph (Single Source of Truth)      │        │
│  │  - Applications, Resources, Dependencies            │        │
│  └─────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Resource Management                                │        │
│  │  - Resource Definitions (databases, caches, etc.)   │        │
│  │  - Resource Matching (dev vs. prod resources)       │        │
│  └─────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Deployment Pipelines                               │        │
│  │  - Environment orchestration                        │        │
│  │  - Approval workflows                               │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│     Infrastructure Provisioning (Terraform, Crossplane)         │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Developer Creates New Service

```
1. Developer opens Backstage portal
   ↓
2. Selects "Create Component" → chooses template (e.g., "Node.js API")
   ↓
3. Fills in template parameters (service name, team, database type)
   ↓
4. Backstage Scaffolder executes template actions:
   a. Create Git repository (GitHub/GitLab API)
   b. Scaffold code (Cookiecutter template)
   c. Add CI/CD pipeline (GitHub Actions workflow file)
   d. Register in service catalog (catalog-info.yaml)
   ↓
5. Developer pushes first commit
   ↓
6. CI/CD pipeline triggers:
   a. Build container image
   b. Security scan (Trivy)
   c. Push to container registry
   ↓
7. Developer creates deployment via portal:
   a. Selects environment (dev, staging, prod)
   b. Crossplane provisions infrastructure (database, cache)
   c. Argo CD syncs application manifests to cluster
   ↓
8. Service is deployed and visible in:
   - Service catalog (ownership, dependencies)
   - Observability dashboards (metrics, logs)
   - Cost insights (resource costs)
```

## Best Practices

### Portal Design

**Navigation:**
- Clear information architecture (catalog, docs, create, admin)
- Search as primary navigation (developers know what they want)
- Personalization (my services, my team's services)

**Performance:**
- Fast load times (<3s for catalog page)
- Pagination for large catalogs (100 services per page)
- Cache frequently accessed data

**Accessibility:**
- Keyboard navigation
- Screen reader support
- High contrast mode

### Orchestration Layer

**Resource Abstraction:**
- Platform-agnostic APIs (request "database", not "RDS instance")
- Environment-aware resource matching (dev: in-cluster Postgres, prod: managed RDS)
- Cost-aware defaults (right-size by default, allow overrides)

**Idempotency:**
- Make infrastructure operations idempotent
- Retry-safe (repeated applies don't create duplicates)
- Rollback-safe (undo without side effects)

### Integration Layer

**API Design:**
- Versioned APIs (v1, v2 with deprecation notices)
- Pagination for list endpoints
- Filtering and sorting
- Clear error messages

**Monitoring:**
- Instrument all integrations (metrics for API calls, latency, errors)
- Circuit breakers (fail fast if backend down)
- Timeouts (don't wait forever for slow backends)
