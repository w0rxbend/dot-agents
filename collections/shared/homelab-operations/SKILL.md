---
name: homelab-operations
description: Prepare and verify repository-managed Ansible, K3s/Flux, Compose/Swarm and SOPS changes for a mixed-architecture homelab, preserving ownership, inventory contracts and operational-readiness gates.
license: MIT
---

Locate the checked-out inventory mode, ownership map, service metadata and validation entrypoints before changing infrastructure. Read [references/change-contracts.md](references/change-contracts.md) for this portfolio's existing contracts and the distinction between repository validation and live operation. Avoid exporting inventories, IPs, credentials, encrypted secret contents or private repository details into global skills or public reports.

Choose the owner of the desired state:

- Ansible: physical hosts, baseline configuration and K3s node lifecycle.
- Flux/Kustomize/Helm: Kubernetes applications and cluster declarative state.
- Compose/Swarm plus their existing automation: standalone services and multi-host Docker stacks.
- SOPS/age: encrypted configuration and recipient policy; private keys remain outside Git.

Do not repair one owner's managed state by making a lasting manual change under another owner. Investigation or emergency recovery can be appropriate when authorized, but reconcile any durable result into the source repository and its recovery documentation. A request to prepare repository changes does not itself authorize applying them to a fleet, decrypting real secrets, publishing a service, or collecting live host identity.

Validate changes using the repository's own contract fixtures and supported full gate. Distinguish missing workstation tools from a failed contract. Syntax/lint success does not prove inventory reachability, successful convergence, safe firewall changes, recoverability, or healthy applications. Keep these evidence layers separate, and do not bypass a readiness lock because another layer passed.

For an authorized application, use the smallest suitable target and stopping condition. Identify expected diff, verification signals, rollback path, secret dependencies, storage/backup effects and public-exposure owner before execution. Ansible check mode is useful evidence but is not a proof that every module or side effect is harmless. Stop on a failed precondition, unexpected target/diff, lost access or ambiguous state; diagnose before retrying mutations.

Preserve mixed ARM hardware constraints: image architecture, memory, persistent storage, boot disks, node role and placement. Replacing a container image or moving a workload requires checking those constraints and the restore path, not merely rendering valid YAML.
