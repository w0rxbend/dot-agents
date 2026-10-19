# Repository contracts and evidence layers

Public source anchors: [ownership/readiness overview](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/README.md), [validation targets](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/Makefile), [inventory mode](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/repo-mode.yml), and [operational readiness validator](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/scripts/validate-operational-readiness). Inspect the current checkout before relying on the snapshot.

Infrastruct has promoted real-fleet inventory with an expected count contract. Do not hard-code its current count, invent hosts to satisfy validation, or loosen the contract to hide drift. Inventory assertions are meaningful automation, while multiple baseline roles are still placeholders. A declared future stack is not evidence that deployment exists or is operationally unlocked. Read the actual role/tasks and readiness validator for the touched area.

The relevant checks have distinct scopes:

| Existing entrypoint | Evidence it supplies |
|---|---|
| `make validate-local-contracts` | Cheap repository contracts and fixture tests, including inventory, exposure, SOPS policy and secret scanning |
| `make validate` / `make validate-full` | Full supported-workstation validation, including Ansible syntax/lint and Compose/Swarm gates |
| `make validate-runner` | Pinned full validation environment |
| `make validate-runner-proof` | Additional no-cache runner proof when container/tool pin changes require it |
| live inventory healthcheck | Explicitly separate host reachability evidence from the management network |

Read [pre-merge checklist](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/docs/pre-merge-checklist.md) before selecting targets. Do not describe an unavailable/skipped full gate as a pass. A live healthcheck can reveal addresses/keys and requires an appropriate authorized environment; ordinary repository tests do not require contacting hosts.

Host metadata must retain hardware identity, architecture, storage, runtime role, reliability/placement and exposure. Service changes need runtime, placement, data path/storage, secret source, backup and maintenance ownership. Public exposure needs protocol, port/proxy owner, internal target and firewall/secret dependencies. Keep service and inventory changes consistent with their docs/validators; examples and production inventory are separate inputs.

For Flux changes inspect reconciliation root, dependsOn, source refs, namespace and secret decryption setup. Reconcile through GitOps rather than `kubectl apply` to managed resources. Render against the appropriate overlays/chart versions and check CRD availability; a generic kubectl dry-run can fail when CRDs are missing and does not prove runtime readiness. See the primary [Flux reconciliation](https://fluxcd.io/flux/components/kustomize/kustomizations/) reference for version-matching fields.

For SOPS changes first check `.sops.yaml` recipients/path rules and the existing [workflow proof](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/docs/sops-workflow-proof.md). Dummy/example recipients must not receive real secrets. Key rotation/recipient changes require verifying a decryptable recovery path for authorized operators; valid ciphertext alone does not establish that. Prefer synthetic secrets for policy fixtures and never print decrypted values in test logs. Consult [SOPS usage](https://github.com/getsops/sops) for the target tool version.

Workstation bootstrap is related but distinct: preserve profile phase/state identity and dry-run behavior in [Ubuntu bootstrap](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/bootstrap.sh); dotbot owns links to the live dotfiles source and session checkpoints deliberately stop for logout/login. A bootstrap assertion may inspect the current machine or use sudo; choose the repo's isolated/fixture checks before host application. Shell formatting/linting in [system-bootstrap lint](https://github.com/w0rxbend/system-bootstrap/blob/0d7bb1de615e5c1d97b646eac25f2943333ffdda/scripts/lint.sh) is not a workstation reinstall or successful service rollout.
