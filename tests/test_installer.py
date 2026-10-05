"""Exercise the dotbot-go installer lifecycle in temporary homes."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'installer', str(ROOT / 'install.sh'),
    loader=importlib.machinery.SourceFileLoader('installer', str(ROOT / 'install.sh')))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
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
        installer.REPO = self.repo
        self.entries = [dict(id='test', name='test', path='collections/test',
                             distribution='vendored')]
        self.catalog()
        self.addCleanup(self.restore_repo)
        os.environ['DOTAGENTS_BACKUP'] = str(self.root / 'backup')

    def restore_repo(self):
        installer.REPO = ROOT

    def catalog(self):
        (self.repo / 'catalog.json').write_text(
            __import__('json').dumps(dict(schema_version=1, skills=self.entries)) + '\n')

    def args(self, command='install', **overrides):
        values = dict(command=command, home=self.home, agents='agents,claude',
                      include_local=False, check=False, dry_run=False)
        values.update(overrides)
        return __import__('argparse').Namespace(**values)

    def invoke(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            installer.main_args(self.args(**kwargs))

    def dotbot_available(self):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                return installer.ensure_dotbot()
        except SystemExit:
            self.skipTest('dotbot-go binary unavailable')

    def test_render_config_shape(self):
        rows = installer.plan(self.entries, ['agents', 'claude', 'pi'], self.home)
        config = installer.render_config(rows)
        self.assertIn('force: true', config)
        self.assertIn('relink: true', config)
        self.assertIn('~/.agents/skills/test: collections/test', config)
        self.assertIn('~/.claude/skills/test: collections/test', config)
        self.assertIn('if: test -d "$HOME/.pi/agent"', config)
        self.assertNotIn('~/.gemini/', config)

    def test_pi_scanned_roots_exclude_other_collections(self):
        self.entries.append(dict(id='hermes--github', name='github', path='collections/hermes/github',
                                 distribution='vendored', collection='hermes'))
        self.catalog()
        rows = installer.plan(self.entries, ['agents', 'pi', 'claude'], self.home)
        destinations = {str(dest) for _, dest, _, _ in rows}
        self.assertNotIn(str(self.home / '.agents/skills/hermes--github'), destinations)
        self.assertNotIn(str(self.home / '.pi/agent/skills/hermes--github'), destinations)
        self.assertIn(str(self.home / '.claude/skills/hermes--github'), destinations)

    def test_lifecycle_and_idempotence(self):
        self.dotbot_available()
        self.invoke()
        link = self.home / '.agents/skills/test'
        self.assertEqual(link.resolve(), self.skill.resolve())
        self.assertEqual((self.home / '.claude/skills/test').resolve(), self.skill.resolve())
        self.invoke()  # idempotent re-install
        self.invoke(command='check')
        self.invoke(command='uninstall')
        self.assertFalse(link.is_symlink())
        self.assertFalse((self.home / '.claude/skills/test').is_symlink())

    def test_dry_run_does_not_create_directories(self):
        self.dotbot_available()
        self.invoke(dry_run=True)
        self.assertFalse((self.home / '.agents').exists())

    def test_real_directory_is_backed_up_not_deleted(self):
        self.dotbot_available()
        victim = self.home / '.agents/skills/test'
        victim.mkdir(parents=True)
        (victim / 'precious.txt').write_text('keep me')
        self.invoke()
        self.assertFalse((victim / 'precious.txt').exists(),
                         'force-linked destination must not keep the old content')
        backups = list((self.root / 'backup').rglob('precious.txt'))
        self.assertEqual(len(backups), 1, 'original real directory must be backed up')
        self.assertEqual(backups[0].read_text(), 'keep me')

    def test_foreign_root_symlink_is_moved_aside(self):
        self.dotbot_available()
        foreign = self.root / 'foreign'
        foreign.mkdir()
        (foreign / 'stale').mkdir()
        (foreign / 'test').mkdir()  # real skill dir behind the root symlink
        root = self.home / '.agents/skills'
        root.parent.mkdir(parents=True)
        root.symlink_to(foreign)
        self.invoke()
        self.assertFalse(root.is_symlink())
        self.assertEqual(root.joinpath('test').resolve(), self.skill.resolve())
        self.assertTrue((foreign / 'test').is_dir(), 'content behind a moved root symlink stays intact')
        moved = list((self.root / 'backup').rglob('.agents/skills'))
        self.assertEqual(len(moved), 1)
        self.assertTrue(moved[0].is_symlink(), 'only the root symlink is backed up')

    def test_uninstall_leaves_foreign_links(self):
        self.dotbot_available()
        self.invoke()
        foreign = self.home / '.agents/skills/foreign-skill'
        foreign.symlink_to(self.root)
        self.invoke(command='uninstall')
        self.assertTrue(foreign.is_symlink())

    def test_check_reports_missing_links(self):
        self.dotbot_available()
        self.invoke()
        (self.home / '.agents/skills/test').unlink()
        with self.assertRaises(SystemExit):
            self.invoke(command='check')


if __name__ == '__main__':
    unittest.main()
