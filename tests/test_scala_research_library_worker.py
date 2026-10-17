"""Library-authoring adapter tests; fake agents never supply research evidence."""
import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.scala_research import library_worker as worker


class LibraryWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prompt = self.root / 'prompt.txt'
        self.prompt.write_text('Synthetic authorized skill-authoring fixture.')
        self.args = argparse.Namespace(query_file=self.prompt, receipt=self.root / 'receipt.json',
            model='gpt-6-astra-900k', provider='openai-codex', max_turns=20, run_budget=300,
            cwd=self.root, hermes_root=self.root / 'runtime', inside_runtime=False)

    def test_launch_uses_installed_interpreter_without_changing_restrictions(self):
        with patch.object(worker.subprocess, 'check_output', return_value='["/runtime/python", "-I", "-c", "bootstrap"]'):
            command = worker.runtime_command(self.args)
        self.assertEqual(['/runtime/python', '-I'], command[:2])
        self.assertIn('--inside-runtime', command)
        self.assertNotIn('--oneshot', command)
        self.assertNotIn('--yolo', command)
        self.assertNotIn('--ignore-rules', command)

    def test_invalid_launcher_response_fails_closed(self):
        for result in ('{}', '[]', '[false]', '["relative/python"]'):
            with self.subTest(result=result), patch.object(worker.subprocess, 'check_output', return_value=result):
                with self.assertRaises(ValueError):
                    worker.runtime_command(self.args)

    def test_one_shot_context_is_rejected_not_unset(self):
        with self.assertRaisesRegex(RuntimeError, 'one-shot'):
            worker.require_authoring_mode(True, {'skill_manage', 'write_file'})

    def test_missing_skill_authoring_capability_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'skill_manage'):
            worker.require_authoring_mode(False, {'write_file', 'read_file'})
        worker.require_authoring_mode(False, {'skill_manage', 'write_file'})

    def test_completion_requires_positive_result_not_just_text(self):
        self.assertTrue(worker.completed({'completed': True, 'final_response': 'Fixture result'}))
        for result in ({}, {'completed': False}, {'completed': True, 'failed': True},
                       {'completed': True, 'partial': True}, {'completed': True, 'interrupted': True}):
            with self.subTest(result=result):
                self.assertFalse(worker.completed(result))

    def test_receipt_does_not_store_prompt_response_or_credentials(self):
        worker.write_receipt(self.args.receipt, status='completed', model=self.args.model,
                             provider=self.args.provider, session_id='synthetic-session')
        data = json.loads(self.args.receipt.read_text())
        self.assertEqual('completed', data['status'])
        self.assertNotIn('prompt', data)
        self.assertNotIn('final_response', data)
        self.assertNotIn('api_key', data)


if __name__ == '__main__':
    unittest.main()
