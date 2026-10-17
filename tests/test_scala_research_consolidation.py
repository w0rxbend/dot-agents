"""Incremental consolidation of accepted skills; synthetic fixtures only, never research evidence."""
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.common import tree_hash
from scripts.scala_research import supervisor as s


class Runner:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def check_running(self):
        pass

    def command(self, label, command, seconds):
        self.calls.append(command)
        return 2 if self.fail_on and self.fail_on in command else 0


class ConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.checkout, self.state = root / 'checkout', root / 'state'
        for path in ('collections/shared/scala-library-contracts', 'collections/hermes', 'docs',
                     'research/scala-history'):
            (self.checkout / path).mkdir(parents=True)
        (self.checkout / 'collections/shared/scala-library-contracts/LICENSE').write_text('Synthetic MIT fixture')
        for path in ('docs/catalog.md', 'install.conf.yaml'):
            (self.checkout / path).write_text('Synthetic generated-file fixture')
        s.atomic_json(self.checkout / 'docs/skill-review.json', {'skills': [], 'summary': {}})
        s.atomic_json(self.checkout / 'catalog.json', {'skills': []})
        s.atomic_json(self.state / 'inventory.json', {'repositories': [
            {'repo': 'zio/zio', 'included': True}, {'repo': 'typelevel/cats-effect', 'included': True},
            {'repo': 'lihaoyi/empty', 'included': True}]})
        s.atomic_json(self.state / 'jobs/lihaoyi--empty.json', {'repository': 'lihaoyi/empty',
                      'status': 'blocked', 'reason': 'Synthetic: no history in window.'})
        for patcher in (patch.object(s, 'ROOT', self.checkout),
                        patch.object(s, 'accepted_job', side_effect=self.accepted),
                        patch.dict(sys.modules, {'scripts.scala_research.quality': self.quality()})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def quality(self):
        module = types.ModuleType('scripts.scala_research.quality')
        module.validate_candidate = lambda *args: []
        module.validate_review = lambda *args: []
        return module

    def accepted(self, state, repository):
        row = s.load(Path(state) / 'jobs' / f'{s.key(repository)}.json')
        candidate = Path(state) / 'candidates' / s.key(repository)
        return row.get('status') == 'accepted' and row.get('candidate_sha256') == s.tree_sha(candidate)

    def write_skill(self, candidate, sid, kind, body='Synthetic fixture body.'):
        skill = candidate / 'skills' / sid
        (skill / 'references').mkdir(parents=True, exist_ok=True)
        (skill / 'SKILL.md').write_text(
            f'---\nname: {sid}\ndescription: Use when testing {sid}. Synthetic only.\nlicense: MIT\n---\n{body}\n')
        (skill / 'references/evidence.json').write_text('{"synthetic": true}\n')
        report = candidate / 'report.json'
        data = s.load(report) if report.exists() else {'status': 'complete', 'skills': []}
        data['skills'] = [x for x in data['skills'] if x['id'] != sid] + [{'id': sid, 'kind': kind}]
        s.atomic_json(report, data)

    def accept(self, repository, skills, model='synthetic-model', write=True):
        candidate = self.state / 'candidates' / s.key(repository)
        for sid, kind in skills:
            if write or not (candidate / 'skills' / sid).is_dir():
                self.write_skill(candidate, sid, kind)
        review = self.state / 'reviews' / f'{s.key(repository)}.json'
        s.atomic_json(review, {'verdict': 'accept'})
        job = dict(repository=repository, status='accepted', attempt=1, model=model,
                   provider='synthetic', skill_ids=[sid for sid, _ in skills],
                   candidate_sha256=s.tree_sha(candidate), review_sha256=s.sha(review))
        s.atomic_json(self.state / 'jobs' / f'{s.key(repository)}.json', job)
        return candidate, job

    def catalog_ids(self):
        return [row['id'] for row in s.load(self.checkout / 'catalog.json')['skills']]

    def test_promotes_new_accepted_skills_with_provenance(self):
        self.accept('zio/zio', [('scala-zio-b', 'review'), ('scala-zio-a', 'hardening')])
        runner = Runner()
        result = s.promote_accepted(self.state, runner)
        self.assertEqual('passed', result['status'])
        self.assertEqual(['scala-zio-a', 'scala-zio-b'], self.catalog_ids())
        for sid in ('scala-zio-a', 'scala-zio-b'):
            dest = self.checkout / 'collections/shared' / sid
            self.assertTrue((dest / 'LICENSE').is_file())
            self.assertEqual(f'../shared/{sid}', os.readlink(self.checkout / 'collections/hermes' / sid))
            entry = next(r for r in s.load(self.checkout / 'catalog.json')['skills'] if r['id'] == sid)
            self.assertEqual(tree_hash(dest), entry['sha256'])
        ledger = s.load(self.checkout / 'research/scala-history/promoted-skills.json')
        row = ledger['skills']['scala-zio-a']
        self.assertEqual(('zio/zio', 'hardening', 'synthetic-model'), (row['repository'], row['kind'], row['model']))
        self.assertEqual(4, len(runner.calls))

    def test_active_deepen_uses_verified_snapshot_not_live_candidate(self):
        candidate, job = self.accept('typelevel/cats-effect', [('scala-ce-old', 'review')])
        snapshot = self.state / 'deepen-snapshots/ce'
        (snapshot).mkdir(parents=True)
        os.rename(candidate, snapshot / 'candidate')
        os.rename(self.state / 'reviews/typelevel--cats-effect.json', snapshot / 'review.json')
        self.write_skill(candidate, 'scala-ce-half-written', 'review')
        s.atomic_json(self.state / 'jobs/typelevel--cats-effect.json',
                      {'repository': 'typelevel/cats-effect', 'status': 'researching'})
        s.atomic_json(self.state / 'deepen/typelevel--cats-effect.json', dict(
            repository='typelevel/cats-effect', status='active', snapshot=str(snapshot), prior_job=job))
        s.promote_accepted(self.state, Runner())
        self.assertEqual(['scala-ce-old'], self.catalog_ids())

    def test_tampered_deepen_snapshot_is_not_promoted(self):
        candidate, job = self.accept('typelevel/cats-effect', [('scala-ce-old', 'review')])
        snapshot = self.state / 'deepen-snapshots/ce'
        snapshot.mkdir(parents=True)
        os.rename(candidate, snapshot / 'candidate')
        os.rename(self.state / 'reviews/typelevel--cats-effect.json', snapshot / 'review.json')
        (snapshot / 'candidate/skills/scala-ce-old/SKILL.md').write_text('tampered')
        s.atomic_json(self.state / 'jobs/typelevel--cats-effect.json',
                      {'repository': 'typelevel/cats-effect', 'status': 'researching'})
        s.atomic_json(self.state / 'deepen/typelevel--cats-effect.json', dict(
            repository='typelevel/cats-effect', status='active', snapshot=str(snapshot), prior_job=job))
        result = s.promote_accepted(self.state, Runner())
        self.assertEqual([], self.catalog_ids())
        self.assertIn('typelevel/cats-effect', result['unverified'])

    def test_rerun_without_changes_runs_no_gates(self):
        self.accept('zio/zio', [('scala-zio-a', 'review')])
        s.promote_accepted(self.state, Runner())
        catalog = (self.checkout / 'catalog.json').read_bytes()
        runner = Runner()
        self.assertEqual('unchanged', s.promote_accepted(self.state, runner)['status'])
        self.assertEqual([], runner.calls)
        self.assertEqual(catalog, (self.checkout / 'catalog.json').read_bytes())

    def test_new_acceptance_updates_previously_promoted_skill(self):
        candidate, _ = self.accept('zio/zio', [('scala-zio-a', 'review')])
        s.promote_accepted(self.state, Runner())
        self.accept('zio/zio', [('scala-zio-a', 'review'), ('scala-zio-new', 'refactoring')])
        (candidate / 'skills/scala-zio-a/SKILL.md').write_text(
            '---\nname: scala-zio-a\ndescription: Use when testing deepened text.\nlicense: MIT\n---\nDeeper.\n')
        self.accept('zio/zio', [('scala-zio-a', 'review'), ('scala-zio-new', 'refactoring')], write=False)
        result = s.promote_accepted(self.state, Runner())
        self.assertEqual(['scala-zio-a'], result['updated'])
        self.assertEqual(['scala-zio-new'], result['added'])
        dest = self.checkout / 'collections/shared/scala-zio-a'
        self.assertIn('Deeper.', (dest / 'SKILL.md').read_text())
        entry = next(r for r in s.load(self.checkout / 'catalog.json')['skills'] if r['id'] == 'scala-zio-a')
        self.assertEqual(tree_hash(dest), entry['sha256'])

    def test_local_edits_to_promoted_skill_are_never_overwritten(self):
        candidate, _ = self.accept('zio/zio', [('scala-zio-a', 'review')])
        s.promote_accepted(self.state, Runner())
        dest = self.checkout / 'collections/shared/scala-zio-a/SKILL.md'
        dest.write_text(dest.read_text() + '\nUser edit.\n')
        (candidate / 'skills/scala-zio-a/references/evidence.json').write_text('{"changed": true}\n')
        self.accept('zio/zio', [('scala-zio-a', 'review')], write=False)
        with self.assertRaisesRegex(ValueError, 'locally modified'):
            s.promote_accepted(self.state, Runner())
        self.assertIn('User edit.', dest.read_text())

    def test_unrelated_catalog_skill_with_same_id_is_refused(self):
        s.atomic_json(self.checkout / 'catalog.json', {'skills': [{'id': 'scala-zio-a'}]})
        self.accept('zio/zio', [('scala-zio-a', 'review')])
        with self.assertRaisesRegex(ValueError, 'not promoted by this pipeline'):
            s.promote_accepted(self.state, Runner())
        self.assertFalse((self.checkout / 'collections/shared/scala-zio-a').exists())

    def test_duplicate_skill_across_repositories_is_refused(self):
        self.accept('zio/zio', [('scala-shared-id', 'review')])
        self.accept('typelevel/cats-effect', [('scala-shared-id', 'review')])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            s.promote_accepted(self.state, Runner())
        self.assertEqual([], self.catalog_ids())

    def test_gate_failure_rolls_back_every_change(self):
        candidate, _ = self.accept('zio/zio', [('scala-zio-a', 'review')])
        s.promote_accepted(self.state, Runner())
        before = {p: (self.checkout / p).read_bytes() for p in (
            'catalog.json', 'research/scala-history/promoted-skills.json',
            'research/scala-history/KNOWLEDGE.md', 'collections/shared/scala-zio-a/SKILL.md')}
        (candidate / 'skills/scala-zio-a/SKILL.md').write_text(
            '---\nname: scala-zio-a\ndescription: Use when testing changed text.\nlicense: MIT\n---\nNew.\n')
        self.accept('zio/zio', [('scala-zio-a', 'review'), ('scala-zio-b', 'hardening')], write=False)
        with self.assertRaisesRegex(RuntimeError, 'gate failed'):
            s.promote_accepted(self.state, Runner(fail_on='check'))
        self.assertEqual(before, {p: (self.checkout / p).read_bytes() for p in before})
        self.assertFalse((self.checkout / 'collections/shared/scala-zio-b').exists())
        self.assertFalse((self.checkout / 'collections/hermes/scala-zio-b').is_symlink())
        self.assertEqual('rolled_back', s.load(self.state / 'consolidation.json')['status'])
        backup = Path(s.load(self.state / 'consolidation.json')['backup'])
        self.assertEqual(before['catalog.json'], (backup / 'catalog.json').read_bytes())
        self.assertEqual(before['research/scala-history/promoted-skills.json'],
                         (backup / 'research/scala-history/promoted-skills.json').read_bytes())

    def test_review_rows_change_only_for_pipeline_owned_skills(self):
        unrelated = {'id': 'unrelated-user-skill', 'sha256': 'user-edit-in-progress', 'reviewed': True,
                     'decision': 'retain', 'note': 'must stay byte-identical'}
        s.atomic_json(self.checkout / 'docs/skill-review.json',
                      {'skills': [unrelated], 'summary': {'decisions': {'retain': 1}}})
        self.accept('zio/zio', [('scala-zio-a', 'review')])
        runner = Runner()
        s.promote_accepted(self.state, runner)
        self.assertFalse(any('refresh_review.py' in ' '.join(c) for c in runner.calls))
        review = s.load(self.checkout / 'docs/skill-review.json')
        rows = {row['id']: row for row in review['skills']}
        self.assertEqual(unrelated, rows['unrelated-user-skill'])
        entry = next(r for r in s.load(self.checkout / 'catalog.json')['skills'] if r['id'] == 'scala-zio-a')
        self.assertTrue(rows['scala-zio-a']['reviewed'])
        self.assertEqual(entry['sha256'], rows['scala-zio-a']['sha256'])
        self.assertIn('independent', rows['scala-zio-a']['review_method'])
        self.assertEqual(2, review['summary']['decisions']['retain'])

    def test_knowledge_index_and_hub_routing_table_are_generated(self):
        hub = self.checkout / 'collections/shared' / s.HUB_SKILL
        (hub / 'references').mkdir(parents=True)
        (hub / 'SKILL.md').write_text(f'---\nname: {s.HUB_SKILL}\ndescription: Use when routing.\nlicense: MIT\n---\nHub.\n')
        s.atomic_json(self.checkout / 'catalog.json', {'skills': [dict(
            id=s.HUB_SKILL, name=s.HUB_SKILL, collection='shared', source='local',
            distribution='vendored', path=f'collections/shared/{s.HUB_SKILL}', sha256=tree_hash(hub))]})
        self.accept('zio/zio', [('scala-zio-a', 'hardening')])
        s.promote_accepted(self.state, Runner())
        knowledge = (self.checkout / 'research/scala-history/KNOWLEDGE.md').read_text()
        self.assertIn('scala-zio-a', knowledge)
        self.assertIn('lihaoyi/empty', knowledge)
        self.assertIn('Synthetic: no history in window.', knowledge)
        index = (hub / 'references/skill-index.md').read_text()
        self.assertIn('scala-zio-a', index)
        entry = next(r for r in s.load(self.checkout / 'catalog.json')['skills'] if r['id'] == s.HUB_SKILL)
        self.assertEqual(tree_hash(hub), entry['sha256'])

    def merge_by_hand(self, sid, target):
        """Simulate folding a promoted skill into a hand-written broader skill."""
        ledger_path = self.checkout / 'research/scala-history/promoted-skills.json'
        ledger = s.load(ledger_path)
        ledger['skills'][sid]['merged_into'] = target
        s.atomic_json(ledger_path, ledger)
        dest = self.checkout / 'collections/shared' / target
        dest.mkdir(parents=True)
        (dest / 'SKILL.md').write_text(f'---\nname: {target}\ndescription: Use when testing merged.\nlicense: MIT\n---\n')
        for path in (self.checkout / 'collections/shared' / sid, self.checkout / 'collections/hermes' / sid):
            path.unlink() if path.is_symlink() else shutil.rmtree(path)
        s.atomic_json(self.checkout / 'catalog.json', {'skills': [
            r for r in s.load(self.checkout / 'catalog.json')['skills'] if r['id'] != sid]})

    def test_merged_skill_is_not_repromoted_and_is_indexed_under_its_target(self):
        self.accept('zio/zio', [('scala-zio-a', 'review'), ('scala-zio-b', 'hardening')])
        s.promote_accepted(self.state, Runner())
        self.merge_by_hand('scala-zio-a', 'scala-zio-merged')
        result = s.promote_accepted(self.state, Runner())
        self.assertEqual(['scala-zio-a', 'scala-zio-b'], result['unchanged'])
        self.assertFalse((self.checkout / 'collections/shared/scala-zio-a').exists())
        self.assertNotIn('scala-zio-a', self.catalog_ids())
        knowledge = (self.checkout / 'research/scala-history/KNOWLEDGE.md').read_text()
        self.assertIn('| `scala-zio-merged` | zio/zio | zio-a (review) | Use when testing merged. |', knowledge)
        self.assertIn('merged into `scala-zio-merged`', knowledge)
        self.assertIn('Installed as 2 skills', knowledge)

    def test_new_acceptance_for_merged_skill_is_refused(self):
        candidate, _ = self.accept('zio/zio', [('scala-zio-a', 'review')])
        s.promote_accepted(self.state, Runner())
        self.merge_by_hand('scala-zio-a', 'scala-zio-merged')
        (candidate / 'skills/scala-zio-a/references/evidence.json').write_text('{"changed": true}\n')
        self.accept('zio/zio', [('scala-zio-a', 'review')], write=False)
        with self.assertRaisesRegex(ValueError, 'merged into scala-zio-merged'):
            s.promote_accepted(self.state, Runner())
        self.assertFalse((self.checkout / 'collections/shared/scala-zio-a').exists())


if __name__ == '__main__':
    unittest.main()
