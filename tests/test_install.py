"""Exercise installation lifecycle in temporary homes, including conflict recovery."""
import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import dump_json
from manage import install, uninstall, STATE_FILE


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dot agents test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.repo = self.root / 'repo with spaces'
        skill = self.repo / 'collections/test'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: test\ndescription: Test fixture\n---\n# Test\n')
        self.skill = skill
        self.entries = [dict(id='test', name='test', path='collections/test', distribution='vendored')]
        self.catalog()

    def catalog(self):
        dump_json(self.repo / 'catalog.json', dict(schema_version=1, skills=self.entries))

    def args(self, **overrides):
        values = dict(home=self.home, agents='agents,claude', target=None, dry_run=False,
                      skills=None, include_local=False, replace=False, check=False)
        values.update(overrides)
        return argparse.Namespace(**values)

    def run_install(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            install(self.args(**kwargs), self.repo)

    def test_lifecycle_and_idempotence(self):
        self.run_install()
        link = self.home / '.agents/skills/test'
        self.assertEqual(link.resolve(), self.skill.resolve())
        self.run_install()
        self.run_install(check=True)
        with contextlib.redirect_stdout(io.StringIO()):
            uninstall(self.args())
        self.assertFalse(link.is_symlink())
        self.assertFalse((link.parent / STATE_FILE).exists())

    def test_dry_run_does_not_create_directories(self):
        self.run_install(dry_run=True)
        self.assertFalse((self.home / '.agents').exists())

    def test_preflight_conflict_changes_nothing(self):
        conflict = self.home / '.claude/skills/test'
        conflict.mkdir(parents=True)
        (conflict / 'mine.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.run_install()
        self.assertFalse((self.home / '.agents').exists())
        self.assertEqual((conflict / 'mine.txt').read_text(), 'keep')

    def test_replace_backs_up_directory(self):
        target = self.home / '.agents/skills/test'
        target.mkdir(parents=True)
        (target / 'mine.txt').write_text('keep')
        self.run_install(replace=True)
        backups = list(target.parent.glob('test.dot-agents-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'mine.txt').read_text(), 'keep')
        self.assertTrue(target.is_symlink())

    def test_root_symlink_is_backed_up_without_touching_source(self):
        original = self.root / 'original'
        original.mkdir()
        (original / 'mine.txt').write_text('keep')
        target = self.home / '.agents/skills'
        target.parent.mkdir()
        target.symlink_to(original, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.run_install()
        self.run_install(replace=True)
        self.assertEqual((original / 'mine.txt').read_text(), 'keep')
        self.assertFalse((original / 'test').exists())
        self.assertTrue(next(target.parent.glob('skills.dot-agents-backup-*')).is_symlink())

    def test_uninstall_preserves_modified_entries_and_unrelated_files(self):
        self.run_install()
        target = self.home / '.agents/skills'
        (target / 'unrelated.txt').write_text('keep')
        (target / 'test').unlink()
        (target / 'test').mkdir()
        with self.assertRaisesRegex(ValueError, 'untouched'):
            with contextlib.redirect_stdout(io.StringIO()):
                uninstall(self.args())
        self.assertTrue((target / 'test').is_dir())
        self.assertEqual((target / 'unrelated.txt').read_text(), 'keep')

    def test_check_detects_broken_link(self):
        self.run_install()
        (self.skill / 'SKILL.md').unlink()
        with self.assertRaisesRegex(ValueError, 'missing SKILL.md'):
            self.run_install(check=True)

    def test_moved_repository_retargets_managed_links(self):
        self.run_install()
        moved = self.root / 'moved repository'
        self.repo.rename(moved)
        self.repo = moved
        self.skill = moved / 'collections/test'
        self.run_install()
        self.assertEqual((self.home / '.agents/skills/test').resolve(), self.skill.resolve())

    def test_external_skills_only_link_existing_local_content(self):
        external = self.home / '.provider/skills/vendor-test'
        external.mkdir(parents=True)
        (external / 'SKILL.md').write_text('---\nname: vendor-test\ndescription: Hosted fixture\n---\n')
        self.entries.append(dict(id='vendor-test', name='vendor-test', distribution='external',
                                 local_globs=['~/.provider/skills/vendor-test']))
        self.catalog()
        self.run_install()
        target = self.home / '.agents/skills/vendor-test'
        self.assertFalse(target.exists())
        self.run_install(include_local=True)
        self.assertTrue(target.is_symlink())
        self.assertEqual(target.resolve(), external.resolve())

    def test_unknown_skill_and_escaping_source_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown skill'):
            self.run_install(skills='does-not-exist')
        self.entries[0]['path'] = '../outside'
        self.catalog()
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.run_install()

    def test_state_path_traversal_is_rejected(self):
        self.run_install()
        dump_json(self.home / '.agents/skills' / STATE_FILE,
                  {'schema_version': 1, 'links': {'../../other': '/somewhere'}})
        with self.assertRaisesRegex(ValueError, 'invalid managed'):
            self.run_install()

    def test_custom_target_and_all_agents(self):
        target = self.root / 'custom skills'
        self.run_install(target=target, agents=None)
        self.assertTrue((target / 'test').is_symlink())
        self.run_install(agents='all')
        self.assertTrue((self.home / '.hermes/skills/test').is_symlink())
        self.assertTrue((self.home / '.config/opencode/skills/test').is_symlink())


if __name__ == '__main__':
    unittest.main()
