#!/usr/bin/env python3
"""Install, check, and remove global agent skills with dotbot-go symlinks.

This repository is the source of truth for the vendored skills in collections/.
`install.sh install` plans link rows from catalog.json for the selected agents,
renders exactly those rows into a temporary dotbot-go configuration, and applies
it. Real files, directories and foreign symlinks at a link destination are moved
to a timestamped backup before dotbot's force linking replaces them.

The committed `install.conf.yaml` is a home-independent reference rendering for
every supported agent (optional agents gated by `if: test -d`); `render` writes
it and `render --check` verifies it. Installing never rewrites it.

Subcommands: install (default), render, check, uninstall.
"""
import argparse
import glob
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent

# Agent key -> skills directory relative to the home directory.
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
# Always installed by default. Every other agent is installed only when its
# configuration directory exists (or when requested with --agents).
REQUIRED = ('agents', 'claude')
# Pi reads ~/.agents/skills and ~/.pi/agent/skills and silently drops skills
# whose frontmatter name collides. Only the collections that historically
# lived in those roots are installed there; other collections stay available
# in the agents that tolerate same-named skills (Claude, Hermes, Codex, ...).
PI_SCOPED_COLLECTIONS = {'shared', 'agent-squad', 'zio-skills', 'scala-zio-skills'}
PI_SCOPED_AGENTS = {'agents', 'pi'}
# Collections that belong to specific agents (see README "Install scope").
# Hermes and Codex system skills only make sense in their own agent. Claude
# already loads the knowledge-work plugins natively, so linking them into
# ~/.claude/skills would load each skill twice.
CLAUDE_PLUGIN_COLLECTIONS = ('claude-design', 'claude-engineering', 'claude-productivity')
COLLECTION_AGENTS = {
    'hermes': frozenset({'hermes'}),
    'codex-system': frozenset({'codex'}),
    **{name: frozenset(AGENTS) - {'claude'} for name in CLAUDE_PLUGIN_COLLECTIONS},
}
# The committed reference config covers every agent; it never depends on the
# machine that rendered it.
RENDER_HOME = Path('/nonexistent-home')
HEADER = '# Generated from catalog.json by `./install.sh render`; do not edit by hand.\n'

# Pinned dotbot-go release used when no binary is available. v0.4.2 joins every
# link source onto the base directory, so all sources are rendered relative.
DOTBOT_VERSION = '0.4.2'
DOTBOT_SHA256 = {
    'darwin-amd64': '89c22f14929dcb11cc8d1c81086d5d0d9336f89438c6326d00aea7420ea8043c',
    'darwin-arm64': 'f7b970f1b325175b0a16c278050502e45b22541c343f6d4082638197d99dddc4',
    'linux-amd64': 'a7229b8d098454ffeb2858ddcf1b63602dfc7be06e08b57c39d839c08f9dbd01',
    'linux-arm64': '21e94e915de43f2cbe086973437ec6a5f81e46ddbc5280707165c0ebb6090b45',
}


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
        return list(dict.fromkeys(names))
    names = list(REQUIRED)
    names += [name for name, rel in AGENTS.items()
              if name not in names and (home / rel).parent.is_dir()]
    return names


def agent_allows(agent, collection):
    """Whether a collection's skills are linked into an agent's skills root."""
    if agent in PI_SCOPED_AGENTS and collection not in PI_SCOPED_COLLECTIONS:
        return False
    return agent in COLLECTION_AGENTS.get(collection, AGENTS)


def local_source(item, home):
    """Resolve a provider-managed skill that is already present locally.

    Matches inside an agent skills root are link destinations, never sources:
    using one would back up the source and link to a path that no longer exists.
    """
    roots = {home / rel for rel in AGENTS.values()}
    for pattern in item.get('local_globs', []):
        if not pattern.startswith('~/'):
            continue
        for match in sorted(glob.glob(str(home / pattern[2:])), reverse=True):
            source = Path(match)
            if source.parent in roots:
                continue
            if (source / 'SKILL.md').is_file():
                return source.resolve()
    return None


def plan(skills, agent_names, home, include_local=False):
    """Return link rows: (agent, destination Path, source, local_only)."""
    rows = []
    for agent in agent_names:
        root = home / AGENTS[agent]
        for item in skills:
            if not agent_allows(agent, item.get('collection', 'shared')):
                continue
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


def render_config(rows, gated=True):
    """Render the dotbot-go configuration for the given link rows.

    gated=True (the committed reference) installs optional agents only when
    their configuration directory exists. gated=False (what install applies)
    links every row, because the rows were already selected for this home.
    Sources are always relative to the repository (dotbot's base directory).
    """
    agents = sorted({agent for agent, _, _, _ in rows})
    cleaned = [agent for agent in agents if not gated or agent in REQUIRED]
    lines = [HEADER.rstrip(), '', '- defaults:', '    link:',
             '      create: true', '      relink: true', '      force: true', '']
    if cleaned:
        lines += ['- clean:'] + [f'    - "~/{AGENTS[agent]}"' for agent in cleaned] + ['']
    lines.append('- link:')
    for agent, dest, source, _ in sorted(rows, key=lambda r: (str(r[1]), r[0])):
        target = f'~/{AGENTS[agent]}/{dest.name}'
        if os.path.isabs(source):
            source = os.path.relpath(source, REPO)
        if gated and agent not in REQUIRED:
            parent = Path(AGENTS[agent]).parent.as_posix()
            lines += [f'    {target}:', f'      path: {source}',
                      f'      if: test -d "$HOME/{parent}"']
        else:
            lines.append(f'    {target}: {source}')
    return '\n'.join(lines) + '\n'


def reference_config():
    """The committed install.conf.yaml: every agent, vendored skills, no host state."""
    return render_config(plan(load_catalog(), list(AGENTS), RENDER_HOME), gated=True)


def find_dotbot():
    candidates = [os.environ.get('DOTBOT'), shutil.which('dotbot'),
                  shutil.which('dotbot-go'), str(Path.home() / '.local/bin/dotbot')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return Path(candidate)
    return None


def download_dotbot(target):
    """Download the pinned dotbot-go release and verify its SHA-256."""
    machine = {'x86_64': 'amd64', 'amd64': 'amd64',
               'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine().lower())
    key = f'{platform.system().lower()}-{machine}'
    expected = DOTBOT_SHA256.get(key)
    if expected is None:
        print(f'no pinned dotbot-go build for {key}', file=sys.stderr)
        return None
    url = (f'https://github.com/worxbend/dotbot-go/releases/download/'
           f'v{DOTBOT_VERSION}/dotbot-{key}.tar.gz')
    print(f'dotbot-go not found; downloading {url}', file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
    except OSError as error:
        print(f'download failed: {error}', file=sys.stderr)
        return None
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SystemExit(f'dotbot-go checksum mismatch for {url}: {actual} != {expected}')
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        member = archive.extractfile('dotbot')
        if member is None:
            raise SystemExit('dotbot-go archive does not contain a dotbot binary')
        binary = member.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(target.name + '.download')
    staged.write_bytes(binary)
    staged.chmod(0o755)
    staged.replace(target)
    return target


def ensure_dotbot():
    """Locate or install the dotbot-go binary; return its path."""
    found = find_dotbot()
    if found:
        return found
    target = Path.home() / '.local/bin/dotbot'
    if download_dotbot(target):
        return target
    source = Path.home() / 'Projects/Github/dotbot-go'
    if source.is_dir() and shutil.which('go'):
        print(f'falling back to building dotbot-go from {source}', file=sys.stderr)
        target.parent.mkdir(parents=True, exist_ok=True)
        built = subprocess.run(['go', 'build', '-buildvcs=false', '-o', str(target),
                                './cmd/dotbot-go'], cwd=source)
        if built.returncode == 0:
            return target
    raise SystemExit('could not obtain a dotbot-go binary; set DOTBOT=/path/to/dotbot')


def run_dotbot(dotbot, rows, home, dry_run=False):
    """Apply a configuration rendered from exactly these rows (never the committed file)."""
    with tempfile.TemporaryDirectory(prefix='dot-agents-') as temp:
        config = Path(temp) / 'install.conf.yaml'
        config.write_text(render_config(rows, gated=False), encoding='utf-8')
        command = [str(dotbot), '--base-directory', str(REPO), '--config-file', str(config)]
        if dry_run:
            command.append('--dry-run')
        env = dict(os.environ, HOME=str(home))
        result = subprocess.run(command, env=env)
    if result.returncode != 0:
        raise SystemExit(f'dotbot failed with exit code {result.returncode}')


def link_target(path):
    return Path(os.path.normpath(os.path.join(path.parent, os.readlink(path))))


def points_into_repo(path):
    """A symlink whose (possibly dangling) target lies inside this repository."""
    if link_target(path).is_relative_to(REPO):
        return True
    return path.exists() and path.resolve().is_relative_to(REPO)


def is_ours(dest, source):
    """Whether dest is a link this installer created for source."""
    if not dest.is_symlink():
        return False
    if points_into_repo(dest):
        return True
    source_path = Path(source) if os.path.isabs(source) else REPO / source
    return dest.exists() and dest.resolve() == source_path.resolve()


def backup_conflicts(rows, home, dry_run=False):
    """Move anything at a link destination that is not our link into a backup.

    dotbot's force/relink would otherwise delete real files and directories and
    silently replace foreign symlinks.
    """
    moved = []
    moved_roots = set()
    for agent in sorted({agent for agent, _, _, _ in rows}):
        root = home / AGENTS[agent]
        # A root symlink would make dotbot create links inside its target, which
        # may be a foreign directory or this repository itself. Move the link
        # aside; its target keeps all content, so children need no backup.
        if root.is_symlink():
            moved.append(root)
            moved_roots.add(root)
    for _, dest, source, _ in rows:
        if dest.parent in moved_roots or is_ours(dest, source):
            continue
        if dest.is_symlink():
            moved.append(dest)
        elif dest.exists():
            if dest.resolve().is_relative_to(REPO):
                raise SystemExit(f'refusing to back up {dest}: it resolves into {REPO}')
            moved.append(dest)
    if not moved:
        return []
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = Path(os.environ.get('DOTAGENTS_BACKUP',
                                      home / '.local/share/dot-agents/backup')) / stamp
    print(f'backing up {len(moved)} conflicting path(s) under {backup_root}')
    if dry_run:
        return moved
    backup_root.mkdir(parents=True, exist_ok=True)
    for path in sorted(set(moved), key=lambda item: len(item.parts), reverse=True):
        target = backup_root / str(path).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
    return moved


def stale_links(rows, agent_names, home):
    """Links into this repository that the current plan no longer wants."""
    planned = {dest for _, dest, _, _ in rows}
    stale = []
    for agent in agent_names:
        root = home / AGENTS[agent]
        if root.is_symlink() or not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_symlink() and child not in planned and points_into_repo(child):
                stale.append(child)
    return stale


def prune_stale(rows, agent_names, home, dry_run=False):
    stale = stale_links(rows, agent_names, home)
    if stale:
        print(f"{'would remove' if dry_run else 'removing'} {len(stale)} link(s) "
              'outside the current install scope')
    if not dry_run:
        for link in stale:
            link.unlink()
    return stale


def command_render(args):
    if args.agents or args.include_local:
        raise SystemExit('render always uses every agent and no local skills; '
                         'pass --agents/--include-local to install or check instead')
    config = reference_config()
    committed = REPO / 'install.conf.yaml'
    if args.check:
        if not committed.exists() or committed.read_text(encoding='utf-8') != config:
            raise SystemExit('install.conf.yaml is stale; run ./install.sh render')
        print('install.conf.yaml is up to date')
    else:
        committed.write_text(config, encoding='utf-8')
        print(f'wrote install.conf.yaml ({config.count(chr(10) + "    ~/")} links)')


def command_install(args):
    agent_names = select_agents(args.agents, args.home)
    rows = plan(load_catalog(), agent_names, args.home, include_local=args.include_local)
    if not rows:
        raise SystemExit('nothing to install')
    dotbot = ensure_dotbot()
    backup_conflicts(rows, args.home, dry_run=args.dry_run)
    prune_stale(rows, agent_names, args.home, dry_run=args.dry_run)
    run_dotbot(dotbot, rows, args.home, dry_run=args.dry_run)
    print(f'{"would install" if args.dry_run else "installed"} {len(rows)} links via {dotbot}')


def command_check(args):
    agent_names = select_agents(args.agents, args.home)
    rows = plan(load_catalog(), agent_names, args.home, include_local=args.include_local)
    problems = []
    for _, dest, source, _ in rows:
        source_path = Path(source) if os.path.isabs(source) else (REPO / source)
        if not dest.is_symlink():
            problems.append(f'missing link: {dest}')
        elif not dest.exists():
            problems.append(f'broken link: {dest} -> {os.readlink(dest)}')
        elif dest.resolve() != source_path.resolve():
            problems.append(f'changed link: {dest} -> {os.readlink(dest)}')
    problems += [f'out-of-scope link: {link}' for link in stale_links(rows, agent_names, args.home)]
    if problems:
        raise SystemExit('\n'.join(problems[:10]) +
                         (f'\n... and {len(problems) - 10} more' if len(problems) > 10 else ''))
    run_dotbot(ensure_dotbot(), rows, args.home, dry_run=True)
    print(f'OK: {len(rows)} links across {len(set(a for a, _, _, _ in rows))} agent(s)')


def command_uninstall(args):
    agent_names = select_agents(args.agents, args.home)
    rows = plan(load_catalog(), agent_names, args.home, include_local=args.include_local)
    # Every link into this repository in a selected root, including links from
    # an older install scope, plus local-only links to their planned source.
    targets = {link for link in stale_links([], agent_names, args.home)}
    targets |= {dest for _, dest, source, local in rows if local and is_ours(dest, source)}
    for link in sorted(targets):
        if not args.dry_run:
            link.unlink()
    print(f"{'would remove' if args.dry_run else 'removed'} {len(targets)} links")


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
