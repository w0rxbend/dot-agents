#!/usr/bin/env python3
"""Install, check, and remove global agent skills with dotbot-go symlinks.

This repository is the source of truth for the vendored skills in collections/.
`install.conf.yaml` is generated from catalog.json and applied with dotbot-go,
which symlinks every skill into each supported agent's global skills directory.
Real files or directories at a link destination are moved to a timestamped
backup before dotbot's force linking replaces them.

Subcommands: install (default), render, check, uninstall.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent

# Agent key -> skills directory relative to the home directory. Optional
# agents are only linked when their configuration directory already exists,
# so a fresh machine only gets the agents that are actually installed.
AGENTS = {
    'agents': '.agents/skills',
    'claude': '.claude/skills',
    'codex': '.codex/skills',
    'pi': '.pi/agent/skills',
    'hermes': '.hermes/skills',
    'cursor': '.cursor/skills',
    'gemini': '.gemini/skills',
    'copilot': '.copilot/skills',
    'opencode': '.config/opencode/skills',
}
OPTIONAL = {'pi', 'hermes', 'cursor', 'gemini', 'copilot', 'opencode'}
HEADER = '# Generated from catalog.json by `./install.sh render`; do not edit by hand.\n'


def load_catalog():
    return json.loads((REPO / 'catalog.json').read_text(encoding='utf-8'))['skills']


def select_agents(requested, home):
    if requested == 'all':
        return list(AGENTS)
    if requested:
        names = requested.split(',')
        unknown = set(names) - set(AGENTS)
        if unknown:
            raise SystemExit('unknown agents: ' + ', '.join(sorted(unknown)))
        return names
    names = ['agents', 'claude']
    names += [name for name, rel in AGENTS.items()
              if name not in names and (home / rel).parent.is_dir()]
    return list(dict.fromkeys(names))


def local_source(item, home):
    """Resolve a provider-managed skill that is already present locally."""
    for pattern in item.get('local_globs', []):
        if not pattern.startswith('~/'):
            continue
        for match in sorted(glob.glob(str(home / pattern[2:])), reverse=True):
            source = Path(match)
            if (source / 'SKILL.md').is_file():
                return source.resolve()
    return None


def plan(skills, agent_names, home, include_local=False):
    """Return link rows: (agent, destination Path, source, local_only)."""
    rows = []
    for agent in agent_names:
        root = home / AGENTS[agent]
        for item in skills:
            if item['distribution'] != 'vendored':
                if not include_local:
                    continue
                source = local_source(item, home)
                if source is None:
                    continue
                rows.append((agent, root / item['id'], str(source), True))
                continue
            rows.append((agent, root / item['id'], item['path'], False))
    return rows


def render_config(rows):
    """Render the dotbot-go configuration for the given link rows."""
    always = sorted({agent for agent, _, _, _ in rows if agent not in OPTIONAL})
    lines = [HEADER.rstrip(), '', '- defaults:', '    link:',
             '      create: true', '      relink: true', '      force: true', '']
    if always:
        lines += ['- clean:'] + [f'    - "~/{AGENTS[agent]}"' for agent in always] + ['']
    lines.append('- link:')
    for agent, dest, source, _ in sorted(rows, key=lambda r: (str(r[1]), r[0])):
        target = f'~/{AGENTS[agent]}/{dest.name}'
        if agent in OPTIONAL:
            parent = Path(AGENTS[agent]).parent.as_posix()
            lines += [f'    {target}:', f'      path: {source}',
                      f'      if: test -d "$HOME/{parent}"']
        else:
            lines.append(f'    {target}: {source}')
    return '\n'.join(lines) + '\n'


def ensure_dotbot():
    """Locate or install the dotbot-go binary; return its path."""
    candidates = [os.environ.get('DOTBOT'), shutil.which('dotbot'),
                  shutil.which('dotbot-go'), str(Path.home() / '.local/bin/dotbot')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return Path(candidate)
    url = ('https://github.com/worxbend/dotbot-go/releases/latest/'
           'download/install.sh')
    print(f'dotbot-go not found; installing from {url}', file=sys.stderr)
    downloader = subprocess.run(['curl', '-fsSL', url], capture_output=True, text=True)
    if downloader.returncode == 0:
        installed = subprocess.run(['sh'], input=downloader.stdout,
                                   capture_output=True, text=True)
        if installed.returncode == 0 and (Path.home() / '.local/bin/dotbot').is_file():
            return Path.home() / '.local/bin/dotbot'
        print(installed.stderr, file=sys.stderr)
    source = Path.home() / 'Projects/Github/dotbot-go'
    if source.is_dir() and shutil.which('go'):
        print(f'falling back to building dotbot-go from {source}', file=sys.stderr)
        target = Path.home() / '.local/bin/dotbot'
        target.parent.mkdir(parents=True, exist_ok=True)
        built = subprocess.run(['go', 'build', '-buildvcs=false', '-o', str(target),
                                './cmd/dotbot-go'], cwd=source)
        if built.returncode == 0:
            return target
    raise SystemExit('could not obtain a dotbot-go binary; set DOTBOT=/path/to/dotbot')


def run_dotbot(dotbot, configs, home, dry_run=False):
    command = [str(dotbot), '--base-directory', str(REPO)]
    for config in configs:
        command += ['--config-file', str(config)]
    if dry_run:
        command.append('--dry-run')
    env = dict(os.environ, HOME=str(home))
    result = subprocess.run(command, env=env)
    if result.returncode != 0:
        raise SystemExit(f'dotbot failed with exit code {result.returncode}')


def backup_conflicts(rows, home, dry_run=False):
    """Move real files/dirs at link destinations aside; dotbot force would delete them."""
    moved = []
    for agent in sorted({agent for agent, _, _, _ in rows}):
        root = home / AGENTS[agent]
        # A root symlink pointing outside the repo would make dotbot create links
        # inside the foreign directory; move it aside so a real directory is created.
        if root.is_symlink() and not root.resolve().is_relative_to(REPO):
            moved.append(root)
        for _, dest, _, _ in rows:
            if dest.parent == root and not dest.is_symlink() and dest.exists():
                moved.append(dest)
    if not moved:
        return []
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = Path(os.environ.get('DOTAGENTS_BACKUP',
                                      Path.home() / '.local/share/dot-agents/backup')) / stamp
    print(f'backing up {len(moved)} conflicting path(s) under {backup_root}')
    if dry_run:
        return moved
    backup_root.mkdir(parents=True, exist_ok=True)
    for path in moved:
        target = backup_root / str(path).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
    return moved


def refresh_committed_config():
    rows = plan(load_catalog(), select_agents(None, Path.home()), Path.home())
    (REPO / 'install.conf.yaml').write_text(render_config(rows), encoding='utf-8')
    return rows


def command_render(args):
    rows = plan(load_catalog(), select_agents(args.agents, args.home), args.home,
                include_local=args.include_local)
    config = render_config(rows)
    if args.check:
        committed = REPO / 'install.conf.yaml'
        if not committed.exists() or committed.read_text(encoding='utf-8') != config:
            raise SystemExit('install.conf.yaml is stale; run ./install.sh render')
        print('install.conf.yaml is up to date')
    else:
        (REPO / 'install.conf.yaml').write_text(config, encoding='utf-8')
        print(f'wrote install.conf.yaml ({len(rows)} links)')


def command_install(args):
    skills = load_catalog()
    agent_names = select_agents(args.agents, args.home)
    rows = plan(skills, agent_names, args.home, include_local=args.include_local)
    if not rows:
        raise SystemExit('nothing to install')
    dotbot = ensure_dotbot()
    refresh_committed_config()
    configs = [REPO / 'install.conf.yaml']
    if args.include_local:
        local_rows = [row for row in rows if row[3]]
        local_config = REPO / 'install.local.conf.yaml'
        local_config.write_text(render_config(local_rows), encoding='utf-8')
        if local_rows:
            configs.append(local_config)
    backup_conflicts(rows, args.home, dry_run=args.dry_run)
    run_dotbot(dotbot, configs, args.home, dry_run=args.dry_run)
    print(f'{"would install" if args.dry_run else "installed"} {len(rows)} links via {dotbot}')


def command_check(args):
    rows = plan(load_catalog(), select_agents(args.agents, args.home), args.home,
                include_local=args.include_local)
    problems = []
    for _, dest, source, _ in rows:
        source_path = Path(source) if os.path.isabs(source) else (REPO / source)
        if not dest.is_symlink():
            problems.append(f'missing link: {dest}')
        elif not dest.exists():
            problems.append(f'broken link: {dest} -> {os.readlink(dest)}')
        elif dest.resolve() != source_path.resolve():
            problems.append(f'changed link: {dest} -> {os.readlink(dest)}')
    if problems:
        raise SystemExit('\n'.join(problems[:10]) +
                         (f'\n... and {len(problems) - 10} more' if len(problems) > 10 else ''))
    run_dotbot(ensure_dotbot(), [REPO / 'install.conf.yaml'], args.home, dry_run=True)
    print(f'OK: {len(rows)} links across {len(set(a for a, _, _, _ in rows))} agent(s)')


def command_uninstall(args):
    rows = plan(load_catalog(), select_agents(args.agents, args.home), args.home,
                include_local=args.include_local)
    removed = 0
    for _, dest, _, _ in rows:
        if not dest.is_symlink():
            continue
        ours = (dest.exists() and dest.resolve().is_relative_to(REPO)) or \
               (not dest.exists() and REPO.as_posix() in os.readlink(dest))
        if ours:
            if not args.dry_run:
                dest.unlink()
            removed += 1
    print(f"{'would remove' if args.dry_run else 'removed'} {removed} links")


def main_args(args):
    args.home = args.home.resolve()
    commands = {'install': command_install, 'render': command_render,
                'check': command_check, 'uninstall': command_uninstall}
    commands[args.command](args)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', nargs='?', default='install',
                        choices=('install', 'render', 'check', 'uninstall'))
    parser.add_argument('--home', type=Path, default=Path.home(),
                        help='override the home directory (testing and CI)')
    parser.add_argument('--agents', help='comma-separated agents, or all; default: agents, claude, detected')
    parser.add_argument('--include-local', action='store_true',
                        help='also link provider-managed skills already present locally')
    parser.add_argument('--check', action='store_true',
                        help='with render: verify install.conf.yaml freshness')
    parser.add_argument('--dry-run', action='store_true')
    main_args(parser.parse_args())


if __name__ == '__main__':
    main()
