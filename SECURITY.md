# Security and imported dependencies

The installer uses Python's standard library and creates filesystem links. It does not execute
skill scripts, install dependency manifests, enable connectors, or load credentials.

Some imported skills include upstream example applications and dependency manifests. GitHub's
[dependency alerts](https://github.com/w0rxbend/dot-agents/security/dependabot) may flag packages in
those examples. Review current alerts and update dependencies before running an example; inclusion
in the snapshot does not mean its dependencies have been audited or upgraded.

The initial scan included a critical advisory for `qdrant-client` in
`collections/shared/using-vector-databases/examples/qdrant-python/requirements.txt` and additional
alerts in several upstream Python and visualization examples. Their original files are retained
as reference material. Unused flowrite development sources and fixtures are excluded from the
snapshot and installation catalog.

Report third-party skill vulnerabilities to the upstream project identified in `catalog.json`.
For installer defects, use GitHub's private vulnerability reporting when available, or contact
the repository owner privately. Keep credentials and exploit details out of public issues.
