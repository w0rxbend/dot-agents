#!/usr/bin/env python3
"""Install, check, and uninstall symlinks without executing skill code."""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import REPO, dump_json, frontmatter, load_catalog

AGENTS = {
    'agents': '.agents/skills',
    'claude': '.claude/skills',
    'codex': '.codex/skills',
    'cursor': '.cursor/skills',
    'gemini': '.gemini/skills',
    'copilot': '.copilot/skills',
    'opencode': '.config/opencode/skills',
    'hermes': '.hermes/skills',
}
STATE_FILE = '.dot-agents-install.json'


def exists(path):
    return path.exists() or path.is_symlink()


def source_for(item, repo, home, include_local):
    if item['distribution'] == 'vendored':
        source = (repo / item['path']).resolve()
        if not source.is_relative_to(repo.resolve()):
            raise ValueError(f"source escapes repository: {item['id']}")
        if not (source / 'SKILL.md').is_file():
            raise ValueError(f"missing SKILL.md: {item['id']}")
        return source
    if include_local:
        for pattern in item['local_globs']:
            for match in sorted(glob.glob(str(home / pattern.removeprefix('~/'))), reverse=True):
                source = Path(match)
                if (source / 'SKILL.md').is_file() and frontmatter(source / 'SKILL.md')['name'] == item['name']:
                    return source.resolve()
    return None


def targets_for(args):
    if args.target:
        if args.agents:
            raise ValueError('--target and --agents cannot be combined')
        return [args.target.expanduser().absolute()]
    if args.agents == 'all':
        names = list(AGENTS)
    elif args.agents:
        names = args.agents.split(',')
    else:
        names = ['agents', 'claude']
        names += [name for name, rel in AGENTS.items() if name not in {'agents', 'claude', 'codex'}
                  and (args.home / Path(rel).parent).is_dir()]
    unknown = set(names) - AGENTS.keys()
    if unknown:
        raise ValueError('unknown agents: ' + ', '.join(sorted(unknown)))
    return list(dict.fromkeys(args.home / AGENTS[name] for name in names))


def read_state(target):
    path = target / STATE_FILE
    if not path.exists():
        return {'schema_version': 1, 'links': {}}
    state = json.loads(path.read_text())
    if state.get('schema_version') != 1 or not isinstance(state.get('links'), dict):
        raise ValueError(f'invalid installation state: {path}')
    for key in state['links']:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', key):
            raise ValueError(f'invalid managed link name: {key}')
    return state


def backup(path):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = path.with_name(path.name + '.dot-agents-backup-' + stamp)
    path.rename(dest)
    print(f'backup: {path} -> {dest}')


def same_link(path, source):
    return path.is_symlink() and path.resolve() == source.resolve()


def install(args, repo=REPO):
    catalog = load_catalog(repo)['skills']
    selected = set(args.skills.split(',')) if args.skills else None
    if selected and selected - {x['id'] for x in catalog}:
        raise ValueError('unknown skill IDs: ' + ', '.join(sorted(selected - {x['id'] for x in catalog})))
    desired = {}
    unavailable = 0
    for item in catalog:
        if selected and item['id'] not in selected:
            continue
        source = source_for(item, repo, args.home, args.include_local)
        if source is None:
            unavailable += 1
            if selected:
                raise ValueError(f"{item['id']} is provider-managed; install its provider and use --include-local")
        else:
            desired[item['id']] = source
    if not desired:
        raise ValueError('no skills selected')
    targets = targets_for(args)
    plans = []
    problems = []
    # Preflight every destination before making any changes.
    for target in targets:
        root_conflict = target.is_symlink() or (target.exists() and not target.is_dir())
        if root_conflict and not args.replace:
            problems.append(f'{target} is a symlink or file; --replace backs it up before installing')
            continue
        if root_conflict and args.check:
            problems.append(f'{target} is not a managed directory')
            continue
        if args.check and not target.is_dir():
            problems.append(f'missing target: {target}')
            continue
        state = read_state(target) if target.is_dir() and not root_conflict else {'schema_version': 1, 'links': {}}
        changes = []
        for skill_id, source in desired.items():
            link = target / skill_id
            if not root_conflict and same_link(link, source):
                continue
            if args.check:
                problems.append(f'missing or changed link: {link}')
            elif not root_conflict and exists(link):
                old = state['links'].get(skill_id)
                if old and link.is_symlink() and os.readlink(link) == old:
                    changes.append((skill_id, source, 'relink'))
                elif args.replace:
                    changes.append((skill_id, source, 'backup'))
                else:
                    problems.append(f'conflict: {link}; --replace keeps a backup')
            else:
                changes.append((skill_id, source, 'link'))
        if args.check:
            for skill_id, old in state['links'].items():
                if not exists(target / skill_id) or not (target / skill_id).is_symlink() or os.readlink(target / skill_id) != old:
                    problems.append(f'managed link changed: {target / skill_id}')
        plans.append((target, root_conflict, state, changes))
    if problems:
        raise ValueError('\n'.join(problems))
    if args.check:
        print(f'OK: {len(desired)} skills in {len(targets)} target(s); {unavailable} provider-managed unavailable')
        return
    for target, root_conflict, state, changes in plans:
        if args.dry_run:
            print(f'would install {len(desired)} skills into {target}; {len(changes)} change(s)' +
                  ('; back up existing target' if root_conflict else ''))
            continue
        if root_conflict:
            backup(target)
        target.mkdir(parents=True, exist_ok=True)
        for skill_id, source, action in changes:
            link = target / skill_id
            if action == 'backup':
                backup(link)
            elif action == 'relink':
                link.unlink()
            link.symlink_to(source, target_is_directory=True)
        for skill_id, source in desired.items():
            state['links'][skill_id] = str(source)
        state['repository'] = str(repo.resolve())
        # Atomic replace protects state from a interrupted write.
        temp = target / (STATE_FILE + '.tmp')
        dump_json(temp, state)
        temp.replace(target / STATE_FILE)
        print(f'installed: {len(desired)} skills into {target}; {len(changes)} change(s)')
    print(f'Provider-managed skills unavailable: {unavailable}. See docs/providers.md.')


def uninstall(args):
    problems = []
    for target in targets_for(args):
        if target.is_symlink() or not target.is_dir():
            print(f'skip: {target} is not a managed directory')
            continue
        state = read_state(target)
        removed = 0
        for skill_id, old in list(state['links'].items()):
            link = target / skill_id
            if link.is_symlink() and os.readlink(link) == old:
                removed += 1
                if not args.dry_run:
                    link.unlink()
                    del state['links'][skill_id]
            elif not exists(link):
                del state['links'][skill_id]
            else:
                problems.append(f'left changed entry untouched: {link}')
        if not args.dry_run:
            if state['links']:
                dump_json(target / STATE_FILE, state)
            else:
                (target / STATE_FILE).unlink(missing_ok=True)
        print(f"{'would remove' if args.dry_run else 'removed'}: {removed} links from {target}")
    if problems:
        raise ValueError('\n'.join(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('install', 'uninstall'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--home', type=Path, default=Path.home(), help='override machine home (useful for testing)')
        cmd.add_argument('--agents', help='comma-separated agents, or all; default: agents, claude, detected agents')
        cmd.add_argument('--target', type=Path, help='one custom skills directory')
        cmd.add_argument('--dry-run', action='store_true')
        if name == 'install':
            cmd.add_argument('--skills', help='comma-separated catalog IDs; default: all vendored skills')
            cmd.add_argument('--include-local', action='store_true', help='also link provider skills already present locally')
            cmd.add_argument('--replace', action='store_true', help='back up conflicts, including existing root symlinks')
            cmd.add_argument('--check', action='store_true', help='verify installation without writing')
    args = parser.parse_args()
    args.home = args.home.expanduser().resolve()
    try:
        if args.command == 'install':
            install(args)
        else:
            uninstall(args)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
