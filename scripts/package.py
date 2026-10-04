#!/usr/bin/env python3
"""Build a release from tracked files with reproducible timestamps and SHA-256."""
import argparse
import gzip
import hashlib
import re
import subprocess
from pathlib import Path
from common import REPO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, default=REPO / 'dist')
    args = parser.parse_args()
    version = args.version.removeprefix('v')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', version):
        parser.error('version must be MAJOR.MINOR.PATCH, optionally with a prerelease suffix')
    if version != (REPO / 'VERSION').read_text().strip():
        parser.error('release version must match VERSION')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip():
        parser.error('commit all changes before building a release')
    args.output.mkdir(parents=True, exist_ok=True)
    name = f'dot-agents-{version}'
    tar = subprocess.check_output(['git', 'archive', '--format=tar', f'--prefix={name}/', 'HEAD'], cwd=REPO)
    asset = args.output / f'{name}.tar.gz'
    asset.write_bytes(gzip.compress(tar, compresslevel=9, mtime=0))
    checksum = hashlib.sha256(asset.read_bytes()).hexdigest()
    (args.output / 'SHA256SUMS').write_text(f'{checksum}  {asset.name}\n')
    print(asset)


if __name__ == '__main__':
    main()
