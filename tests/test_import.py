"""Imported global skill aliases must survive transfer to another machine."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_skills import copy_tree, make_links_portable
import import_skills


class ImportTests(unittest.TestCase):
    def test_shared_skill_alias_survives_removing_original_home(self):
        self.check_shared_skill_alias(relative=False)

    def test_relative_shared_skill_alias_survives_removing_original_home(self):
        self.check_shared_skill_alias(relative=True)

    def check_shared_skill_alias(self, relative):
        with tempfile.TemporaryDirectory(prefix='dot agents import ') as temp:
            root = Path(temp).resolve()
            home = root / 'original-home'
            source = home / '.agents/skills/code-complete'
            source.mkdir(parents=True)
            (source / 'SKILL.md').write_text('skill instructions')
            hermes = home / '.hermes/skills'
            hermes.mkdir(parents=True)
            target = os.path.relpath(source, hermes) if relative else source
            (hermes / 'code-complete').symlink_to(target, target_is_directory=True)
            snapshot = root / 'snapshot/collections'
            shared_copy = snapshot / 'shared/code-complete'
            copy_tree(source, shared_copy)
            copy_tree(hermes, snapshot / 'hermes')
            make_links_portable(snapshot, {source: shared_copy, hermes: snapshot / 'hermes'})
            alias = snapshot / 'hermes/code-complete'
            self.assertFalse(os.path.isabs(os.readlink(alias)))
            shutil.rmtree(home)
            self.assertEqual((alias / 'SKILL.md').read_text(), 'skill instructions')

    def test_unimported_external_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            outside = root / 'unrelated-file'
            outside.write_text('must not be imported')
            snapshot = root / 'collections'
            snapshot.mkdir()
            (snapshot / 'link').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'outside imported'):
                make_links_portable(snapshot, {})

    def test_internal_relative_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp).resolve()
            (snapshot / 'SKILL.md').write_text('skill instructions')
            alias = snapshot / 'alias.md'
            alias.symlink_to('SKILL.md')
            make_links_portable(snapshot, {})
            self.assertEqual(os.readlink(alias), 'SKILL.md')

    def test_absolute_link_into_repository_becomes_relative(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp).resolve()
            (snapshot / 'SKILL.md').write_text('skill instructions')
            alias = snapshot / 'alias.md'
            alias.symlink_to(snapshot / 'SKILL.md')
            make_links_portable(snapshot, {})
            self.assertEqual(os.readlink(alias), 'SKILL.md')


class SourcePolicyTests(unittest.TestCase):
    def test_provider_alias_and_nested_copy_are_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source'
            provider = source / 'provider'
            provider.mkdir(parents=True)
            (provider / 'SKILL.md').write_text('provider-only content')
            (source / 'public.txt').write_text('public')
            (source / 'alias').symlink_to(provider, target_is_directory=True)
            dest = root / 'snapshot'
            copy_tree(source, dest)
            copies = {source: dest}
            import_skills.omit_external_copies(copies, {provider})
            make_links_portable(dest, copies, {provider})
            self.assertFalse((dest / 'provider').exists())
            self.assertFalse((dest / 'alias').is_symlink())
            self.assertEqual('public', (dest / 'public.txt').read_text())

    def test_unknown_upstream_cannot_be_vendored(self):
        with self.assertRaises(ValueError):
            import_skills.source_policy('unknown/upstream', {})

    def test_explicit_unlicensed_source_stays_external(self):
        policy = {'VirtusLab/scala-skill': {'spdx': 'LicenseRef-No-Redistribution-Grant', 'distribution': 'external'}}
        self.assertEqual(('LicenseRef-No-Redistribution-Grant', False),
                         import_skills.source_policy('VirtusLab/scala-skill', policy))

    def test_local_authored_license_and_upstream_file_required(self):
        self.assertEqual(('MIT', True), import_skills.source_policy('local', {}, 'MIT'))
        with self.assertRaises(ValueError):
            import_skills.source_policy('known/upstream', {'known/upstream': {'spdx': 'MIT'}})


if __name__ == '__main__':
    unittest.main()
