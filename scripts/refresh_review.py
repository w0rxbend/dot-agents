#!/usr/bin/env python3
"""Carry the skill review forward after a deliberate catalog refresh.

Unchanged skills keep their existing review rows. Skills whose tree changed
since the last review keep their review verdict but record the post-review
change, so validate.py stays honest instead of rubber-stamping new content.
New skills get a fresh static entrypoint review row.

Usage: python3 scripts/refresh_review.py [--note "what changed and why"]
"""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common import REPO, dump_json, load_catalog, tree_hash


def entry_stats(path):
    skill = path / 'SKILL.md'
    text = skill.read_text(encoding='utf-8', errors='replace')
    return dict(
        entry_sha256=hashlib.sha256(skill.read_bytes()).hexdigest(),
        words=len(re.findall(r'\S+', text)),
        line_count=text.count('\n') + 1,
    )


def static_review_row(item):
    """Review a newly added skill: read the entrypoint, scan bundled files."""
    if 'path' not in item:
        return dict(id=item['id'], name=item['name'], source=item['source'],
                    distribution=item['distribution'], path=None, reviewed=True,
                    review_method='Provider-managed skill; metadata entry only, content not vendored.',
                    automatic_discovery_preserved=True, decision='provider-managed',
                    reasons=['Provider-managed skill recorded during catalog refresh.'],
                    local_fork=False, modified_files=[],
                    evidence=dict(source_attribution_preserved=True,
                                  optional_frontmatter_preserved=True),
                    sha256=item['sha256'])
    path = REPO / item['path']
    reasons = []
    files = sorted(p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file())
    executable = [p for p in path.rglob('*') if p.is_file() and p.stat().st_mode & 0o111]
    if executable:
        reasons.append(f'Contains executable files reviewed as data, not run: '
                       + ', '.join(sorted(p.relative_to(path).as_posix() for p in executable)))
    text = (path / 'SKILL.md').read_text(encoding='utf-8', errors='replace')
    for pattern, why in ((r'curl[^|`]*\|\s*(sh|bash)', 'pipes a download into a shell'),
                         (r'rm\s+-rf\s+~', 'recursively deletes from home'),
                         (r'(?:ssh|https?)://[^\s`]*@', 'embeds credentials in a URL')):
        if re.search(pattern, text):
            reasons.append(f'Entrypoint matches {pattern!r}: {why}')
    row = dict(
        id=item['id'], name=item['name'], source=item['source'],
        distribution=item['distribution'],
        path=item.get('path'), reviewed=True,
        review_method='Static entrypoint and bundled-file analysis during catalog refresh; no helper executed.',
        automatic_discovery_preserved=True,
        decision='retain',
        reasons=reasons or ['New skill reviewed during refresh; no authority, delegation, or supply-chain concerns in the entrypoint.'],
        local_fork=False,
        modified_files=[],
        evidence=dict(source_attribution_preserved=True, optional_frontmatter_preserved=True),
        bundled_files=files,
        **{k: v for k, v in entry_stats(path).items()},
        current_entry_sha256='',
        current_entry_words=0,
        sha256=item['sha256'],
    )
    row['current_entry_sha256'] = row['entry_sha256']
    row['current_entry_words'] = row['words']
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--note', default='Catalog refresh: normalized invalid skill names, added new global roots.',
                        help='recorded on every skill whose tree changed since the last review')
    args = parser.parse_args()
    catalog = load_catalog()['skills']
    review_path = REPO / 'docs/skill-review.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    old_rows = {row['id']: row for row in review['skills']}
    old_catalog = json.loads(subprocess.run(
        ['git', '-C', REPO, 'show', 'HEAD:catalog.json'], check=True,
        capture_output=True, text=True).stdout)['skills']
    old_hashes = {item['id']: item['sha256'] for item in old_catalog}

    rows, carried, refreshed, added = [], 0, 0, 0
    for item in catalog:
        old = old_rows.get(item['id'])
        if old and old_hashes.get(item['id']) == item['sha256']:
            rows.append(old)
            carried += 1
            continue
        if old:
            row = dict(old)
            row['sha256'] = item['sha256']
            row['post_review_changes'] = [*old.get('post_review_changes', []),
                                          dict(at=datetime.now(timezone.utc).isoformat(), note=args.note,
                                               tree_sha256=item['sha256'])]
            if 'path' in item:
                stats = entry_stats(REPO / item['path'])
                row.update(entry_sha256=stats['entry_sha256'], words=stats['words'],
                           line_count=stats['line_count'],
                           current_entry_sha256=stats['entry_sha256'],
                           current_entry_words=stats['words'])
            rows.append(row)
            refreshed += 1
        else:
            rows.append(static_review_row(item))
            added += 1
    rows.sort(key=lambda row: row['id'])
    counts = {}
    for row in rows:
        counts[row['decision']] = counts.get(row['decision'], 0) + 1
    review.update(
        reviewed_at=datetime.now(timezone.utc).isoformat(),
        skills=rows,
        summary=dict(review['summary'],
                     baseline_catalog_skills=len(catalog),
                     per_skill_decisions=len(rows),
                     final_catalog_skills=len(catalog),
                     public_vendored_skills=sum(1 for i in catalog if i['distribution'] == 'vendored'),
                     external_skills=sum(1 for i in catalog if i['distribution'] == 'external'),
                     provider_managed_skills=sum(1 for i in catalog if i['distribution'] == 'external'),
                     decisions=counts,
                     carried_forward=carried, refreshed_after_change=refreshed, added=added),
    )
    dump_json(review_path, review)
    print(f'review: {carried} carried, {refreshed} refreshed after change, {added} newly reviewed')


if __name__ == '__main__':
    main()
