#!/usr/bin/env python3
"""Incrementally consolidate independently accepted skills into the dot-agents catalog.

Unlike the all-or-nothing portfolio promotion, this integrates every accepted
repository package as it becomes available, records provenance in a ledger,
regenerates a cross-repository knowledge index, and rolls everything back if
any catalog gate fails. It never deletes a promoted skill and never overwrites
a skill it did not promote or one that was edited locally after promotion.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

LEDGER = 'research/scala-history/promoted-skills.json'
KNOWLEDGE = 'research/scala-history/KNOWLEDGE.md'
HUB_SKILL = 'scala-oss-library-review'
HUB_INDEX = 'references/skill-index.md'
GENERATED = ['catalog.json', 'docs/skill-review.json', 'docs/catalog.md', 'install.conf.yaml']
KIND_ORDER = ['development', 'review', 'refactoring', 'hardening']


class LocalRunner:
    """Deterministic local catalog gates; not agent workers, so no transient units."""

    def __init__(self, root, state, seconds=1800):
        self.root, self.state = Path(root), Path(state)
        self.deadline = time.monotonic() + seconds

    def check_running(self):
        if time.monotonic() >= self.deadline:
            raise InterruptedError('consolidation budget exhausted')

    def command(self, label, command, seconds):
        self.check_running()
        log = self.state / 'logs' / f'consolidate-{label}.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as stream:
            try:
                return subprocess.run(command, cwd=self.root, stdout=stream, stderr=subprocess.STDOUT,
                                      timeout=min(seconds, max(1, self.deadline - time.monotonic()))).returncode
            except subprocess.TimeoutExpired:
                return 124


def _s():
    from . import supervisor
    return supervisor


def snapshot_accepted(state, repository, record):
    """Re-verify a deepen snapshot with the same gates as a live accepted package."""
    s = _s()
    from .quality import validate_candidate, validate_review
    snapshot = Path(record['snapshot'])
    job = record.get('prior_job') or {}
    candidate, review = snapshot / 'candidate', snapshot / 'review.json'
    try:
        if (job.get('status') != 'accepted' or job.get('repository', '').lower() != repository.lower()
                or s.tree_sha(candidate) != job.get('candidate_sha256')
                or s.sha(review) != job.get('review_sha256')
                or validate_candidate(candidate, repository)
                or s.load(review).get('verdict') != 'accept'):
            return False
        # Review evidence paths are relative to the review file: rebuild that layout.
        with tempfile.TemporaryDirectory(dir=state) as temp:
            temp = Path(temp)
            shutil.copy2(review, temp / 'review.json')
            if (snapshot / 'evaluation').is_dir():
                shutil.copytree(snapshot / 'evaluation', temp / 'evaluations' / s.key(repository))
            return not validate_review(temp / 'review.json', candidate, repository)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def accepted_packages(state):
    """Every verified accepted package, preferring an active deepen run's snapshot."""
    s = _s()
    state = Path(state)
    packages, unverified = {}, []
    for item in s.load(state / 'inventory.json')['repositories']:
        if not item['included']:
            continue
        repository, repo_key = item['repo'], s.key(item['repo'])
        record_path = state / 'deepen' / f'{repo_key}.json'
        record = s.load(record_path) if record_path.is_file() else None
        if record and record.get('status') == 'active':
            if snapshot_accepted(state, repository, record):
                packages[repository] = (Path(record['snapshot']) / 'candidate', record['prior_job'])
            else:
                unverified.append(repository)
            continue
        job_path = state / 'jobs' / f'{repo_key}.json'
        if not job_path.is_file() or s.load(job_path).get('status') != 'accepted':
            continue
        if s.accepted_job(state, repository):
            packages[repository] = (state / 'candidates' / repo_key, s.load(job_path))
        else:
            unverified.append(repository)
    return packages, unverified


def review_row(root, sid, entry, provenance):
    """Review row for a pipeline-owned skill, mirroring refresh_review's static schema."""
    import hashlib
    import re
    path = Path(root) / entry['path']
    text = (path / 'SKILL.md').read_text(encoding='utf-8', errors='replace')
    words = len(re.findall(r'\S+', text))
    entry_sha = hashlib.sha256((path / 'SKILL.md').read_bytes()).hexdigest()
    method = ('Historical research pipeline: independent evidence audit and model-based behavioral '
              'evaluation before promotion; static entrypoint scan; no helper executed.')
    reasons = ['Hand-authored routing skill for the history-derived Scala collection; makes no historical claims.']
    if provenance:
        reasons = [f'Authored from {provenance["repository"]} 2018-2024 source and PR review history; '
                   f'independently accepted (review sha256 {provenance["review_sha256"][:12]}).']
    return dict(id=sid, name=entry['name'], source=entry['source'], distribution=entry['distribution'],
                path=entry['path'], reviewed=True, review_method=method,
                automatic_discovery_preserved=True, decision='retain', reasons=reasons,
                local_fork=False, modified_files=[],
                evidence=dict(source_attribution_preserved=True, optional_frontmatter_preserved=True),
                bundled_files=sorted(p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file()),
                entry_sha256=entry_sha, words=words, line_count=text.count('\n') + 1,
                current_entry_sha256=entry_sha, current_entry_words=words, sha256=entry['sha256'])


def update_review(root, rows):
    """Replace review rows only for the given pipeline-owned skills; leave all others untouched."""
    s = _s()
    path = Path(root) / 'docs/skill-review.json'
    review = json.loads(path.read_text(encoding='utf-8'))
    merged = {row['id']: row for row in review['skills']}
    merged.update(rows)
    review['skills'] = [merged[k] for k in sorted(merged)]
    summary = dict(review.get('summary') or {})
    decisions = {}
    for row in review['skills']:
        decisions[row['decision']] = decisions.get(row['decision'], 0) + 1
    catalog = json.loads((Path(root) / 'catalog.json').read_text(encoding='utf-8'))['skills']
    for field in ('baseline_catalog_skills', 'final_catalog_skills'):
        if field in summary:
            summary[field] = len(catalog)
    if 'per_skill_decisions' in summary:
        summary['per_skill_decisions'] = len(review['skills'])
    if 'public_vendored_skills' in summary:
        summary['public_vendored_skills'] = sum(1 for i in catalog if i.get('distribution') == 'vendored')
    summary['decisions'] = decisions
    review['summary'] = summary
    try:
        from scripts.common import dump_json
        dump_json(path, review)
    except ImportError:
        s.atomic_json(path, review)


def _description(skill_md):
    from scripts.common import frontmatter
    return frontmatter(skill_md)


def _first_sentence(text):
    head = text.strip().split('. ')[0].rstrip('.')
    return head + '.'


def _outcomes(state, ledger):
    s = _s()
    promoted = {}
    for sid, row in ledger.items():
        promoted.setdefault(row['repository'], []).append(sid)
    rows = []
    for item in s.load(Path(state) / 'inventory.json')['repositories']:
        if not item['included']:
            continue
        repository = item['repo']
        if repository in promoted:
            rows.append((repository, f'{len(promoted[repository])} promoted skill(s)'))
            continue
        job_path = Path(state) / 'jobs' / f'{s.key(repository)}.json'
        job = s.load(job_path) if job_path.is_file() else {}
        reason = ' '.join((job.get('reason') or 'not yet researched in an authoring run').split())
        if len(reason) > 220:
            reason = reason[:217].rstrip() + '...'
        rows.append((repository, f'{job.get("status", "pending")}: {reason}'))
    return rows


def render_knowledge(state, ledger, descriptions):
    by_repo = {}
    for sid, row in sorted(ledger.items()):
        by_repo.setdefault(row['repository'], []).append(sid)
    counts = {kind: sum(1 for r in ledger.values() if r['kind'] == kind) for kind in KIND_ORDER}
    lines = ['# Historical Scala library knowledge (2018-2024)', '',
             'Generated by `python3 -m scripts.scala_research.supervisor consolidate`; do not edit by hand.',
             'Every skill below was authored from 2018-01-01..2024-12-31 UTC source and PR review history,',
             'then independently audited and behaviorally evaluated before promotion. Each skill carries its',
             'own `references/evidence.json` with pinned SHAs and exact review-comment permalinks.', '',
             f'Promoted skills: {len(ledger)} from {len(by_repo)} repositories '
             f'({", ".join(f"{counts[k]} {k}" for k in KIND_ORDER)}).',
             f'Start with the routing skill `{HUB_SKILL}` when unsure which one applies.', '']
    for repository in sorted(by_repo, key=str.lower):
        lines += [f'## {repository}', '', '| Skill | Kind | Use when |', '| --- | --- | --- |']
        for sid in by_repo[repository]:
            lines.append(f'| `{sid}` | {ledger[sid]["kind"]} | {descriptions[sid]} |')
        lines.append('')
    lines += ['## Repository outcomes', '',
              'Repositories without promoted skills, with the reason recorded by the research pipeline.', '',
              '| Repository | Outcome |', '| --- | --- |']
    lines += [f'| {repo} | {outcome.replace("|", "/")} |' for repo, outcome in _outcomes(state, ledger)
              if repo not in by_repo]
    return '\n'.join(lines) + '\n'


def render_hub_index(ledger, descriptions):
    lines = ['# Routing index', '',
             'Generated from the promotion ledger; do not edit by hand. Pick the narrowest skill whose',
             'trigger matches the code under change. Several may apply to one PR.', '']
    for kind in KIND_ORDER:
        ids = sorted(sid for sid, row in ledger.items() if row['kind'] == kind)
        if not ids:
            continue
        lines += [f'## {kind.capitalize()}', '', '| Skill | Repository | Use when |', '| --- | --- | --- |']
        lines += [f'| `{sid}` | {ledger[sid]["repository"]} | {descriptions[sid]} |' for sid in ids]
        lines.append('')
    return '\n'.join(lines) + '\n'


def promote_accepted(state, runner):
    """Integrate every verified accepted skill; all-or-nothing per invocation with rollback."""
    s = _s()
    from scripts.common import tree_hash
    state, root = Path(state), s.ROOT
    runner.check_running()
    with s.exclusive_lock(root / '.git/scala-research-integration.lock'):
        packages, unverified = accepted_packages(state)
        ledger_path, knowledge_path = root / LEDGER, root / KNOWLEDGE
        ledger_doc = s.load(ledger_path) if ledger_path.is_file() else {'schema_version': 1, 'skills': {}}
        ledger = dict(ledger_doc['skills'])
        tracked = GENERATED + [LEDGER, KNOWLEDGE]
        hub = root / 'collections/shared' / HUB_SKILL
        snapshot = {p: (root / p).read_bytes() if (root / p).is_file() else None for p in tracked}
        hub_index = hub / HUB_INDEX
        hub_before = hub_index.read_bytes() if hub_index.is_file() else None
        catalog = json.loads(snapshot['catalog.json'])
        entries = {row['id']: row for row in catalog['skills']}

        owners, actions, sources = {}, {}, {}
        for repository, (candidate, job) in sorted(packages.items()):
            kinds = {row['id']: row.get('kind') for row in s.load(candidate / 'report.json')['skills']}
            for sid in job['skill_ids']:
                if sid in owners:
                    raise ValueError(f'duplicate skill id across repositories: {sid} '
                                     f'({owners[sid]}, {repository})')
                owners[sid] = repository
                source = candidate / 'skills' / sid
                if _description(source / 'SKILL.md')['name'] != sid:
                    raise ValueError(f'skill frontmatter name does not match id: {sid}')
                sources[sid] = (source, repository, kinds.get(sid), job)
                dest = root / 'collections/shared' / sid
                link = root / 'collections/hermes' / sid
                row = ledger.get(sid)
                if row is None:
                    if sid in entries:
                        raise ValueError(f'catalog already has {sid}, not promoted by this pipeline')
                    if dest.exists() or link.exists() or link.is_symlink():
                        raise ValueError(f'promotion destination already exists: {sid}')
                    actions[sid] = 'add'
                elif row['source_tree_sha256'] == tree_hash(source) and row['repository'] == repository:
                    actions[sid] = 'unchanged'
                else:
                    if not dest.is_dir() or tree_hash(dest) != row['promoted_tree_sha256']:
                        raise ValueError(f'{sid} was locally modified after promotion; reconcile by hand')
                    actions[sid] = 'update'

        descriptions = {}
        for sid, row in ledger.items():
            path = root / 'collections/shared' / sid / 'SKILL.md'
            if path.is_file():
                descriptions[sid] = _first_sentence(_description(path)['description'])
        for sid, (source, *_rest) in sources.items():
            descriptions[sid] = _first_sentence(_description(source / 'SKILL.md')['description'])
        new_ledger = dict(ledger)
        for sid, (source, repository, kind, job) in sources.items():
            if actions[sid] == 'unchanged':
                continue
            new_ledger[sid] = dict(repository=repository, kind=kind, model=job.get('model'),
                                   provider=job.get('provider'), candidate_sha256=job['candidate_sha256'],
                                   review_sha256=job['review_sha256'], source_tree_sha256=tree_hash(source))
        knowledge = render_knowledge(state, new_ledger, descriptions).encode()
        index = render_hub_index(new_ledger, descriptions).encode() if HUB_SKILL in entries and hub.is_dir() else None
        changed = [sid for sid, action in actions.items() if action != 'unchanged']
        result = dict(added=sorted(k for k, v in actions.items() if v == 'add'),
                      updated=sorted(k for k, v in actions.items() if v == 'update'),
                      unchanged=sorted(k for k, v in actions.items() if v == 'unchanged'),
                      unverified=sorted(unverified), promoted_total=len(new_ledger))
        if not changed and knowledge == snapshot[KNOWLEDGE] and (index is None or index == hub_before):
            s.atomic_json(state / 'consolidation.json', dict(result, status='unchanged', at=s.now()))
            return dict(result, status='unchanged')

        backup = state / 'integration-backup' / f'consolidate-{time.time_ns()}'
        backup.mkdir(parents=True)
        for p, data in snapshot.items():
            if data is not None:
                (backup / p).parent.mkdir(parents=True, exist_ok=True)
                (backup / p).write_bytes(data)
        if hub_before is not None:
            (backup / 'hub-index.md').write_bytes(hub_before)
        created, replaced = [], []

        def rollback():
            for sid in created:
                link = root / 'collections/hermes' / sid
                if link.is_symlink():
                    link.unlink()
                shutil.rmtree(root / 'collections/shared' / sid, ignore_errors=True)
            for sid in replaced:
                dest = root / 'collections/shared' / sid
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(backup / 'skills' / sid, dest, symlinks=True)
            for p, data in snapshot.items():
                if data is None:
                    (root / p).unlink(missing_ok=True)
                else:
                    (root / p).write_bytes(data)
            if index is not None:
                if hub_before is None:
                    hub_index.unlink(missing_ok=True)
                else:
                    hub_index.write_bytes(hub_before)

        try:
            if any(((root / p).read_bytes() if (root / p).is_file() else None) != data
                   for p, data in snapshot.items()):
                raise RuntimeError('shared files changed during consolidation; refusing stale overwrite')
            license_source = root / 'collections/shared/scala-library-contracts/LICENSE'
            for sid in sorted(changed):
                runner.check_running()
                source, *_rest = sources[sid]
                s.tree_sha(source)  # refuses symlinks in candidate trees
                dest = root / 'collections/shared' / sid
                if actions[sid] == 'update':
                    shutil.copytree(dest, backup / 'skills' / sid, symlinks=True)
                    replaced.append(sid)
                    shutil.rmtree(dest)
                else:
                    created.append(sid)
                shutil.copytree(source, dest)
                shutil.copy2(license_source, dest / 'LICENSE')
                entry = dict(id=sid, name=sid, collection='shared', source='local', license='MIT',
                             sha256=tree_hash(dest), local_globs=[f'~/.agents/skills/{sid}', f'~/.hermes/skills/{sid}'],
                             path=f'collections/shared/{sid}', distribution='vendored',
                             license_file=f'collections/shared/{sid}/LICENSE')
                entries[sid] = entry
                new_ledger[sid]['promoted_tree_sha256'] = entry['sha256']
                new_ledger[sid]['promoted_at'] = s.now()
                if actions[sid] == 'add':
                    (root / 'collections/hermes' / sid).symlink_to(f'../shared/{sid}')
            if index is not None:
                hub_index.parent.mkdir(parents=True, exist_ok=True)
                hub_index.write_bytes(index)
                entries[HUB_SKILL] = dict(entries[HUB_SKILL], sha256=tree_hash(hub))
            catalog['skills'] = sorted(entries.values(), key=lambda row: row['id'])
            s.atomic_json(root / 'catalog.json', catalog)
            owned = {sid: review_row(root, sid, entries[sid], new_ledger[sid]) for sid in changed}
            if index is not None:
                owned[HUB_SKILL] = review_row(root, HUB_SKILL, entries[HUB_SKILL], None)
            update_review(root, owned)
            s.atomic_json(ledger_path, dict(schema_version=1, skills=dict(sorted(new_ledger.items()))))
            knowledge_path.parent.mkdir(parents=True, exist_ok=True)
            knowledge_path.write_bytes(knowledge)
            # Review rows are updated above for owned skills only. refresh_review.py diffs against
            # git HEAD and would annotate unrelated uncommitted skills with this pipeline's note.
            gates = [[os.environ.get('PYTHON', 'python3'), 'scripts/catalog.py'],
                     ['./install.sh', 'render'], ['make', 'test'], ['make', 'check']]
            for number, command in enumerate(gates):
                runner.check_running()
                code = runner.command(f'gate-{number}', command, 1200)
                if code:
                    raise RuntimeError(f'integration gate failed ({code}): {" ".join(command)}')
        except BaseException as exc:
            rollback()
            s.atomic_json(state / 'consolidation.json', dict(
                result, status='rolled_back', at=s.now(), backup=str(backup),
                error=f'{type(exc).__name__}: {exc}'))
            raise
        s.atomic_json(state / 'consolidation.json', dict(result, status='passed', at=s.now(), backup=str(backup)))
        return dict(result, status='passed')
