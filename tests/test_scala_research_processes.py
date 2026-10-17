"""Synthetic process-ownership regressions; never launches research agents.

Live cases skip only when the user manager is unavailable. Every live service
is a fresh scala-history-<UUID>.service, with a finite independent deadline.
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from scripts.scala_research import processes as p

TREE = '''import json, os, signal, time
from pathlib import Path
child = os.fork()
if child == 0:
    os.setsid()
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    ticks = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    Path('child.json').write_text(json.dumps({'pid': os.getpid(), 'ticks': ticks}))
    while True:
        time.sleep(1)
while not Path('child.json').exists():
    time.sleep(.01)
'''
SLEEPING_TREE = TREE + '\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\ntime.sleep(60)\n'


class TemporaryState(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = (self.root / 'synthetic.log').open('w+')
        self.addCleanup(self.log.close)

    def record(self, **changes) -> dict:
        directory = self.root / 'processes'
        directory.mkdir(exist_ok=True)
        record = dict(schema_version=1, backend=p._BACKEND, label='fixture',
                      unit=f'scala-history-{uuid.uuid4()}.service', boot_id=p._boot_id(),
                      record_path=str(directory / 'fixture.json'), pid=None,
                      start_ticks=None, invocation_id=None, cgroup=None,
                      phase='executing', cancelled=False, launch_settled=True, stopped=False)
        record.update(changes)
        p._atomic(Path(record['record_path']), record)
        return record


class OfflineProcessTests(TemporaryState):
    def test_linux_backend_exposes_the_required_api(self):
        for name in ('start', 'stop', 'alive', 'live_records', 'require_available'):
            self.assertTrue(callable(getattr(p, name, None)), name)

    def test_boot_change_ignores_stale_unit_without_contacting_manager(self):
        record = self.record(boot_id=str(uuid.uuid4()))
        with patch.object(p, '_control') as control, patch.object(p, '_kill_wrapper') as kill:
            self.assertFalse(p.alive(record))
            p.stop(None, record)
            self.assertEqual([], p.live_records(self.root))
        control.assert_not_called()
        kill.assert_not_called()

    def test_group_only_record_blocks_even_with_dead_leader_and_finished_flag(self):
        record = self.record()
        record = {k: record[k] for k in ('pid', 'start_ticks', 'boot_id', 'label')}
        record.update(pid=999999999, finished_at='previous supervisor claimed success')
        p._atomic(self.root / 'processes/fixture.json', record)
        with self.assertRaisesRegex(RuntimeError, 'legacy'):
            p.live_records(self.root)
        with self.assertRaises(RuntimeError):
            p.stop(None, record)

    def test_corrupt_record_is_not_silently_skipped(self):
        self.record()
        (self.root / 'processes/fixture.json').write_text('{partial')
        with self.assertRaisesRegex(RuntimeError, 'cannot verify'):
            p.live_records(self.root)

    def test_missing_boot_identity_is_not_stale(self):
        with self.assertRaisesRegex(RuntimeError, 'boot ID'):
            p.alive({'pid': 1})

    def test_unavailable_manager_is_a_blocker_not_empty_result(self):
        record = self.record()
        with patch.object(p, '_control', side_effect=RuntimeError('manager unavailable')):
            with self.assertRaises(RuntimeError):
                p.alive(record)
            with self.assertRaises(RuntimeError):
                p.require_available()

    def test_systemctl_failure_and_timeout_are_not_unit_absence(self):
        for response in (subprocess.CompletedProcess([], 1, '', 'bus unavailable'),
                         subprocess.TimeoutExpired('systemctl', 1)):
            with self.subTest(response=type(response).__name__), patch.object(p.subprocess, 'run') as run:
                if isinstance(response, Exception):
                    run.side_effect = response
                else:
                    run.return_value = response
                with self.assertRaises(RuntimeError):
                    p._control(['show', 'fixture.service'])

    def test_explicit_not_found_can_be_verified(self):
        record = self.record()
        response = subprocess.CompletedProcess([], 1, 'LoadState=not-found\n', '')
        with patch.object(p.subprocess, 'run', return_value=response):
            self.assertFalse(p.alive(record))

    def test_prepared_launch_is_not_assumed_inactive(self):
        record = self.record(phase='prepared', launch_settled=False)
        with patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            with self.assertRaisesRegex(RuntimeError, 'unresolved launch'):
                p.alive(record)

    def test_unit_invocation_change_refuses_shutdown(self):
        record = self.record(invocation_id='a' * 32)
        info = self.unit_info(record, InvocationID='b' * 32)
        with patch.object(p, '_control', return_value=info):
            with self.assertRaisesRegex(RuntimeError, 'invocation'):
                p.stop(None, record)

    @staticmethod
    def unit_info(record, **changes):
        result = dict(Id=record['unit'], LoadState='loaded', ActiveState='active',
                      SubState='running', ControlGroup='', InvocationID='a' * 32,
                      Description='Scala research ownership ' + record['unit'],
                      Transient='yes', Job='')
        result.update(changes)
        return result

    def test_dead_wrapper_does_not_hide_populated_cgroup(self):
        record = self.record(cgroup='/synthetic/placeholder')
        record['cgroup'] = '/synthetic/' + record['unit']
        p._atomic(Path(record['record_path']), record)
        root = self.root / 'cgroups'
        group = root / record['cgroup'].lstrip('/')
        group.mkdir(parents=True)
        (root / 'cgroup.controllers').write_text('memory pids')
        (group / 'cgroup.events').write_text('populated 1\nfrozen 0\n')
        with patch.object(p, '_CGROUP_ROOT', root), patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            self.assertTrue(p.alive(record))
            self.assertEqual([record['unit']], [r['unit'] for r in p.live_records(self.root)])
            (group / 'cgroup.events').write_text('populated 0\nfrozen 0\n')
            self.assertFalse(p.alive(record))

    def test_reused_pid_never_receives_a_signal(self):
        record = self.record(pid=7654, start_ticks='first')
        with patch.object(p.os, 'pidfd_open', return_value=42), patch.object(p.os, 'close'), \
                patch.object(p, '_identity', return_value={'pid': 7654, 'start_ticks': 'second'}), \
                patch.object(p.signal, 'pidfd_send_signal') as send:
            p._kill_wrapper(record)
        send.assert_not_called()

    def test_collection_between_show_and_stop_is_still_verified(self):
        record = self.record()
        with patch.object(p, '_show', side_effect=[self.unit_info(record),
                {'LoadState': 'not-found'}, {'LoadState': 'not-found'}]), \
                patch.object(p, '_control', side_effect=RuntimeError('unit already collected')):
            p.stop(None, record)
        self.assertTrue(record['stopped'])

    def test_stop_is_bounded_and_fail_closed_on_populated_cgroup(self):
        record = self.record()
        started = time.monotonic()
        with patch.object(p, '_STOP_SECONDS', .1), \
                patch.object(p, '_show', return_value=self.unit_info(record)), \
                patch.object(p, '_control', return_value={}), patch.object(p, '_populated', return_value=True):
            with self.assertRaisesRegex(RuntimeError, 'cleanup unverified'):
                p.stop(None, record)
        self.assertLess(time.monotonic() - started, 1)
        self.assertTrue(p._read(Path(record['record_path']))['cancelled'])

    def test_cancelled_launch_gate_never_executes_systemd_run(self):
        record = self.record(phase='prepared', launch_settled=False, cancelled=True)
        with patch.object(p.os, 'execv') as execute:
            self.assertEqual(125, p._entry('_launch', Path(record['record_path']), record['unit'], ['/bin/false']))
        execute.assert_not_called()

    def test_cancelled_service_gate_never_executes_real_command(self):
        record = self.record(phase='launching', launch_settled=False, cancelled=True)
        with patch.dict(os.environ, {'INVOCATION_ID': 'a' * 32}), patch.object(p.os, 'execv') as execute:
            self.assertEqual(125, p._entry('_execute', Path(record['record_path']), record['unit'], ['/bin/false']))
        execute.assert_not_called()
        self.assertTrue(p._read(Path(record['record_path']))['launch_settled'])

    def test_ambiguous_launch_stop_does_not_claim_success(self):
        record = self.record(phase='launching', launch_settled=False)
        with patch.object(p, '_STOP_SECONDS', .05), patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            with self.assertRaisesRegex(RuntimeError, 'cleanup unverified'):
                p.stop(None, record)
        self.assertTrue(p._read(Path(record['record_path']))['cancelled'])

    def test_stop_during_known_pre_exec_window_is_safe(self):
        record = self.record(phase='prepared', launch_settled=False, pid=999999999, start_ticks='0')
        with patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            p.stop(None, record)
            p.stop(None, record)
            self.assertFalse(p.alive(record))

    def test_same_label_cannot_overwrite_live_record(self):
        record = self.record()
        with patch.object(p, 'require_available'), \
                patch.object(p, '_show', return_value=self.unit_info(record)), patch.object(p, 'Popen') as spawn:
            with self.assertRaisesRegex(RuntimeError, 'already owns'):
                p.start([sys.executable, '-c', 'pass'], label='fixture', state=self.root,
                        cwd=self.root, seconds=10, stdout=self.log)
        spawn.assert_not_called()
        self.assertEqual(record, p._read(Path(record['record_path'])))

    def test_invalid_labels_and_budgets_do_not_launch(self):
        for label in ('', '../bad', '.', '..', '/root', '-flag', 'x/y', 'x\n', 'x' * 129):
            with self.subTest(label=label), self.assertRaises(ValueError):
                p.start([sys.executable], label=label, state=self.root, cwd=self.root,
                        seconds=10, stdout=self.log)
        for seconds in (0, -1, float('inf'), float('nan'), True):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                p.start([sys.executable], label='valid', state=self.root, cwd=self.root,
                        seconds=seconds, stdout=self.log)
        self.assertFalse((self.root / 'processes').exists())

    def test_record_is_published_before_spawn_and_spawn_failure_is_resolved(self):
        def failed_spawn(*args, **kwargs):
            record = p._read(self.root / 'processes/fixture.json')
            self.assertRegex(record['unit'], p._UNIT)
            self.assertEqual('prepared', record['phase'])
            self.assertEqual(p._boot_id(), record['boot_id'])
            self.assertIsNone(record['pid'])
            argv = args[0]
            for option in ('--user', '--wait', '--pipe', '--collect',
                           '--property=KillMode=control-group', '--property=Restart=no',
                           '--property=TimeoutStopSec=1s'):
                self.assertIn(option, argv)
            self.assertNotIn('--yolo', argv)
            self.assertNotIn('--scope', argv)
            raise OSError('synthetic spawn failure')
        with patch.object(p, 'require_available'), patch.object(p, 'Popen', side_effect=failed_spawn):
            with self.assertRaisesRegex(OSError, 'synthetic spawn failure'):
                p.start([sys.executable], label='fixture', state=self.root, cwd=self.root,
                        seconds=10, stdout=self.log)
        with patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            self.assertEqual([], p.live_records(self.root))

    def test_truthy_but_invalid_completion_flag_is_rejected(self):
        record = self.record(launch_settled='false')
        with patch.object(p, '_control', return_value={'LoadState': 'not-found'}):
            with self.assertRaisesRegex(RuntimeError, 'record'):
                p.alive(record)

    def test_old_record_cannot_stop_a_new_lifetime_of_the_same_label(self):
        old = self.record()
        current = self.record()
        with patch.object(p, '_control') as control, patch.object(p, '_kill_wrapper') as kill:
            with self.assertRaisesRegex(RuntimeError, 'different lifetime'):
                p.stop(None, old)
        kill.assert_not_called()
        control.assert_not_called()
        self.assertEqual(current, p._read(Path(current['record_path'])))

    def test_relative_path_lookup_uses_child_cwd(self):
        directory = self.root / 'relative-bin'
        directory.mkdir()
        (directory / 'synthetic-executable').symlink_to(sys.executable)
        original_path = os.environ.get('PATH', '')
        def inspect_spawn(*args, **kwargs):
            record = p._read(self.root / 'processes/fixture.json')
            self.assertEqual(str(Path(sys.executable).resolve()), record['executable'])
            raise OSError('synthetic spawn failure')
        with patch.dict(os.environ, {'PATH': 'relative-bin' + os.pathsep + original_path}), \
                patch.object(p, 'require_available'), patch.object(p, 'Popen', side_effect=inspect_spawn):
            with self.assertRaisesRegex(OSError, 'synthetic spawn failure'):
                p.start(['synthetic-executable'], label='fixture', state=self.root,
                        cwd=self.root, seconds=10, stdout=self.log)

    def test_tiny_runtime_never_rounds_to_an_unbounded_zero(self):
        def inspect_spawn(args, **kwargs):
            budgets = [arg for arg in args if arg.startswith('--property=RuntimeMaxSec=')]
            self.assertEqual(['--property=RuntimeMaxSec=1us'], budgets)
            raise OSError('synthetic spawn failure')
        with patch.object(p, 'require_available'), patch.object(p, 'Popen', side_effect=inspect_spawn):
            with self.assertRaises(OSError):
                p.start([sys.executable], label='microsecond', state=self.root,
                        cwd=self.root, seconds=1e-12, stdout=self.log)


class LiveProcessTests(TemporaryState):
    @classmethod
    def setUpClass(cls):
        try:
            result = subprocess.run(['systemctl', '--user', 'show', '--property=Version'],
                                    capture_output=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            raise unittest.SkipTest('systemd user manager is unavailable')
        if result.returncode:
            raise unittest.SkipTest('systemd user manager is unavailable')
        p.require_available()

    def spawn(self, code, *, seconds=10, label='synthetic'):
        process, record = p.start([sys.executable, '-c', code], label=label,
                                  state=self.root, cwd=self.root,
                                  seconds=seconds, stdout=self.log)
        self.addCleanup(self.cleanup_owned, process, record)
        return process, record

    def cleanup_owned(self, process, record):
        p.stop(process, record)
        self.assertFalse(p.alive(record))
        self.assertFalse(p._populated(record.get('cgroup'), record['unit']))
        self.assertEqual('not-found', p._show(record)['LoadState'])

    def child(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                return json.loads((self.root / 'child.json').read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(.01)
        self.fail('synthetic descendant did not become ready')

    @staticmethod
    def child_running(child):
        try:
            fields = Path(f'/proc/{child["pid"]}/stat').read_text().rsplit(')', 1)[1].split()
        except FileNotFoundError:
            return False
        return fields[0] != 'Z' and fields[19] == child['ticks']

    def test_normal_main_exit_kills_term_ignoring_setsid_descendant(self):
        process, record = self.spawn(TREE)
        self.assertNotEqual(0, process.wait(timeout=15))
        # The main exits zero, but forced cleanup exhausts TimeoutStopSec and
        # systemd reports failure. Preserve that rather than accepting the job.
        self.assertFalse(self.child_running(self.child()))
        self.assertFalse(p.alive(record))
        self.assertEqual([], p.live_records(self.root))
        p.stop(process, record)
        p.stop(None, record)

    def test_runtime_timeout_kills_term_ignoring_setsid_descendant(self):
        process, record = self.spawn(SLEEPING_TREE, seconds=3)
        child = self.child()
        self.assertTrue(self.child_running(child))
        self.assertNotEqual(0, process.wait(timeout=15))
        self.assertFalse(self.child_running(child))
        self.assertFalse(p.alive(record))

    def test_wrapper_disappearance_is_discoverable_and_stoppable(self):
        process, record = self.spawn(SLEEPING_TREE)
        child = self.child()
        process.kill()  # Only this test's exact Popen, never a process group.
        process.wait(timeout=5)
        self.assertTrue(self.child_running(child))
        self.assertTrue(p.alive(record))
        self.assertEqual([record['unit']], [r['unit'] for r in p.live_records(self.root)])
        p.stop(None, record)
        self.assertFalse(self.child_running(child))
        self.assertEqual([], p.live_records(self.root))
        p.stop(None, record)

    def test_command_failure_and_success_propagate(self):
        for code in (0, 7):
            with self.subTest(code=code):
                process, record = self.spawn(f'print("synthetic status {code}"); raise SystemExit({code})',
                                             label=f'exit-{code}')
                self.assertEqual(code, process.wait(timeout=10))
                self.assertFalse(p.alive(record))

    def test_environment_is_forwarded_by_name_without_persisting_values(self):
        marker = 'SYNTHETIC-not-a-real-secret-' + uuid.uuid4().hex
        with patch.dict(os.environ, {'HERMES_HOME': marker, 'http_proxy': marker}):
            process, record = self.spawn('import os; from pathlib import Path; '
                'Path("environment.json").write_text(__import__("json").dumps('
                '{k:os.environ.get(k) for k in ("HERMES_HOME","http_proxy","TMPDIR")}))')
            self.assertEqual(0, process.wait(timeout=10))
        data = json.loads((self.root / 'environment.json').read_text())
        self.assertEqual(marker, data['HERMES_HOME'])
        self.assertEqual(marker, data['http_proxy'])
        self.assertEqual(os.environ.get('TMPDIR'), data['TMPDIR'])
        self.assertNotIn(marker, json.dumps(record))
        self.assertNotIn(marker, Path(record['record_path']).read_text())
        self.assertNotIn(marker, ' '.join(process.args))

    def test_literals_are_not_expanded_by_systemd(self):
        process, record = p.start([sys.executable, '-c',
            'import sys; from pathlib import Path; Path("literal.txt").write_text(sys.argv[1])',
            '$HOME %n %u ${HOME}'], label='literals', state=self.root, cwd=self.root,
            seconds=5, stdout=self.log)
        self.addCleanup(self.cleanup_owned, process, record)
        self.assertEqual(0, process.wait(timeout=10))
        self.assertEqual('$HOME %n %u ${HOME}', (self.root / 'literal.txt').read_text())

    def test_relative_executable_and_percent_cwd_are_resolved_exactly(self):
        directory = self.root / 'literal-%n'
        directory.mkdir()
        (directory / 'python').symlink_to(sys.executable)
        process, record = p.start(['./python', '-c',
            'from pathlib import Path; Path("cwd.txt").write_text(str(Path.cwd()))'],
            label='cwd', state=self.root, cwd=directory, seconds=5, stdout=self.log)
        self.addCleanup(self.cleanup_owned, process, record)
        self.assertEqual(0, process.wait(timeout=10))
        self.assertEqual(str(directory.resolve()), (directory / 'cwd.txt').read_text())

    def test_cancel_before_launcher_exec_never_starts_service(self):
        real_popen = p.Popen
        def delayed_launch(args, **kwargs):
            return real_popen([sys.executable, '-c',
                'import os,sys,time; time.sleep(2); os.execv(sys.argv[1], sys.argv[1:])',
                *args], **kwargs)
        with patch.object(p, 'Popen', side_effect=delayed_launch), \
                concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(p.start, [sys.executable, '-c',
                'from pathlib import Path; Path("must-not-exist").touch()'],
                label='cancel-start', state=self.root, cwd=self.root, seconds=5, stdout=self.log)
            deadline = time.monotonic() + 5
            path = self.root / 'processes/cancel-start.json'
            while time.monotonic() < deadline:
                if path.exists():
                    record = p._read(path)
                    if record.get('pid'):
                        break
                time.sleep(.01)
            else:
                self.fail('launch reservation was not published')
            self.addCleanup(p.stop, None, record)
            p.stop(None, record)
            with self.assertRaises(InterruptedError):
                future.result(timeout=5)
        self.assertFalse((self.root / 'must-not-exist').exists())
        self.assertFalse(p.alive(record))
        self.assertEqual('not-found', p._show(record)['LoadState'])


if __name__ == '__main__':
    unittest.main()
