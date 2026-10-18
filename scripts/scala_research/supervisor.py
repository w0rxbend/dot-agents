#!/usr/bin/env python3
"""Bounded, restartable historical Scala research with independent Hermes workers.

Raw evidence and logs are private local state, not catalog content. Candidate,
peer review, and portfolio acceptance are separate gates. No upstream code runs.
"""
import argparse
import concurrent.futures
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import processes as managed
from .consolidate import HUB_SKILL  # noqa: F401 - public constant for callers/tests

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = Path.home() / '.local/share/dot-agents/scala-history-2018-2024'
CORE = {'zio/zio', 'zio/zio-kafka', 'zio/zio-http', 'typelevel/cats',
        'typelevel/cats-effect', 'http4s/http4s', 'typelevel/fs2', 'playframework/playframework'}
ID = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z')
# EX_TEMPFAIL: the provider refused work; checkpoints are intact and resumable.
EXIT_PROVIDER_EXHAUSTED = 75
# Final quota/credit failures only. Transient per-minute 429s that exhaust Hermes
# retries still fail one attempt; they must not pause every sibling worker.
EXHAUSTED = re.compile(r'ProviderCredentialsExhaustedError|usage limit has been reached|'
                       r'quota exhausted|insufficient_quota|credit balance is too low|'
                       r'credential pool exhausted|\b402\b|billing', re.I)
# Only structured failure lines count, never free-form agent output that may quote
# upstream text: library_worker's marker, or Hermes one-shot's own failure line.
EXHAUSTED_MARKER = 'scala-research: provider-exhausted'
ONESHOT_FAILURE = 'hermes -z: agent failed:'
# Agent units must not reach these even read-only (gh/ssh/gpg credentials).
SECRET_PATHS = ('.config/gh', '.ssh', '.gnupg', '.git-credentials', '.netrc')
# Hermes state that, if writable, would let one agent steer later sessions or reviewers.
HERMES_READ_ONLY = ('skills', 'config.yaml', 'hermes-agent', 'plugins', 'hooks', 'memories')
SANDBOX_PATH = re.compile(r'/[^\s"\'\\%;]*\Z')


class ProviderExhausted(RuntimeError):
    """The pinned provider cannot serve requests; pause instead of burning attempts."""


def now():
    return datetime.now(timezone.utc).isoformat()


def key(repository):
    if not ID.fullmatch(repository) or any(p in {'.', '..'} for p in repository.split('/')):
        raise ValueError('invalid repository identifier')
    return repository.replace('/', '--')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f'.{path.name}.{os.getpid()}.{threading.get_ident()}.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(directory):
    directory = Path(directory)
    digest = hashlib.sha256()
    for item in sorted(directory.rglob('*')):
        if item.is_symlink():
            raise ValueError(f'candidate symlink forbidden: {item}')
        if item.is_file():
            digest.update(item.relative_to(directory).as_posix().encode() + b'\0')
            digest.update(item.read_bytes() + b'\0')
    return digest.hexdigest()


def process_identity(pid):
    """Linux boot ID + start ticks prevents stale-PID signalling after reuse/reboot."""
    try:
        text = Path(f'/proc/{int(pid)}/stat').read_text()
        fields = text.rsplit(')', 1)[1].split()
        if fields[0] == 'Z':
            return None
        return {'pid': int(pid), 'start_ticks': fields[19],
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    except (OSError, ValueError, IndexError):
        return None


def provider_exhausted(segment):
    for line in segment.splitlines():
        line = line.strip()
        if line.startswith(EXHAUSTED_MARKER):
            return True
        if line.startswith(ONESHOT_FAILURE) and EXHAUSTED.search(line[len(ONESHOT_FAILURE):]):
            return True
    return False


def integration_lock_path(root):
    """Lock in the git common dir, so every worktree of one checkout serializes too."""
    root = Path(root)
    git = root / '.git'
    if git.is_file():
        try:
            out = subprocess.run(['git', '-C', str(root), 'rev-parse', '--git-common-dir'],
                                 capture_output=True, text=True, timeout=30, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError('cannot locate the shared git directory for the integration lock') from exc
        git = Path(out) if Path(out).is_absolute() else root / out
    return git / 'scala-research-integration.lock'


def same_process(record):
    return bool(record and process_identity(record.get('pid', -1)) ==
                {k: record.get(k) for k in ('pid', 'start_ticks', 'boot_id')})


@contextlib.contextmanager
def exclusive_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f'another writer owns {path}') from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def live_workers(state):
    return managed.live_records(Path(state))

def accepted_job(state, repository):
    """Recheck all bytes and gates, not just a historic success flag."""
    from .quality import validate_candidate, validate_review
    candidate = state / 'candidates' / key(repository)
    review = state / 'reviews' / f'{key(repository)}.json'
    path = state / 'jobs' / f'{key(repository)}.json'
    try:
        row = load(path)
        return (row.get('status') == 'accepted'
                and row.get('candidate_sha256') == tree_sha(candidate)
                and row.get('review_sha256') == sha(review)
                and not validate_candidate(candidate, repository)
                and not validate_review(review, candidate, repository)
                and load(review).get('verdict') == 'accept')
    except (OSError, ValueError, KeyError, TypeError):
        return False


class Supervisor:
    def __init__(self, state, *, workers=6, per_year=6, attempts=3,
                 job_seconds=2700, hours=48, model='gpt-6-astra-900k',
                 provider='openai-codex', max_turns=100, deepen=False, consolidate=False,
                 require_sandbox=False):
        self.state = Path(state).resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        self.workers, self.per_year, self.attempts = workers, per_year, attempts
        self.job_seconds, self.hours, self.max_turns = job_seconds, hours, max_turns
        self.model, self.provider = model, provider
        self.stopping = threading.Event()
        self.done = threading.Event()
        self.mutex = threading.RLock()
        self.active = {}
        self.collect_slots = threading.BoundedSemaphore(min(workers, 3))
        self.deadline = None
        self.exhausted = None
        self.deepen = deepen
        self.consolidate = consolidate
        self.require_sandbox = require_sandbox

    def check_running(self):
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.stopping.set()
        if self.stopping.is_set():
            raise InterruptedError('supervisor cancelled or total budget exhausted')

    def event(self, kind, **data):
        record = dict(at=now(), event=kind, **data)
        with self.mutex:
            with (self.state / 'events.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
            print(json.dumps(record, ensure_ascii=False), flush=True)

    def checkpoint(self, repository, status, **data):
        row = dict(repository=repository, status=status, updated_at=now(), **data)
        atomic_json(self.state / 'jobs' / f'{key(repository)}.json', row)
        self.event('job', **row)

    def cancel_active(self):
        with self.mutex:
            processes = list(self.active.values())
        failures = []
        for process, record in processes:
            try:
                managed.stop(process, record)
            except RuntimeError as exc:
                failures.append(f'{record["label"]}: {exc}')
        if failures:
            raise RuntimeError('unverified worker cleanup: ' + '; '.join(failures))

    def cancellation_watcher(self):
        self.stopping.wait()
        if not self.done.is_set():
            self.event('cancellation_requested')
            try:
                self.cancel_active()
            except RuntimeError as exc:
                self.event('cleanup_blocked', error=str(exc))

    def command(self, label, command, seconds, properties=()):
        self.check_running()
        if self.deadline is not None:
            seconds = min(seconds, max(0.01, self.deadline - time.monotonic()))
        log = self.state / 'logs' / f'{label}.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        offset = log.stat().st_size if log.exists() else 0
        with log.open('a', encoding='utf-8') as stream:
            stream.write(f'\n--- {now()} ---\n')
            stream.flush()
            with self.mutex:
                self.check_running()
                process, record = managed.start(command, label=label, state=self.state,
                                                cwd=ROOT, seconds=seconds, stdout=stream,
                                                properties=properties)
                self.active[label] = (process, record)
            self.event('process_started', label=label, pid=process.pid,
                       unit=record['unit'], log=str(log))
            try:
                result = process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                result = 124
            finally:
                # The backend owns records and checks the entire cgroup, not just PID.
                # On failure retain ownership and propagate; never license a new writer.
                managed.stop(process, record)
                with self.mutex:
                    self.active.pop(label, None)
            self.event('process_finished', label=label, exit_code=result, log=str(log))
        if result:
            with log.open('rb') as stream:
                stream.seek(offset)
                segment = stream.read().decode('utf-8', 'replace')
            if provider_exhausted(segment):
                with self.mutex:
                    first = self.exhausted is None
                    if first:
                        self.exhausted = label
                if first:
                    self.event('provider_exhausted', label=label, model=self.model,
                               provider=self.provider, log=str(log))
                # Stop siblings too: every pinned worker shares the exhausted provider.
                self.stopping.set()
                raise ProviderExhausted(f'{self.provider} unavailable during {label}')
        return result

    def sandbox(self, writable, read_only=()):
        """systemd namespace properties for one agent unit.

        Only effective where the user manager can create mount namespaces; `run` probes
        that and records `sandbox_enforced`. Paths are absolute and specifier-free.
        """
        home = Path.home()
        hermes = Path(os.environ.get('HERMES_HOME') or home / '.hermes')
        groups = {'ReadWritePaths': [self.state / 'processes', hermes, *writable],
                  'ReadOnlyPaths': [*(hermes / name for name in HERMES_READ_ONLY), *read_only],
                  'InaccessiblePaths': [home / name for name in SECRET_PATHS]}
        properties = ['ProtectSystem=strict', 'ProtectHome=read-only', 'PrivateTmp=yes', 'NoNewPrivileges=yes']
        for name, paths in groups.items():
            paths = [str(Path(path).absolute()) for path in paths]
            if any(not SANDBOX_PATH.fullmatch(path) for path in paths):
                raise ValueError('sandbox paths must be absolute without whitespace, quotes or %')
            # "-" ignores a missing path instead of failing the unit start.
            properties.append(name + '=' + ' '.join('-' + path for path in paths))
        return properties

    def agent(self, label, template, variables):
        prompt = self.state / 'prompts' / f'{label}.txt'
        prompt.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / 'research/scala-history' / template).read_text()
        if template == 'research-prompt.txt' and variables.get('deepen'):
            text += '\n\n' + (ROOT / 'research/scala-history/deepen-addendum.txt').read_text()
        for name, value in variables.items():
            text = text.replace('{' + name + '}', str(value))
        prompt.write_text(text, encoding='utf-8')
        if template == 'research-prompt.txt':
            command = [sys.executable, str(ROOT / 'scripts/scala_research/library_worker.py'),
                       '--provider', self.provider, '--model', self.model,
                       '--max-turns', str(self.max_turns), '--run-budget', str(self.job_seconds),
                       '--query-file', str(prompt), '--cwd', str(ROOT),
                       '--receipt', str(self.state / 'receipts' / f'{label}.json')]
            (self.state / 'receipts').mkdir(parents=True, exist_ok=True)
            properties = self.sandbox([variables['candidate'], self.state / 'receipts'])
        else:
            # Read-only review remains a one-shot task; only authors need library mode.
            command = ['hermes', 'chat', '--provider', self.provider, '--model', self.model,
                       '--reasoning', 'high', '--toolsets', 'terminal,file,skills',
                       '--max-turns', str(self.max_turns), '--run-budget', str(self.job_seconds),
                       '--oneshot', '--quiet', '--query-file', str(prompt)]
            if template == 'portfolio-prompt.txt':
                # Writes portfolio.json in the state root; every research artifact stays read-only.
                protected = ('jobs', 'candidates', 'reviews', 'corpus', 'deepen', 'deepen-snapshots',
                             'deepen-attempts', 'feedback', 'receipts', 'prompts', 'review-history',
                             'portfolio-input.json', 'inventory.json', 'supervisor.json')
                properties = self.sandbox([self.state], [self.state / name for name in protected])
            else:
                (self.state / 'reviews').mkdir(parents=True, exist_ok=True)
                properties = self.sandbox([self.state / 'reviews'])
        return self.command(label, command, self.job_seconds + 120, properties=properties)

    def repository(self, repository):
        from .quality import validate_candidate, validate_review
        repo_key = key(repository)
        candidate = self.state / 'candidates' / repo_key
        corpus = self.state / 'corpus' / repo_key / 'index.json'
        review = self.state / 'reviews' / f'{repo_key}.json'
        feedback = self.state / 'feedback' / f'{repo_key}.json'
        candidate.mkdir(parents=True, exist_ok=True)
        evaluation = self.state / 'reviews' / 'evaluations' / repo_key
        variables = dict(root=ROOT, state=self.state, repository=repository,
                         candidate=candidate, corpus=corpus, review=review,
                         evaluation=evaluation, feedback=feedback)
        deepening = None
        try:
            self.recover_deepen(repository)
            if accepted_job(self.state, repository):
                if not self.deepen:
                    self.event('accepted_checkpoint_reused', repository=repository)
                    return
                deepening = self.begin_deepen(repository, candidate, review)
                variables.update(deepen=True, prior_skill_ids=', '.join(deepening['prior_job']['skill_ids']),
                                 deepen_previous=deepening['previous'])
            if self.evidence_blocked(repository, candidate, validate_candidate):
                self.event('evidence_blocked_checkpoint_reused', repository=repository)
                return
            self.checkpoint(repository, 'collecting')
            with self.collect_slots:
                result = self.command(f'{repo_key}-collect',
                    [sys.executable, '-m', 'scripts.scala_research.collector',
                     '--state', str(self.state), 'collect', repository,
                     '--per-year', str(self.per_year)], max(5400, self.job_seconds))
            if result or not corpus.is_file():
                raise RuntimeError(f'corpus collection failed (exit {result}); resumable cache retained')
            index = load(corpus)
            if index.get('repository', '').lower() != repository.lower():
                raise ValueError('corpus repository mismatch')
            for attempt in range(1, self.attempts + 1):
                self.checkpoint(repository, 'researching', attempt=attempt)
                result = self.agent(f'{repo_key}-research-{attempt}', 'research-prompt.txt', variables)
                # A worker killed by cancellation is not an evidence/quality failure.
                self.check_running()
                # New candidates are cross-checked against the cached corpus they cite.
                errors = validate_candidate(candidate, repository, corpus=corpus.parent)
                if result:
                    errors.insert(0, f'research process exit {result}; artifacts are not accepted')
                if errors:
                    atomic_json(feedback, dict(phase='candidate', errors=errors, at=now()))
                    self.event('candidate_rejected', repository=repository, errors=errors[:12])
                    continue
                report = load(candidate / 'report.json')
                if report['status'] == 'blocked':
                    if deepening:
                        # An honest "no deeper evidence" still restores the accepted package.
                        self.restore_deepen(repository, 'blocked', reason=report['summary'])
                        return
                    self.checkpoint(repository, 'blocked', reason=report['summary'],
                                    gaps=report['gaps'], candidate_sha256=tree_sha(candidate))
                    return
                before = tree_sha(candidate)
                # Archive prior reviews so a worker cannot accidentally reuse stale acceptance.
                if review.exists():
                    archive = self.state / 'review-history' / f'{repo_key}-{time.time_ns()}.json'
                    archive.parent.mkdir(parents=True, exist_ok=True)
                    review.replace(archive)
                self.checkpoint(repository, 'reviewing', attempt=attempt)
                result = self.agent(f'{repo_key}-review-{attempt}', 'review-prompt.txt', variables)
                self.check_running()
                errors = validate_review(review, candidate, repository)
                if result:
                    errors.insert(0, f'review process exit {result}')
                if tree_sha(candidate) != before:
                    errors.insert(0, 'read-only reviewer changed candidate bytes')
                try:
                    review_data = load(review)
                    verdict = review_data.get('verdict', 'malformed') if isinstance(review_data, dict) else 'malformed'
                except (OSError, ValueError):
                    verdict = 'malformed'
                if verdict == 'malformed' and not errors:
                    errors.append('review is missing, malformed, or lacks a verdict')
                if not errors and verdict == 'accept':
                    extra = {}
                    if deepening:
                        extra = dict(deepened=True, prior_skill_ids=deepening['prior_job']['skill_ids'])
                    self.checkpoint(repository, 'accepted', attempt=attempt,
                                    model=self.model, provider=self.provider,
                                    candidate_sha256=before, review_sha256=sha(review),
                                    skill_ids=[s['id'] for s in load(candidate / 'report.json')['skills']],
                                    **extra)
                    if deepening:
                        self.finish_deepen(repository, 'accepted')
                    return
                atomic_json(feedback, dict(phase='review', errors=errors, verdict=verdict,
                                           review=str(review), at=now()))
                self.event('peer_revision_requested', repository=repository,
                           verdict=verdict, errors=errors[:12])
            if deepening:
                self.restore_deepen(repository, 'not_accepted')
                return
            self.checkpoint(repository, 'blocked', reason='bounded research/review attempts exhausted',
                            feedback=str(feedback))
        except ProviderExhausted as exc:
            # Never charge provider unavailability against the bounded repair budget.
            self.stopping.set()
            if deepening:
                self.restore_deepen(repository, 'interrupted', reason=f'ProviderExhausted: {exc}')
                return
            self.checkpoint(repository, 'interrupted', reason=f'ProviderExhausted: {exc}')
        except Exception as exc:
            if deepening:
                # Prior independent acceptance is never lost to a failed deepening pass.
                self.restore_deepen(repository, 'interrupted' if self.stopping.is_set() else 'failed',
                                    reason=f'{type(exc).__name__}: {exc}')
                return
            self.checkpoint(repository, 'interrupted' if self.stopping.is_set() else 'blocked',
                            reason=f'{type(exc).__name__}: {exc}')

    def deepen_paths(self, repository):
        repo_key = key(repository)
        return dict(record=self.state / 'deepen' / f'{repo_key}.json',
                    candidate=self.state / 'candidates' / repo_key,
                    review=self.state / 'reviews' / f'{repo_key}.json',
                    evaluation=self.state / 'reviews' / 'evaluations' / repo_key,
                    job=self.state / 'jobs' / f'{repo_key}.json')

    def begin_deepen(self, repository, candidate, review):
        """Snapshot an accepted package so a deeper pass can add skills without risking it."""
        paths = self.deepen_paths(repository)
        record_path = paths['record']
        previous = 'none'
        if record_path.is_file():
            old = load(record_path)
            archive = Path(old.get('attempt_archive') or '')
            if old.get('attempt_archive') and (archive / 'candidate').is_dir():
                previous = str(archive / 'candidate')
        root = self.state / 'deepen-snapshots' / f'{key(repository)}-{time.time_ns()}'
        root.mkdir(parents=True)
        shutil.copytree(paths['candidate'], root / 'candidate', symlinks=True)
        shutil.copy2(paths['review'], root / 'review.json')
        if paths['evaluation'].is_dir():
            shutil.copytree(paths['evaluation'], root / 'evaluation', symlinks=True)
        shutil.copy2(paths['job'], root / 'job.json')
        prior_job = load(paths['job'])
        record = dict(repository=repository, status='active', started_at=now(), snapshot=str(root),
                      prior_job=prior_job, previous=previous, model=self.model, provider=self.provider)
        atomic_json(record_path, record)
        self.event('deepen_started', repository=repository, snapshot=str(root),
                   prior_skill_ids=prior_job.get('skill_ids'))
        return record

    def restore_deepen(self, repository, status, **data):
        paths = self.deepen_paths(repository)
        record = load(paths['record'])
        snapshot = Path(record['snapshot'])
        archive = self.state / 'deepen-attempts' / f'{key(repository)}-{time.time_ns()}'
        archive.mkdir(parents=True)
        if paths['candidate'].exists():
            shutil.move(str(paths['candidate']), str(archive / 'candidate'))
        if paths['review'].exists():
            shutil.move(str(paths['review']), str(archive / 'review.json'))
        if paths['evaluation'].exists():
            shutil.move(str(paths['evaluation']), str(archive / 'evaluation'))
        shutil.copytree(snapshot / 'candidate', paths['candidate'], symlinks=True)
        shutil.copy2(snapshot / 'review.json', paths['review'])
        if (snapshot / 'evaluation').is_dir():
            shutil.copytree(snapshot / 'evaluation', paths['evaluation'], symlinks=True)
        atomic_json(paths['job'], record['prior_job'])
        if not accepted_job(self.state, repository):
            raise RuntimeError(f'deepen restore failed to re-verify prior acceptance: {repository}')
        atomic_json(paths['record'], dict(record, status=status, finished_at=now(),
                                         attempt_archive=str(archive), **data))
        self.event('deepen_restored', repository=repository, status=status,
                   attempt_archive=str(archive), **data)

    def finish_deepen(self, repository, status):
        paths = self.deepen_paths(repository)
        record = load(paths['record'])
        atomic_json(paths['record'], dict(record, status=status, finished_at=now()))
        self.event('deepen_finished', repository=repository, status=status)

    def recover_all_deepen(self):
        """Restore every deepen pass an unclean exit left active, scheduled or not."""
        directory = self.state / 'deepen'
        for path in sorted(directory.glob('*.json')) if directory.is_dir() else []:
            record = load(path)
            if record.get('status') != 'active':
                continue
            repository = record.get('repository', '')
            if f'{key(repository)}.json' != path.name:
                raise ValueError(f'deepen record does not match its repository: {path.name}')
            self.recover_deepen(repository)

    def recover_deepen(self, repository):
        """An active record at startup means an unclean exit; restore before any new work."""
        path = self.deepen_paths(repository)['record']
        if path.is_file() and load(path).get('status') == 'active':
            self.restore_deepen(repository, 'recovered_after_unclean_exit')

    def evidence_blocked(self, repository, candidate, validate_candidate):
        """Reuse an author's verified evidence-blocked outcome; rerun exhausted attempts."""
        try:
            row = load(self.state / 'jobs' / f'{key(repository)}.json')
            return (row.get('status') == 'blocked' and bool(row.get('candidate_sha256'))
                    and row['candidate_sha256'] == tree_sha(candidate)
                    and load(candidate / 'report.json').get('status') == 'blocked'
                    and not validate_candidate(candidate, repository))
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def portfolio(self, inventory):
        jobs = []
        for item in inventory['repositories']:
            if not item['included']:
                continue
            repository = item['repo']
            row = load(self.state / 'jobs' / f'{key(repository)}.json')
            if row['status'] == 'accepted' and not accepted_job(self.state, repository):
                raise ValueError(f'acceptance invalidated: {repository}')
            jobs.append(row)
        source = self.state / 'portfolio-input.json'
        output = self.state / 'portfolio.json'
        atomic_json(source, dict(schema_version=1, inventory=inventory, jobs=jobs))
        if output.exists():
            output.replace(self.state / f'portfolio-previous-{time.time_ns()}.json')
        result = self.agent('portfolio-review', 'portfolio-prompt.txt',
                           dict(root=ROOT, state=self.state, portfolio_input=source,
                                portfolio_output=output))
        if result or not output.exists():
            raise RuntimeError(f'portfolio review failed: exit {result}')
        decision = validate_portfolio(self.state)
        self.event('portfolio_reviewed', verdict=decision['verdict'],
                   selected_count=len(decision['selected_skill_ids']))
        return decision

    def run(self, *, repositories=None, promote=False, promotion_only=False):
        with exclusive_lock(self.state / 'supervisor.lock'):
            managed.require_available()
            orphans = live_workers(self.state)
            if orphans:
                raise RuntimeError(f'live orphan workers; stop them before resume: {[p["pid"] for p in orphans]}')
            identity = process_identity(os.getpid())
            if identity is None:
                raise RuntimeError('cannot identify supervisor process')
            sandboxed = managed.sandbox_enforced(self.state)
            if self.require_sandbox and not sandboxed:
                raise RuntimeError('this systemd user manager does not enforce agent sandbox properties '
                                   '(mount namespaces unavailable); refusing --require-sandbox run')
            self.deadline = time.monotonic() + self.hours * 3600
            run_record = dict(identity, model=self.model, provider=self.provider,
                              workers=self.workers, per_year=self.per_year, attempts=self.attempts,
                              job_seconds=self.job_seconds, hours=self.hours, deepen=self.deepen,
                              sandbox_enforced=sandboxed, started_at=now())
            atomic_json(self.state / 'supervisor.json', run_record)
            previous = {}
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous[sig] = signal.signal(sig, lambda *_: self.stopping.set())
            timer = threading.Timer(self.hours * 3600, self.stopping.set)
            timer.daemon = True
            timer.start()
            watcher = threading.Thread(target=self.cancellation_watcher, daemon=True)
            watcher.start()
            try:
                self.event('run_started', **run_record)
                if not sandboxed:
                    self.event('sandbox_unenforced', detail='agent units run without namespace isolation; '
                               'write limits are prompt policy only')
                if self.deepen and repositories is None:
                    raise ValueError('deepen requires explicit --repo selections')
                # Before any new work: never leave another repository's deepen half-written.
                self.recover_all_deepen()
                if promotion_only:
                    result = promote_portfolio(self.state, self)
                    self.event('promotion_finished', status=result['status'])
                    return 0
                result = self.command('inventory', [sys.executable, '-m',
                    'scripts.scala_research.collector', '--state', str(self.state), 'discover'], 1800)
                if result:
                    raise RuntimeError(f'inventory failed: exit {result}')
                inventory = load(self.state / 'inventory.json')
                all_repos = [r['repo'] for r in inventory['repositories'] if r['included']]
                if len({r.lower() for r in all_repos}) != len(all_repos):
                    raise ValueError('duplicate repository inventory')
                selected = all_repos if repositories is None else repositories
                if not set(selected) <= set(all_repos):
                    raise ValueError('requested repo missing from included inventory')
                # Large core ecosystems start first; smaller libraries still get explicit jobs.
                selected = sorted(selected, key=lambda r: (
                    not (self.state / 'corpus' / key(r) / 'index.json').is_file(),
                    r.lower() not in CORE, r.lower()))
                self.event('inventory_ready', included=len(all_repos), scheduled=len(selected),
                           excluded=sum(not r['included'] for r in inventory['repositories']))
                if repositories is None:
                    # Exercise the actual deliverable before spending a whole fanout.
                    pilot = 'com-lihaoyi/sourcecode' if 'com-lihaoyi/sourcecode' in selected else selected[0]
                    self.event('authoring_preflight_started', repository=pilot)
                    self.repository(pilot)
                    if self.exhausted:
                        return self.paused()
                    if not accepted_job(self.state, pilot):
                        raise RuntimeError('authoring preflight did not produce independently accepted skills; fanout refused')
                    atomic_json(self.state / 'authoring-preflight.json', dict(
                        repository=pilot, status='passed', at=now(),
                        job=load(self.state / 'jobs' / f'{key(pilot)}.json')))
                    selected = [repo for repo in selected if repo != pilot]
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                    futures = [executor.submit(self.repository, repo) for repo in selected]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
                if self.exhausted:
                    return self.paused()
                if self.stopping.is_set():
                    exit_code = 130
                elif repositories is None:
                    try:
                        decision = self.portfolio(inventory)
                    except ProviderExhausted:
                        return self.paused()
                    exit_code = 0 if decision['verdict'] == 'accept' else 2
                    if promote and decision['verdict'] == 'accept':
                        promote_portfolio(self.state, self)
                elif self.deepen:
                    exit_code = 0 if all(self.deepened(repo) for repo in selected) else 2
                else:
                    exit_code = 0 if all(accepted_job(self.state, repo) for repo in selected) else 2
                if self.consolidate and not self.stopping.is_set():
                    try:
                        result = promote_accepted(self.state, self)
                        self.event('consolidated', status=result['status'], added=result.get('added'),
                                   updated=result.get('updated'), total=result.get('promoted_total'),
                                   merged_needs_manual_fold=result.get('merged_needs_manual_fold'))
                        if result.get('merged_needs_manual_fold'):
                            exit_code = exit_code or 3
                    except (OSError, ValueError, RuntimeError) as exc:
                        # Research results stay intact in state; integration can be rerun by hand.
                        self.event('consolidation_failed', error=f'{type(exc).__name__}: {exc}')
                        exit_code = exit_code or 3
                self.event('run_finished', status=summary(self.state), exit_code=exit_code)
                return exit_code
            finally:
                timer.cancel()
                self.done.set()
                self.stopping.set()
                self.cancel_active()
                watcher.join(timeout=10)
                atomic_json(self.state / 'supervisor.json', dict(
                    run_record, finished_at=now(), provider_exhausted=self.exhausted))
                for sig, handler in previous.items():
                    signal.signal(sig, handler)


    def deepened(self, repository):
        path = self.deepen_paths(repository)['record']
        try:
            return (accepted_job(self.state, repository) and path.is_file()
                    and load(path).get('status') == 'accepted')
        except (OSError, ValueError):
            return False

    def paused(self):
        self.event('run_paused', reason='provider_exhausted', label=self.exhausted,
                   status=summary(self.state), exit_code=EXIT_PROVIDER_EXHAUSTED)
        return EXIT_PROVIDER_EXHAUSTED


def validate_portfolio(state):
    decision = load(state / 'portfolio.json')
    source = state / 'portfolio-input.json'
    if not isinstance(decision, dict) or decision.get('input_sha256') != sha(source):
        raise ValueError('portfolio input hash mismatch')
    if decision.get('schema_version') != 1:
        raise ValueError('invalid portfolio schema_version')
    for field in ('inventory_assessment', 'summary'):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            raise ValueError(f'portfolio requires substantive {field}')
    for field in ('gaps', 'excluded_skills', 'duplicate_groups'):
        if not isinstance(decision.get(field), list):
            raise ValueError(f'portfolio requires {field} array')
    if any(not isinstance(gap, str) or not gap.strip() for gap in decision['gaps']):
        raise ValueError('portfolio gaps must be nonempty strings')
    for row in decision['excluded_skills']:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or not isinstance(row.get('reason'), str) or not row['reason'].strip()
                or 'replaced_by' not in row
                or (row['replaced_by'] is not None and not isinstance(row['replaced_by'], str))):
            raise ValueError('invalid portfolio exclusion')
    data = load(source)
    if data.get('schema_version') != 1 or not isinstance(data.get('jobs'), list):
        raise ValueError('invalid portfolio input schema')
    inventory = data.get('inventory', {}).get('repositories')
    if not isinstance(inventory, list):
        raise ValueError('portfolio inventory is missing')
    included = set()
    all_repositories = set()
    for row in inventory:
        if (not isinstance(row, dict) or not isinstance(row.get('repo'), str)
                or not isinstance(row.get('included'), bool)):
            raise ValueError('invalid portfolio inventory row')
        key(row['repo'])
        repo = row['repo'].lower()
        if repo in all_repositories:
            raise ValueError('duplicate portfolio inventory repository')
        all_repositories.add(repo)
        if row['included']:
            included.add(repo)
    if not CORE <= included:
        raise ValueError('required core repositories absent from inventory')
    outcomes = set()
    for row in data['jobs']:
        if not isinstance(row, dict) or not isinstance(row.get('repository'), str):
            raise ValueError('invalid repository outcome')
        repository = row['repository']
        key(repository)
        if repository.lower() in outcomes or row.get('status') not in {'accepted', 'blocked'}:
            raise ValueError('duplicate or nonterminal repository outcome')
        outcomes.add(repository.lower())
        if row['status'] == 'blocked' and not row.get('reason'):
            raise ValueError('blocked repository outcome lacks a reason')
        if load(state / 'jobs' / f'{key(repository)}.json') != row:
            raise ValueError('repository outcome changed after portfolio review')
    if outcomes != included:
        raise ValueError('exactly one terminal outcome required per included repository')
    ids = decision.get('selected_skill_ids')
    if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('portfolio selected_skill_ids must be unique strings')
    if decision.get('verdict') not in {'accept', 'revise', 'blocked'}:
        raise ValueError('invalid portfolio verdict')
    available = {}
    for row in load(source)['jobs']:
        if row['status'] != 'accepted':
            continue
        repository = row['repository']
        if not accepted_job(state, repository):
            raise ValueError(f'stale accepted artifacts: {repository}')
        current = load(state / 'jobs' / f'{key(repository)}.json')
        if any(row.get(k) != current.get(k) for k in ('candidate_sha256', 'review_sha256')):
            raise ValueError('portfolio job hashes changed')
        report = load(state / 'candidates' / key(repository) / 'report.json')
        for item in report['skills']:
            if item['id'] in available:
                raise ValueError(f'duplicate skill across repos: {item["id"]}')
            available[item['id']] = (repository, item['kind'])
    if not set(ids) <= set(available):
        raise ValueError('portfolio contains non-accepted skills')
    if decision['verdict'] == 'accept':
        if len(ids) < 36:
            raise ValueError('fewer than 36 accepted distinct skills')
        if not CORE <= {available[i][0].lower() for i in ids}:
            raise ValueError('required core repository skills missing')
        if not {'development', 'review', 'refactoring', 'hardening'} <= {available[i][1] for i in ids}:
            raise ValueError('required skill categories missing')
        if decision.get('gaps'):
            raise ValueError('portfolio accepts while listing unresolved gaps')
    return decision


def promote_portfolio(state, runner):
    """Exclusive integrator; all gates share the supervisor's cancellation budget."""
    from scripts.common import frontmatter, tree_hash
    state = Path(state)
    runner.check_running()
    with exclusive_lock(integration_lock_path(ROOT)):
        decision = validate_portfolio(state)
        if decision['verdict'] != 'accept':
            raise ValueError('portfolio is not accepted')
        if live_workers(state):
            raise ValueError('cannot promote while workers are alive')
        # Parse and hash the SAME bytes; a later edit cannot bless an earlier parse.
        paths = ['catalog.json', 'docs/skill-review.json', 'docs/catalog.md', 'install.conf.yaml']
        snapshot = {p: (ROOT / p).read_bytes() for p in paths}
        expected = {p: hashlib.sha256(data).hexdigest() for p, data in snapshot.items()}
        catalog_path = ROOT / 'catalog.json'
        catalog = json.loads(snapshot['catalog.json'])
        existing = {item['id']: item for item in catalog['skills']}
        selected = set(decision['selected_skill_ids'])
        receipt = state / 'promotion.json'
        portfolio_hash = sha(state / 'portfolio.json')
        if receipt.exists():
            previous = load(receipt)
            if previous.get('status') == 'passed' and set(previous['skill_ids']) == selected:
                if previous.get('portfolio_sha256') != portfolio_hash:
                    raise ValueError('portfolio changed since promotion receipt')
                if set(previous.get('artifact_sha256', {})) != selected or not selected <= set(existing):
                    raise ValueError('promotion receipt lacks artifacts or selected catalog entries')
                for sid in selected:
                    dest = ROOT / 'collections/shared' / sid
                    link = ROOT / 'collections/hermes' / sid
                    item = existing[sid]
                    if (item.get('path') != f'collections/shared/{sid}' or not dest.is_dir()
                            or dest.is_symlink() or not link.is_symlink()
                            or os.readlink(link) != f'../shared/{sid}'
                            or tree_hash(dest) != previous['artifact_sha256'][sid]
                            or item.get('sha256') != previous['artifact_sha256'][sid]):
                        raise ValueError(f'promoted artifact missing or changed: {sid}')
                if previous.get('generated_sha256') != expected:
                    raise ValueError('generated files changed since verified promotion')
                runner.check_running()
                return previous
        if selected & set(existing):
            raise ValueError('refusing to overwrite existing catalog skills; reconcile interrupted promotion first')
        sources, provenance = {}, {}
        for row in load(state / 'portfolio-input.json')['jobs']:
            if row['status'] == 'accepted':
                for sid in row['skill_ids']:
                    if sid in selected:
                        sources[sid] = state / 'candidates' / key(row['repository']) / 'skills' / sid
                        provenance[sid] = dict(repository=row['repository'],
                                               review_sha256=row.get('review_sha256') or '')
        if set(sources) != selected:
            raise ValueError('selected skills lack source artifacts')
        shared_paths = [ROOT / 'collections/shared' / sid for sid in selected]
        hermes_paths = [ROOT / 'collections/hermes' / sid for sid in selected]
        if any(p.exists() or p.is_symlink() for p in shared_paths + hermes_paths):
            raise ValueError('promotion destination already exists')
        backup = state / 'integration-backup' / str(time.time_ns())
        backup.mkdir(parents=True)
        for p, data in snapshot.items():
            dest = backup / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        progress = dict(status='started', skill_ids=sorted(selected), backup=str(backup),
                        portfolio_sha256=portfolio_hash, installed_globally=False)
        atomic_json(receipt, progress)
        artifacts = {}
        def unchanged():
            runner.check_running()
            if any(sha(ROOT / p) != expected[p] for p in paths):
                raise RuntimeError('shared files changed during integration; refusing stale overwrite')
        try:
            unchanged()
            for sid, source in sorted(sources.items()):
                runner.check_running()
                tree_sha(source)
                dest = ROOT / 'collections/shared' / sid
                shutil.copytree(source, dest)
                shutil.copy2(ROOT / 'collections/shared/scala-library-contracts/LICENSE', dest / 'LICENSE')
                metadata = frontmatter(dest / 'SKILL.md')
                artifacts[sid] = tree_hash(dest)
                catalog['skills'].append(dict(id=sid, name=metadata['name'], collection='shared',
                    source='local', license='MIT', sha256=artifacts[sid],
                    local_globs=[f'~/.agents/skills/{sid}', f'~/.hermes/skills/{sid}'],
                    path=f'collections/shared/{sid}', distribution='vendored',
                    license_file=f'collections/shared/{sid}/LICENSE'))
                (ROOT / 'collections/hermes' / sid).symlink_to(f'../shared/{sid}')
            unchanged()
            catalog['skills'].sort(key=lambda row: row['id'])
            atomic_json(catalog_path, catalog)
            expected['catalog.json'] = sha(catalog_path)
            # Owned rows only: refresh_review.py diffs against git HEAD and would stamp this
            # pipeline's note on unrelated uncommitted skills.
            from .consolidate import review_row, update_review
            entries = {row['id']: row for row in catalog['skills']}
            update_review(ROOT, {sid: review_row(ROOT, sid, entries[sid], provenance[sid]) for sid in selected})
            expected['docs/skill-review.json'] = sha(ROOT / 'docs/skill-review.json')
            commands = [([sys.executable, 'scripts/catalog.py'], {'docs/catalog.md'}),
                        (['./install.sh', 'render'], {'install.conf.yaml'}),
                        (['make', 'test'], set()), (['make', 'check'], set())]
            for index, (command, allowed_changes) in enumerate(commands):
                unchanged()
                result = runner.command(f'integration-{index}', command, 1200)
                runner.check_running()
                if result:
                    raise RuntimeError(f'integration gate failed ({result}): {command}')
                after = {p: sha(ROOT / p) for p in paths}
                if any(after[p] != expected[p] for p in paths if p not in allowed_changes):
                    raise RuntimeError('unexpected shared-file change during integration gate')
                expected = after
            unchanged()
            result = dict(progress, status='passed', completed_at=now(), artifact_sha256=artifacts,
                          generated_sha256=expected)
            atomic_json(receipt, result)
            return result
        except Exception as exc:
            atomic_json(receipt, dict(progress,
                status='interrupted' if isinstance(exc, InterruptedError) else 'failed',
                error=f'{type(exc).__name__}: {exc}', artifact_sha256=artifacts))
            raise


def promote_accepted(state, runner):
    from .consolidate import promote_accepted as integrate
    return integrate(state, runner)


def summary(state):
    state = Path(state)
    jobs = [load(p) for p in sorted((state / 'jobs').glob('*.json'))]
    result = dict(state=str(state), jobs=len(jobs), counts=dict(Counter(j['status'] for j in jobs)),
                  accepted_skill_count=sum(len(j.get('skill_ids', [])) for j in jobs if j['status'] == 'accepted'),
                  live_workers=[{'pid': p['pid'], 'label': p['label']} for p in live_workers(state)])
    for name in ('supervisor', 'portfolio', 'promotion'):
        path = state / f'{name}.json'
        if path.exists():
            data = load(path)
            if name == 'supervisor':
                result['supervisor_alive'] = same_process(data) and not data.get('finished_at')
                result['model'] = data.get('model')
                result['provider'] = data.get('provider')
                if data.get('provider_exhausted'):
                    result['provider_exhausted'] = data['provider_exhausted']
            else:
                result[name] = data.get('verdict', data.get('status'))
    return result


def _terminate(record):
    """SIGTERM the recorded supervisor; pidfd closes the check-then-signal PID-reuse window."""
    pid = record['pid']
    if not (hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal')):
        os.kill(pid, signal.SIGTERM)
        return True
    try:
        fd = os.pidfd_open(pid)
    except ProcessLookupError:
        return False
    try:
        # Re-verify through the pinned pidfd: a reused PID no longer matches.
        if not same_process(record):
            return False
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return False
    finally:
        os.close(fd)


def stop(state):
    state = Path(state)
    path = state / 'supervisor.json'
    record = load(path) if path.exists() else None
    if record and same_process(record) and not record.get('finished_at') and _terminate(record):
        return {'status': 'cancellation_requested', 'pid': record['pid']}
    orphans = live_workers(state)
    for row in orphans:
        managed.stop(None, row)
    return {'status': 'orphan_cleanup_verified', 'units': [row['unit'] for row in orphans]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    sub = parser.add_subparsers(dest='action', required=True)
    run = sub.add_parser('run')
    run.add_argument('--workers', type=int, default=6)
    run.add_argument('--per-year', type=int, default=6)
    run.add_argument('--attempts', type=int, default=3)
    run.add_argument('--job-seconds', type=int, default=2700)
    run.add_argument('--hours', type=float, default=48)
    run.add_argument('--max-turns', type=int, default=100)
    run.add_argument('--model', default='gpt-6-astra-900k')
    run.add_argument('--provider', default='openai-codex')
    run.add_argument('--repo', action='append')
    run.add_argument('--promote', action='store_true')
    run.add_argument('--consolidate', action='store_true',
                     help='after the run, integrate every verified accepted skill into the catalog')
    run.add_argument('--require-sandbox', action='store_true',
                     help='refuse to run unless the user manager enforces agent sandbox properties')
    run.add_argument('--deepen', action='store_true',
                     help='re-research accepted --repo selections for more skills; failure restores prior acceptance')
    for action in ('status', 'stop', 'promote', 'consolidate'):
        sub.add_parser(action)
    args = parser.parse_args()
    try:
        if args.action == 'run':
            if not (1 <= args.workers <= 10 and 1 <= args.attempts <= 4 and
                    1 <= args.per_year <= 30 and 30 <= args.job_seconds <= 7200 and
                    0 < args.hours <= 168 and 5 <= args.max_turns <= 200):
                parser.error('invalid budgets; see documented safe ranges')
            result = Supervisor(args.state, workers=args.workers, per_year=args.per_year,
                       attempts=args.attempts, job_seconds=args.job_seconds, hours=args.hours,
                       model=args.model, provider=args.provider, max_turns=args.max_turns,
                       deepen=args.deepen, consolidate=args.consolidate,
                       require_sandbox=args.require_sandbox).run(
                           repositories=args.repo, promote=args.promote)
            raise SystemExit(result)
        elif args.action == 'status':
            print(json.dumps(summary(args.state), indent=2))
        elif args.action == 'stop':
            print(json.dumps(stop(args.state), indent=2))
        elif args.action == 'promote':
            raise SystemExit(Supervisor(args.state, hours=2).run(promotion_only=True))
        elif args.action == 'consolidate':
            from .consolidate import LocalRunner
            result = promote_accepted(args.state, LocalRunner(ROOT, args.state))
            print(json.dumps(result, indent=2))
            if result.get('merged_needs_manual_fold'):
                # Everything else was integrated; these acceptances wait for a hand fold.
                raise SystemExit(2)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
