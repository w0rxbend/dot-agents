"""Offline collector contracts. Fixtures below are synthetic, never research evidence."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)

    def test_module_exists_and_cache_avoids_network_on_resume(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.scala_research.collector'))
        from scripts.scala_research.collector import GitHubAPI
        response = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\r\nETag: abc\r\n\r\n{"ok": true}', '')
        with patch('subprocess.run', return_value=response) as run, patch('time.sleep'):
            api = GitHubAPI(self.state)
            self.assertEqual(api.get('repos/example/library')['body'], {'ok': True})
            again = GitHubAPI(self.state).get('repos/example/library')
            self.assertEqual(again['body'], {'ok': True})
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][:5], ['gh', 'api', '--hostname', 'github.com', '--method'])
        cached = list((self.state / 'cache' / 'api').glob('*.json'))
        self.assertEqual(len(cached), 1)
        self.assertEqual(json.loads(cached[0].read_text())['endpoint'], 'repos/example/library')

    def test_pagination_preserves_pages_and_reports_failure(self):
        from scripts.scala_research.collector import APIError, GitHubAPI, paginated
        api = GitHubAPI(self.state)
        first = {'body': [{'id': n} for n in range(100)], 'headers': {}, 'endpoint': 'first'}
        error = APIError('second', 'http_error', status=500, retryable=True)
        with patch.object(api, 'get', side_effect=[first, error]):
            result = paginated(api, 'repos/example/library/pulls/1/reviews')
        self.assertEqual(len(result['items']), 100)
        self.assertFalse(result['coverage']['complete'])
        self.assertEqual(result['gaps'][0]['kind'], 'endpoint_failed')
        with patch.object(api, 'get', side_effect=[first, dict(first, body=[{'id': 101}])]):
            result = paginated(api, 'repos/example/library/pulls/1/reviews')
        self.assertTrue(result['coverage']['complete'])
        self.assertEqual(len(result['coverage']['pages']), 2)
        self.assertEqual(len(result['items']), 101)

    def test_endpoint_caps_are_not_silently_complete(self):
        from scripts.scala_research.collector import GitHubAPI, paginated
        api = GitHubAPI(self.state)
        with patch.object(api, 'get', return_value={'body': list(range(100)), 'headers': {}}):
            result = paginated(api, 'repos/example/library/pulls/1/files', max_pages=1)
        self.assertFalse(result['coverage']['complete'])
        self.assertEqual(result['gaps'][0]['kind'], 'pagination_cap')

    def test_discovery_paginates_deduplicates_aliases_and_fails_closed(self):
        from scripts.scala_research import collector as c
        def get(endpoint):
            if endpoint.startswith('users/lihaoyi/repos'):
                page = 'page=2' in endpoint
                body = ([self.repo('lihaoyi/unknown', language=None)] if page else
                        [self.repo('lihaoyi/lib' + str(n)) for n in range(100)])
            elif endpoint.startswith('orgs/com-lihaoyi/repos'):
                body = [self.repo('com-lihaoyi/Lib'), self.repo('com-lihaoyi/fork', fork=True),
                        self.repo('com-lihaoyi/future', created_at='2025-01-01T00:00:00Z')]
            else:
                name = endpoint.removeprefix('repos/')
                body = self.repo('com-lihaoyi/Lib' if name == 'lihaoyi/Lib' else name)
            return {'body': body, 'headers': {}, 'endpoint': endpoint}
        with patch.object(c.GitHubAPI, 'get', side_effect=get), patch.object(c, 'ALIASES', ('lihaoyi/Lib',)):
            inventory = c.discover(self.state)
        entries = {x['repo']: x for x in inventory['repositories']}
        self.assertTrue(entries['lihaoyi/unknown']['included'])
        self.assertEqual(entries['lihaoyi/unknown']['classification'], 'unknown')
        self.assertFalse(entries['com-lihaoyi/fork']['included'])
        self.assertFalse(entries['com-lihaoyi/future']['included'])
        self.assertIn('lihaoyi/Lib', entries['com-lihaoyi/Lib']['aliases'])
        self.assertEqual(len(entries), len(inventory['repositories']))
        old = (self.state / 'inventory.json').read_bytes()
        with patch.object(c.GitHubAPI, 'get', side_effect=c.APIError('x', 'http_error', status=403)):
            with self.assertRaises(c.DiscoveryError):
                c.discover(self.state)
        self.assertEqual((self.state / 'inventory.json').read_bytes(), old)
        self.assertTrue((self.state / 'inventory.failure.json').exists())

    def test_search_reports_counts_caps_incomplete_and_filters_dates(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        body = {'total_count': 1500, 'incomplete_results': True, 'items': [
            {'number': 1, 'closed_at': '2020-02-01T00:00:00Z', 'pull_request': {'merged_at': '2020-02-01T00:00:00Z'}},
            {'number': 2, 'closed_at': '2025-01-01T00:00:00Z', 'pull_request': {'merged_at': '2025-01-01T00:00:00Z'}}]}
        with patch.object(api, 'get', return_value={'body': body, 'headers': {}}):
            result = c.search_pulls(api, 'example/library', 2020, 'merged', 1)
        self.assertEqual([x['number'] for x in result['items']], [1])
        self.assertEqual(result['coverage']['total_count'], 1500)
        self.assertTrue(result['coverage']['incomplete_results'])
        self.assertTrue(result['coverage']['search_cap_limited'])
        self.assertEqual(result['coverage']['excluded_dates'], [2])
        self.assertTrue(result['coverage']['sampled'])

    def test_pull_keeps_full_discussion_but_marks_late_edits_ineligible(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        detail = {'number': 1, 'created_at': '2020-01-01T00:00:00Z',
                  'closed_at': '2020-01-03T00:00:00Z', 'merged_at': None,
                  'changed_files': 1, 'commits': 1, 'comments': 2, 'review_comments': 1,
                  'base': {'sha': 'a' * 40}, 'head': {'sha': 'b' * 40}}
        def get(endpoint):
            route = endpoint.split('?')[0]
            if route.endswith('/pulls/1'):
                body = detail
            elif route.endswith('/reviews'):
                body = [{'id': 1, 'submitted_at': '2020-01-02T00:00:00Z', 'body': 'fixture review'}]
            elif route.endswith('/issues/1/comments'):
                body = [{'id': 2, 'created_at': '2020-01-02T00:00:00Z', 'updated_at': '2025-01-01T00:00:00Z'},
                        {'id': 3, 'created_at': '2020-01-02T00:00:00Z', 'updated_at': '2020-01-02T00:00:00Z'}]
            elif route.endswith('/comments'):
                raise c.APIError(endpoint, 'http_error', status=404)
            elif route.endswith('/files'):
                body = [{'filename': 'src/A.scala', 'patch': 'fixture'}]
            elif route.endswith('/commits'):
                body = [{'sha': 'b' * 40, 'commit': {'committer': {'date': '2020-01-01T00:00:00Z'}}}]
            else:
                self.fail(endpoint)
            return {'body': body, 'headers': {}}
        with patch.object(api, 'get', side_effect=get):
            result = c.collect_pull(api, 'example/library', 1)
        self.assertEqual(len(result['issue_comments']), 2)
        self.assertEqual(result['historical']['eligible_ids']['issue_comments'], [3])
        self.assertEqual(result['historical']['eligible_ids']['reviews'], [1])
        self.assertFalse(result['coverage']['review_comments']['complete'])
        self.assertTrue(any(x['kind'] == 'endpoint_failed' for x in result['gaps']))

    def test_snapshots_pin_commits_content_and_report_tree_truncation(self):
        import base64
        import hashlib
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        source = b'// offline fixture\n'
        blob_sha = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
        commit = {'sha': 'a' * 40, 'commit': {'committer': {'date': '2020-02-01T00:00:00Z'}, 'tree': {'sha': 'b' * 40}}}
        def get(endpoint):
            if '/commits?' in endpoint:
                body = [commit]
            elif '/git/trees/' in endpoint:
                body = {'truncated': True, 'tree': [dict(path=path, type='blob', mode='100644', size=len(source), sha=blob_sha)
                                                   for path in ['build.sbt', 'src/main/A.scala', 'src/test/ASpec.scala', '../escape.scala']]}
            elif '/git/blobs/' in endpoint:
                body = {'encoding': 'base64', 'content': base64.b64encode(source).decode(), 'sha': blob_sha, 'size': len(source)}
            else:
                self.fail(endpoint)
            return {'body': body, 'headers': {}}
        with patch.object(api, 'get', side_effect=get):
            snapshot = c.collect_snapshot(api, 'example/library', 2020)
        self.assertEqual(snapshot['commit_sha'], 'a' * 40)
        self.assertEqual({f['category'] for f in snapshot['files']}, {'build', 'source', 'test'})
        self.assertTrue(all(f['content'] == source.decode() for f in snapshot['files']))
        self.assertTrue(any(g['kind'] == 'tree_truncated' for g in snapshot['gaps']))
        self.assertTrue(any(g['kind'] == 'unsafe_source_path' for g in snapshot['gaps']))

    def test_repository_index_resume_and_cli_fatal_exit(self):
        from scripts.scala_research import collector as c
        from urllib.parse import parse_qs, urlsplit
        def run(command, **kwargs):
            endpoint = command[-1]
            route, query = urlsplit(endpoint).path, parse_qs(urlsplit(endpoint).query)
            if route == 'repos/example/library':
                body = self.repo('example/library')
            elif route == 'search/issues':
                body = {'total_count': 0, 'incomplete_results': False, 'items': []}
            elif route == 'repos/example/library/commits':
                body = []
            else:
                self.fail(endpoint)
            return subprocess.CompletedProcess(command, 0, 'HTTP/2.0 200 OK\n\n' + json.dumps(body), '')
        with patch('subprocess.run', side_effect=run) as network, patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
            before = network.call_count
            c.collect_repository(self.state, 'example/library', per_year=1)
            self.assertEqual(network.call_count, before)
        persisted = json.loads((self.state / 'corpus/example--library/index.json').read_text())
        self.assertEqual(persisted['repository'], 'example/library')
        self.assertEqual(len(index['coverage']['years']), 7)
        self.assertEqual(len(index['snapshots']), 3)
        with patch.object(c, 'discover', side_effect=c.DiscoveryError('fixture')), patch('sys.stderr'):
            self.assertNotEqual(c.main(['--state', str(self.state), 'discover']), 0)

    def test_retry_exhaustion_is_bounded_and_failed_pages_are_not_cached(self):
        from scripts.scala_research import collector as c
        failed = subprocess.CompletedProcess([], 1, 'HTTP/2.0 503 Unavailable\n\n{"message":"fixture"}', 'must not leak stderr')
        with patch('subprocess.run', return_value=failed) as run, patch('time.sleep'):
            api = c.GitHubAPI(self.state)
            with self.assertRaises(c.APIError) as caught:
                api.get('repos/example/library')
            self.assertEqual(run.call_count, c.MAX_ATTEMPTS)
        self.assertTrue(caught.exception.record['retryable'])
        self.assertFalse((self.state / api.cache_relative('repos/example/library')).exists())
        record = json.loads(next((self.state / 'failures/api').glob('*.json')).read_text())
        self.assertEqual(len(record['attempt_errors']), c.MAX_ATTEMPTS)
        self.assertNotIn('must not leak', json.dumps(record))
        success = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n{"ok":true}', '')
        with patch('subprocess.run', return_value=success), patch('time.sleep'):
            self.assertEqual(api.get('repos/example/library')['body'], {'ok': True})

    def test_long_rate_limit_blocks_other_instances_without_sleeping(self):
        from scripts.scala_research import collector as c
        response = subprocess.CompletedProcess([], 1, 'HTTP/2.0 429 Slow Down\nRetry-After: 3600\n\n{"message":"fixture"}', '')
        with patch('subprocess.run', return_value=response) as run, patch('time.sleep') as sleep:
            with self.assertRaises(c.APIError):
                c.GitHubAPI(self.state).get('search/issues?q=first')
            with self.assertRaises(c.APIError):
                c.GitHubAPI(self.state).get('search/issues?q=other')
            self.assertEqual(run.call_count, 1)
            sleep.assert_not_called()

    def test_private_metadata_never_enters_cache_or_failure_response(self):
        from scripts.scala_research import collector as c
        response = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n{"private":true,"description":"private-fixture"}', '')
        with patch('subprocess.run', return_value=response) as run:
            api = c.GitHubAPI(self.state)
            with self.assertRaises(c.APIError):
                api.get('repos/example/private')
            self.assertEqual(run.call_count, 1)
        self.assertFalse((self.state / api.cache_relative('repos/example/private')).exists())
        self.assertNotIn('private-fixture', ''.join(p.read_text() for p in self.state.rglob('*.json')))

    def test_repo_and_state_path_safety_and_atomic_failure(self):
        from scripts.scala_research import collector as c
        for repo in ('../library', 'owner/..', '/owner/repo', 'owner/repo/evil', 'owner/repo%2fextra', ' owner/repo', 'owner\\repo'):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                c.collect_repository(self.state, repo)
        for relative in ('../escape', '/absolute', 'a/../../escape', 'a\\escape'):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                c.atomic_json(self.state, relative, {})
        outside = self.state / 'outside'
        outside.mkdir()
        (self.state / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.atomic_json(self.state, 'linked/escape.json', {})
        c.atomic_json(self.state, 'kept.json', {'old': True})
        with patch('os.replace', side_effect=OSError('fixture interrupt')):
            with self.assertRaises(OSError):
                c.atomic_json(self.state, 'kept.json', {'old': False})
        self.assertEqual(json.loads((self.state / 'kept.json').read_text()), {'old': True})
        self.assertFalse(list(self.state.glob('.kept.json.*')))
        with patch.object(Path, 'mkdir'), self.assertRaises(ValueError):
            c.state_root(Path(c.__file__).resolve().parents[2] / 'corpus-fixture-forbidden')

    def test_corrupt_cache_refetches_and_date_boundaries(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        c.atomic_json(self.state, api.cache_relative('repos/example/library'), {'body': 'corrupt'})
        success = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n{"ok":true}', '')
        with patch('subprocess.run', return_value=success):
            self.assertEqual(api.get('repos/example/library')['body'], {'ok': True})
        self.assertEqual(api.events[0]['kind'], 'cache_corrupt')
        for value in (c.WINDOW['start'], c.WINDOW['end'], '2024-12-31T23:59:59.999999Z'):
            self.assertTrue(c.in_window(value), value)
        for value in (None, 'bad', '2020-01-01', '2017-12-31T23:59:59Z', '2025-01-01T00:00:00Z'):
            self.assertFalse(c.in_window(value), value)

    def test_shared_search_pacing_serializes_threads(self):
        from concurrent.futures import ThreadPoolExecutor
        from scripts.scala_research import collector as c
        clock = [100.0]
        sleeps = []
        def sleep(delay):
            sleeps.append(delay)
            clock[0] += delay
        with patch('time.time', side_effect=lambda: clock[0]), patch('time.sleep', side_effect=sleep):
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(lambda _: c.GitHubAPI(self.state)._pace('search'), range(3)))
        self.assertEqual(len(sleeps), 2)
        for delay in sleeps:
            self.assertAlmostEqual(delay, c.SEARCH_INTERVAL)

    def test_snapshot_fallback_uses_final_page_and_rejects_future_commit(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        latest = {'sha': 'a' * 40, 'commit': {'committer': {'date': '2024-01-01T00:00:00Z'}}}
        earliest = {'sha': 'b' * 40, 'commit': {'committer': {'date': '2021-01-01T00:00:00Z'}}}
        responses = [{'body': [], 'headers': {}},
                     {'body': [latest], 'headers': {'link': '<https://api.github.com/repos/example/library/commits?page=4>; rel="last"'}},
                     {'body': [earliest], 'headers': {}}]
        with patch.object(api, 'get', side_effect=responses) as get:
            selected, coverage = c.choose_snapshot_commit(api, 'example/library', 2020)
        self.assertEqual(selected, earliest)
        self.assertIn('page=4', get.call_args.args[0])
        with patch.object(api, 'get', return_value={'body': [latest], 'headers': {}}):
            with self.assertRaises(c.APIError):
                c.choose_snapshot_commit(api, 'example/library', 2020)

    def test_api_commit_cap_mismatch_is_explicit(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        responses = [{'body': list(range(n)), 'headers': {}} for n in (100, 100, 50)]
        with patch.object(api, 'get', side_effect=responses):
            result = c.paginated(api, 'repos/example/library/pulls/1/commits', api_cap=250, expected=251)
        self.assertFalse(result['coverage']['complete'])
        self.assertEqual(len(result['items']), 250)
        self.assertEqual({g['kind'] for g in result['gaps']}, {'api_cap', 'count_mismatch'})

    def test_search_follows_second_page_and_retains_both_page_references(self):
        from scripts.scala_research import collector as c
        api = c.GitHubAPI(self.state)
        item = {'number': 1, 'closed_at': '2020-02-01T00:00:00Z', 'pull_request': {}}
        pages = [{'body': {'total_count': 101, 'incomplete_results': False, 'items': [item] * 100}, 'headers': {}},
                 {'body': {'total_count': 101, 'incomplete_results': False, 'items': [dict(item, number=2)]}, 'headers': {}}]
        with patch.object(api, 'get', side_effect=pages) as get:
            result = c.search_pulls(api, 'example/library', 2020, 'closed_unmerged', 2)
        self.assertEqual([item['number'] for item in result['items']], [1, 2])
        self.assertEqual(len(result['coverage']['pages']), 2)
        self.assertEqual(result['coverage']['scanned'], 101)
        self.assertIn('page=2', get.call_args.args[0])

    def test_timeout_is_retried_but_not_found_is_not(self):
        from scripts.scala_research import collector as c
        success = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n{"ok":true}', '')
        with patch('subprocess.run', side_effect=[subprocess.TimeoutExpired('gh', 1), success]) as run, patch('time.sleep'):
            api = c.GitHubAPI(self.state)
            response = api.get('repos/example/library')
            self.assertEqual(run.call_count, 2)
            self.assertEqual(response['prior_attempt_errors'][0]['kind'], 'timeout')
        missing = subprocess.CompletedProcess([], 1, 'HTTP/2.0 404 Not Found\n\n{"message":"not found"}', '')
        with patch('subprocess.run', return_value=missing) as run, patch('time.sleep'):
            with self.assertRaises(c.APIError):
                api.get('repos/example/missing')
            self.assertEqual(run.call_count, 1)

    def test_fatal_collection_preserves_old_index(self):
        from scripts.scala_research import collector as c
        c.atomic_json(self.state, 'corpus/example--library/index.json', {'repository': 'example/library', 'previous': True})
        old = (self.state / 'corpus/example--library/index.json').read_bytes()
        with patch.object(c.GitHubAPI, 'get', side_effect=c.APIError('x', 'http_error', status=404)):
            with self.assertRaises(c.APIError):
                c.collect_repository(self.state, 'example/library', per_year=1)
        self.assertEqual((self.state / 'corpus/example--library/index.json').read_bytes(), old)
        self.assertTrue((self.state / 'corpus/example--library/collection.failure.json').exists())

    def test_open_activity_is_discovered_context_only_and_fully_cached(self):
        from scripts.scala_research import collector as c
        detail = self.activity_detail(49)
        groups = {49: {
            'reviews': [{'id': 1, 'submitted_at': '2019-01-02T00:00:00Z', 'body': 'fixture review'}],
            'review_comments': [{'id': 2, 'created_at': '2019-01-02T00:00:00Z', 'body': 'fixture inline'}],
            'issue_comments': [{'id': 3, 'created_at': '2019-01-02T00:00:00Z', 'body': 'fixture discussion'}],
            'commits': [{'sha': 'b' * 40, 'commit': {'committer': {'date': '2019-01-01T00:00:00Z'}}}],
            'files': [{'filename': 'src/A.scala', 'patch': 'synthetic fixture, not evidence'}],
        }}
        with patch('subprocess.run', side_effect=self.activity_transport([detail], groups)) as network, patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
            self.assertEqual([p['number'] for p in index.get('activity_pulls', [])], [49])
            before = network.call_count
            again = c.collect_repository(self.state, 'example/library', per_year=1)
            self.assertEqual(network.call_count, before)
        self.assertEqual(index['pulls'], [])
        self.assertEqual(again['coverage']['network_requests_this_run'], 0)
        entry = index['activity_pulls'][0]
        artifact = json.loads((self.state / 'corpus/example--library' / entry['path']).read_text())
        self.assertEqual(artifact['outcome'], 'open')
        self.assertTrue(artifact['historical']['activity_eligible'])
        self.assertTrue(artifact['historical']['contextual_only'])
        self.assertFalse(artifact['historical']['diff_eligible'])
        self.assertFalse(artifact['historical']['adopted_in_window'])
        self.assertEqual(artifact['historical']['activity_counts'],
                         {'reviews': 1, 'review_comments': 1, 'issue_comments': 1, 'commits': 1})
        for group, rows in groups[49].items():
            self.assertEqual(artifact[group], rows)
            self.assertTrue(artifact['coverage'][group]['complete'])
            self.assertTrue(artifact['coverage'][group]['pages'])
        self.assertEqual(index['coverage']['retrieved_activity_pulls'], 1)
        self.assertEqual(index['coverage']['retrieved_unique_pulls'], 1)
        persisted = json.loads((self.state / 'corpus/example--library/index.json').read_text())
        self.assertEqual(persisted['activity_pulls'], again['activity_pulls'])

    def test_later_closed_and_merged_activity_is_not_historical_adoption(self):
        from scripts.scala_research import collector as c
        details = [self.activity_detail(51, state='closed', closed_at='2025-01-01T00:00:00Z'),
                   self.activity_detail(53, state='closed', closed_at='2026-01-01T00:00:00Z',
                                        merged_at='2026-01-01T00:00:00Z'),
                   self.activity_detail(54, created_at='2025-01-01T00:00:00Z')]
        groups = {number: {'issue_comments': [{'id': number, 'created_at': c.WINDOW['end'], 'body': 'fixture'}],
                           'commits': [{'sha': 'b' * 40, 'commit': {'committer': {'date': '2025-01-01T00:00:00Z'}}}],
                           'files': [{'filename': 'Future.scala', 'patch': 'post-cutoff fixture'}]}
                  for number in (51, 53, 54)}
        with patch('subprocess.run', side_effect=self.activity_transport(details, groups)), patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
        self.assertEqual([p['number'] for p in index.get('activity_pulls', [])], [51, 53])
        self.assertEqual(index['pulls'], [])
        self.assertEqual([p['outcome'] for p in index['activity_pulls']], ['closed_unmerged', 'merged'])
        for entry in index['activity_pulls']:
            self.assertEqual(entry['stratum'], 'closed_after_window')
            artifact = json.loads((self.state / 'corpus/example--library' / entry['path']).read_text())
            self.assertFalse(artifact['historical']['adopted_in_window'])
            self.assertFalse(artifact['historical']['diff_eligible'])
            self.assertFalse(artifact['historical']['pull_body_eligible'])
            self.assertEqual(artifact['historical']['eligible_ids']['commits'], [])
            self.assertIn('not observed/adopted implementation', artifact['historical']['activity_limitation'])
        searches = index['coverage']['activity_discovery']['searches']
        self.assertIn('created:<2025-01-01', searches['closed_after_window']['query'])
        self.assertIn('closed:>=2025-01-01', searches['closed_after_window']['query'])
        self.assertEqual(searches['open']['excluded_dates'], [54])

    def test_activity_requires_real_window_events_not_creation_or_late_edits(self):
        from scripts.scala_research import collector as c
        details = [self.activity_detail(n, created_at='2020-01-01T00:00:00Z') for n in range(1, 6)]
        groups = {
            1: {'issue_comments': [{'id': 1, 'body': 'old fixture', 'created_at': '2017-12-31T23:59:59Z'}],
                'commits': [{'sha': 'b' * 40, 'commit': {'committer': {'date': '2017-01-01T00:00:00Z'}}}]},
            2: {},
            3: {'reviews': [{'id': 3, 'body': 'edited fixture', 'submitted_at': c.WINDOW['start'],
                             'updated_at': '2025-01-01T00:00:00Z'}],
                'issue_comments': [{'id': 4, 'body': 'edited fixture', 'created_at': c.WINDOW['end'],
                                    'updated_at': '2025-01-01T00:00:00Z'}]},
            4: {'reviews': [{'id': 5, 'body': '', 'state': 'APPROVED', 'submitted_at': c.WINDOW['start']}]},
            5: {'commits': [{'sha': 'b' * 40, 'commit': {'committer': {'date': c.WINDOW['start']}}}]},
        }
        with patch('subprocess.run', side_effect=self.activity_transport(details, groups)), patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
        self.assertEqual([p['number'] for p in index['activity_pulls']], [5])
        search = index['coverage']['activity_discovery']['searches']['open']
        self.assertEqual(search['selected_numbers'], [1, 2, 3, 4, 5])
        self.assertEqual([p['number'] for p in search['excluded']], [1, 2, 3, 4])
        self.assertEqual({p['reason'] for p in search['excluded']}, {'no_eligible_activity'})
        self.assertEqual(len(search['inspected']), 5)
        for entry in search['inspected']:
            artifact = json.loads((self.state / 'corpus/example--library' / entry['path']).read_text())
            self.assertFalse(artifact['historical']['diff_eligible'])
            self.assertEqual(artifact['historical']['activity_eligible'], entry['number'] == 5)
            self.assertEqual(entry['activity_eligible'], entry['number'] == 5)
        self.assertEqual(index['coverage']['retrieved_activity_pulls'], 1)

    def test_activity_failures_and_empty_searches_never_invent_evidence_totals(self):
        from scripts.scala_research import collector as c
        cases = [('empty', [], {}, None),
                 ('search_failed', [], {'search/issues': 503}, None),
                 ('detail_failed', [self.activity_detail(1)], {'repos/example/library/pulls/1': 404}, None),
                 ('discussion_failed', [self.activity_detail(1)], {'repos/example/library/issues/1/comments': 503},
                  'activity_unverified_incomplete_endpoints')]
        for label, details, failures, exclusion in cases:
            with self.subTest(case=label):
                state = self.state / label
                with patch('subprocess.run', side_effect=self.activity_transport(details, failures=failures)), patch('time.sleep'):
                    index = c.collect_repository(state, 'example/library', per_year=1)
                self.assertEqual(index['activity_pulls'], [])
                self.assertEqual(index['coverage']['retrieved_activity_pulls'], 0)
                self.assertEqual(index['coverage']['retrieved_unique_pulls'], 0)
                search = index['coverage']['activity_discovery']['searches']['open']
                self.assertEqual(search['total_count'], None if label == 'search_failed' else len(details))
                self.assertEqual(search['endpoint_failed'], label == 'search_failed')
                if label != 'empty':
                    self.assertEqual(index['status'], 'partial')
                if exclusion:
                    self.assertEqual(search['excluded'][0]['reason'], exclusion)
                    entry = search['inspected'][0]
                    artifact = json.loads((state / 'corpus/example--library' / entry['path']).read_text())
                    self.assertFalse(artifact['coverage']['issue_comments']['complete'])
                    self.assertFalse(artifact['historical']['activity_evaluation_complete'])
                    self.assertTrue(any(g['kind'] == 'endpoint_failed' for g in artifact['gaps']))
                    # Failed endpoint is retried on resume, successful pages are not.
                    groups = {1: {'issue_comments': [{'id': 1, 'body': 'recovered fixture', 'created_at': c.WINDOW['start']}]}}
                    with patch('subprocess.run', side_effect=self.activity_transport(details, groups)) as network, patch('time.sleep'):
                        resumed = c.collect_repository(state, 'example/library', per_year=1)
                    self.assertEqual(network.call_count, 1)
                    self.assertEqual([p['number'] for p in resumed['activity_pulls']], [1])

    def test_activity_deduplicates_normal_and_supplemental_candidates(self):
        from scripts.scala_research import collector as c
        normal = self.activity_detail(1, state='closed', closed_at='2020-01-02T00:00:00Z',
                                      merged_at='2020-01-02T00:00:00Z')
        opened = self.activity_detail(2)
        queries = {
            'repo:example/library is:pr is:merged merged:2020-01-01..2020-12-31': [dict(normal, pull_request={'merged_at': normal['merged_at']})],
            # Search caches can describe a different observation than PR details.
            'open': [self.activity_detail(1), opened, opened],
            'closed_after_window': [dict(opened, state='closed', closed_at='2026-01-01T00:00:00Z')],
        }
        groups = {n: {'issue_comments': [{'id': n, 'body': 'fixture', 'created_at': c.WINDOW['start']}]}
                  for n in (1, 2)}
        with patch('subprocess.run', side_effect=self.activity_transport([normal, opened], groups, queries)), patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
        self.assertEqual([(p['number'], p['year']) for p in index['pulls']], [(1, 2020)])
        self.assertEqual([p['number'] for p in index['activity_pulls']], [2])
        self.assertEqual(index['coverage']['retrieved_unique_pulls'], 2)
        searches = index['coverage']['activity_discovery']['searches']
        self.assertEqual(searches['open'].get('duplicate_numbers'), [1])
        self.assertEqual(searches['closed_after_window']['duplicate_numbers'], [2])
        self.assertEqual(searches['open']['selected_numbers'], [2])
        self.assertEqual(searches['closed_after_window']['selected_numbers'], [])
        self.assertFalse(any(g['kind'] == 'activity_pull_failed' for g in index['gaps']))

    def test_year_sample_diff_requires_a_verified_in_window_head_commit(self):
        from scripts.scala_research import collector as c
        detail = self.activity_detail(1, state='closed', closed_at='2020-01-02T00:00:00Z',
                                      merged_at='2020-01-02T00:00:00Z')
        for label, date, sha, eligible in (
                ('postcutoff', '2025-01-01T00:00:00Z', 'b' * 40, False),
                ('prewindow', '2017-12-31T23:59:59Z', 'b' * 40, False),
                ('head_missing', '2020-01-01T00:00:00Z', 'c' * 40, False),
                ('historical', '2020-01-01T00:00:00Z', 'b' * 40, True)):
            with self.subTest(case=label):
                groups = {1: {'commits': [{'sha': sha, 'commit': {'committer': {'date': date}}}],
                              'files': [{'filename': 'A.scala', 'patch': 'fixture'}]}}
                with patch('subprocess.run', side_effect=self.activity_transport([detail], groups)), patch('time.sleep'):
                    pull = c.collect_pull(c.GitHubAPI(self.state / label), 'example/library', 1)
                self.assertEqual(pull['historical']['diff_eligible'], eligible)
                self.assertEqual(pull['historical']['contextual_only'], not eligible)
                self.assertTrue(pull['historical']['adopted_in_window'])  # Merge event, not code provenance.
                self.assertEqual(len(pull['files']), 1)  # Raw observation is still retained.

    def test_activity_discovery_reports_hard_inspection_and_search_budgets(self):
        from scripts.scala_research import collector as c
        details = [self.activity_detail(n) for n in range(1, 8)] + [
            self.activity_detail(n, state='closed', closed_at='2025-01-01T00:00:00Z') for n in range(8, 15)]
        groups = {row['number']: {'issue_comments': [{'id': row['number'], 'body': 'fixture',
                                                     'created_at': c.WINDOW['start']}]}
                  for row in details}
        with patch('subprocess.run', side_effect=self.activity_transport(details, groups)), patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
        coverage = index['coverage']['activity_discovery']
        self.assertEqual(len(index['activity_pulls']), 2 * c.ACTIVITY_PULL_LIMIT)
        self.assertEqual(coverage.get('inspection_limit'), 2 * c.ACTIVITY_PULL_LIMIT)
        self.assertEqual(coverage['inspected_pulls'], len(index['activity_pulls']))
        self.assertEqual(coverage['search_page_limit'], 2 * c.SEARCH_PAGE_LIMIT)
        self.assertEqual(coverage['network_requests_this_run'], 2 + 6 * len(index['activity_pulls']))
        for search in coverage['searches'].values():
            self.assertEqual(search['total_count'], 7)
            self.assertEqual(search['selection_limit'], c.ACTIVITY_PULL_LIMIT)
            self.assertTrue(search['selection_limited'])
        api = c.GitHubAPI(self.state)
        first = {'body': {'total_count': 1001, 'incomplete_results': True,
                          'items': [self.activity_detail(1)] * 100}, 'headers': {}}
        second = {'body': {'total_count': 1002, 'incomplete_results': False,
                           'items': [self.activity_detail(2)] * 100}, 'headers': {}}
        with patch.object(api, 'get', side_effect=[first, second]) as get:
            result = c.search_activity_pulls(api, 'example/library', 'open')
        self.assertEqual(get.call_count, c.SEARCH_PAGE_LIMIT)
        self.assertEqual([p['number'] for p in result['items']], [1, 2])
        self.assertEqual(result['coverage']['scanned'], 200)
        self.assertEqual(result['coverage']['page_total_counts'], [1001, 1002])
        self.assertTrue(result['coverage']['scan_limited'])
        self.assertTrue({'search_incomplete', 'search_api_cap', 'search_count_changed'} <= {g['kind'] for g in result['gaps']})
        for limit in (0, True, c.ACTIVITY_PULL_LIMIT + 1):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                c.search_activity_pulls(api, 'example/library', 'open', limit=limit)

    def test_activity_search_detail_mismatch_fails_honestly(self):
        from scripts.scala_research import collector as c
        detail = self.activity_detail(1, state='closed', closed_at='2025-01-01T00:00:00Z')
        groups = {1: {'issue_comments': [{'id': 1, 'body': 'fixture', 'created_at': c.WINDOW['start']}]}}
        queries = {'open': [self.activity_detail(1)], 'closed_after_window': []}
        with patch('subprocess.run', side_effect=self.activity_transport([detail], groups, queries)), patch('time.sleep'):
            index = c.collect_repository(self.state, 'example/library', per_year=1)
        self.assertEqual(index['activity_pulls'], [])
        self.assertEqual(index['status'], 'partial')
        failures = [g for g in index['gaps'] if g['kind'] == 'activity_pull_failed']
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]['error']['kind'], 'search_detail_mismatch')

    def test_unidentifiable_activity_is_not_counted_as_historical_evidence(self):
        from scripts.scala_research import collector as c
        detail = self.activity_detail(1)
        groups = {1: {'issue_comments': [{'body': 'fixture without source id', 'created_at': c.WINDOW['start']}],
                      'commits': [{'sha': 'not-a-sha', 'commit': {'committer': {'date': c.WINDOW['start']}}}]}}
        with patch('subprocess.run', side_effect=self.activity_transport([detail], groups)), patch('time.sleep'):
            pull = c.collect_pull(c.GitHubAPI(self.state), 'example/library', 1, activity=True)
        self.assertFalse(pull['historical']['activity_eligible'])
        self.assertEqual(sum(pull['historical']['activity_counts'].values()), 0)

    @staticmethod
    def activity_detail(number, **extra):
        return dict({'number': number, 'state': 'open', 'created_at': '2017-01-01T00:00:00Z',
                     'updated_at': '2026-01-01T00:00:00Z', 'closed_at': None, 'merged_at': None,
                     'base': {'sha': 'a' * 40}, 'head': {'sha': 'b' * 40}}, **extra)

    def activity_transport(self, details, groups=None, searches=None, failures=None):
        """Synthetic public GitHub transport; exercise real cache and pagination."""
        from urllib.parse import parse_qs, urlsplit
        groups, searches, failures = groups or {}, searches or {}, failures or {}
        by_number = {row['number']: row for row in details}
        def run(command, **kwargs):
            endpoint = command[-1]
            route, query = urlsplit(endpoint).path, parse_qs(urlsplit(endpoint).query)
            status = failures.get(route, 200)
            if status != 200:
                body = {'message': 'synthetic failure'}
            elif route == 'repos/example/library':
                body = self.repo('example/library')
            elif route == 'search/issues':
                q = query['q'][0]
                stratum = 'open' if 'is:open' in q else 'closed_after_window' if 'closed:>=' in q else q
                rows = searches.get(stratum, [dict(row, pull_request={'merged_at': row.get('merged_at')})
                                              for row in details if
                                              (stratum == 'open' and row['state'] == 'open') or
                                              (stratum == 'closed_after_window' and row.get('closed_at', '') and row['closed_at'] >= '2025')])
                body = {'total_count': len(rows), 'incomplete_results': False, 'items': rows}
            elif route == 'repos/example/library/commits':
                body = []
            elif '/pulls/' in route or '/issues/' in route:
                parts = route.split('/')
                number = int(parts[4])
                if len(parts) == 5:
                    body = by_number[number]
                else:
                    group = ('issue_comments' if parts[3] == 'issues' else 'review_comments') if parts[-1] == 'comments' else parts[-1]
                    body = groups.get(number, {}).get(group, [])
            else:
                self.fail(endpoint)
            return subprocess.CompletedProcess(command, int(status != 200),
                                               f'HTTP/2.0 {status} Fixture\n\n' + json.dumps(body), '')
        return run

    @staticmethod
    def repo(name, **extra):
        return dict(full_name=name, private=False, fork=extra.get('fork', False), archived=False,
                    language=extra.get('language', 'Scala'), description='',
                    created_at=extra.get('created_at', '2017-01-01T00:00:00Z'))


if __name__ == '__main__':
    unittest.main()
