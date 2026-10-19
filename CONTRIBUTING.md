# Maintaining dot-agents

Keep imported skill instructions unchanged unless intentionally maintaining a local fork.
Preserve scripts, references, assets, license files, and relative paths. Catalog entries distinguish
redistributable files from provider-managed metadata. New provider-managed skills must remain external.

Run `make check` before pushing. Installer tests use temporary homes; never run CI installation tests
against your real home directory. Refresh the inventory with `scripts/import_skills.py --replace` only
after reviewing local snapshot edits and adding any new upstream license records. This rebuilds the
repository's `collections/`, not your installed skill sources.

The readable catalog is generated with `python3 scripts/catalog.py`. Checksum changes require an
intentional catalog refresh. Imported legacy names are retained even when they are not lowercase kebab case.

Dependabot manages GitHub Actions updates. Renovate is disabled here to avoid duplicate updates
and dependency changes to the preserved example projects inside imported skills.

## Release

1. Update `VERSION` to `MAJOR.MINOR.PATCH`.
2. Run `make check`, commit the change, and push `main`.
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
upstream sources. Record reasons, affected files, attribution, and entrypoint hashes.
Update the complete `docs/skill-review.json` for new or modified catalog entries;
validation checks coverage and current hashes. Keep optional invocation policies and
license notices intact. Do not repair provider caches by editing them locally.

Follow [the repository review guide](docs/repository-skills.md) to refresh profiles.
Evidence and account analyses belong outside the public clone. Public export must
select explicitly public records and match reviewed commits. Private context is an
external local skill and never enters `collections/` or a release archive.
