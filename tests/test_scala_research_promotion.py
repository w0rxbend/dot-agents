"""Synthetic promotion fixtures, not historical evidence or real catalog writes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.common import tree_hash
from scripts.scala_research import supervisor as s


class SyntheticRunner:
    def __init__(self):
        self.cancelled = False
        self.calls = []
        self.cancel_on_first = False

    def check_running(self):
        if self.cancelled:
            raise InterruptedError('synthetic cancellation')

    def command(self, label, command, seconds):
        self.check_running()
        self.calls.append(command)
        if self.cancel_on_first:
            self.cancelled = True
        return 0


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.checkout, self.state = root / 'checkout', root / 'state'
        self.state.mkdir()
        self.sid = 'scala-synthetic-fixture'
        for path in ('collections/shared/scala-library-contracts', 'collections/hermes', 'docs'):
            (self.checkout / path).mkdir(parents=True)
        (self.checkout / 'collections/shared/scala-library-contracts/LICENSE').write_text('Synthetic MIT fixture')
        for path in ('docs/catalog.md', 'install.conf.yaml'):
            (self.checkout / path).write_text('Synthetic generated-file fixture')
        self.unrelated = {'id': 'unrelated-user-skill', 'decision': 'retain', 'note': 'uncommitted user edit'}
        s.atomic_json(self.checkout / 'docs/skill-review.json', {'skills': [self.unrelated], 'summary': {}})
        s.atomic_json(self.checkout / 'catalog.json', {'skills': []})
        skill = self.state / 'candidates/zio--zio/skills' / self.sid
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(f'---\nname: {self.sid}\ndescription: Synthetic only.\nlicense: MIT\n---\nFixture.\n')
        s.atomic_json(self.state / 'portfolio-input.json', {'jobs': [
            {'repository': 'zio/zio', 'status': 'accepted', 'skill_ids': [self.sid]}]})
        self.decision = {'verdict': 'accept', 'selected_skill_ids': [self.sid]}
        s.atomic_json(self.state / 'portfolio.json', self.decision)
        self.runner = SyntheticRunner()
        self.root_patch = patch.object(s, 'ROOT', self.checkout)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.acceptance_patch = patch.object(s, 'validate_portfolio', return_value=self.decision)
        self.acceptance_patch.start()
        self.addCleanup(self.acceptance_patch.stop)

    def test_concurrent_catalog_edit_cannot_become_baseline_for_stale_data(self):
        real_sha = s.sha
        injected = False
        def edit_before_hash(path):
            nonlocal injected
            if Path(path) == self.checkout / 'catalog.json' and not injected:
                injected = True
                catalog = s.load(path)
                catalog['skills'].append({'id': 'unrelated-concurrent-edit'})
                s.atomic_json(path, catalog)
            return real_sha(path)
        with patch.object(s, 'sha', side_effect=edit_before_hash):
            with self.assertRaisesRegex(RuntimeError, 'shared files changed'):
                s.promote_portfolio(self.state, self.runner)
        self.assertIn('unrelated-concurrent-edit',
                      [row['id'] for row in s.load(self.checkout / 'catalog.json')['skills']])
        self.assertFalse(self.runner.calls)

    def test_stale_receipt_does_not_certify_missing_skills(self):
        s.atomic_json(self.state / 'promotion.json',
                      {'status': 'passed', 'skill_ids': [self.sid], 'portfolio_sha256': s.sha(self.state / 'portfolio.json')})
        with self.assertRaises(ValueError):
            s.promote_portfolio(self.state, self.runner)
        self.assertFalse(self.runner.calls)

    def test_cancellation_stops_later_gates_and_never_marks_passed(self):
        self.runner.cancel_on_first = True
        with self.assertRaises(InterruptedError):
            s.promote_portfolio(self.state, self.runner)
        self.assertEqual(1, len(self.runner.calls))
        self.assertNotEqual('passed', s.load(self.state / 'promotion.json')['status'])

    def test_promotion_preserves_existing_catalog_entry(self):
        s.atomic_json(self.checkout / 'catalog.json', {'skills': [{'id': 'pre-existing-user-change'}]})
        result = s.promote_portfolio(self.state, self.runner)
        self.assertEqual('passed', result['status'])
        self.assertEqual(['pre-existing-user-change', self.sid],
                         [row['id'] for row in s.load(self.checkout / 'catalog.json')['skills']])
        self.assertTrue((self.checkout / 'collections/hermes' / self.sid).is_symlink())
        self.assertEqual(4, len(self.runner.calls))
        self.assertFalse(any('refresh_review.py' in ' '.join(c) for c in self.runner.calls))
        rows = {row['id']: row for row in s.load(self.checkout / 'docs/skill-review.json')['skills']}
        self.assertEqual(self.unrelated, rows['unrelated-user-skill'])
        self.assertIn('zio/zio', rows[self.sid]['reasons'][0])
        self.assertIn(self.sid, result['artifact_sha256'])

    def test_receipt_reuse_requires_unchanged_portfolio(self):
        s.promote_portfolio(self.state, self.runner)
        s.atomic_json(self.state / 'portfolio.json', dict(self.decision, summary='changed'))
        with self.assertRaisesRegex(ValueError, 'portfolio'):
            s.promote_portfolio(self.state, self.runner)

    def test_receipt_reuse_detects_removed_catalog_entry(self):
        s.promote_portfolio(self.state, self.runner)
        s.atomic_json(self.checkout / 'catalog.json', {'skills': []})
        with self.assertRaises(ValueError):
            s.promote_portfolio(self.state, self.runner)

    def test_receipt_reuse_detects_modified_skill_even_with_updated_catalog_hash(self):
        s.promote_portfolio(self.state, self.runner)
        dest = self.checkout / 'collections/shared' / self.sid
        (dest / 'SKILL.md').write_text('changed skill bytes')
        catalog = s.load(self.checkout / 'catalog.json')
        catalog['skills'][0]['sha256'] = tree_hash(dest)
        s.atomic_json(self.checkout / 'catalog.json', catalog)
        with self.assertRaises(ValueError):
            s.promote_portfolio(self.state, self.runner)


if __name__ == '__main__':
    unittest.main()
