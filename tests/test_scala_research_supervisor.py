"""Offline supervisor tests; subprocess fixtures are synthetic, never research evidence."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.scala_research import supervisor as s

# Supervisor identity (pid + start ticks + boot ID) comes from Linux /proc.
LINUX_PROC = Path('/proc/self/stat').exists() and Path('/proc/sys/kernel/random/boot_id').exists()


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Never launch a probe unit from unit tests; tests that need it patch it again.
        patches = [patch.object(s.managed, 'sandbox_enforced', return_value=False)]
        if not LINUX_PROC:
            # Keep the platform-neutral run() orchestration covered off Linux (macOS CI).
            patches.append(patch.object(s, 'process_identity', return_value={
                'pid': os.getpid(), 'start_ticks': '0', 'boot_id': 'synthetic'}))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_repository_identifier_rejects_traversal_and_flags(self):
        self.assertEqual('zio--zio-http', s.key('zio/zio-http'))
        for bad in ('../zio', 'zio/..', '/zio/zio', 'zio/zio/extra', 'zio/zio;sh', '-x'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                s.key(bad)

    def test_atomic_write_replaces_complete_json(self):
        path = self.root / 'nested/report.json'
        s.atomic_json(path, {'status': 'first'})
        s.atomic_json(path, {'status': 'second'})
        self.assertEqual({'status': 'second'}, s.load(path))
        self.assertEqual(['report.json'], [p.name for p in path.parent.iterdir()])

    def test_lock_refuses_duplicate_and_releases(self):
        path = self.root / 'lock'
        with s.exclusive_lock(path):
            with self.assertRaisesRegex(RuntimeError, 'another writer'):
                with s.exclusive_lock(path):
                    self.fail('lock acquired twice')
        with s.exclusive_lock(path):
            pass

    def test_hash_detects_changed_body_and_symlinks(self):
        directory = self.root / 'candidate'
        directory.mkdir()
        file = directory / 'SKILL.md'
        file.write_text('before')
        before = s.tree_sha(directory)
        file.write_text('after!')
        self.assertNotEqual(before, s.tree_sha(directory))
        (directory / 'bad').symlink_to(file)
        with self.assertRaisesRegex(ValueError, 'symlink forbidden'):
            s.tree_sha(directory)

    @unittest.skipUnless(LINUX_PROC, 'Linux /proc identity')
    def test_identity_rejects_reused_pid_and_boot(self):
        current = s.process_identity(os.getpid())
        self.assertTrue(s.same_process(current))
        self.assertFalse(s.same_process(dict(current, start_ticks='0')))
        self.assertFalse(s.same_process(dict(current, boot_id='different')))
        self.assertFalse(s.same_process(None))

    def require_unit_backend(self):
        try:
            s.managed.require_available()
        except RuntimeError as exc:
            self.skipTest(str(exc))

    def test_worker_exit_code_and_log_are_real(self):
        self.require_unit_backend()
        supervisor = s.Supervisor(self.root)
        code = supervisor.command('fixture', [sys.executable, '-c',
                                             'print("synthetic subprocess fixture"); raise SystemExit(7)'], 10)
        self.assertEqual(7, code)
        self.assertIn('synthetic subprocess fixture', (self.root / 'logs/fixture.log').read_text())
        self.assertFalse(s.live_workers(self.root))
        self.assertEqual({}, supervisor.active)

    def test_deadline_terminates_owned_process(self):
        self.require_unit_backend()
        supervisor = s.Supervisor(self.root)
        result = supervisor.command('timeout', [sys.executable, '-c', 'import time; time.sleep(60)'], 2)
        self.assertNotEqual(0, result)
        self.assertFalse(s.live_workers(self.root))

    def test_cancelled_supervisor_spawns_nothing(self):
        supervisor = s.Supervisor(self.root)
        supervisor.stopping.set()
        with self.assertRaises(InterruptedError):
            supervisor.command('not-started', [sys.executable, '-c', 'raise SystemExit(0)'], 10)
        self.assertFalse((self.root / 'processes').exists())

    @unittest.skipUnless(LINUX_PROC, 'Linux /proc identity')
    def test_stop_never_signals_reused_identity(self):
        s.atomic_json(self.root / 'supervisor.json',
                      dict(s.process_identity(os.getpid()), start_ticks='stale'))
        with patch.object(os, 'kill') as kill, patch.object(os, 'killpg') as killpg:
            self.assertEqual([], s.stop(self.root)['units'])
            kill.assert_not_called()
            killpg.assert_not_called()

    def test_prompt_renders_only_known_placeholders(self):
        supervisor = s.Supervisor(self.root)
        variables = dict(root=s.ROOT, state=self.root, repository='zio/zio',
                         corpus='/corpus', candidate='/candidate', review='/review',
                         evaluation='/evaluation', feedback='/feedback')
        with patch.object(supervisor, 'command', return_value=0) as command:
            supervisor.agent('review', 'review-prompt.txt', variables)
        text = (self.root / 'prompts/review.txt').read_text()
        self.assertIn('[{severity,skill_id,problem,evidence}]', text)
        self.assertIn('Repo: zio/zio', text)
        self.assertNotIn('{candidate}', text)
        argv = command.call_args.args[1]
        self.assertEqual('openai-codex', argv[argv.index('--provider') + 1])
        self.assertEqual('gpt-6-astra-900k', argv[argv.index('--model') + 1])
        self.assertNotIn('--yolo', argv)

    def test_portfolio_stale_input_rejected_without_importing_quality(self):
        s.atomic_json(self.root / 'portfolio-input.json', {'jobs': []})
        s.atomic_json(self.root / 'portfolio.json', {'input_sha256': 'stale'})
        with self.assertRaisesRegex(ValueError, 'input hash mismatch'):
            s.validate_portfolio(self.root)

    def test_research_author_uses_library_not_prohibited_oneshot_mode(self):
        supervisor = s.Supervisor(self.root)
        variables = dict(root=s.ROOT, state=self.root, repository='zio/zio',
                         corpus='/corpus', candidate='/candidate', review='/review',
                         evaluation='/evaluation', feedback='/feedback')
        with patch.object(supervisor, 'command', return_value=0) as command:
            supervisor.agent('author', 'research-prompt.txt', variables)
        argv = command.call_args.args[1]
        self.assertIn(str(s.ROOT / 'scripts/scala_research/library_worker.py'), argv)
        self.assertNotIn('--oneshot', argv)
        self.assertNotIn('--ignore-rules', argv)
        self.assertNotIn('--yolo', argv)
        self.assertIn('--receipt', argv)

    def test_full_fanout_requires_a_real_accepted_authoring_pilot(self):
        supervisor = s.Supervisor(self.root)
        s.atomic_json(self.root / 'inventory.json', {'repositories': [
            {'repo': 'com-lihaoyi/sourcecode', 'included': True},
            {'repo': 'zio/zio', 'included': True}]})
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository') as research, \
             patch.object(s, 'accepted_job', return_value=False), \
             patch.object(s.concurrent.futures, 'ThreadPoolExecutor') as fanout:
            with self.assertRaisesRegex(RuntimeError, 'authoring preflight'):
                supervisor.run()
        research.assert_called_once_with('com-lihaoyi/sourcecode')
        fanout.assert_not_called()

    def test_blocked_scoped_run_returns_nonzero_instead_of_false_success(self):
        supervisor = s.Supervisor(self.root)
        s.atomic_json(self.root / 'inventory.json', {'repositories': [{'repo': 'zio/zio', 'included': True}]})
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository'), \
             patch.object(s, 'accepted_job', return_value=False):
            self.assertEqual(2, supervisor.run(repositories=['zio/zio']))

    def portfolio_fixture(self, verdict='blocked'):
        source = self.root / 'portfolio-input.json'
        inventory = {'repositories': [{'repo': repo, 'included': True} for repo in sorted(s.CORE)]}
        jobs = [{'repository': repo, 'status': 'blocked', 'reason': 'Synthetic evidence gap'}
                for repo in sorted(s.CORE)]
        for row in jobs:
            s.atomic_json(self.root / 'jobs' / f'{s.key(row["repository"])}.json', row)
        s.atomic_json(source, {'schema_version': 1, 'inventory': inventory, 'jobs': jobs})
        decision = dict(schema_version=1, input_sha256=s.sha(source), verdict=verdict,
                        selected_skill_ids=[], gaps=[], excluded_skills=[], duplicate_groups=[],
                        inventory_assessment='Synthetic complete inventory; no historical evidence.',
                        summary='Synthetic structural fixture, never research evidence.')
        s.atomic_json(self.root / 'portfolio.json', decision)
        return source, decision

    def test_portfolio_rejects_quota_padding(self):
        self.portfolio_fixture('accept')
        with self.assertRaisesRegex(ValueError, 'fewer than 36'):
            s.validate_portfolio(self.root)

    def test_portfolio_blocked_can_record_honest_empty_result(self):
        self.portfolio_fixture()
        self.assertEqual('blocked', s.validate_portfolio(self.root)['verdict'])

    def test_portfolio_requires_schema_and_deduplication_fields(self):
        for field in ('schema_version', 'gaps', 'inventory_assessment', 'excluded_skills',
                      'duplicate_groups', 'summary'):
            with self.subTest(field=field):
                _, decision = self.portfolio_fixture()
                del decision[field]
                s.atomic_json(self.root / 'portfolio.json', decision)
                with self.assertRaises(ValueError):
                    s.validate_portfolio(self.root)

    def test_portfolio_requires_outcome_for_every_included_repository(self):
        source, decision = self.portfolio_fixture()
        data = s.load(source)
        data['inventory']['repositories'].append({'repo': 'com-lihaoyi/upickle', 'included': True})
        s.atomic_json(source, data)
        decision['input_sha256'] = s.sha(source)
        s.atomic_json(self.root / 'portfolio.json', decision)
        with self.assertRaisesRegex(ValueError, 'outcome'):
            s.validate_portfolio(self.root)

    def test_malformed_review_generates_feedback_and_uses_repair_budget(self):
        supervisor = s.Supervisor(self.root, attempts=3)
        s.atomic_json(self.root / 'corpus/zio--zio/index.json', {'repository': 'zio/zio'})
        calls = []
        def agent(label, template, variables):
            calls.append(template)
            if template == 'research-prompt.txt':
                s.atomic_json(variables['candidate'] / 'report.json', {'status': 'complete', 'skills': [{'id': 'scala-fixture'}]})
            else:
                variables['review'].parent.mkdir(exist_ok=True)
                variables['review'].write_text('{')
            return 0
        quality = types.ModuleType('scripts.scala_research.quality')
        quality.validate_candidate = lambda *args, **kwargs: []
        quality.validate_review = lambda *args, **kwargs: ['malformed JSON']
        with patch.dict(sys.modules, {'scripts.scala_research.quality': quality}), \
             patch.object(s, 'accepted_job', return_value=False), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=agent):
            supervisor.repository('zio/zio')
        self.assertEqual(3, calls.count('review-prompt.txt'))
        self.assertEqual('malformed', s.load(self.root / 'feedback/zio--zio.json')['verdict'])
        self.assertEqual('blocked', s.load(self.root / 'jobs/zio--zio.json')['status'])

    def test_provider_exhaustion_output_pauses_the_whole_run(self):
        self.require_unit_backend()
        supervisor = s.Supervisor(self.root)
        with self.assertRaises(s.ProviderExhausted):
            supervisor.command('quota', [sys.executable, '-c',
                'print("scala-research: provider-exhausted error_type=ProviderCredentialsExhaustedError"); '
                'raise SystemExit(2)'], 10)
        self.assertTrue(supervisor.stopping.is_set())
        self.assertEqual('quota', supervisor.exhausted)
        events = [json.loads(line)['event'] for line in (self.root / 'events.jsonl').read_text().splitlines()]
        self.assertIn('provider_exhausted', events)
        self.assertFalse(s.live_workers(self.root))

    def test_exhaustion_detection_ignores_earlier_log_segments(self):
        self.require_unit_backend()
        log = self.root / 'logs/retry.log'
        log.parent.mkdir(parents=True)
        log.write_text('HTTP 429: The usage limit has been reached\n')
        supervisor = s.Supervisor(self.root)
        code = supervisor.command('retry', [sys.executable, '-c', 'raise SystemExit(7)'], 10)
        self.assertEqual(7, code)
        self.assertIsNone(supervisor.exhausted)
        self.assertFalse(supervisor.stopping.is_set())

    def test_exhaustion_matches_structured_failures_not_quoted_upstream_text(self):
        self.assertTrue(s.provider_exhausted('noise\nscala-research: provider-exhausted error_type=x\n'))
        self.assertTrue(s.provider_exhausted('hermes -z: agent failed: usage limit has been reached\n'))
        for quoted in ('Reviewer: on insufficient_quota the client must retry\n',
                       'HTTP 429: The usage limit has been reached\n',
                       '> library worker failed: ProviderCredentialsExhaustedError\n',
                       'hermes -z: agent failed: unrelated tool crash\n'):
            with self.subTest(quoted=quoted):
                self.assertFalse(s.provider_exhausted(quoted))

    def test_agent_units_get_sandbox_write_scopes(self):
        supervisor = s.Supervisor(self.root)
        state = supervisor.state  # resolved, as the supervisor uses it
        variables = dict(root=s.ROOT, state=state, repository='zio/zio', corpus='/corpus',
                         candidate=state / 'candidates/zio--zio', review='/review',
                         evaluation='/evaluation', feedback='/feedback')
        scopes = {}
        for label, template in (('author', 'research-prompt.txt'), ('review', 'review-prompt.txt')):
            with patch.object(supervisor, 'command', return_value=0) as command:
                supervisor.agent(label, template, variables)
            properties = command.call_args.kwargs['properties']
            self.assertIn('ProtectSystem=strict', properties)
            self.assertIn('ProtectHome=read-only', properties)
            scopes[label] = next(p for p in properties if p.startswith('ReadWritePaths='))
            hidden = next(p for p in properties if p.startswith('InaccessiblePaths='))
            self.assertIn(str(Path.home() / '.config/gh'), hidden)
            readonly = next(p for p in properties if p.startswith('ReadOnlyPaths='))
            self.assertIn('/skills', readonly)
        self.assertIn(str(state / 'candidates/zio--zio'), scopes['author'])
        self.assertNotIn(str(state / 'reviews'), scopes['author'])
        self.assertIn(str(state / 'reviews'), scopes['review'])
        for scope in scopes.values():
            self.assertNotIn(f'-{state} ', scope + ' ')
            self.assertNotIn(str(state / 'jobs'), scope)

    def test_require_sandbox_refuses_unenforced_manager(self):
        supervisor = s.Supervisor(self.root, require_sandbox=True)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command') as command:
            with self.assertRaisesRegex(RuntimeError, 'sandbox'):
                supervisor.run(repositories=['zio/zio'])
        command.assert_not_called()

    def test_provider_exhaustion_does_not_consume_research_attempts(self):
        supervisor = s.Supervisor(self.root, attempts=3)
        s.atomic_json(self.root / 'corpus/zio--zio/index.json', {'repository': 'zio/zio'})
        quality = types.ModuleType('scripts.scala_research.quality')
        quality.validate_candidate = lambda *args, **kwargs: []
        quality.validate_review = lambda *args, **kwargs: []
        with patch.dict(sys.modules, {'scripts.scala_research.quality': quality}), \
             patch.object(s, 'accepted_job', return_value=False), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=s.ProviderExhausted('synthetic')) as agent:
            supervisor.repository('zio/zio')
        self.assertEqual(1, agent.call_count)
        self.assertEqual('interrupted', s.load(self.root / 'jobs/zio--zio.json')['status'])
        self.assertFalse((self.root / 'feedback/zio--zio.json').exists())

    def test_evidence_blocked_checkpoint_is_reused_but_exhausted_attempts_rerun(self):
        quality = types.ModuleType('scripts.scala_research.quality')
        quality.validate_candidate = lambda *args, **kwargs: []
        quality.validate_review = lambda *args, **kwargs: []
        candidate = self.root / 'candidates/zio--zio'
        s.atomic_json(candidate / 'report.json', {'status': 'blocked', 'summary': 'No evidence', 'gaps': []})
        supervisor = s.Supervisor(self.root)
        s.atomic_json(self.root / 'jobs/zio--zio.json', dict(repository='zio/zio', status='blocked',
            reason='No evidence', candidate_sha256=s.tree_sha(candidate)))
        with patch.dict(sys.modules, {'scripts.scala_research.quality': quality}), \
             patch.object(supervisor, 'command') as command, patch.object(supervisor, 'agent') as agent:
            supervisor.repository('zio/zio')
        command.assert_not_called()
        agent.assert_not_called()
        s.atomic_json(self.root / 'jobs/zio--zio.json', dict(repository='zio/zio', status='blocked',
            reason='bounded research/review attempts exhausted'))
        with patch.dict(sys.modules, {'scripts.scala_research.quality': quality}), \
             patch.object(supervisor, 'command', return_value=1) as command:
            supervisor.repository('zio/zio')
        command.assert_called_once()

    def fanout_fixture(self):
        s.atomic_json(self.root / 'inventory.json', {'repositories': [
            {'repo': 'com-lihaoyi/sourcecode', 'included': True},
            {'repo': 'zio/zio', 'included': True}]})
        s.atomic_json(self.root / 'jobs/com-lihaoyi--sourcecode.json',
                      {'repository': 'com-lihaoyi/sourcecode', 'status': 'accepted'})

    def test_exhausted_fanout_skips_portfolio_and_returns_tempfail(self):
        self.fanout_fixture()
        supervisor = s.Supervisor(self.root)
        def research(repository):
            if repository == 'zio/zio':
                supervisor.exhausted = 'zio--zio-research-1'
                supervisor.stopping.set()
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository', side_effect=research), \
             patch.object(s, 'accepted_job', return_value=True), \
             patch.object(supervisor, 'portfolio') as portfolio:
            self.assertEqual(s.EXIT_PROVIDER_EXHAUSTED, supervisor.run())
        portfolio.assert_not_called()
        self.assertEqual('zio--zio-research-1', s.load(self.root / 'supervisor.json')['provider_exhausted'])

    def test_exhausted_portfolio_review_returns_tempfail(self):
        self.fanout_fixture()
        supervisor = s.Supervisor(self.root)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository'), \
             patch.object(s, 'accepted_job', return_value=True), \
             patch.object(supervisor, 'portfolio', side_effect=s.ProviderExhausted('synthetic')):
            self.assertEqual(s.EXIT_PROVIDER_EXHAUSTED, supervisor.run())

    def accepted_fixture(self, repository='zio/zio'):
        repo_key = s.key(repository)
        candidate = self.root / 'candidates' / repo_key
        s.atomic_json(candidate / 'report.json', {'status': 'complete', 'skills': [{'id': 'scala-old'}]})
        (candidate / 'skills/scala-old').mkdir(parents=True)
        (candidate / 'skills/scala-old/SKILL.md').write_text('synthetic accepted fixture\n')
        review = self.root / 'reviews' / f'{repo_key}.json'
        s.atomic_json(review, {'verdict': 'accept', 'note': 'synthetic accepted review'})
        evaluation = self.root / 'reviews/evaluations' / repo_key
        evaluation.mkdir(parents=True)
        (evaluation / 'case.md').write_text('synthetic accepted evaluation\n')
        s.atomic_json(self.root / 'corpus' / repo_key / 'index.json', {'repository': repository})
        job = dict(repository=repository, status='accepted', attempt=1, skill_ids=['scala-old'],
                   candidate_sha256=s.tree_sha(candidate), review_sha256=s.sha(review))
        s.atomic_json(self.root / 'jobs' / f'{repo_key}.json', job)
        return candidate, review, evaluation, job

    def fake_quality(self):
        quality = types.ModuleType('scripts.scala_research.quality')
        quality.validate_candidate = lambda *args, **kwargs: []
        quality.validate_review = lambda *args, **kwargs: []
        return patch.dict(sys.modules, {'scripts.scala_research.quality': quality})

    def deep_agent(self, verdict, calls=None):
        def agent(label, template, variables):
            if calls is not None:
                calls.append((template, dict(variables)))
            if template == 'research-prompt.txt':
                candidate = variables['candidate']
                (candidate / 'skills/scala-new').mkdir(parents=True, exist_ok=True)
                (candidate / 'skills/scala-new/SKILL.md').write_text('synthetic deepened fixture\n')
                s.atomic_json(candidate / 'report.json', {'status': 'complete',
                              'skills': [{'id': 'scala-old'}, {'id': 'scala-new'}]})
            else:
                s.atomic_json(variables['review'], {'verdict': verdict})
                (variables['evaluation'] / 'case.md').write_text('synthetic deep evaluation\n')
            return 0
        return agent

    def test_failed_deepen_restores_prior_acceptance_byte_for_byte(self):
        candidate, review, evaluation, job = self.accepted_fixture()
        before = (s.tree_sha(candidate), review.read_bytes(), (evaluation / 'case.md').read_text())
        supervisor = s.Supervisor(self.root, attempts=2, per_year=20, deepen=True)
        calls = []
        with self.fake_quality(), patch.object(supervisor, 'command', return_value=0) as command, \
             patch.object(supervisor, 'agent', side_effect=self.deep_agent('revise', calls)):
            supervisor.repository('zio/zio')
            self.assertTrue(s.accepted_job(self.root, 'zio/zio'))
        self.assertIn('--per-year', command.call_args.args[1])
        self.assertEqual('20', command.call_args.args[1][-1])
        self.assertEqual(before, (s.tree_sha(candidate), review.read_bytes(), (evaluation / 'case.md').read_text()))
        self.assertEqual(job, s.load(self.root / 'jobs/zio--zio.json'))
        record = s.load(self.root / 'deepen/zio--zio.json')
        self.assertEqual('not_accepted', record['status'])
        archived = Path(record['attempt_archive'])
        self.assertTrue((archived / 'candidate/skills/scala-new/SKILL.md').is_file())
        research = [v for t, v in calls if t == 'research-prompt.txt']
        self.assertEqual(2, len(research))
        self.assertTrue(research[0]['deepen'])
        self.assertIn('scala-old', research[0]['prior_skill_ids'])
        self.assertEqual('none', research[0]['deepen_previous'])

    def test_deepen_acceptance_records_expanded_skill_set(self):
        candidate, *_ = self.accepted_fixture()
        supervisor = s.Supervisor(self.root, deepen=True)
        with self.fake_quality(), patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=self.deep_agent('accept')):
            supervisor.repository('zio/zio')
            self.assertTrue(s.accepted_job(self.root, 'zio/zio'))
        job = s.load(self.root / 'jobs/zio--zio.json')
        self.assertEqual(['scala-old', 'scala-new'], job['skill_ids'])
        self.assertEqual(['scala-old'], job['prior_skill_ids'])
        self.assertTrue(job['deepened'])
        self.assertEqual('accepted', s.load(self.root / 'deepen/zio--zio.json')['status'])
        self.assertTrue((candidate / 'skills/scala-new/SKILL.md').is_file())

    def test_unclean_deepen_exit_is_recovered_before_any_work(self):
        candidate, review, _, job = self.accepted_fixture()
        before = s.tree_sha(candidate)
        crashed = s.Supervisor(self.root, deepen=True)
        with self.fake_quality():
            crashed.begin_deepen('zio/zio', candidate, review)
        (candidate / 'skills/scala-half').mkdir()
        (candidate / 'skills/scala-half/SKILL.md').write_text('interrupted partial work\n')
        review.unlink()
        s.atomic_json(self.root / 'jobs/zio--zio.json', dict(repository='zio/zio', status='researching'))
        supervisor = s.Supervisor(self.root)
        with self.fake_quality(), patch.object(supervisor, 'command') as command, \
             patch.object(supervisor, 'agent') as agent:
            supervisor.repository('zio/zio')
        command.assert_not_called()
        agent.assert_not_called()
        self.assertEqual(before, s.tree_sha(candidate))
        self.assertEqual(job, s.load(self.root / 'jobs/zio--zio.json'))
        self.assertEqual('recovered_after_unclean_exit', s.load(self.root / 'deepen/zio--zio.json')['status'])

    def test_blocked_deepen_report_restores_prior_acceptance(self):
        candidate, review, _, job = self.accepted_fixture()
        before = (s.tree_sha(candidate), review.read_bytes())
        supervisor = s.Supervisor(self.root, deepen=True)
        def author(label, template, variables):
            s.atomic_json(variables['candidate'] / 'report.json',
                          {'status': 'blocked', 'summary': 'No deeper evidence', 'gaps': ['synthetic']})
            return 0
        with self.fake_quality(), patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=author):
            supervisor.repository('zio/zio')
            self.assertTrue(s.accepted_job(self.root, 'zio/zio'))
        self.assertEqual(before, (s.tree_sha(candidate), review.read_bytes()))
        self.assertEqual(job, s.load(self.root / 'jobs/zio--zio.json'))
        record = s.load(self.root / 'deepen/zio--zio.json')
        self.assertEqual(('blocked', 'No deeper evidence'), (record['status'], record['reason']))

    def test_run_recovers_unclean_deepen_of_unscheduled_repository_first(self):
        candidate, review, _, job = self.accepted_fixture()
        before = s.tree_sha(candidate)
        with self.fake_quality():
            s.Supervisor(self.root, deepen=True).begin_deepen('zio/zio', candidate, review)
        (candidate / 'skills/scala-half').mkdir()
        (candidate / 'skills/scala-half/SKILL.md').write_text('interrupted partial work\n')
        s.atomic_json(self.root / 'jobs/zio--zio.json', dict(repository='zio/zio', status='researching'))
        s.atomic_json(self.root / 'inventory.json', {'repositories': [
            {'repo': 'zio/zio', 'included': True}, {'repo': 'typelevel/cats', 'included': True}]})
        supervisor = s.Supervisor(self.root)
        with self.fake_quality(), patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository') as research:
            supervisor.run(repositories=['typelevel/cats'])
        research.assert_called_once_with('typelevel/cats')
        self.assertEqual(before, s.tree_sha(candidate))
        self.assertEqual(job, s.load(self.root / 'jobs/zio--zio.json'))
        self.assertEqual('recovered_after_unclean_exit', s.load(self.root / 'deepen/zio--zio.json')['status'])

    def test_consolidation_needing_manual_fold_is_nonzero(self):
        s.atomic_json(self.root / 'inventory.json', {'repositories': [{'repo': 'zio/zio', 'included': True}]})
        supervisor = s.Supervisor(self.root, consolidate=True)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository'), \
             patch.object(s, 'accepted_job', return_value=True), \
             patch.object(s, 'promote_accepted', return_value={
                 'status': 'passed', 'merged_needs_manual_fold': [{'id': 'scala-zio-a'}]}):
            self.assertEqual(3, supervisor.run(repositories=['zio/zio']))

    def test_integration_lock_lives_in_the_shared_git_dir_of_a_worktree(self):
        main = self.root / 'main'
        (main / '.git').mkdir(parents=True)
        self.assertEqual(main / '.git/scala-research-integration.lock', s.integration_lock_path(main))
        worktree = self.root / 'worktree'
        worktree.mkdir()
        (worktree / '.git').write_text(f'gitdir: {main}/.git/worktrees/wt\n')
        result = subprocess.CompletedProcess([], 0, stdout=f'{main}/.git\n')
        with patch.object(s.subprocess, 'run', return_value=result) as git:
            self.assertEqual(main / '.git/scala-research-integration.lock', s.integration_lock_path(worktree))
        self.assertIn('--git-common-dir', git.call_args.args[0])

    def test_second_deepen_reuses_previous_attempt_notes(self):
        self.accepted_fixture()
        first = s.Supervisor(self.root, attempts=1, deepen=True)
        with self.fake_quality(), patch.object(first, 'command', return_value=0), \
             patch.object(first, 'agent', side_effect=self.deep_agent('revise')):
            first.repository('zio/zio')
        previous = s.load(self.root / 'deepen/zio--zio.json')['attempt_archive']
        calls = []
        second = s.Supervisor(self.root, attempts=1, deepen=True)
        with self.fake_quality(), patch.object(second, 'command', return_value=0), \
             patch.object(second, 'agent', side_effect=self.deep_agent('revise', calls)):
            second.repository('zio/zio')
        self.assertEqual(previous + '/candidate', calls[0][1]['deepen_previous'])

    def test_provider_exhaustion_during_deepen_restores_acceptance_and_pauses(self):
        _, _, _, job = self.accepted_fixture()
        supervisor = s.Supervisor(self.root, deepen=True)
        with self.fake_quality(), patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=s.ProviderExhausted('synthetic')):
            supervisor.repository('zio/zio')
            self.assertTrue(s.accepted_job(self.root, 'zio/zio'))
        self.assertTrue(supervisor.stopping.is_set())
        self.assertEqual(job, s.load(self.root / 'jobs/zio--zio.json'))
        self.assertEqual('interrupted', s.load(self.root / 'deepen/zio--zio.json')['status'])

    def test_deepen_prompt_appends_addendum_with_prior_skills(self):
        supervisor = s.Supervisor(self.root, deepen=True)
        variables = dict(root=s.ROOT, state=self.root, repository='zio/zio', corpus='/corpus',
                         candidate='/candidate', review='/review', evaluation='/evaluation',
                         feedback='/feedback', deepen=True, prior_skill_ids='scala-old',
                         deepen_previous='none')
        with patch.object(supervisor, 'command', return_value=0):
            supervisor.agent('author', 'research-prompt.txt', variables)
        text = (self.root / 'prompts/author.txt').read_text()
        self.assertIn('DEEPENING PASS', text)
        self.assertIn('scala-old', text)
        self.assertNotIn('{prior_skill_ids}', text)
        self.assertNotIn('{deepen_previous}', text)

    def test_deepen_requires_explicit_repositories(self):
        supervisor = s.Supervisor(self.root, deepen=True)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'deepen requires'):
                supervisor.run()

    def test_deepen_scoped_run_is_nonzero_when_only_restored(self):
        s.atomic_json(self.root / 'inventory.json', {'repositories': [{'repo': 'zio/zio', 'included': True}]})
        s.atomic_json(self.root / 'deepen/zio--zio.json', {'repository': 'zio/zio', 'status': 'not_accepted'})
        supervisor = s.Supervisor(self.root, deepen=True)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository'), \
             patch.object(s, 'accepted_job', return_value=True):
            self.assertEqual(2, supervisor.run(repositories=['zio/zio']))
        s.atomic_json(self.root / 'deepen/zio--zio.json', {'repository': 'zio/zio', 'status': 'accepted'})
        supervisor = s.Supervisor(self.root, deepen=True)
        with patch.object(s.managed, 'require_available'), \
             patch.object(s, 'live_workers', return_value=[]), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'repository'), \
             patch.object(s, 'accepted_job', return_value=True):
            self.assertEqual(0, supervisor.run(repositories=['zio/zio']))

    def test_cancellation_during_last_attempt_is_interrupted_not_blocked(self):
        supervisor = s.Supervisor(self.root, attempts=1)
        s.atomic_json(self.root / 'corpus/zio--zio/index.json', {'repository': 'zio/zio'})
        def agent(label, template, variables):
            if template == 'research-prompt.txt':
                s.atomic_json(variables['candidate'] / 'report.json', {'status': 'complete', 'skills': []})
                return 0
            supervisor.stopping.set()
            return -9
        with self.fake_quality(), patch.object(s, 'accepted_job', return_value=False), \
             patch.object(supervisor, 'command', return_value=0), \
             patch.object(supervisor, 'agent', side_effect=agent):
            supervisor.repository('zio/zio')
        self.assertEqual('interrupted', s.load(self.root / 'jobs/zio--zio.json')['status'])

    def test_consolidate_flag_integrates_after_run_but_not_after_pause(self):
        s.atomic_json(self.root / 'inventory.json', {'repositories': [{'repo': 'zio/zio', 'included': True}]})
        for exhausted, expected in ((False, 1), (True, 0)):
            supervisor = s.Supervisor(self.root, consolidate=True)
            def research(repository, supervisor=supervisor, exhausted=exhausted):
                if exhausted:
                    supervisor.exhausted = 'zio--zio-research-1'
                    supervisor.stopping.set()
            with self.subTest(exhausted=exhausted), \
                 patch.object(s.managed, 'require_available'), \
                 patch.object(s, 'live_workers', return_value=[]), \
                 patch.object(supervisor, 'command', return_value=0), \
                 patch.object(supervisor, 'repository', side_effect=research), \
                 patch.object(s, 'accepted_job', return_value=True), \
                 patch.object(s, 'promote_accepted', return_value={'status': 'passed'}) as integrate:
                supervisor.run(repositories=['zio/zio'])
                self.assertEqual(expected, integrate.call_count)

    def test_summary_counts_from_persisted_jobs(self):
        for repo, status, ids in [('zio/zio', 'accepted', ['scala-a', 'scala-b']),
                                  ('typelevel/cats', 'blocked', [])]:
            s.atomic_json(self.root / 'jobs' / f'{s.key(repo)}.json',
                          dict(repository=repo, status=status, skill_ids=ids))
        result = s.summary(self.root)
        self.assertEqual(2, result['jobs'])
        self.assertEqual({'accepted': 1, 'blocked': 1}, result['counts'])
        self.assertEqual(2, result['accepted_skill_count'])


if __name__ == '__main__':
    unittest.main()
