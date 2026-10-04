#!/usr/bin/env python3
"""Generate the browsable catalog without rewriting any upstream skill instructions."""
import argparse
from collections import Counter
from common import REPO, load_catalog


def render(repo=REPO):
    entries = load_catalog(repo)['skills']
    counts = Counter(item['distribution'] for item in entries)
    lines = ['# Skill catalog', '', f"{len(entries)} unique installed skills: {counts['vendored']} included, "
             f"{counts['external']} external (provider-managed, direct-source, or local-only).", '',
             'Install IDs keep same-named skills from different collections in separate directories. '
             'The upstream `name` in each skill remains unchanged.', '',
             '| Install ID | Skill | Collection | License | Files |',
             '| --- | --- | --- | --- | --- |']
    for item in entries:
        files = f"[SKILL.md](../{item['path']}/SKILL.md)" if 'path' in item else '[Provider](providers.md)'
        lines.append(f"| `{item['id']}` | {item['name']} | {item['collection']} | {item['license']} | {files} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = render()
    path = REPO / 'docs/catalog.md'
    if args.check:
        if not path.exists() or path.read_text(encoding='utf-8') != expected:
            parser.error('docs/catalog.md is stale; run python3 scripts/catalog.py')
    else:
        path.write_text(expected, encoding='utf-8')


if __name__ == '__main__':
    main()
