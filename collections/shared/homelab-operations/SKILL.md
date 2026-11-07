---
name: homelab-operations
description: Prepare and verify repository-managed Ansible, K3s/Flux, Compose/Swarm and SOPS changes for a mixed-architecture homelab, preserving ownership, inventory contracts and operational-readiness gates.
license: MIT
---

Before changing infrastructure, find checkout's inventory mode, ownership map, service metadata and validation entrypoints. Read [references/change-contracts.md](references/change-contracts.md) for existing contracts and how repository validation differs from live operation. Avoid exporting inventories, IPs, credentials, encrypted secret contents or private repository details into global skills or public reports.

Choose owner of desired state:

- Ansible: physical hosts, baseline configuration and K3s node lifecycle.
- Flux/Kustomize/Helm: Kubernetes applications and cluster declarative state.
- Compose/Swarm plus existing automation: standalone services and multi-host Docker stacks.
- SOPS/age: encrypted configuration and recipient policy; private keys stay outside Git.

Do not fix one owner's managed state by lasting manual change under another owner. Authorized investigation or emergency recovery can be fine; reconcile durable results into source repository and its recovery docs. Request to prepare repository changes does not itself authorize applying them to a fleet, decrypting real secrets, publishing a service or collecting live host identity.

Validate with repository's own contract fixtures and supported full gate. Distinguish missing workstation tools from failed contract. Syntax/lint success does not prove inventory reachability, convergence, safe firewall changes, recoverability or healthy applications. Keep evidence layers separate. Do not bypass readiness lock because another layer passed.

For authorized application, use smallest suitable target and stopping condition. Before execution, identify expected diff, verification signals, rollback path, secret dependencies, storage/backup effects and public-exposure owner. Ansible check mode is useful evidence, not proof every module or side effect is harmless. Stop on failed precondition, unexpected target/diff, lost access or ambiguous state. Diagnose before retrying mutations.

Preserve mixed ARM hardware constraints: image architecture, memory, persistent storage, boot disks, node role and placement. Before replacing container image or moving workload, check those constraints and restore path. Valid YAML alone is not enough.
