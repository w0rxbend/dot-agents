#!/usr/bin/env python3
"""Export public structure profiles from local pinned evidence; never export private records."""
import argparse
import hashlib
import json
from pathlib import Path
from review_repositories import BUILD_FILES, SKIP_PARTS

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / 'collections/shared/worxbend-repository-context/references/profiles.json'


def verify_evidence_files(manifest, files_root):
    """Fail before export if a recorded byte or path no longer matches the review."""
    root = files_root.resolve()
    for item in manifest['files']:
        if item['status'] != 'read':
            continue
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('reviewed evidence file is missing or outside its root')
        payload = path.read_bytes()
        if len(payload) != item['bytes'] or hashlib.sha256(payload).hexdigest() != item['sha256']:
            raise ValueError('reviewed evidence file hash differs; recollect before export')


def read_evidence_tree(manifest, folder):
    path = folder / 'tree.json'
    if not path.exists():
        if manifest['status'] == 'empty':
            return {'tree': []}
        raise ValueError('reviewed evidence tree is missing')
    payload = path.read_bytes()
    if manifest.get('tree_sha256') and hashlib.sha256(payload).hexdigest() != manifest['tree_sha256']:
        raise ValueError('reviewed evidence tree hash differs; recollect before export')
    tree = json.loads(payload)
    if tree.get('truncated'):
        raise ValueError('reviewed evidence tree is incomplete')
    return tree


def relevant_skills(repository, paths):
    combined = (' '.join(paths) + ' ' + repository).lower()
    names = {Path(path).name for path in paths}
    skills = []
    if any(name.startswith(('build.mill', 'package.mill')) for name in names):
        skills += ['mill-project-models', 'mill-jvm-modules', 'mill-monorepo']
    if any(name in {'build.sbt', 'build.mill', 'build.mill.yaml', 'pom.xml'} for name in names) or '.scala' in combined:
        skills += ['scala-library-contracts'] if any(word in repository.lower() for word in
                   ['worxbend/worxbend', 'codeberg4s', 'gitea-scala', 'scalacv', 'glyphora', 'obs-websocket', 'kui']) else []
    if 'Cargo.toml' in names:
        skills += ['rust-systems-contracts']
    if 'shard.yml' in names:
        skills += ['crystal-build-and-test']
    if 'mix.exs' in names:
        skills += ['elixir-project-workflow']
    if any(name in {'build.zig', 'build.zig.zon'} for name in names):
        skills += ['zig-build-and-memory']
    if 'go.mod' in names:
        skills += ['golang-project-layout', 'golang-lint']
    if any(name in {'build.gradle.kts', 'build.gradle', 'settings.gradle.kts'} for name in names):
        skills += ['kotlin-coroutines', 'kotlin-null-safety']
    if any(name in {'pyproject.toml', 'requirements.txt'} for name in names):
        skills += ['python-development']
    if any(word in repository.lower() for word in ['obs', 'twitch', 'scenedeck', 'multistream', 'prismcast', 'streaming', 'bounce-io', 'twi', '/yc']):
        skills += ['streaming-integrations']
    if 'airgradient' in repository.lower():
        skills += ['airgradient-clients']
    if any(word in repository.lower() for word in ['spycam', 'chillmate', 'paranoid', 'macropad', 'led-matrix', 'neoncore']):
        skills += ['embedded-device-protocols']
    if any(word in repository.lower() for word in ['fluxion', 'binstaller', 'dotbot', 'bootstrap', 'nerd-font']):
        skills += ['workstation-installers']
    if any(word in repository.lower() for word in ['infrastruct', 'ops-dashboard', 'airgradient-observability']):
        skills += ['homelab-operations']
    if any(word in repository.lower() for word in ['compression-flix', 'scalachess-flix', 'shield', 'instachron']):
        skills += ['compatibility-ports']
    return list(dict.fromkeys(skills))


def public_record(manifest, tree, files_root=None):
    if manifest.get('private') is not False:
        raise ValueError('only explicitly public evidence may be exported')
    if manifest['status'] not in {'reviewed', 'empty'}:
        raise ValueError('resolve incomplete evidence before publishing its profile')
    paths = [row['path'] for row in tree.get('tree', []) if row['type'] == 'blob'
             and not any(part in SKIP_PARTS for part in Path(row['path']).parts)]
    build_files = sorted(path for path in paths if Path(path).name in BUILD_FILES)
    ci_files = sorted(path for path in paths if path.startswith('.github/workflows/'))
    instructions = sorted(path for path in paths if Path(path).name == 'AGENTS.md')
    packages = {}
    if files_root is not None:
        verify_evidence_files(manifest, files_root)
        for item in manifest['files']:
            if item['status'] != 'read' or Path(item['path']).name != 'package.json':
                continue
            if any(part in SKIP_PARTS for part in Path(item['path']).parts):
                continue
            package = json.loads((files_root / item['path']).read_text())
            deps = {**package.get('dependencies', {}), **package.get('devDependencies', {})}
            selected = {name: version for name, version in deps.items()
                        if name in {'pixi.js', 'solid-js', 'react', 'svelte', 'next', 'typescript', 'vite'}}
            if selected:
                packages[item['path']] = selected
    skills = relevant_skills(manifest['repository'], paths)
    if any('pixi.js' in deps for deps in packages.values()):
        skills += ['pixijs-application', 'pixijs-core-concepts', 'pixijs-performance']
    if any('typescript' in deps for deps in packages.values()) or any(Path(path).name.startswith('tsconfig') for path in paths):
        skills += ['typescript-project-contracts']
    return {
        'repository': manifest['repository'], 'url': manifest['url'],
        'head_sha': manifest['head_sha'], 'archived': manifest['archived'], 'fork': manifest['fork'],
        'build_files': build_files, 'ci_files': ci_files, 'instruction_files': instructions,
        'skills': list(dict.fromkeys(skills)), 'frontend_packages': packages,
        'baseline_coverage': {
            'files_read': len(manifest['files']),
            'remaining_candidates': manifest.get('remaining_candidates', []),
            'scope': 'build/instructions/CI/documentation plus separate representative-source review',
        },
        'evidence': [{key: item[key] for key in ('path', 'url', 'sha256', 'bytes')}
                     for item in manifest['files'] if item['status'] == 'read'],
    }


def merge_analysis(rows, analyses):
    """Merge only whitelisted public observations matching the pinned commit."""
    by_repo = {row['repository'].lower(): row for row in rows}
    for analysis in analyses:
        entries = list(analysis.get('entries', []))
        public_entries = analysis.get('public_repositories', [])
        if isinstance(public_entries, list):
            entries += public_entries
        for item in entries:
            if item.get('private') is not False:
                continue
            row = by_repo.get(item['repository'].lower())
            if row is None:
                raise ValueError('analysis references a repository outside the public evidence')
            if item['head_sha'] != row['head_sha']:
                raise ValueError('analysis commit differs from evidence; review the updated repository')
            observations = {key: item[key] for key in [
                'build', 'classification', 'summary', 'languages_observed', 'constraints',
                'review_level', 'review_depth', 'source_files_reviewed',
            ] if key in item}
            if item.get('supplemental_evidence'):
                observations['source_files_reviewed'] = [
                    {key: record[key] for key in ['path', 'url', 'sha256'] if key in record}
                    for record in item['supplemental_evidence']]
            row['review_observations'] = observations
            aliases = {'cpp-pro': 'cpp-obs-plugin-development',
                       'elixir-expert': 'elixir-project-workflow',
                       'typescript-expert': 'typescript-project-contracts',
                       'skill-creator': 'codex-system--skill-creator',
                       'skill-installer': 'codex-system--skill-installer'}
            candidates = row['skills'] + item.get('skill_routes', []) + item.get('skill_routing', [])
            row['skills'] = list(dict.fromkeys(aliases.get(name, name) for name in candidates))
    return rows


def filter_available_skills(rows, available):
    for row in rows:
        row['skills'] = [name for name in row['skills'] if name in available]
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=TARGET)
    parser.add_argument('--analysis', type=Path, nargs='*', default=[], help='local account analyses; only public observations export')
    args = parser.parse_args()
    manifests = json.loads((args.evidence / 'repository-evidence.json').read_text())
    rows = []
    for manifest in manifests:
        if manifest.get('private') is True:
            continue
        folder = args.evidence / 'evidence' / manifest['repository'].replace('/', '--')
        tree = read_evidence_tree(manifest, folder)
        rows.append(public_record(manifest, tree, folder / 'files'))
    merge_analysis(rows, [json.loads(path.read_text()) for path in args.analysis])
    available = {row['id'] for row in json.loads((REPO / 'catalog.json').read_text())['skills']}
    available.update(path.name for path in (REPO / 'collections/shared').iterdir()
                     if (path / 'SKILL.md').is_file())
    filter_available_skills(rows, available)
    review_date = max((item.get('validated_at') or item['retrieved_at']).split('T')[0] for item in manifests)
    data = {'schema_version': 1, 'review_date': review_date,
            'scope': 'public repository structure and evidence; current checkout remains authoritative',
            'repositories': sorted(rows, key=lambda row: row['repository'].lower())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(f'Exported {len(rows)} public profiles; private evidence excluded')


if __name__ == '__main__':
    main()
