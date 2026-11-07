"""Configuration, external prerequisites and real exec/health/signal contracts."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from llamasrv.constants.DLlama import DLlama
from llamasrv.constants.DQwen import DQwen
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import Llama
from llamasrv.interface.Network import Network
from support import ROOT, fixture_configuration, wait_for_health, write_configuration


class LlamaTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.path = self.base / 'llamasrv.json'
        self.values = fixture_configuration(self.base)
        write_configuration(self.path, self.values)

    def llama(self):
        write_configuration(self.path, self.values)
        return Llama(Configuration(self.path))

    def test_defaults_and_existing_network_only_configuration(self):
        self.path.unlink()
        configuration = Configuration(self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(Network(configuration).binding('llm'), ('0.0.0.0', 51001))
        self.assertEqual(configuration.llama['binary'], DLlama.DEFAULT_BINARY)
        self.assertEqual(configuration.llama['model'], DQwen.GGUF)
        self.assertEqual(configuration.llama['mmproj'], DQwen.MMPROJ)
        self.assertEqual(configuration.llama['context_size'], 12288)
        write_configuration(self.path, {'network': {'http': {'port': 51005}}})
        self.assertEqual(Network(Configuration(self.path)).binding('http')[1], 51005)

    def test_command_preserves_paths_with_spaces_and_optional_vision(self):
        llama = self.llama()
        binary, model, projector = llama.files()
        self.assertEqual(llama.command(), [
            str(binary), '--model', str(model), '--mmproj', str(projector),
            '-c', '12288', '--host', '127.0.0.1', '--port',
            str(self.values['network']['llm']['port']), '--metrics', '--jinja'])
        self.values['llama'].update(mmproj=None, metrics=False, jinja=False,
                                    model='/other/model.gguf', context_size=4096)
        command = self.llama().command()
        self.assertEqual(command[command.index('--model') + 1], '/other/model.gguf')
        self.assertNotIn('--mmproj', command)
        self.assertNotIn('--metrics', command)
        self.assertNotIn('--jinja', command)
        self.assertIn('--no-jinja', command)
        self.assertIn('4096', command)

    def test_configuration_rejects_unknown_fields_and_wrong_types(self):
        invalid = [('llama', []), ('unknown', {}), ('binary', ''), ('binary', 'relative'),
                   ('model_dir', 'relative'), ('model', None), ('model', 'a\0b'),
                   ('mmproj', False), ('context_size', True), ('context_size', 0),
                   ('context_size', '12288'), ('metrics', 1), ('jinja', 'true')]
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                values = {'llama': {key: value}} if key != 'llama' else {'llama': value}
                write_configuration(self.path, values)
                with self.assertRaises(ValueError) as caught:
                    Configuration(self.path)
                self.assertIn(str(self.path), str(caught.exception))

    def test_missing_unreadable_and_nonexecutable_artifacts_fail(self):
        llama = self.llama()
        binary, model, projector = llama.files()
        llama.validate_files()
        binary.chmod(0o644)
        with self.assertRaisesRegex(ValueError, str(binary)):
            llama.validate_files()
        binary.chmod(0o755)
        projector.unlink()
        with self.assertRaisesRegex(ValueError, str(projector)):
            llama.validate_files()
        self.values['llama']['mmproj'] = None
        self.llama().validate_files()
        with patch('llamasrv.interface.Llama.os.access', side_effect=lambda path, mode: path != model):
            with self.assertRaisesRegex(ValueError, str(model)):
                self.llama().validate_files()
        model.unlink()
        with self.assertRaisesRegex(ValueError, str(model)):
            self.llama().validate_files()

    def test_external_symlinks_are_allowed(self):
        alias = self.base / 'binary-link'
        alias.symlink_to(self.values['llama']['binary'])
        self.values['llama']['binary'] = str(alias)
        self.llama().validate_files()

    def test_check_is_read_only_and_missing_files_are_fatal(self):
        original = self.path.read_bytes()
        command = [sys.executable, '-B', '-m', 'llamasrv.activity.RunLlama',
                   '--config', str(self.path), '--check']
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), original)
        Path(self.values['llama']['binary']).unlink()
        result = subprocess.run(command[:-1], cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn(self.values['llama']['binary'], result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_real_exec_health_failure_recovery_and_signals(self):
        state = self.base / 'health'
        state.write_text('ok')
        arguments = self.base / 'arguments.json'
        env = dict(os.environ, LLAMASRV_TEST_HEALTH=str(state), LLAMASRV_TEST_ARGUMENTS=str(arguments))
        for stop_signal in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=stop_signal):
                self.values['llama']['jinja'] = stop_signal == signal.SIGTERM
                self.llama()
                with subprocess.Popen([
                    sys.executable, '-B', '-m', 'llamasrv.activity.RunLlama',
                    '--config', str(self.path)], cwd=ROOT, env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) as process:
                    try:
                        wait_for_health(self.values['network']['llm']['port'], process)
                        actual = json.loads(arguments.read_text())
                        self.assertEqual(actual['model'], str(self.llama().files()[1]))
                        self.assertEqual(actual['c'], 12288)
                        self.assertEqual(actual['jinja'], self.values['llama']['jinja'])
                        self.assertTrue(self.llama().health())
                        state.write_text('loading model')
                        self.assertFalse(self.llama().health())
                        state.write_text('ok')
                        self.assertTrue(self.llama().health())
                        process.send_signal(stop_signal)
                        _, errors = process.communicate(timeout=5)
                        self.assertEqual(process.returncode, 0, errors)
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.communicate(timeout=2)
                self.assertFalse(self.llama().health())


if __name__ == '__main__':
    unittest.main()
