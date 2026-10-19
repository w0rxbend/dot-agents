#!/usr/bin/env python3
"""Generate local-only private repository context from authorized review evidence."""
import argparse
import datetime
import hashlib
import json
import tempfile
from pathlib import Path
from build_repository_profiles import relevant_skills, read_evidence_tree, verify_evidence_files
from review_repositories import BUILD_FILES, SKIP_PARTS

REPO = Path(__file__).resolve().parents[1]
NAME = 'worxbend-private-repository-context'
BODY = '''---
name: worxbend-private-repository-context
description: Select build and test conventions for this user's private repositories from a local-only profile. Use when a repository is absent from the public worxbend/w0rxbend index.
license: LicenseRef-Private-Local
---

# Local private repository context

Identify the current Git origin, then read only its matching record in
[profiles.json](references/profiles.json). The dated index records private repository
structure and evidence hashes; current committed instructions, build configuration,
source, and CI remain authoritative. It contains no credentials or copied project code.

If `worxbend-repository-context` is installed, its `scripts/repo_profile.py` can read
this file with `--index <this-skill-directory>/references/profiles.json --cwd .`.
Otherwise look up the origin directly in the JSON. Unknown origins require normal
repository inspection, not a guessed architecture or migration.

Prefer Mill when choosing a new JVM build, preserve existing builds and deliberately
chosen effect systems, and select only relevant specialist skills. Scope tests to the
actual component and repository CI contract. A metadata review does not prove builds,
service integration, native targets, or deployment.

Keep this local context, private names, source, and operational details out of public
skill exports, issue comments, and release notes. The dot-agents importer explicitly
classifies this skill as external. Recreate it from a new authorized local evidence
review with `scripts/build_private_profile.py`; no private profile ships in releases.
'''


def generate(evidence, target, replace=False):
    target = target.expanduser().resolve()
    if target.is_relative_to(REPO):
        raise ValueError('private context must stay outside the public checkout')
    manifests = json.loads((evidence / 'repository-evidence.json').read_text())
    rows = []
    for item in manifests:
        if item.get('private') is not True:
            continue
        if item['status'] not in {'reviewed', 'empty'}:
            raise ValueError('private evidence is incomplete; finish collection first')
        folder = evidence / 'evidence' / item['repository'].replace('/', '--')
        tree = read_evidence_tree(item, folder)['tree']
        verify_evidence_files(item, folder / 'files')
        paths = [row['path'] for row in tree if row['type'] == 'blob'
                 and not any(part in SKIP_PARTS for part in Path(row['path']).parts)]
        rows.append({
            'repository': item['repository'], 'url': item['url'], 'head_sha': item['head_sha'],
            'archived': item['archived'], 'fork': item['fork'],
            'build_files': sorted(path for path in paths if Path(path).name in BUILD_FILES),
            'ci_files': sorted(path for path in paths if path.startswith('.github/workflows/')),
            'instruction_files': sorted(path for path in paths if Path(path).name == 'AGENTS.md'),
            'skills': relevant_skills(item['repository'], paths),
            'evidence': [{key: record[key] for key in ('path', 'sha256', 'bytes')}
                         for record in item['files'] if record['status'] == 'read'],
        })
    if not rows:
        raise ValueError('no reviewed private repositories in the local evidence')
    data = {'schema_version': 1, 'scope': 'private local-only structure profile',
            'repositories': sorted(rows, key=lambda row: row['repository'].lower())}
    files = {'SKILL.md': BODY.encode(),
             'references/profiles.json': (json.dumps(data, indent=2) + '\n').encode()}
    marker = {name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()}
    backup = None
    if target.exists():
        same = all((target / name).is_file() and (target / name).read_bytes() == payload
                   for name, payload in files.items())
        actual = {path.relative_to(target).as_posix() for path in target.rglob('*') if path.is_file()}
        if same and actual == set(files) | {'.dot-agents-private.json'}:
            return target, len(rows)
        if not replace:
            raise ValueError('existing private context differs; --replace preserves a backup')
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = target.with_name(target.name + '.backup-' + stamp)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.private-profile-', dir=target.parent) as temporary:
        stage = Path(temporary) / NAME
        stage.mkdir(mode=0o700)
        for name, payload in files.items():
            destination = stage / name
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination.write_bytes(payload)
            destination.chmod(0o600)
        state = stage / '.dot-agents-private.json'
        state.write_text(json.dumps(marker, indent=2) + '\n')
        state.chmod(0o600)
        if backup:
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup:
                backup.rename(target)
            raise
    return target, len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--target', type=Path)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    target = args.target or args.home / '.local/share/dot-agents/private-skills' / NAME
    try:
        destination, count = generate(args.evidence, target, args.replace)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f'Created local private context for {count} repositories: {destination}')


if __name__ == '__main__':
    main()
