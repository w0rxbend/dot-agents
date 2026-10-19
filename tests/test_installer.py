"""Exercise the dotbot-go installer lifecycle in temporary homes.

Hermetic: temporary homes and repositories, no network. Tests that apply links
need an existing dotbot-go binary (DOTBOT, PATH, or ~/.local/bin/dotbot) and
are skipped without one; they never download it.
"""
import argparse
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.repo = self.root / 'repo with spaces'
        self.skill = self.make_skill('collections/test', 'test')
        patcher = mock.patch.object(installer, 'REPO', self.repo)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, {'DOTAGENTS_BACKUP': str(self.root / 'backup')})
        env.start()
        self.addCleanup(env.stop)
        self.entries = [dict(id='test', name='test', path='collections/test',
                             distribution='vendored')]
        self.catalog()

    def make_skill(self, relative, name, base=None):
        skill = (base or self.repo) / relative
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Test fixture\n---\n# Test\n')
        return skill

    def catalog(self):
        (self.repo / 'catalog.json').write_text(
            json.dumps(dict(schema_version=1, skills=self.entries)) + '\n')

    def args(self, command='install', **overrides):
        values = dict(command=command, home=self.home, agents='agents,claude',
                      include_local=False, check=False, dry_run=False)
        values.update(overrides)
        return argparse.Namespace(**values)

    def invoke(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            installer.main_args(self.args(**kwargs))
        return out.getvalue()

    def dotbot_available(self):
        found = installer.find_dotbot()
        if found is None:
            self.skipTest('dotbot-go binary unavailable')
        return found

    def destinations(self, rows):
        return {str(dest.relative_to(self.home)) for _, dest, _, _ in rows}

    # Planning and rendering -------------------------------------------------

    def test_render_config_shape(self):
        rows = installer.plan(self.entries, ['agents', 'claude', 'pi'], self.home)
        config = installer.render_config(rows)
        self.assertIn('force: true', config)
        self.assertIn('relink: true', config)
        self.assertIn('~/.agents/skills/test: collections/test', config)
        self.assertIn('~/.claude/skills/test: collections/test', config)
        self.assertIn('if: test -d "$HOME/.pi/agent"', config)
        self.assertNotIn('~/.gemini/', config)

    def test_applied_config_is_ungated_and_relative(self):
        local = self.make_skill('providers/local', 'local', base=self.home)
        rows = [('gemini', self.home / '.gemini/skills/test', 'collections/test', False),
                ('agents', self.home / '.agents/skills/local', str(local), True)]
        config = installer.render_config(rows, gated=False)
        self.assertNotIn('if:', config)
        self.assertIn('    - "~/.gemini/skills"', config)
        self.assertIn('~/.gemini/skills/test: collections/test', config)
        self.assertIn('~/.agents/skills/local: ../home/providers/local', config)
        self.assertNotIn(str(self.root), config, 'sources must not be absolute')

    def test_pi_scanned_roots_exclude_other_collections(self):
        self.entries.append(dict(id='mattpocock--tdd', name='tdd', path='collections/test',
                                 distribution='vendored', collection='mattpocock'))
        rows = installer.plan(self.entries, ['agents', 'pi', 'claude'], self.home)
        destinations = self.destinations(rows)
        self.assertNotIn('.agents/skills/mattpocock--tdd', destinations)
        self.assertNotIn('.pi/agent/skills/mattpocock--tdd', destinations)
        self.assertIn('.claude/skills/mattpocock--tdd', destinations)

    def test_collection_install_scope(self):
        for skill_id, collection in (('hermes--github', 'hermes'),
                                     ('codex-system--imagegen', 'codex-system'),
                                     ('claude-design--ux-copy', 'claude-design'),
                                     ('claude-engineering--debug', 'claude-engineering'),
                                     ('claude-productivity--start', 'claude-productivity')):
            self.entries.append(dict(id=skill_id, name=skill_id, path='collections/test',
                                     distribution='vendored', collection=collection))
        rows = installer.plan(self.entries, list(installer.AGENTS), self.home)
        agents_for = {}
        for agent, dest, _, _ in rows:
            agents_for.setdefault(dest.name, set()).add(agent)
        self.assertEqual(agents_for['hermes--github'], {'hermes'})
        self.assertEqual(agents_for['codex-system--imagegen'], {'codex'})
        plugin_agents = set(installer.AGENTS) - {'claude'} - installer.PI_SCOPED_AGENTS
        for skill_id in ('claude-design--ux-copy', 'claude-engineering--debug',
                         'claude-productivity--start'):
            self.assertEqual(agents_for[skill_id], plugin_agents)
        self.assertEqual(agents_for['test'], set(installer.AGENTS))

    def test_render_is_home_independent(self):
        rendered = []
        for setup in (lambda home: None,
                      lambda home: [(home / rel).parent.mkdir(parents=True, exist_ok=True)
                                    for rel in installer.AGENTS.values()]):
            home = Path(tempfile.mkdtemp(dir=self.root))
            setup(home)
            self.invoke(command='render', home=home, agents=None)
            rendered.append((self.repo / 'install.conf.yaml').read_text())
            self.invoke(command='render', home=home, agents=None, check=True)
        self.assertEqual(rendered[0], rendered[1])
        for rel in installer.AGENTS.values():
            self.assertIn(f'~/{rel}/test', rendered[0])
        self.assertNotIn(str(self.root), rendered[0])

    def test_render_rejects_agent_selection(self):
        with self.assertRaises(SystemExit):
            self.invoke(command='render', agents='agents')

    def test_render_check_detects_stale_file(self):
        (self.repo / 'install.conf.yaml').write_text('stale\n')
        with self.assertRaises(SystemExit):
            self.invoke(command='render', agents=None, check=True)

    def test_local_source_ignores_link_destinations(self):
        item = dict(id='vss', name='vss', distribution='external',
                    local_globs=['~/providers/vss', '~/.agents/skills/vss'])
        self.make_skill('.agents/skills/vss', 'vss', base=self.home)
        self.assertIsNone(installer.local_source(item, self.home))
        provider = self.make_skill('providers/vss', 'vss', base=self.home)
        self.assertEqual(installer.local_source(item, self.home), provider)

    # Lifecycle with dotbot ---------------------------------------------------

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

    def test_install_never_rewrites_committed_config(self):
        self.dotbot_available()
        committed = self.repo / 'install.conf.yaml'
        committed.write_text('# committed reference\n')
        self.invoke()
        self.assertEqual(committed.read_text(), '# committed reference\n')
        self.assertFalse((self.repo / 'install.local.conf.yaml').exists())

    def test_agent_subset_leaves_other_agents_alone(self):
        self.dotbot_available()
        precious = self.home / '.claude/skills/test/notes.md'
        precious.parent.mkdir(parents=True)
        precious.write_text('mine')
        (self.home / '.codex').mkdir()  # detected agents must not leak into --agents
        self.invoke(agents='agents')
        self.assertTrue((self.home / '.agents/skills/test').is_symlink())
        self.assertEqual(precious.read_text(), 'mine')
        self.assertFalse((self.home / '.codex/skills').exists())
        self.assertFalse((self.root / 'backup').exists())

    def test_explicit_optional_agent_is_created(self):
        self.dotbot_available()
        self.invoke(agents='agents,gemini')
        self.assertEqual((self.home / '.gemini/skills/test').resolve(), self.skill.resolve())
        self.invoke(command='check', agents='agents,gemini')

    def test_out_of_scope_links_are_pruned(self):
        self.dotbot_available()
        self.entries.append(dict(id='hermes--x', name='x', path='collections/test',
                                 distribution='vendored', collection='hermes'))
        self.catalog()
        stale = self.home / '.claude/skills/hermes--x'
        stale.parent.mkdir(parents=True)
        stale.symlink_to(self.skill)  # left by an install before scoping
        with self.assertRaises(SystemExit):
            self.invoke(command='check')
        self.invoke()
        self.assertFalse(stale.is_symlink())
        self.invoke(command='check')

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

    def test_backup_defaults_under_selected_home(self):
        self.dotbot_available()
        os.environ.pop('DOTAGENTS_BACKUP')
        victim = self.home / '.agents/skills/test'
        victim.mkdir(parents=True)
        self.invoke()
        backups = list((self.home / '.local/share/dot-agents/backup').rglob('skills/test'))
        self.assertEqual(len(backups), 1)

    def test_foreign_symlink_at_destination_is_backed_up(self):
        self.dotbot_available()
        mine = self.make_skill('mine/test', 'test', base=self.root)
        link = self.home / '.agents/skills/test'
        link.parent.mkdir(parents=True)
        link.symlink_to(mine)
        self.invoke()
        self.assertEqual(link.resolve(), self.skill.resolve())
        moved = [p for p in (self.root / 'backup').rglob('test') if p.is_symlink()]
        self.assertEqual([p.resolve() for p in moved], [mine])

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

    def test_root_symlink_into_repository_does_not_move_repo_content(self):
        self.dotbot_available()
        root = self.home / '.agents/skills'
        root.parent.mkdir(parents=True)
        root.symlink_to(self.repo / 'collections')
        self.invoke()
        self.assertTrue((self.skill / 'SKILL.md').is_file(), 'repository skill must stay in place')
        self.assertFalse(root.is_symlink())
        self.assertEqual(root.joinpath('test').resolve(), self.skill.resolve())

    def test_include_local_links_relative_source(self):
        self.dotbot_available()
        provider = self.make_skill('.local/share/dot-agents/providers/skills/vss', 'vss',
                                   base=self.home)
        self.entries.append(dict(id='vss', name='vss', distribution='external',
                                 local_globs=['~/.local/share/dot-agents/providers/skills/vss',
                                              '~/.agents/skills/vss']))
        self.catalog()
        self.invoke(include_local=True)
        link = self.home / '.agents/skills/vss'
        self.assertEqual(link.resolve(), provider)
        self.assertTrue(provider.is_dir(), 'the local source must not be backed up')
        self.invoke(command='check', include_local=True)
        self.invoke(include_local=True)  # rerun: the link is now a destination, not a source
        self.assertEqual(link.resolve(), provider)
        self.invoke(command='uninstall', include_local=True)
        self.assertFalse(link.is_symlink())
        self.assertTrue((provider / 'SKILL.md').is_file())

    def test_uninstall_leaves_foreign_links(self):
        self.dotbot_available()
        self.invoke()
        foreign = self.home / '.agents/skills/foreign-skill'
        foreign.symlink_to(self.root)
        self.invoke(command='uninstall')
        self.assertTrue(foreign.is_symlink())

    def test_uninstall_broken_links(self):
        root = self.home / '.agents/skills'
        root.mkdir(parents=True)
        ours = root / 'test'
        ours.symlink_to(self.repo / 'collections/removed-skill')
        sibling = Path(str(self.repo) + '-old') / 'collections/test'
        theirs = root / 'other'
        theirs.symlink_to(sibling)  # shares the repository path as a string prefix
        self.invoke(command='uninstall', agents='agents')
        self.assertFalse(ours.is_symlink())
        self.assertTrue(theirs.is_symlink())

    def test_check_reports_missing_links(self):
        self.dotbot_available()
        self.invoke()
        (self.home / '.agents/skills/test').unlink()
        with self.assertRaises(SystemExit):
            self.invoke(command='check')


if __name__ == '__main__':
    unittest.main()
