#!/usr/bin/env python3
"""Look up a repository profile without network access or project execution."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

INDEX = Path(__file__).resolve().parents[1] / 'references/profiles.json'


def repository_name(remote):
    value = remote.strip()
    scp = re.fullmatch(r'(?:git@)?github\.com:([^\s]+)', value, re.IGNORECASE)
    if scp:
        path = scp.group(1)
    else:
        parsed = urlparse(value)
        if parsed.scheme not in {'https', 'http', 'ssh', 'git'} or parsed.hostname != 'github.com':
            raise ValueError('expected a GitHub repository URL or git@github.com:owner/repo')
        path = parsed.path.lstrip('/')
    path = path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', path):
        raise ValueError('expected exactly owner/repository without a branch or extra path')
    return path.lower()


def lookup(remote, index=INDEX):
    name = repository_name(remote)
    data = json.loads(index.read_text())
    return next((row for row in data['repositories'] if row['repository'].lower() == name), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote')
    parser.add_argument('--cwd', type=Path, default=Path.cwd())
    parser.add_argument('--index', type=Path, default=INDEX, help='profile index; defaults to the public index')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    remote = args.remote
    if not remote:
        result = subprocess.run(['git', '-C', str(args.cwd), 'remote', 'get-url', 'origin'],
                                text=True, capture_output=True)
        if result.returncode:
            parser.error('origin is unavailable; supply --remote or inspect the repository directly')
        remote = result.stdout.strip()
    try:
        profile = lookup(remote, args.index.expanduser())
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if not profile:
        print('No public profile: inspect current repository instructions/build/CI; preserve its chosen stack.')
        return
    if args.json:
        print(json.dumps(profile, indent=2))
        return
    snapshot = profile.get('head_sha') or 'no commit'
    print(f"{profile['repository']} — snapshot {snapshot[:12]}")
    print(f"Archived: {profile['archived']}; fork: {profile['fork']}")
    for title, field in [('Build evidence', 'build_files'), ('Instructions', 'instruction_files'),
                         ('CI evidence', 'ci_files'), ('Relevant skills', 'skills')]:
        print(f"{title}: {', '.join(profile[field]) or 'inspect current checkout'}")
    if profile.get('frontend_packages'):
        print('Frontend version evidence: ' + json.dumps(profile['frontend_packages'], sort_keys=True))
    observations = profile.get('review_observations', {})
    for field in ['build', 'classification', 'summary', 'constraints']:
        if observations.get(field):
            print(f"{field.replace('_', ' ').title()}: {observations[field]}")
    remaining = profile.get('baseline_coverage', {}).get('remaining_candidates', [])
    if remaining:
        print(f'Baseline file cap: {len(remaining)} candidates were not fetched; inspect relevant current files.')
    print('Read current files before choosing commands; the profile does not authorize execution or migration.')


if __name__ == '__main__':
    main()
