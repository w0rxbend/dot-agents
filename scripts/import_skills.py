#!/usr/bin/env python3
"""Snapshot recognized global skill roots. Hosted skills remain metadata only."""
import argparse
import os
import re
import shutil
from pathlib import Path

from common import REPO, IGNORED, dump_json, frontmatter, tree_hash
import json


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def source_policy(source, licenses, declared_license=None):
    """Only explicitly reviewed external sources may skip vendoring."""
    if source == 'local':
        return declared_license or 'LicenseRef-Local', True
    if source not in licenses:
        raise ValueError(f'add and verify the upstream license before importing: {source}')
    policy = licenses[source]
    if policy.get('distribution') == 'external':
        return policy['spdx'], False
    if not policy.get('file'):
        raise ValueError(f'missing upstream license file: {source}')
    return policy['spdx'], True


def copy_tree(source, dest):
    def ignore(directory, names):
        skipped = [n for n in names if n in IGNORED or n in {
            '.gitignore', '.bundled_manifest', '.curator_state', '.codex-system-skills.marker',
            '.dot-agents-install.json'
        }]
        if source.name == 'zio-skills' and Path(directory) == source:
            skipped += [n for n in names if n == 'flowrite']
        return skipped
    shutil.copytree(source, dest, symlinks=True, ignore=ignore)


def make_links_portable(destination, copies, external_roots=()):
    """Keep installed aliases, but retarget them to the copied collection."""
    # Canonicalize the roots too: macOS /var and /private/var, or a symlinked
    # home directory, must compare consistently with resolved link targets.
    destination = destination.resolve()
    copies = {source.resolve(): copied.resolve() for source, copied in copies.items()}
    external_roots = {root.resolve() for root in external_roots}
    sources = sorted(copies, key=lambda path: len(path.parts), reverse=True)
    destinations = sorted(copies.items(), key=lambda item: len(item[1].parts), reverse=True)
    for link in destination.rglob('*'):
        if not link.is_symlink():
            continue
        target = link.resolve()
        if target.is_relative_to(destination) and target.exists():
            if os.path.isabs(os.readlink(link)):
                link.unlink()
                link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=target.is_dir())
            continue
        # A relative link outside its source collection resolves differently after copying.
        # Resolve the original link before mapping its target into the snapshot.
        for source, copied_root in destinations:
            if link.is_relative_to(copied_root):
                target = (source / link.relative_to(copied_root)).resolve()
                break
        if any(target.is_relative_to(root) for root in external_roots):
            # Provider aliases remain inventory entries, never public file links.
            link.unlink()
            continue
        for source in sources:
            if target.is_relative_to(source):
                copied_target = copies[source] / target.relative_to(source)
                if not copied_target.exists():
                    raise ValueError(f'symlink target was excluded from snapshot: {link}')
                link.unlink()
                link.symlink_to(os.path.relpath(copied_target, link.parent),
                                target_is_directory=copied_target.is_dir())
                break
        else:
            raise ValueError(f'symlink points outside imported skill sources: {link}')


def omit_external_copies(copies, external_roots):
    """A provider skill inside a larger vendored collection still stays external."""
    copies = {source.resolve(): destination.resolve() for source, destination in copies.items()}
    external_roots = {root.resolve() for root in external_roots}
    for source, destination in copies.items():
        for external in external_roots:
            if external != source and external.is_relative_to(source):
                excluded = destination / external.relative_to(source)
                if excluded.is_symlink() or excluded.is_file():
                    excluded.unlink()
                elif excluded.is_dir():
                    shutil.rmtree(excluded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--replace', action='store_true', help='replace existing repository snapshot')
    args = parser.parse_args()
    home = args.home.resolve()
    destination = REPO / 'collections'
    if destination.exists():
        if not args.replace:
            parser.error('collections already exists; use --replace after reviewing local edits')
        shutil.rmtree(destination)
    destination.mkdir()
    lock_path = home / '.agents/.skill-lock.json'
    lock = json.loads(lock_path.read_text())['skills'] if lock_path.exists() else {}
    licenses = json.loads((REPO / 'licenses/upstream/index.json').read_text())
    overrides_path = REPO / 'sources/global-overrides.json'
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    installed = []
    seen = {}
    copied = set()
    copies = {}
    external_roots = set()
    for override in overrides.values():
        _, vendored = source_policy(override['source'], licenses)
        if not vendored:
            for pattern in override.get('local_globs', []):
                if pattern.startswith('~/'):
                    candidate = (home / pattern[2:]).resolve()
                    if candidate.is_dir():
                        external_roots.add(candidate)
    ids = set()

    def add(doc, collection, local_glob, source, license_id, dest_root=None, src_root=None):
        info = frontmatter(doc)
        # The reviewed policy applies across agent aliases and nested collections too.
        override = overrides.get(info['name'], {})
        if override:
            source = override['source']
            license_id, vendored = source_policy(source, licenses, info.get('license'))
            if not vendored:
                dest_root = None
        if dest_root is None:
            external_roots.add(doc.parent.resolve())
        fingerprint = tree_hash(doc.parent)
        key = (info['name'], fingerprint)
        if key in seen:
            seen[key]['local_globs'].append(local_glob)
            return seen[key]
        base = slug(doc.parent.name)
        skill_id = base if collection == 'shared' else f'{collection}--{base}'
        if skill_id in ids:
            skill_id += '--' + fingerprint[:8]
        ids.add(skill_id)
        item = dict(id=skill_id, name=info['name'], collection=collection,
                    source=source, license=license_id, sha256=fingerprint,
                    local_globs=[local_glob])
        if dest_root is not None:
            if dest_root not in copied:
                copy_tree(src_root, dest_root)
                copied.add(dest_root)
                copies[src_root.resolve()] = dest_root
            path = dest_root / doc.parent.relative_to(src_root)
            item['path'] = path.relative_to(REPO).as_posix()
            item['distribution'] = 'vendored'
            item['sha256'] = tree_hash(path)
            if source in licenses:
                item['license_file'] = licenses[source]['file']
            else:
                local_licenses = [p for p in path.iterdir() if p.name.lower().startswith('license')]
                if local_licenses:
                    item['license_file'] = local_licenses[0].relative_to(REPO).as_posix()
        else:
            item['distribution'] = 'external'
            item['reason'] = 'provider-managed or redistribution permission not established'
        installed.append(item)
        seen[key] = item
        return item

    shared = home / '.agents/skills'
    if shared.exists():
        for child in sorted(shared.iterdir()):
            if child.name in IGNORED or not child.is_dir():
                continue
            if (child / 'SKILL.md').exists():
                info = frontmatter(child / 'SKILL.md')
                meta = lock.get(info['name'], lock.get(child.name, {}))
                if not meta:
                    meta = next((x for x in lock.values() if Path(x['skillPath']).parent.name == child.name), {})
                meta = {**meta, **overrides.get(info['name'], {})}
                source = meta.get('source', 'local')
                license_id, vendored = source_policy(source, licenses, info.get('license'))
                dest_root = destination / 'shared' / child.name if vendored else None
                item = add(child / 'SKILL.md', 'shared', f'~/.agents/skills/{child.name}', source, license_id,
                           dest_root, child)
                if meta.get('upstream_ref'):
                    item['upstream_ref'] = meta['upstream_ref']
                if not vendored:
                    item['local_globs'] = list(dict.fromkeys(meta.get('local_globs', []) + item['local_globs']))
                for doc in sorted(child.rglob('SKILL.md')):
                    if doc == child / 'SKILL.md' or any(x in doc.relative_to(child).parts for x in IGNORED):
                        continue
                    add(doc, child.name, '~/.agents/skills/' + doc.parent.relative_to(shared).as_posix(),
                        source, license_id, dest_root, child)
            elif child.name in {'zio-skills', 'scala-zio-skills'}:
                source = 'zio/zio-skills' if child.name == 'zio-skills' else 'linux-root/scala-zio-skills'
                for doc in sorted(child.rglob('SKILL.md')):
                    # flowrite is a development library; .opencode repeats the canonical skill.
                    if any(x in doc.relative_to(child).parts for x in IGNORED | {'flowrite', '.opencode'}):
                        continue
                    add(doc, child.name, '~/.agents/skills/' + doc.parent.relative_to(shared).as_posix(),
                        source, licenses[source]['spdx'], destination / child.name, child)
            elif child.name == 'agent-squad':
                for doc in sorted(child.rglob('SKILL.md')):
                    source = 'sickn33/antigravity-awesome-skills'
                    add(doc, 'agent-squad', '~/.agents/skills/' + doc.parent.relative_to(shared).as_posix(),
                        source, licenses[source]['spdx'], destination / 'shared/agent-squad', child)
            elif child.name == 'synced':
                for doc in sorted(child.rglob('SKILL.md')):
                    add(doc, 'claude-hosted', '~/.agents/skills/synced/*/' + doc.parent.name,
                        'Anthropic hosted skills', 'LicenseRef-Provider')
            elif list(child.rglob('SKILL.md')):
                raise ValueError(f'unrecognized nested collection: {child}')

    system = home / '.codex/skills/.system'
    for doc in sorted(system.rglob('SKILL.md')):
        local_licenses = [p for p in doc.parent.iterdir() if p.name.lower().startswith('license')]
        kwargs = dict(dest_root=destination / 'codex-system' / doc.parent.name, src_root=doc.parent) if local_licenses else {}
        add(doc, 'codex-system', '~/.codex/skills/.system/' + doc.parent.name,
            'OpenAI Codex bundled skills', 'Apache-2.0' if local_licenses else 'LicenseRef-Provider', **kwargs)

    plugins = home / '.codex/plugins/cache'
    for doc in sorted(plugins.rglob('SKILL.md')):
        relative = doc.relative_to(plugins)
        market, package, version = relative.parts[:3]
        info = frontmatter(doc)
        collection = 'codex-' + ('render' if package.startswith('app-6a624') else slug(package))
        local = '~/.codex/plugins/cache/' + '/'.join([market, package, '*', *relative.parts[3:-1]])
        # Explicitly licensed Render skills can be redistributed. Other hosted plugins stay local.
        if package.startswith('app-6a624') and info.get('license') == 'MIT':
            add(doc, collection, local, 'render-oss/skills', 'MIT',
                destination / 'render' / doc.parent.name, doc.parent)
        else:
            add(doc, collection, local, 'OpenAI plugin: ' + package, 'LicenseRef-Provider')

    claude = home / '.claude/plugins/synced'
    for doc in sorted(claude.rglob('SKILL.md')):
        relative = doc.relative_to(claude)
        group = relative.parts[1]
        add(doc, 'claude-' + group, '~/.claude/plugins/synced/*/' + '/'.join(relative.parts[1:-1]),
            'anthropics/knowledge-work-plugins', 'Apache-2.0',
            destination / 'claude-plugins' / group / doc.parent.name, doc.parent)

    hermes = home / '.hermes/skills'
    hermes_docs = set(hermes.rglob('SKILL.md'))
    if hermes.is_dir():
        hermes_docs.update(child / 'SKILL.md' for child in hermes.iterdir()
                           if child.is_symlink() and (child / 'SKILL.md').is_file())
    for doc in sorted(hermes_docs):
        add(doc, 'hermes', '~/.hermes/skills/' + doc.parent.relative_to(hermes).as_posix(),
            'NousResearch/hermes-agent', 'MIT', destination / 'hermes', hermes)

    desktop = home / '.config/Claude/local-agent-mode-sessions/skills-plugin'
    for doc in sorted(desktop.rglob('SKILL.md')):
        add(doc, 'claude-hosted', '~/.config/Claude/local-agent-mode-sessions/skills-plugin/*/*/skills/' + doc.parent.name,
            'Anthropic hosted skills', 'LicenseRef-Provider')

    omit_external_copies(copies, external_roots)
    make_links_portable(destination, copies, external_roots)
    for item in installed:
        if item['distribution'] == 'vendored':
            item['sha256'] = tree_hash(REPO / item['path'])
    installed.sort(key=lambda item: item['id'])
    dump_json(REPO / 'catalog.json', dict(schema_version=1, skills=installed, excluded=[
        'project-local skills', 'marketplace catalogs and temporary staging directories',
        'deleted .trash skills', 'dependency package examples', 'optional Hermes skills not installed',
        'flowrite development source skills and duplicate .opencode mirrors'
    ]))
    print(f'Inventoried {len(installed)} unique skills: ' +
          f"{sum(x['distribution'] == 'vendored' for x in installed)} vendored, " +
          f"{sum(x['distribution'] == 'external' for x in installed)} provider-managed")


if __name__ == '__main__':
    main()
