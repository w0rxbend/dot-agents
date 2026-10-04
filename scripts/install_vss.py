#!/usr/bin/env python3
"""Install the official VSS skill directly from its pinned source with Mill preferences."""
import argparse
import hashlib
import io
import json
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
REF = '51eb40a55fa1c2a4c99f2980830d28bbea4a2ac7'
URL = f'https://codeload.github.com/VirtusLab/scala-skill/zip/{REF}'
SHA256 = '57a30ca9d0be179d6edc494b79c0c62ad3e22c2acacdc9c5e67f7c8ce4e80021'
SKILL_PATH = f'scala-skill-{REF}/direct-style-scala/skills/direct-style-scala/'
MARKER = '.dot-agents-vss.json'


def unpack(raw, destination):
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('upstream archive checksum mismatch; verify source before updating the pin')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            if not item.filename.startswith(SKILL_PATH) or item.is_dir():
                continue
            relative = PurePosixPath(item.filename[len(SKILL_PATH):])
            if relative.is_absolute() or '..' in relative.parts or not relative.parts:
                raise ValueError('unsafe archive path')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('unexpected archive symlink')
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    doc = destination / 'SKILL.md'
    if not doc.is_file():
        raise ValueError('official skill missing from pinned archive')
    head, body = doc.read_text().split('\n---\n', 1)
    overlay = (REPO / 'overlays/direct-style-scala/preferences.md').read_text()
    doc.write_text(head + '\n---\n\n' + overlay.strip() + '\n\n' + body.lstrip())
    (destination / MARKER).write_text(json.dumps(dict(source='VirtusLab/scala-skill', ref=REF,
        archive_sha256=SHA256, overlay_sha256=hashlib.sha256(overlay.encode()).hexdigest()), indent=2) + '\n')


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and p.name != MARKER}


def install(target, raw, replace=False):
    target.mkdir(parents=True, exist_ok=True)
    destination = target / 'direct-style-scala'
    # Stage on the target filesystem so the final directory rename is atomic.
    with tempfile.TemporaryDirectory(prefix='.vss-install-', dir=target) as temporary:
        staged = Path(temporary) / 'direct-style-scala'
        staged.mkdir()
        unpack(raw, staged)
        if destination.exists() or destination.is_symlink():
            if not destination.is_symlink() and destination.is_dir() and files(destination) == files(staged):
                shutil.copy2(staged / MARKER, destination / MARKER)
                print(f'Already installed: {destination}')
                return destination
            if not replace:
                raise ValueError(f'{destination} differs; use --replace to retain a backup and install')
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = destination.with_name(destination.name + '.dot-agents-backup-' + stamp)
            destination.rename(backup)
            print(f'Backup: {backup}')
        staged.rename(destination)
    print(f'Installed official VSS skill with Mill preference: {destination}')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--target', type=Path,
                        help='source skills root; defaults to HOME/.local/share/dot-agents/providers/skills')
    parser.add_argument('--replace', action='store_true', help='back up a conflicting skill first')
    args = parser.parse_args()
    try:
        with urllib.request.urlopen(URL, timeout=60) as response:
            raw = response.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError('unexpected archive size')
        install((args.target or args.home / '.local/share/dot-agents/providers/skills').expanduser().resolve(),
                raw, args.replace)
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
