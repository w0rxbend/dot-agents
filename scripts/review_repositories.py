#!/usr/bin/env python3
"""Collect pinned repository evidence without running project code or publishing it."""
import argparse
import base64
import concurrent.futures
import datetime
import hashlib
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD_FILES = {
    'build.mill', 'build.mill.yaml', 'package.mill', 'package.mill.yaml', '.mill-version',
    'build.sbt', 'build.properties', 'plugins.sbt', 'pom.xml', 'build.gradle',
    'build.gradle.kts', 'settings.gradle.kts', 'gradle.properties', 'Cargo.toml',
    'go.mod', 'package.json', 'pyproject.toml', 'requirements.txt', 'shard.yml',
    'mix.exs', 'flix.toml', 'build.zig', 'build.zig.zon', 'platformio.ini',
    'CMakeLists.txt', 'meson.build', 'Makefile', 'justfile', 'Taskfile.yml',
    'snapcraft.yaml', 'metadata.json', 'Chart.yaml', 'ansible.cfg',
}
SKIP_PARTS = {'node_modules', 'vendor', '.git', 'target', 'out', 'dist', 'build',
              'third_party', 'third-party', '.venv', 'generated', 'collections',
              '.agents', '.claude', '.codex'}


def gh_json(endpoint):
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True, timeout=90)
    if result.returncode:
        # API diagnostics may contain private identifiers; keep them in local evidence.
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def discover(owners, include_private):
    repositories = []
    for owner in owners:
        result = subprocess.run([
            'gh', 'repo', 'list', owner, '--limit', '1000', '--json',
            'nameWithOwner,isPrivate,isArchived,isFork,defaultBranchRef,url,description',
        ], capture_output=True, text=True, timeout=90, check=True)
        rows = json.loads(result.stdout)
        if len(rows) == 1000:
            raise ValueError('repository limit reached; use a paginated discovery implementation')
        repositories.extend(row for row in rows if include_private or not row['isPrivate'])
    return sorted(repositories, key=lambda row: row['nameWithOwner'].lower())


def select_files(tree, limit):
    """Prioritize instructions, README, toolchains and CI; record remaining candidates."""
    candidates = []
    for entry in tree:
        path = Path(entry['path'])
        if entry['type'] != 'blob' or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name == 'AGENTS.md':
            priority = 0
        elif path.name.lower().startswith('readme') and path.suffix.lower() in {'.md', '.rst', '.txt', ''}:
            priority = 1 if len(path.parts) == 1 else 5
        elif path.name in BUILD_FILES:
            priority = 2 if len(path.parts) <= 2 else 4
        elif path.parts[:2] == ('.github', 'workflows') and path.suffix in {'.yml', '.yaml'}:
            priority = 3
        elif path.name in {'CONTRIBUTING.md', 'SECURITY.md'}:
            priority = 5
        else:
            continue
        candidates.append((priority, len(path.parts), entry['path']))
    ordered = [item[2] for item in sorted(candidates)]
    return ordered[:limit], ordered[limit:]


def fetch_file(full_name, sha, path, private):
    if private:
        endpoint = f'repos/{full_name}/contents/{urllib.parse.quote(path)}?ref={sha}'
        data = gh_json(endpoint)
        if data.get('encoding') != 'base64':
            raise ValueError('file exceeds the supported API content size')
        return base64.b64decode(data['content'])
    url = f'https://raw.githubusercontent.com/{full_name}/{sha}/{urllib.parse.quote(path)}'
    with urllib.request.urlopen(url, timeout=40) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError('evidence file exceeds two megabytes')
    return payload


def cache_valid(previous, repository, folder, sha, max_files):
    """Never reuse stale visibility, scope, or corrupt/missing cached evidence."""
    if previous.get('head_sha') != sha or previous.get('status') != 'reviewed':
        return False
    expected = {'repository': repository['nameWithOwner'], 'private': repository['isPrivate'],
                'archived': repository['isArchived'], 'fork': repository['isFork'],
                'url': repository['url'], 'max_files': max_files}
    if any(previous.get(key) != value for key, value in expected.items()):
        return False
    try:
        tree_bytes = (folder / 'tree.json').read_bytes()
        if hashlib.sha256(tree_bytes).hexdigest() != previous.get('tree_sha256'):
            return False
        tree = json.loads(tree_bytes)
        if tree.get('truncated'):
            return False
        chosen, _ = select_files(tree['tree'], max_files)
        if chosen != [item['path'] for item in previous['files']]:
            return False
        for item in previous['files']:
            path = folder / 'files' / item['path']
            if not path.resolve().is_relative_to((folder / 'files').resolve()):
                return False
            payload = path.read_bytes()
            if item['status'] != 'read' or len(payload) != item['bytes']:
                return False
            if hashlib.sha256(payload).hexdigest() != item['sha256']:
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def review(repository, output, max_files, refresh):
    full_name = repository['nameWithOwner']
    folder = output / 'evidence' / full_name.replace('/', '--')
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / 'manifest.json'
    branch = repository['defaultBranchRef']
    manifest = {
        'repository': full_name, 'url': repository['url'], 'private': repository['isPrivate'],
        'archived': repository['isArchived'], 'fork': repository['isFork'],
        'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'files': [], 'status': 'pending', 'max_files': max_files,
    }
    try:
        if not branch:
            manifest.update(status='empty', head_sha=None, tree_entries=0)
        else:
            ref = gh_json(f'repos/{full_name}/git/ref/heads/{urllib.parse.quote(branch["name"], safe="")}')
            sha = ref['object']['sha']
            manifest['head_sha'] = sha
            if manifest_path.exists() and not refresh:
                previous = json.loads(manifest_path.read_text())
                if cache_valid(previous, repository, folder, sha, max_files):
                    previous['validated_at'] = manifest['retrieved_at']
                    manifest_path.write_text(json.dumps(previous, indent=2) + '\n')
                    return previous
            tree = gh_json(f'repos/{full_name}/git/trees/{sha}?recursive=1')
            tree_bytes = (json.dumps(tree, indent=2) + '\n').encode()
            (folder / 'tree.json').write_bytes(tree_bytes)
            manifest['tree_sha256'] = hashlib.sha256(tree_bytes).hexdigest()
            manifest['tree_entries'] = len(tree['tree'])
            manifest['tree_truncated'] = tree.get('truncated', False)
            chosen, remaining = select_files(tree['tree'], max_files)
            manifest['remaining_candidates'] = remaining
            manifest['coverage'] = 'bounded-baseline' if remaining else 'all-eligible-baseline-files'
            for path in chosen:
                record = {'path': path, 'url': f'https://github.com/{full_name}/blob/{sha}/{path}'}
                try:
                    payload = fetch_file(full_name, sha, path, repository['isPrivate'])
                    destination = folder / 'files' / path
                    if not destination.resolve().is_relative_to((folder / 'files').resolve()):
                        raise ValueError('path escapes evidence directory')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(payload)
                    record.update(status='read', bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
                except (OSError, ValueError, RuntimeError) as error:
                    record.update(status='error', error=str(error))
                manifest['files'].append(record)
            manifest['status'] = 'reviewed' if all(item['status'] == 'read' for item in manifest['files']) else 'partial'
            if manifest['tree_truncated']:
                manifest['status'] = 'partial'
    except (OSError, ValueError, RuntimeError) as error:
        manifest.update(status='error', error=str(error))
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owners', nargs='+', default=['worxbend', 'w0rxbend'])
    parser.add_argument('--output', type=Path, required=True, help='local evidence directory')
    parser.add_argument('--include-private', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--max-files', type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16 or not 1 <= args.max_files <= 100:
        parser.error('workers must be 1..16 and max-files 1..100')
    if args.include_private and args.output.resolve().is_relative_to(REPO):
        parser.error('private evidence must be stored outside the public checkout')
    repositories = discover(args.owners, args.include_private)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.include_private:
        # The inventory and nested cached evidence can contain private identifiers.
        args.output.chmod(0o700)
    (args.output / 'accessible-repositories.json').write_text(json.dumps(repositories, indent=2) + '\n')
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        tasks = [executor.submit(review, row, args.output, args.max_files, args.refresh) for row in repositories]
        for future in concurrent.futures.as_completed(tasks):
            results.append(future.result())
            print(f'Collected {len(results)}/{len(repositories)} repositories', flush=True)
    results.sort(key=lambda row: row['repository'])
    (args.output / 'repository-evidence.json').write_text(json.dumps(results, indent=2) + '\n')
    errors = sum(row['status'] in {'error', 'partial'} for row in results)
    print(f'{len(results)} repositories; {errors} incomplete; no project code executed')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
