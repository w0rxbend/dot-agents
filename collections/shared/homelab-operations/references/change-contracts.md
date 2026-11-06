# Repository contracts and evidence layers

Public source anchors: [ownership/readiness overview](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/README.md), [validation targets](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/Makefile), [inventory mode](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/repo-mode.yml), [operational readiness validator](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/scripts/validate-operational-readiness). Inspect current checkout before relying on this snapshot.

Infrastruct has promoted real-fleet inventory with expected count contract. Do not hard-code its current count, invent hosts to satisfy validation, or loosen contract to hide drift. Inventory assertions are real automation; several baseline roles are still placeholders. Declared future stack does not prove deployment exists or is operationally unlocked. Read actual role/tasks and readiness validator for touched area.

| Existing entrypoint | Evidence it supplies |
|---|---|
| `make validate-local-contracts` | Cheap repository contracts and fixture tests: inventory, exposure, SOPS policy, secret scanning |
| `make validate` / `make validate-full` | Full supported-workstation validation with Ansible syntax/lint and Compose/Swarm gates |
| `make validate-runner` | Pinned full validation environment |
| `make validate-runner-proof` | Extra no-cache runner proof when container/tool pin changes require it |
| live inventory healthcheck | Explicitly separate host reachability evidence from management network |

Read [pre-merge checklist](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/docs/pre-merge-checklist.md) before selecting targets. Do not report unavailable/skipped full gate as pass. Live healthcheck can reveal addresses/keys; run it only in suitable authorized environment. Ordinary repository tests need not contact hosts.

Host metadata must retain hardware identity, architecture, storage, runtime role, reliability/placement and exposure. Service changes need runtime, placement, data path/storage, secret source, backup and maintenance ownership. Public exposure needs protocol, port/proxy owner, internal target and firewall/secret dependencies. Keep service and inventory changes consistent with their docs/validators. Examples and production inventory are separate inputs.

For Flux changes, inspect reconciliation root, dependsOn, source refs, namespace and secret decryption setup. Reconcile through GitOps, not `kubectl apply` to managed resources. Render against correct overlays/chart versions; check CRD availability. Generic kubectl dry-run can fail on missing CRDs and does not prove runtime readiness. See [Flux reconciliation](https://fluxcd.io/flux/components/kustomize/kustomizations/) for version-matching fields.

For SOPS changes, first check `.sops.yaml` recipients/path rules and existing [workflow proof](https://github.com/w0rxbend/infrastruct/blob/e1d893edca2a871c3e0a72aafee3b365ce7d4690/docs/sops-workflow-proof.md). Dummy/example recipients must not receive real secrets. Key rotation/recipient changes require verifying decryptable recovery path for authorized operators; valid ciphertext alone does not prove it. Prefer synthetic secrets for policy fixtures. Never print decrypted values in test logs. Check [SOPS usage](https://github.com/getsops/sops) for target tool version.

Workstation bootstrap is related but distinct. In [Ubuntu bootstrap](https://github.com/w0rxbend/ubuntu-bootstrap/blob/bfb647d445df752349dd2c6c41a7e4be56fb4b28/bootstrap.sh), preserve profile phase/state identity and dry-run behavior; dotbot owns links to live dotfiles source. Session checkpoints deliberately stop for logout/login. Bootstrap assertion may inspect current machine or use sudo; choose repo's isolated/fixture checks before host application. Shell formatting/linting in [system-bootstrap lint](https://github.com/w0rxbend/system-bootstrap/blob/0d7bb1de615e5c1d97b646eac25f2943333ffdda/scripts/lint.sh) is not a workstation reinstall or successful service rollout.
