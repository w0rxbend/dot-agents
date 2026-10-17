"""Own Linux research jobs with per-job systemd user *transient* services.

No process-group fallback. ``alive`` and ``live_records`` raise on unverifiable
ownership, including same-boot legacy records. A successful ``stop`` proves the
unit/cgroup and launcher are gone; ambiguous startup or an unavailable manager
raises instead. Callers must treat these errors as blockers, not empty results.

A tiny launcher records its PID before execing systemd-run. A service-side exec
gate records the invocation/cgroup before executing the real command. Both use
the same record lock as cancellation: cancellation is durable, and a delayed
launch can never execute research after cancellation. No daemon is installed.
The returned Popen is the systemd-run wrapper; wait() preserves command status.
"""
import contextlib
import fcntl
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from subprocess import Popen
from typing import IO

_BACKEND = 'systemd-user-v1'
_LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z')
_UNIT = re.compile(r'scala-history-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\.service\Z')
_CGROUP_ROOT = Path('/sys/fs/cgroup')
_RPC_SECONDS = 3.0
_STOP_SECONDS = 12.0
_START_SECONDS = 10.0
_ENV_NAMES = ('PATH', 'HOME', 'TMPDIR', 'HERMES_HOME',
              'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
              'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')
_PROPERTIES = ('Id', 'LoadState', 'ActiveState', 'SubState', 'ControlGroup',
               'InvocationID', 'Description', 'Transient', 'Job')


def _boot_id() -> str:
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def _identity(pid: int | None) -> dict | None:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] in {'Z', 'X'}:
            return None
        return {'pid': pid, 'start_ticks': fields[19]}
    except (FileNotFoundError, ProcessLookupError):
        return None
    except (OSError, IndexError) as exc:
        raise RuntimeError('cannot verify wrapper process identity') from exc


def _same_wrapper(record: dict) -> bool:
    identity = _identity(record.get('pid'))
    return identity is not None and identity == {k: record.get(k) for k in identity}


def _atomic(path: Path, record: dict) -> None:
    """Atomic publication plus file/directory fsync; no credentials in records."""
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(record, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


def _read(path: Path) -> dict:
    try:
        if path.is_symlink():
            raise ValueError('symlink record')
        record = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(record, dict):
            raise ValueError('non-object record')
        return record
    except (OSError, ValueError) as exc:
        raise RuntimeError(f'cannot verify process record: {path.name}') from exc


@contextlib.contextmanager
def _lock(path: Path, deadline: float):
    fd = os.open(path.with_suffix('.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('process record lock deadline exceeded')
                time.sleep(.02)
        yield
    finally:
        os.close(fd)


def _stale_boot(record: dict) -> bool:
    if not isinstance(record, dict):
        raise RuntimeError('unrecognized process record')
    boot = record.get('boot_id')
    try:
        if str(uuid.UUID(boot)) != boot:
            raise ValueError('noncanonical boot ID')
    except (ValueError, TypeError, AttributeError) as exc:
        raise RuntimeError('process record lacks a verifiable boot ID') from exc
    return boot != _boot_id()


def _validate(record: dict) -> Path:
    if (record.get('backend') != _BACKEND or record.get('schema_version') != 1
            or not _UNIT.fullmatch(str(record.get('unit', '')))
            or not _LABEL.fullmatch(str(record.get('label', '')))):
        raise RuntimeError('unknown/legacy process ownership; cannot prove descendants are gone')
    if (any(type(record.get(key)) is not bool for key in ('cancelled', 'launch_settled', 'stopped'))
            or record.get('phase') not in {'prepared', 'launching', 'executing'}
            or not isinstance(record.get('record_path'), str)):
        raise RuntimeError('invalid process record lifecycle fields')
    path = Path(record.get('record_path', ''))
    if (not path.is_absolute() or path.parent.name != 'processes'
            or path.name != record['label'] + '.json'):
        raise RuntimeError('invalid process record path')
    return path


def _refresh(record: dict) -> dict:
    path = _validate(record)
    current = _read(path)
    _validate(current)
    if any(current.get(k) != record.get(k) for k in ('unit', 'boot_id', 'record_path')):
        raise RuntimeError('process record replaced by a different lifetime')
    return current


def _control(arguments: list[str], *, timeout: float = _RPC_SECONDS) -> dict:
    executable = shutil.which('systemctl')
    if not executable:
        raise RuntimeError('systemctl unavailable; systemd user manager is required')
    try:
        result = subprocess.run([executable, '--user', '--no-pager', *arguments],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=max(.01, timeout), check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError('systemd user manager unavailable or timed out') from exc
    values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    # Missing units are not a missing manager. Never interpret empty/error output
    # as absence. Only the explicit property from a responding manager suffices.
    if result.returncode and values.get('LoadState') != 'not-found':
        raise RuntimeError(f'systemd user manager command failed (exit {result.returncode})')
    return values


def require_available() -> None:
    """Require a reachable user manager, unified cgroups and pidfd support."""
    if not (sys.platform == 'linux' and hasattr(os, 'pidfd_open')
            and hasattr(signal, 'pidfd_send_signal') and shutil.which('systemd-run')):
        raise RuntimeError('Linux systemd-run and pidfd support are required')
    if not (_CGROUP_ROOT / 'cgroup.controllers').is_file():
        raise RuntimeError('unified cgroup v2 is required')
    info = _control(['show', '--property=Version', '--property=ControlGroup'])
    if not info.get('Version') or not info.get('ControlGroup'):
        raise RuntimeError('cannot verify systemd user manager')


def _show(record: dict, *, timeout: float = _RPC_SECONDS) -> dict:
    info = _control(['show', record['unit'], *['--property=' + key for key in _PROPERTIES]],
                    timeout=timeout)
    if info.get('LoadState') == 'not-found':
        return info
    if (info.get('LoadState') != 'loaded' or info.get('Id') != record['unit']
            or info.get('Transient') != 'yes'
            or info.get('Description') != 'Scala research ownership ' + record['unit']):
        raise RuntimeError('cannot verify owned transient unit identity')
    invocation = record.get('invocation_id')
    if invocation and info.get('InvocationID') and invocation != info['InvocationID']:
        raise RuntimeError('unit invocation identity changed; refusing reused lifetime')
    return info


def _populated(cgroup: str | None, unit: str) -> bool:
    if not cgroup:
        return False
    parts = cgroup.split('/')
    if (not cgroup.startswith('/') or any(p in {'.', '..'} for p in parts)
            or not cgroup.endswith('/' + unit)):
        raise RuntimeError('invalid owned cgroup path')
    try:
        data = (_CGROUP_ROOT / cgroup.lstrip('/') / 'cgroup.events').read_text()
    except FileNotFoundError:
        if not (_CGROUP_ROOT / 'cgroup.controllers').is_file():
            raise RuntimeError('cgroup filesystem unavailable')
        return False
    except OSError as exc:
        raise RuntimeError('cannot inspect owned cgroup') from exc
    values = dict(line.split() for line in data.splitlines())
    if values.get('populated') not in {'0', '1'}:
        raise RuntimeError('cannot verify cgroup population')
    return values['populated'] == '1'


def _unit_live(record: dict, info: dict) -> bool:
    # cgroup.events counts the whole subtree, including setsid descendants.
    populated = _populated(info.get('ControlGroup') or record.get('cgroup'), record['unit'])
    if info.get('LoadState') == 'not-found':
        return populated
    state = info.get('ActiveState')
    if state not in {'active', 'activating', 'deactivating', 'inactive', 'failed', 'reloading'}:
        raise RuntimeError('unknown transient unit state')
    return populated or state not in {'inactive', 'failed'} or info.get('Job', '') not in {'', '0'}


def alive(record: dict) -> bool:
    """Return liveness; raise if absence cannot be proved (fail closed)."""
    if _stale_boot(record):
        return False
    current = _refresh(record)
    info = _show(current)
    if _unit_live(current, info) or _same_wrapper(current):
        return True
    if current.get('launch_settled') or current.get('stopped'):
        return False
    raise RuntimeError('unresolved launch; refusing resume without verified cleanup')


def live_records(state: Path) -> list[dict]:
    """Never silently skip corrupt or legacy same-boot ownership records."""
    directory = Path(state).resolve() / 'processes'
    if not directory.exists():
        return []
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError('invalid process records directory')
    result = []
    for path in sorted(directory.iterdir()):
        if path.suffix == '.json':
            record = _read(path)
            if alive(record):
                result.append(_refresh(record))
    return result


def _kill_wrapper(record: dict) -> None:
    pid = record.get('pid')
    if not pid:
        return
    try:
        fd = os.pidfd_open(pid)
    except ProcessLookupError:
        return
    except OSError as exc:
        raise RuntimeError('cannot acquire wrapper pidfd') from exc
    try:
        if _same_wrapper(record):
            try:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
            except ProcessLookupError:
                pass
    finally:
        os.close(fd)


def stop(process: Popen | None, record: dict) -> None:
    """Bounded cancellation; all owned processes gone or RuntimeError.

    A crash in the pre-registration launch window may require a second stop
    after the delayed unit becomes visible. The cancellation tombstone prevents
    its real command from starting. Never remove records to work around errors.
    """
    if _stale_boot(record):
        return
    deadline = time.monotonic() + _STOP_SECONDS
    path = _validate(record)
    with _lock(path, deadline):
        current = _refresh(record)
        if process is not None and current.get('pid') not in {None, process.pid}:
            raise RuntimeError('wrapper does not match process record')
        if process is not None and current.get('pid') is None:
            # Recover a parent-side publication failure while the launch gate
            # is still waiting on this lock. Never infer ownership from a PID
            # supplied without the original Popen object.
            current.update(_identity(process.pid) or {'pid': process.pid})
        never_submitted = current.get('phase') == 'prepared' and bool(current.get('pid'))
        current['cancelled'] = True
        _atomic(path, current)
        # Kill the exact launcher FIRST, so it cannot submit a start after stop.
        # pidfd guards the check/signal race against PID reuse.
        _kill_wrapper(current)
        observed = bool(current.get('launch_settled') or current.get('stopped') or never_submitted)
        stop_sent = False
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            info = _show(current, timeout=min(_RPC_SECONDS, remaining))
            if info.get('LoadState') == 'loaded':
                observed = True
                if not stop_sent:
                    try:
                        _control(['stop', '--no-block', '--job-mode=replace-irreversibly', current['unit']],
                                 timeout=min(_RPC_SECONDS, max(.01, deadline - time.monotonic())))
                    except RuntimeError:
                        # --collect may unload between show and stop. Only a
                        # fresh, successful absence query can excuse that race.
                        check = _show(current, timeout=min(_RPC_SECONDS, max(.01, deadline - time.monotonic())))
                        if check.get('LoadState') != 'not-found':
                            raise
                    stop_sent = True
                    continue
            if not _unit_live(current, info) and not _same_wrapper(current) and observed:
                if process is not None:
                    try:
                        process.wait(timeout=max(.01, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired as exc:
                        raise RuntimeError('wrapper did not exit after cancellation') from exc
                current['stopped'] = True
                _atomic(path, current)
                record.update(current)
                return
            time.sleep(min(.05, max(0, deadline - time.monotonic())))
    raise RuntimeError('owned service cleanup unverified before deadline; resume is blocked')


def start(command: list[str], *, label: str, state: Path, cwd: Path,
          seconds: float, stdout: IO) -> tuple[Popen, dict]:
    """Publish ownership before spawning; return systemd-run Popen and record.

    The caller must serialize global supervisor ownership and call stop in its
    finally path, including when wait() times out. RuntimeMaxSec independently
    bounds the service even if the supervisor and wrapper disappear.
    """
    if not isinstance(label, str) or not _LABEL.fullmatch(label):
        raise ValueError('invalid process label')
    if (not isinstance(command, list) or not command
            or any(not isinstance(arg, str) or '\0' in arg for arg in command)
            or not command[0]):
        raise ValueError('command must be a nonempty argv list')
    if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('seconds must be finite and positive')
    if seconds >= (2 ** 63) / 1_000_000:
        raise ValueError('seconds exceeds the finite systemd runtime range')
    runtime_us = max(1, math.ceil(seconds * 1_000_000))
    directory = Path(cwd).resolve(strict=True)
    if not directory.is_dir():
        raise ValueError('cwd must be a directory')
    executable = command[0]
    if '/' in executable:
        executable = str((directory / executable).resolve(strict=True))
    else:
        # execvp interprets relative PATH entries against the child's cwd.
        search_path = os.pathsep.join(str(directory / entry) for entry in os.get_exec_path())
        executable = shutil.which(executable, path=search_path)
    if not executable or not os.access(executable, os.X_OK) or not Path(executable).is_file():
        raise ValueError('command executable unavailable')
    executable = str(Path(executable).resolve(strict=True))
    require_available()
    records = Path(state).resolve() / 'processes'
    records.mkdir(parents=True, exist_ok=True)
    if records.is_symlink():
        raise ValueError('process records directory must not be a symlink')
    path = records / (label + '.json')
    unit = f'scala-history-{uuid.uuid4()}.service'
    record = dict(schema_version=1, backend=_BACKEND, unit=unit, label=label,
                  boot_id=_boot_id(), record_path=str(path), pid=None, start_ticks=None,
                  invocation_id=None, cgroup=None, phase='prepared', cancelled=False,
                  launch_settled=False, stopped=False, executable=executable, cwd=str(directory))
    helper = str(Path(__file__).resolve())
    runner = shutil.which('systemd-run')
    if runner is None:
        raise RuntimeError('systemd-run disappeared after preflight')
    argv = [str(Path(runner).resolve()), '--user', '--quiet',
            '--wait', '--pipe', '--collect', '--service-type=exec',
            '--expand-environment=no', '--unit=' + unit,
            '--description=Scala research ownership ' + unit,
            '--working-directory=' + str(directory),
            '--property=KillMode=control-group', '--property=SendSIGKILL=yes',
            '--property=Restart=no', '--property=TimeoutStopSec=1s',
            '--property=TimeoutStartSec=10s', f'--property=RuntimeMaxSec={runtime_us}us',
            *['--setenv=' + name for name in _ENV_NAMES if name in os.environ],
            '--', sys.executable, helper, '_execute', str(path), unit, executable, *command[1:]]
    process = None
    try:
        with _lock(path, time.monotonic() + _START_SECONDS):
            if path.exists() and alive(_read(path)):
                raise RuntimeError('live process already owns this label')
            _atomic(path, record)
            try:
                process = Popen([sys.executable, helper, '_launch', str(path), unit, *argv],
                                cwd=directory, stdin=subprocess.DEVNULL, stdout=stdout,
                                stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
            except OSError:
                # Popen failed before creating an executable child: unlike a
                # supervisor crash, we can positively close this reservation.
                record.update(cancelled=True, stopped=True)
                _atomic(path, record)
                raise
            record.update(_identity(process.pid) or {'pid': process.pid})
            _atomic(path, record)
        # The service gate proves the single request reached the manager.
        # A wrapper PID alone is not evidence of cgroup ownership.
        deadline = time.monotonic() + _START_SECONDS
        while time.monotonic() < deadline:
            current = _refresh(record)
            if current.get('cancelled'):
                raise InterruptedError('process cancelled during startup')
            if current.get('launch_settled'):
                return process, current
            if process.poll() is not None:
                break
            time.sleep(.02)
        raise RuntimeError('transient service did not acknowledge startup')
    except BaseException:
        if process is not None:
            stop(process, record)
        raise


def _entry(mode: str, path: Path, unit: str, command: list[str]) -> int:
    """Private launch/exec gates; never use a shell or record argument values."""
    with _lock(path, time.monotonic() + _START_SECONDS):
        record = _read(path)
        _validate(record)
        if record['unit'] != unit or _stale_boot(record):
            return 125
        if mode == '_launch':
            identity = _identity(os.getpid())
            if identity is None:
                raise RuntimeError('cannot identify launch gate')
            record.update(identity)
            if record.get('cancelled'):
                _atomic(path, record)
                return 125
            record['phase'] = 'launching'
        elif mode == '_execute':
            cgroups = Path('/proc/self/cgroup').read_text().splitlines()
            record['cgroup'] = next(line[3:] for line in cgroups if line.startswith('0::'))
            invocation = os.environ.get('INVOCATION_ID', '')
            if not re.fullmatch(r'[0-9a-f]{32}', invocation):
                raise RuntimeError('service lacks systemd invocation identity')
            record['invocation_id'] = invocation
            record['launch_settled'] = True
            record['phase'] = 'executing'
            _atomic(path, record)
            if record.get('cancelled'):
                return 125
        else:
            return 125
        _atomic(path, record)
        # fd is CLOEXEC: release cancellation lock atomically with exec. The
        # cancelling process cannot pass the lock between our check and exec.
        os.execv(command[0], command)
    return 125


if __name__ == '__main__':
    try:
        raise SystemExit(_entry(sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4:]))
    except Exception:
        # Avoid traceback/argv/environment leakage into persistent job logs.
        print('research process ownership gate failed', file=sys.stderr)
        raise SystemExit(125)
