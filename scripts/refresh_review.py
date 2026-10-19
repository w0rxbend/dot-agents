#!/usr/bin/env python3
"""Carry the skill review forward after a deliberate catalog refresh.

Each review row records the tree sha256 it was reviewed at. A catalog skill
whose sha256 still matches its row is carried forward unchanged. A skill whose
tree changed keeps its previous verdict for reference but is marked
`reviewed: false` with `needs_review`, and a skill without a row gets a static
entrypoint scan, also marked `reviewed: false`. validate.py fails until a
maintainer has read the changes and cleared the rows:

    python3 scripts/refresh_review.py                      # record changes
    python3 scripts/refresh_review.py --list               # show rows needing review
    python3 scripts/refresh_review.py --mark-reviewed all-changed --note "why"
    python3 scripts/refresh_review.py --mark-reviewed astro,debug --note "why"

--mark-reviewed accepts comma-separated install IDs or `all-changed` (every
row currently needing review) and requires --note, which is recorded in the
row's `review_log` together with the reviewed sha256.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone

from common import REPO, dump_json, load_catalog

ALL_CHANGED = 'all-changed'


def now():
    return datetime.now(timezone.utc).isoformat()


def entry_stats(path):
    skill = path / 'SKILL.md'
    text = skill.read_text(encoding='utf-8', errors='replace')
    return dict(
        entry_sha256=hashlib.sha256(skill.read_bytes()).hexdigest(),
        words=len(re.findall(r'\S+', text)),
        line_count=text.count('\n') + 1,
    )


def static_review_row(item, repo=REPO):
    """Pre-scan a newly added skill; a maintainer still has to review it."""
    if 'path' not in item:
        return dict(id=item['id'], name=item['name'], source=item['source'],
                    distribution=item['distribution'], path=None, reviewed=False,
                    needs_review='new provider-managed entry',
                    review_method='Provider-managed skill; metadata entry only, content not vendored.',
                    automatic_discovery_preserved=True, decision='provider-managed',
                    reasons=['Provider-managed skill recorded during catalog refresh.'],
                    local_fork=False, modified_files=[],
                    evidence=dict(source_attribution_preserved=True,
                                  optional_frontmatter_preserved=True),
                    sha256=item['sha256'])
    path = repo / item['path']
    reasons = []
    files = sorted(p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file())
    executable = [p for p in path.rglob('*') if p.is_file() and p.stat().st_mode & 0o111]
    if executable:
        reasons.append('Contains executable files reviewed as data, not run: '
                       + ', '.join(sorted(p.relative_to(path).as_posix() for p in executable)))
    text = (path / 'SKILL.md').read_text(encoding='utf-8', errors='replace')
    for pattern, why in ((r'curl[^|`]*\|\s*(sh|bash)', 'pipes a download into a shell'),
                         (r'rm\s+-rf\s+~', 'recursively deletes from home'),
                         (r'(?:ssh|https?)://[^\s`]*@', 'embeds credentials in a URL')):
        if re.search(pattern, text):
            reasons.append(f'Entrypoint matches {pattern!r}: {why}')
    stats = entry_stats(path)
    return dict(
        id=item['id'], name=item['name'], source=item['source'],
        distribution=item['distribution'],
        path=item.get('path'), reviewed=False,
        needs_review='new skill',
        review_method='Static entrypoint and bundled-file scan during catalog refresh; no helper executed.',
        automatic_discovery_preserved=True,
        decision='retain',
        reasons=reasons or ['Automated scan found no flagged patterns in the entrypoint.'],
        local_fork=False,
        modified_files=[],
        evidence=dict(source_attribution_preserved=True, optional_frontmatter_preserved=True),
        bundled_files=files,
        **stats,
        current_entry_sha256=stats['entry_sha256'],
        current_entry_words=stats['words'],
        sha256=item['sha256'],
    )


def changed_row(old, item, repo=REPO):
    row = dict(old)
    row.update(reviewed=False, sha256=item['sha256'],
               needs_review=f"tree changed since review at {old.get('sha256', '?')[:12]}")
    row['post_review_changes'] = [*old.get('post_review_changes', []),
                                  dict(at=now(), from_sha256=old.get('sha256'),
                                       tree_sha256=item['sha256'])]
    if item.get('path'):
        stats = entry_stats(repo / item['path'])
        row.update(current_entry_sha256=stats['entry_sha256'],
                   current_entry_words=stats['words'], line_count=stats['line_count'])
    return row


def refresh(repo=REPO, mark=None, note=None):
    """Update docs/skill-review.json; return counts and the ids still needing review."""
    catalog = load_catalog(repo)['skills']
    review_path = repo / 'docs/skill-review.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    old_rows = {row['id']: row for row in review['skills']}

    rows, counts = [], dict(carried=0, changed=0, added=0, marked=0)
    for item in catalog:
        old = old_rows.get(item['id'])
        if old and old.get('sha256') == item['sha256']:
            rows.append(old)
            counts['carried'] += 1
        elif old:
            rows.append(changed_row(old, item, repo))
            counts['changed'] += 1
        else:
            rows.append(static_review_row(item, repo))
            counts['added'] += 1

    if mark:
        by_id = {row['id']: row for row in rows}
        pending = {row['id'] for row in rows if not row.get('reviewed')}
        ids = pending if mark == [ALL_CHANGED] else set(mark)
        unknown = ids - set(by_id)
        if unknown:
            raise ValueError('unknown skill ids: ' + ', '.join(sorted(unknown)))
        for skill_id in sorted(ids):
            row = by_id[skill_id]
            row['reviewed'] = True
            row.pop('needs_review', None)
            row['review_log'] = [*row.get('review_log', []),
                                 dict(at=now(), note=note, sha256=row['sha256'])]
            counts['marked'] += 1

    rows.sort(key=lambda row: row['id'])
    decisions = {}
    for row in rows:
        decisions[row['decision']] = decisions.get(row['decision'], 0) + 1
    pending = sorted(row['id'] for row in rows if not row.get('reviewed'))
    external = sum(1 for i in catalog if i['distribution'] == 'external')
    review.update(
        skills=rows,
        summary=dict(review['summary'],
                     baseline_catalog_skills=len(catalog),
                     per_skill_decisions=len(rows),
                     final_catalog_skills=len(catalog),
                     public_vendored_skills=sum(1 for i in catalog if i['distribution'] == 'vendored'),
                     external_skills=external,
                     provider_managed_skills=external,
                     decisions=decisions,
                     carried_forward=counts['carried'],
                     refreshed_after_change=counts['changed'],
                     added=counts['added'],
                     needs_review=len(pending)),
    )
    if counts['changed'] or counts['added'] or counts['marked']:
        review['reviewed_at'] = now()
    dump_json(review_path, review)
    return counts, pending


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mark-reviewed', metavar='IDS',
                        help=f'comma-separated install IDs, or {ALL_CHANGED}, to record as reviewed')
    parser.add_argument('--note', help='what was reviewed and why it is acceptable (required with --mark-reviewed)')
    parser.add_argument('--list', action='store_true', help='print the IDs that still need review')
    args = parser.parse_args(argv)
    mark = None
    if args.mark_reviewed:
        if not args.note:
            parser.error('--mark-reviewed requires --note')
        mark = [part for part in args.mark_reviewed.split(',') if part]
        if ALL_CHANGED in mark and len(mark) > 1:
            parser.error(f'{ALL_CHANGED} cannot be combined with explicit IDs')
    try:
        counts, pending = refresh(mark=mark, note=args.note)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"review: {counts['carried']} carried, {counts['changed']} changed, "
          f"{counts['added']} new, {counts['marked']} marked reviewed; "
          f'{len(pending)} need review')
    if args.list:
        print('\n'.join(pending))
    elif pending:
        print('run with --list to see them, then --mark-reviewed after reading the changes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
