#!/usr/bin/env python3
"""Verify distribution boundaries, inventory checksums, metadata, and symlinks."""
import re
import json
import hashlib
import sys
from pathlib import Path
from common import REPO, frontmatter, load_catalog, tree_hash
from catalog import render


def validate(repo=REPO):
    data = load_catalog(repo)
    if data['schema_version'] != 1:
        raise ValueError('unsupported catalog schema')
    ids = set()
    for item in data['skills']:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', item['id']) or item['id'] in ids:
            raise ValueError(f"invalid or duplicate ID: {item['id']}")
        ids.add(item['id'])
        if item['distribution'] == 'external':
            if 'path' in item:
                raise ValueError(f"provider-managed content is vendored: {item['id']}")
            continue
        if item['distribution'] != 'vendored':
            raise ValueError('unknown distribution value')
        path = (repo / item['path']).resolve()
        if not path.is_relative_to(repo.resolve()):
            raise ValueError(f'path escapes repository: {path}')
        info = frontmatter(path / 'SKILL.md')
        if info['name'] != item['name']:
            raise ValueError(f"name changed: {item['id']}")
        if tree_hash(path) != item['sha256']:
            raise ValueError(f"skill checksum changed: {item['id']}; refresh catalog deliberately")
        if item['source'] != 'local' and not (repo / item['license_file']).is_file():
            raise ValueError(f"missing license: {item['id']}")
    for p in (repo / 'collections').rglob('*'):
        if p.is_symlink() and (not p.exists() or not p.resolve().is_relative_to(repo.resolve())):
            raise ValueError(f'broken or external symlink: {p}')
        if p.is_file() and p.name.lower().startswith('license'):
            text = p.read_text(errors='replace')
            if 'Extract these materials from the Services' in text:
                raise ValueError(f'restricted hosted skill accidentally included: {p}')
        if p.is_file() and p.stat().st_size > 90_000_000:
            raise ValueError(f'file exceeds repository size limit: {p}')
    if (repo / 'docs/catalog.md').read_text(encoding='utf-8') != render(repo):
        raise ValueError('catalog documentation is stale')
    review_path = repo / 'docs/skill-review.json'
    if not review_path.is_file():
        raise ValueError('complete skill review is missing')
    if review_path.exists():
        review = json.loads(review_path.read_text())
        reviewed = {row['id']: row for row in review['skills']}
        if len(reviewed) != len(review['skills']) or set(reviewed) != ids:
            raise ValueError('skill review does not cover the complete catalog')
        for item in data['skills']:
            row = reviewed[item['id']]
            if not row.get('reviewed') or row['sha256'] != item['sha256']:
                raise ValueError(f"stale skill review: {item['id']}")
        forks = json.loads((repo / 'sources/local-forks.json').read_text())
        for fork in forks['changes']:
            entry = repo / fork['path'] / 'SKILL.md'
            if hashlib.sha256(entry.read_bytes()).hexdigest() != fork['after_entry_sha256']:
                raise ValueError(f"stale local fork record: {fork['id']}")
        profiles = json.loads((repo / 'collections/shared/worxbend-repository-context/references/profiles.json').read_text())
        for profile in profiles['repositories']:
            if any(skill not in ids for skill in profile['skills']):
                raise ValueError('repository profile references an unavailable skill')
        private = next(item for item in data['skills'] if item['id'] == 'worxbend-private-repository-context')
        if private['distribution'] != 'external' or 'path' in private:
            raise ValueError('private context must remain local-only')
    print(f"OK: {len(ids)} skills, hashes, metadata, licenses, symlinks, and catalog")


if __name__ == '__main__':
    try:
        validate()
    except (ValueError, KeyError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
