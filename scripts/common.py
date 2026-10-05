"""Shared catalog helpers; installation requires only the Python standard library."""
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IGNORED = {'.git', '.trash', 'node_modules', '__pycache__', '.venv', '.DS_Store',
           '.usage.json', '.usage.json.lock'}


def load_catalog(repo=REPO):
    return json.loads((repo / 'catalog.json').read_text(encoding='utf-8'))


def frontmatter(path):
    """Read the small scalar subset needed for indexing, preserving upstream YAML."""
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError(f'{path}: missing YAML frontmatter')
    head, separator, _ = text[4:].partition('\n---')
    if not separator:
        raise ValueError(f'{path}: unterminated YAML frontmatter')
    values = {}
    for key in ('name', 'description', 'license'):
        match = re.search(rf'^{key}:\s*(.*)$', head, re.MULTILINE)
        if match:
            values[key] = match.group(1).strip().strip('\"\'')
    if not values.get('name') or not values.get('description'):
        raise ValueError(f'{path}: missing name or description')
    return values


def tree_hash(root):
    digest = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if any(part in IGNORED for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            digest.update(p.relative_to(root).as_posix().encode())
            digest.update(b'\0')
            digest.update(p.read_bytes())
            digest.update(b'\0')
    return digest.hexdigest()


def dump_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
