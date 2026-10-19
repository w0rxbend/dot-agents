#!/usr/bin/env python3
"""Run authorized skill-authoring tasks through the documented Hermes Python API.

`hermes chat --oneshot` prohibits skill creation in its system instructions.
This adapter uses a normal AIAgent library session; it never changes that policy,
unsets its marker, overrides prompts, enables YOLO, or edits Hermes configuration.
The enclosing supervisor still owns the process cgroup and its finite deadline.
"""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

# The supervisor pauses the fleet only on this exact line, never on free-form output
# (which can quote upstream text). Keep in sync with supervisor.EXHAUSTED_MARKER.
EXHAUSTED_MARKER = 'scala-research: provider-exhausted'
EXHAUSTED = re.compile(r'usage limit has been reached|quota exhausted|insufficient_quota|'
                       r'credit balance is too low|credential pool exhausted', re.I)


def provider_exhausted(error):
    """True for a provider quota/credit failure (an exception or a result error string)."""
    if isinstance(error, BaseException):
        if type(error).__name__ == 'ProviderCredentialsExhaustedError':
            return True
        error = str(error)
    return isinstance(error, str) and bool(EXHAUSTED.search(error))


def report_exhausted(kind):
    print(f'{EXHAUSTED_MARKER} error_type={kind}', flush=True)


def runtime_command(args):
    """Use the installation's PM-owned interpreter, not an ambient Python ABI."""
    raw = subprocess.check_output(['hermes', '--print-runtime-command'], text=True, timeout=30)
    command = json.loads(raw)
    if (not isinstance(command, list) or not command or not isinstance(command[0], str)
            or not Path(command[0]).is_absolute()):
        raise ValueError('unrecognized Hermes runtime command')
    return [command[0], '-I', str(Path(__file__).resolve()), '--inside-runtime',
            '--hermes-root', str(args.hermes_root), '--query-file', str(args.query_file),
            '--receipt', str(args.receipt), '--cwd', str(args.cwd),
            '--model', args.model, '--provider', args.provider,
            '--max-turns', str(args.max_turns), '--run-budget', str(args.run_budget)]


def require_authoring_mode(single_query, tool_names):
    if single_query:
        raise RuntimeError('one-shot sessions cannot author skills; use a normal library session')
    if 'skill_manage' not in tool_names:
        raise RuntimeError('skill_manage capability unavailable; authoring is not enabled')


def completed(result):
    return (isinstance(result, dict) and result.get('completed') is True
            and not any(result.get(k) for k in ('failed', 'partial', 'interrupted')))


def write_receipt(path, **fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(dict(schema_version=1, at=datetime.now(timezone.utc).isoformat(), **fields), stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def run_library(args):
    root = args.hermes_root.resolve(strict=True)
    if not (root / 'run_agent.py').is_file() or not (root / 'hermes_bootstrap.py').is_file():
        raise ValueError('Hermes source installation is missing required library modules')
    sys.path.insert(0, str(root))
    import hermes_bootstrap  # noqa: F401 - activates the installation's dependency lease
    from agent.oneshot_footprint import is_single_query_session
    if is_single_query_session():
        # Never alter this approval/lifecycle marker to defeat the one-shot guard.
        require_authoring_mode(True, set())
    from agent.ssl_verify import install_truststore
    install_truststore()
    from run_agent import AIAgent
    agent = AIAgent(model=args.model, provider=args.provider,
                    enabled_toolsets=['terminal', 'file', 'skills'],
                    max_iterations=args.max_turns, run_budget_seconds=args.run_budget,
                    reasoning_config={'effort': 'high'}, quiet_mode=True,
                    skip_memory=True, skip_background_review=True, cwd=str(args.cwd))
    try:
        require_authoring_mode(is_single_query_session(), agent.valid_tool_names)
        write_receipt(args.receipt, status='running', model=agent.model, provider=agent.provider,
                      session_id=agent.session_id, mode='AIAgent-library', authoring_capability=True)
        result = agent.run_conversation(args.query_file.read_text(encoding='utf-8'))
        ok = completed(result)
        exhausted = not ok and isinstance(result, dict) and provider_exhausted(result.get('error'))
        write_receipt(args.receipt, status='completed' if ok else 'failed',
                      model=agent.model, provider=agent.provider, session_id=agent.session_id,
                      mode='AIAgent-library', authoring_capability=True,
                      completed=ok, api_calls=result.get('api_calls'),
                      message_count=len(result.get('messages', [])), provider_exhausted=exhausted)
        if exhausted:
            report_exhausted('result')
        print(json.dumps({'status': 'completed' if ok else 'failed',
                          'session_id': agent.session_id, 'receipt': str(args.receipt)}), flush=True)
        return 0 if ok else 2
    finally:
        agent.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query-file', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--cwd', type=Path, default=Path.cwd())
    parser.add_argument('--hermes-root', type=Path, default=Path.home() / '.hermes/hermes-agent')
    parser.add_argument('--model', default='gpt-6-astra-900k')
    parser.add_argument('--provider', default='openai-codex')
    parser.add_argument('--max-turns', type=int, default=100)
    parser.add_argument('--run-budget', type=int, default=2700)
    parser.add_argument('--inside-runtime', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.max_turns <= 200 or not 30 <= args.run_budget <= 7200:
        parser.error('invalid finite authoring budget')
    args.query_file = args.query_file.resolve(strict=True)
    args.receipt = args.receipt.resolve()
    args.cwd = args.cwd.resolve(strict=True)
    try:
        if args.inside_runtime:
            return run_library(args)
        write_receipt(args.receipt, status='starting', model=args.model, provider=args.provider,
                      mode='AIAgent-library')
        return subprocess.run(runtime_command(args), cwd=args.cwd, check=False,
                              timeout=args.run_budget + 90).returncode
    except Exception as exc:
        # Do not persist provider response bodies, credentials, prompt or argv values.
        exhausted = provider_exhausted(exc)
        write_receipt(args.receipt, status='failed', error_type=type(exc).__name__,
                      model=args.model, provider=args.provider, mode='AIAgent-library',
                      provider_exhausted=exhausted)
        print(f'library worker failed: {type(exc).__name__}', file=sys.stderr)
        if exhausted:
            report_exhausted(type(exc).__name__)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
