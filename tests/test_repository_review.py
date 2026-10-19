import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_repository_profiles import public_record, merge_analysis, filter_available_skills, read_evidence_tree
from build_private_profile import generate
from review_repositories import select_files, review

spec = importlib.util.spec_from_file_location('repo_profile', ROOT /
        'collections/shared/worxbend-repository-context/scripts/repo_profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class RepositoryReviewTests(unittest.TestCase):
    def repo_fixture(self):
        return {'nameWithOwner': 'owner/project', 'url': 'https://github.com/owner/project',
                'isPrivate': False, 'isArchived': False, 'isFork': False,
                'defaultBranchRef': {'name': 'main'}}

    def api_fixture(self, endpoint):
        if '/git/ref/' in endpoint:
            return {'object': {'sha': 'a' * 40}}
        return {'tree': [{'path': 'README.md', 'type': 'blob'},
                         {'path': 'build.sbt', 'type': 'blob'}], 'truncated': False}

    def test_same_commit_cache_respects_visibility_metadata_and_budget(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch('review_repositories.gh_json', side_effect=self.api_fixture), \
                patch('review_repositories.fetch_file', return_value=b'fixture') as fetch:
            root = Path(temp)
            repository = self.repo_fixture()
            first = review(repository, root, 1, False)
            self.assertEqual('bounded-baseline', first['coverage'])
            self.assertEqual(1, fetch.call_count)
            review(repository, root, 1, False)
            self.assertEqual(1, fetch.call_count, 'unchanged valid cache should be reused')
            larger = review(repository, root, 2, False)
            self.assertEqual(2, len(larger['files']))
            self.assertEqual(3, fetch.call_count)
            repository['isPrivate'] = True
            private = review(repository, root, 2, False)
            self.assertTrue(private['private'])
            self.assertEqual(5, fetch.call_count)
            with self.assertRaisesRegex(ValueError, 'explicitly public'):
                public_record(private, {'tree': []})
            repository['isArchived'] = True
            self.assertTrue(review(repository, root, 2, False)['archived'])
            self.assertEqual(7, fetch.call_count)

    def test_cache_recollects_missing_or_corrupt_files_and_tree(self):
        for damaged in ['missing-file', 'modified-file', 'missing-tree', 'modified-tree']:
            with self.subTest(damaged=damaged), tempfile.TemporaryDirectory() as temp, \
                    patch('review_repositories.gh_json', side_effect=self.api_fixture), \
                    patch('review_repositories.fetch_file', return_value=b'fixture') as fetch:
                root = Path(temp)
                repository = self.repo_fixture()
                review(repository, root, 2, False)
                folder = root / 'evidence/owner--project'
                target = folder / ('tree.json' if 'tree' in damaged else 'files/README.md')
                if damaged.startswith('missing'):
                    target.unlink()
                else:
                    target.write_bytes(b'changed')
                result = review(repository, root, 2, False)
                self.assertEqual('reviewed', result['status'])
                self.assertEqual(4, fetch.call_count)

    def test_routes_expose_only_installed_capabilities(self):
        rows = [{'skills': ['existing', 'unavailable-proposal', 'newly-installed']}]
        self.assertEqual(['existing', 'newly-installed'],
                         filter_available_skills(rows, {'existing', 'newly-installed'})[0]['skills'])

    def test_public_export_rejects_changed_missing_and_escaping_evidence(self):
        for damage in ['changed-package', 'changed-readme', 'missing-file', 'escaping-link']:
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                files = root / 'files'
                files.mkdir()
                payloads = {'README.md': b'fixture',
                            'package.json': b'{"dependencies":{"pixi.js":"8.5.1"}}'}
                manifest = {'private': False, 'status': 'reviewed', 'repository': 'owner/project',
                            'url': 'https://github.com/owner/project', 'head_sha': 'a' * 40,
                            'archived': False, 'fork': False, 'files': []}
                for path, payload in payloads.items():
                    (files / path).write_bytes(payload)
                    manifest['files'].append({'path': path, 'status': 'read', 'bytes': len(payload),
                                              'sha256': hashlib.sha256(payload).hexdigest(),
                                              'url': f'https://github.com/owner/project/blob/{"a" * 40}/{path}'})
                tree = {'tree': [{'path': path, 'type': 'blob'} for path in payloads]}
                original = public_record(manifest, tree, files)
                self.assertEqual('8.5.1', original['frontend_packages']['package.json']['pixi.js'])
                if damage == 'changed-package':
                    (files / 'package.json').write_bytes(payloads['package.json'].replace(b'8.5.1', b'8.5.2'))
                elif damage == 'changed-readme':
                    (files / 'README.md').write_bytes(b'changed')  # Equal length; the hash must catch it.
                elif damage == 'missing-file':
                    (files / 'README.md').unlink()
                else:
                    outside = root / 'outside.md'
                    outside.write_bytes(payloads['README.md'])
                    (files / 'README.md').unlink()
                    (files / 'README.md').symlink_to(outside)
                with self.assertRaises(ValueError):
                    public_record(manifest, tree, files)

    def test_reviewed_tree_integrity_and_truncation_fail_before_export(self):
        for damage in ['modified-tree', 'truncated-tree']:
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                payload = json.dumps({'tree': [{'path': 'build.mill', 'type': 'blob'}]}).encode()
                manifest = {'status': 'reviewed', 'tree_sha256': hashlib.sha256(payload).hexdigest()}
                (folder / 'tree.json').write_bytes(payload)
                self.assertEqual('build.mill', read_evidence_tree(manifest, folder)['tree'][0]['path'])
                changed = json.dumps({'tree': [], 'truncated': damage == 'truncated-tree'}).encode()
                (folder / 'tree.json').write_bytes(changed)
                if damage == 'truncated-tree':
                    manifest['tree_sha256'] = hashlib.sha256(changed).hexdigest()
                with self.assertRaises(ValueError):
                    read_evidence_tree(manifest, folder)

    def test_private_export_rejects_modified_pinned_tree_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = self.private_evidence(root)
            manifests = json.loads((evidence / 'repository-evidence.json').read_text())
            tree = evidence / 'evidence/owner--private-example/tree.json'
            manifests[0]['tree_sha256'] = hashlib.sha256(tree.read_bytes()).hexdigest()
            (evidence / 'repository-evidence.json').write_text(json.dumps(manifests))
            tree.write_text(json.dumps({'tree': [{'path': 'Cargo.toml', 'type': 'blob'}]}))
            target = root / 'private-output'
            with self.assertRaisesRegex(ValueError, 'tree hash differs'):
                generate(evidence, target)
            self.assertFalse(target.exists())

    def test_origin_formats_and_unrelated_hosts(self):
        for remote in ['https://github.com/worxbend/worxbend.git',
                       'git@github.com:worxbend/worxbend.git',
                       'ssh://git@github.com/worxbend/worxbend',
                       'https://github.com/Worxbend/Worxbend/']:
            self.assertEqual('worxbend/worxbend', profile.repository_name(remote))
        for remote in ['https://evil.example/worxbend/worxbend',
                       'https://github.com/worxbend/worxbend/tree/main',
                       'https://github.com@evil.example/worxbend/worxbend']:
            with self.assertRaises(ValueError):
                profile.repository_name(remote)

    def test_unknown_repo_has_no_fabricated_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            index = Path(temp) / 'profiles.json'
            index.write_text(json.dumps({'repositories': [{'repository': 'worxbend/worxbend'}]}))
            self.assertIsNone(profile.lookup('git@github.com:worxbend/new-repo.git', index))
            self.assertEqual('worxbend/worxbend', profile.lookup('git@github.com:worxbend/worxbend.git', index)['repository'])

    def test_evidence_selection_prioritizes_instructions_and_excludes_dependencies(self):
        tree = [{'path': path, 'type': 'blob'} for path in [
            'node_modules/pkg/package.json', 'README.md', 'build.mill', 'AGENTS.md',
            '.github/workflows/test.yml', 'service/package.json', 'src/App.scala', '.env',
        ]]
        chosen, remaining = select_files(tree, 3)
        self.assertEqual(['AGENTS.md', 'README.md', 'build.mill'], chosen)
        self.assertEqual(['service/package.json', '.github/workflows/test.yml'], remaining)

    def test_private_and_unclassified_evidence_cannot_be_exported(self):
        for manifest in [{'private': True}, {}]:
            with self.assertRaisesRegex(ValueError, 'explicitly public'):
                public_record(manifest, {'tree': []})

    def test_analysis_merge_ignores_private_data_and_checks_commit(self):
        rows = [{'repository': 'owner/public', 'head_sha': 'a' * 40, 'skills': []}]
        analysis = {'public_repositories': 1, 'entries': [
            {'repository': 'owner/private', 'private': True, 'summary': 'must-not-export'},
            {'repository': 'owner/public', 'private': False, 'head_sha': 'a' * 40,
             'build': 'sbt', 'evidence_path': '/private/local/path', 'constraints': ['preserve stack']}]}
        merged = merge_analysis(rows, [analysis])
        self.assertEqual({'build': 'sbt', 'constraints': ['preserve stack']}, merged[0]['review_observations'])
        self.assertNotIn('must-not-export', json.dumps(merged))
        analysis['entries'][1]['head_sha'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'commit differs'):
            merge_analysis(rows, [analysis])

    def test_profile_preserves_scoped_multiple_builds_and_commit_evidence(self):
        manifest = {'private': False, 'status': 'reviewed', 'repository': 'worxbend/example',
                    'url': 'https://github.com/worxbend/example', 'head_sha': 'a' * 40,
                    'archived': False, 'fork': False, 'files': [{
                        'path': 'build.sbt', 'url': 'immutable-source', 'sha256': 'filehash',
                        'bytes': 20, 'status': 'read'}]}
        tree = {'tree': [{'path': path, 'type': 'blob'} for path in [
            'build.sbt', 'web/package.json', 'AGENTS.md', '.github/workflows/ci.yml',
            'node_modules/pkg/package.json']]}
        row = public_record(manifest, tree)
        self.assertEqual(['build.sbt', 'web/package.json'], row['build_files'])
        self.assertEqual('a' * 40, row['head_sha'])
        self.assertEqual(['AGENTS.md'], row['instruction_files'])
        self.assertNotIn('private', row)
        self.assertEqual('filehash', row['evidence'][0]['sha256'])

    def private_evidence(self, root):
        evidence = root / 'evidence-input'
        evidence.mkdir()
        rows = []
        for private, name in [(True, 'private-example'), (False, 'public-example')]:
            folder = evidence / 'evidence' / f'owner--{name}'
            folder.mkdir(parents=True)
            (folder / 'tree.json').write_text(json.dumps({'tree': [
                {'path': 'go.mod', 'type': 'blob'}, {'path': 'secrets.txt', 'type': 'blob'}]}))
            (folder / 'secrets.txt').write_text('raw-private-payload-must-not-be-copied')
            rows.append({'private': private, 'status': 'reviewed', 'repository': f'owner/{name}',
                         'url': f'https://github.com/owner/{name}', 'head_sha': 'a' * 40,
                         'archived': False, 'fork': False, 'files': []})
        (evidence / 'repository-evidence.json').write_text(json.dumps(rows))
        return evidence

    def test_private_generation_includes_only_private_structure_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = self.private_evidence(root)
            target = root / 'local-private-context'
            destination, count = generate(evidence, target)
            self.assertEqual(1, count)
            data = json.loads((destination / 'references/profiles.json').read_text())
            self.assertEqual(['owner/private-example'], [row['repository'] for row in data['repositories']])
            self.assertNotIn('raw-private-payload', (destination / 'references/profiles.json').read_text())
            self.assertFalse((destination / 'secrets.txt').exists())
            self.assertEqual(0o700, destination.stat().st_mode & 0o777)
            self.assertEqual(0o600, (destination / 'references/profiles.json').stat().st_mode & 0o777)
            before = (destination / 'SKILL.md').stat().st_mtime_ns
            generate(evidence, target)
            self.assertEqual(before, (destination / 'SKILL.md').stat().st_mtime_ns)

    def test_private_generation_preserves_customization_or_backs_it_up(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = self.private_evidence(root)
            target = root / 'context'
            generate(evidence, target)
            (target / 'SKILL.md').write_text('custom local instructions')
            with self.assertRaises(ValueError):
                generate(evidence, target)
            self.assertEqual('custom local instructions', (target / 'SKILL.md').read_text())
            generate(evidence, target, replace=True)
            backup, = root.glob('context.backup-*')
            self.assertEqual('custom local instructions', (backup / 'SKILL.md').read_text())

    def test_private_output_inside_public_checkout_is_rejected_before_writing(self):
        with self.assertRaisesRegex(ValueError, 'outside the public'):
            generate(Path('/not-read'), ROOT / 'must-not-create-private')
        self.assertFalse((ROOT / 'must-not-create-private').exists())

    def test_reviewed_private_tree_missing_fails_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = self.private_evidence(root)
            (evidence / 'evidence/owner--private-example/tree.json').unlink()
            target = root / 'private-target'
            with self.assertRaisesRegex(ValueError, 'tree is missing'):
                generate(evidence, target)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
