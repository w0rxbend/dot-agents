# Maintaining dot-agents

This repository holds the maintained skills, `justfile`, and `install.sh`. Do not vendor Codex,
Hermes, Claude, or Render system skills. Preserve scripts, references, assets, license files, and
relative paths inside a skill. Adapted skills keep their upstream license and a record in
`sources/local-forks.json`.

Run `just check` before pushing. Installer tests use temporary homes; never run CI installation tests
against your real home directory. Edit skills in `skills/`, then refresh catalog hashes and the
rendered installer config. Do not rebuild `skills/` by scanning agent skill directories.

The readable catalog is generated with `python3 scripts/catalog.py`. Checksum changes require an
intentional catalog refresh. Imported legacy names are retained even when they are not lowercase kebab case.

Dependabot manages GitHub Actions updates. Renovate is disabled here to avoid duplicate updates
and dependency changes to the preserved example projects inside imported skills.

## Release

1. Update `VERSION` to `MAJOR.MINOR.PATCH`.
2. Run `just check`, commit the change, and push `main`.
3. Wait for CI to pass.
4. Create and push the matching tag:

```sh
git tag -a "v$(cat VERSION)" -m "dot-agents $(cat VERSION)"
git push origin "v$(cat VERSION)"
```

The release workflow validates again and publishes `dot-agents-VERSION.tar.gz` and `SHA256SUMS`.
The archive contains the tagged tracked files with reproducible compression. It excludes Git history,
provider-managed skill files, credentials, and machine-specific installation state.

For a local preview from a clean, committed checkout:

```sh
python3 scripts/package.py --version "$(cat VERSION)"
```

## Reviewed local forks and repository context

Preserve intentional fork changes recorded in `sources/local-forks.json` when updating
an adapted skill. Record reasons, affected files, attribution, and entrypoint hashes.
Validation checks those hashes and the catalog checksums. Keep optional invocation
policies and license notices intact.

Follow [the repository review guide](docs/repository-skills.md) when editing public
repository profiles. Private context is an external local skill and never enters
`skills/` or a release archive.
