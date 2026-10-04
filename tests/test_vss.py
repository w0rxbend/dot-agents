import hashlib
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('install_vss', ROOT / 'scripts/install_vss.py')
vss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vss)


def archive(extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as bundle:
        bundle.writestr(vss.SKILL_PATH + 'SKILL.md', '---\nname: direct-style-scala\ndescription: fixture\n---\n\nUpstream body\n')
        bundle.writestr(vss.SKILL_PATH + 'chapter.md', 'chapter\n')
        bundle.writestr('elsewhere/secret.txt', 'outside requested skill\n')
        if extra:
            bundle.writestr(vss.SKILL_PATH + extra, 'unexpected\n')
    return stream.getvalue()


class VssInstallTests(unittest.TestCase):
    def test_direct_source_install_overlay_and_idempotency(self):
        raw = archive()
        with tempfile.TemporaryDirectory() as temp, patch.object(vss, 'SHA256', hashlib.sha256(raw).hexdigest()):
            target = Path(temp) / 'skills'
            dest = vss.install(target, raw)
            doc = (dest / 'SKILL.md').read_text()
            self.assertTrue(doc.startswith('---\nname: direct-style-scala\n'))
            self.assertIn('Prefer **Mill**', doc)
            self.assertTrue(doc.index('Local build preference') < doc.index('Upstream body'))
            self.assertFalse((target / 'elsewhere').exists())
            before = (dest / 'SKILL.md').stat().st_mtime_ns
            vss.install(target, raw)
            self.assertEqual(before, (dest / 'SKILL.md').stat().st_mtime_ns)

    def test_modified_install_is_preserved_or_backed_up(self):
        raw = archive()
        with tempfile.TemporaryDirectory() as temp, patch.object(vss, 'SHA256', hashlib.sha256(raw).hexdigest()):
            target = Path(temp)
            dest = vss.install(target, raw)
            (dest / 'chapter.md').write_text('user customization')
            with self.assertRaises(ValueError):
                vss.install(target, raw)
            self.assertEqual('user customization', (dest / 'chapter.md').read_text())
            vss.install(target, raw, replace=True)
            backup, = target.glob('direct-style-scala.dot-agents-backup-*')
            self.assertEqual('user customization', (backup / 'chapter.md').read_text())
            self.assertEqual('chapter\n', (dest / 'chapter.md').read_text())

    def test_archive_integrity_and_path_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                vss.unpack(archive(), root)
            raw = archive('../escape.txt')
            with patch.object(vss, 'SHA256', hashlib.sha256(raw).hexdigest()):
                with self.assertRaisesRegex(ValueError, 'unsafe archive'):
                    vss.unpack(raw, root)
            self.assertFalse((root.parent / 'escape.txt').exists())
