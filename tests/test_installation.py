"""Disposable lifecycle tests: simulated systemd controls real installed processes."""

import json
from http.client import HTTPConnection
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from llamasrv.constants.DLlama import DLlama
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DQwen import DQwen
from llamasrv.constants.DService import DService
from llamasrv.interface.Llama import probe
from scripts.install import Installation, MANIFEST, SYSTEM_PYTHON, VERSION_MARKER, SUDOERS_OWNED
from support import ROOT, fixture_configuration, dependency_wheels


class LocalSystem:
    """Only systemd/account operations are simulated; Python and HTTP are real."""
    def __init__(self, destination, unit_dir, health, wheels):
        self.destination, self.unit_dir, self.health = destination, unit_dir, health
        self.calls = []
        self.processes = {}
        self.fail = None
        self.wheels = wheels

    def close(self):
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        if command[0] == 'chown':
            return subprocess.CompletedProcess(command, 0, '', '')
        if '-m' in command and 'pip' in command:
            if self.fail == 'pip':
                raise subprocess.CalledProcessError(1, command, stderr='fixture pip failure')
            kwargs['env'] = {**kwargs.get('env', {}), 'PIP_NO_INDEX': '1',
                             'PIP_FIND_LINKS': str(self.wheels)}
        if command[0] == 'getent':
            return subprocess.CompletedProcess(command, 0, 'fixture account\n', '')
        if command[0] == DService.RUNUSER:
            if self.fail == 'permission':
                raise subprocess.CalledProcessError(1, command, stderr='fixture permission denied')
            return subprocess.run(command[4:], **kwargs)
        if command[0] == 'systemd-analyze' and self.fail == 'verify':
            raise subprocess.CalledProcessError(1, command, stderr='fixture invalid unit')
        if command[0] != 'systemctl':
            return subprocess.run(command, **kwargs)
        action, name = command[1], command[-1]
        output, code = '', 0
        if action == 'show':
            output = 'loaded\n' if (self.unit_dir / name).is_file() else 'not-found\n'
        elif action == 'is-active':
            process = self.processes.get(name)
            code = 0 if process is not None and process.poll() is None else 3
        elif action == 'start':
            if self.fail == 'start':
                raise subprocess.CalledProcessError(1, command, stderr='fixture startup failure')
            module = 'llamasrv.activity.RunLlama' if name == DService.LLM else 'llamasrv'
            environment = Installation.python_environment()
            environment['LLAMASRV_TEST_HEALTH'] = str(self.health)
            self.processes[name] = subprocess.Popen([
                str(self.destination / '.venv/bin/python'), '-B', '-m', module, '--config',
                str(self.destination / 'conf/llamasrv.json')], cwd=self.destination,
                env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif action == 'stop':
            process = self.processes.get(name)
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        result = subprocess.CompletedProcess(command, code, output, '')
        if kwargs.get('check') and code:
            result.check_returncode()
        return result


class InstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wheel_directory = tempfile.TemporaryDirectory(prefix='llamasrv-test-wheels-')
        cls.addClassCleanup(cls.wheel_directory.cleanup)
        dependency_wheels(Path(cls.wheel_directory.name))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.checkout = self.base / 'checkout'
        self.checkout.mkdir()
        for name in ('llamasrv', 'scripts', 'systemd'):
            shutil.copytree(ROOT / name, self.checkout / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(ROOT / 'requirements.txt', self.checkout / 'requirements.txt')
        # Only the disposable checkout uses fixed versions for lifecycle transitions.
        metadata = self.checkout / 'llamasrv/constants/DLlamaSrv.py'
        metadata.write_text(re.sub(r'(?m)^(    VERSION: Final\[str\] = )"[^"]+"$',
                                   r'\g<1>"0.0.0"', metadata.read_text()))
        self.destination = self.base / 'installed app'
        self.unit_dir = self.base / 'units'
        self.unit_dir.mkdir()
        self.sudoers_dir = self.base / 'sudoers.d'
        self.sudoers_dir.mkdir()
        self.values = fixture_configuration(self.base)
        self.health = self.base / 'health'
        self.health.write_text('ok')
        self.system = LocalSystem(self.destination, self.unit_dir, self.health,
                                  Path(self.wheel_directory.name))
        self.addCleanup(self.system.close)
        defaults = self.values['llama']
        patches = [patch.object(DLlama, 'DEFAULT_BINARY', defaults['binary']),
                   patch.object(DLlama, 'DEFAULT_MODEL_DIR', defaults['model_dir']),
                   patch.object(DQwen, 'GGUF', defaults['model']),
                   patch.object(DQwen, 'MMPROJ', defaults['mmproj']),
                   patch.object(DLlamaSrv, 'CMDB_NETWORK', tuple(
                       (use, settings['interface'], settings['port'])
                       for use, settings in self.values['network'].items()))]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def installer(self, **options):
        return Installation(self.checkout, destination=self.destination,
                            unit_dir=self.unit_dir, sudoers_dir=self.sudoers_dir,
                            run=self.system, startup_timeout=3, **options)

    def snapshot(self):
        return {str(path.relative_to(self.base)): (path.read_bytes(), path.stat().st_mode)
                for path in self.base.rglob('*') if path.is_file()}

    def next_version(self):
        path = self.checkout / 'llamasrv/constants/DLlamaSrv.py'
        path.write_text(path.read_text().replace('VERSION: Final[str] = "0.0.0"',
                                                'VERSION: Final[str] = "0.0.1"'))

    def test_fresh_and_installed_checks_are_read_only(self):
        before = self.snapshot()
        self.installer().apply('install', check=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.destination.exists())
        self.installer().apply('install')
        before = self.snapshot()
        self.system.calls.clear()
        self.installer().apply('upgrade', check=True)
        self.installer().apply('uninstall', check=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(any(call[0] == 'systemctl' for call in self.system.calls))

    def test_install_reinstall_upgrade_and_retained_config(self):
        self.installer().apply('install')
        configuration = self.destination / 'conf/llamasrv.json'
        self.assertEqual(json.loads(configuration.read_text()), self.values)
        self.assertEqual((self.destination / VERSION_MARKER).read_text(), '0.0.0\n')
        self.assertTrue(probe('127.0.0.1', self.values['network']['http']['port'],
                              components=('http', 'llm')))
        self.assertTrue((self.destination / '.venv/bin/python').is_file())
        sudoers = self.sudoers_dir / DService.SUDOERS_FILE
        self.assertEqual(sudoers.stat().st_mode & 0o777, 0o440)
        self.assertEqual(sudoers.read_text(), (ROOT / 'systemd/llamasrv.sudoers').read_text())
        self.assertTrue(json.loads((self.destination / MANIFEST).read_text())[SUDOERS_OWNED])
        for name in DService.START_ORDER:
            text = (self.unit_dir / name).read_text()
            self.assertNotIn('/opt/dev/', text)
            self.assertIn(str(self.destination), text)
            self.assertIn('ProtectSystem=strict', text)
            self.assertEqual((self.unit_dir / name).stat().st_mode & 0o777, 0o644)
            self.assertIn(str(self.destination / '.venv/bin/python'), text)
        self.assertIn('NoNewPrivileges=false', (self.unit_dir / DService.HTTP).read_text())
        self.assertIn('NoNewPrivileges=true', (self.unit_dir / DService.LLM).read_text())
        self.installer().apply('install')
        settings = json.loads(configuration.read_text())
        settings['llama'].update(mmproj=None, context_size=4096, metrics=False, jinja=False)
        configuration.write_text(json.dumps(settings) + '\n')
        saved = configuration.read_bytes()
        user_file = self.destination / 'notes.txt'
        user_file.write_text('retain this')
        obsolete = self.destination / 'llamasrv/obsolete.py'
        obsolete.write_text('# formerly managed\n')
        manifest = self.destination / MANIFEST
        ownership = json.loads(manifest.read_text())
        ownership['files'].append('llamasrv/obsolete.py')
        manifest.write_text(json.dumps(ownership))
        self.next_version()
        self.system.calls.clear()
        self.installer().apply('upgrade')
        self.assertEqual(configuration.read_bytes(), saved)
        self.assertEqual(user_file.read_text(), 'retain this')
        self.assertFalse(obsolete.exists())
        self.assertEqual((self.destination / VERSION_MARKER).read_text(), '0.0.1\n')
        actions = [call[1:] for call in self.system.calls if call[0] == 'systemctl']
        self.assertLess(actions.index(['stop', DService.HTTP]), actions.index(['stop', DService.LLM]))
        self.assertLess(actions.index(['start', DService.LLM]), actions.index(['start', DService.HTTP]))

    def test_upgrade_from_stopped_services_skips_health_check(self):
        self.installer().apply('install')
        self.installer().services.stop()
        self.assertTrue(all(process.poll() is not None
                            for process in self.system.processes.values()))
        self.health.write_text('loading model')
        self.next_version()
        self.system.calls.clear()
        with patch('llamasrv.interface.Services.probe') as health_probe:
            self.installer().apply('upgrade')
        health_probe.assert_not_called()
        self.assertEqual((self.destination / VERSION_MARKER).read_text(), '0.0.1\n')
        self.assertEqual([call[1:] for call in self.system.calls
                          if call[:2] == ['systemctl', 'start']], [
            ['start', DService.LLM], ['start', DService.HTTP]])

    def test_deployed_code_runs_without_checkout(self):
        self.installer().apply('install')
        self.system.close()
        hidden = self.base / 'hidden-checkout'
        self.checkout.rename(hidden)
        try:
            result = subprocess.run([
                str(self.destination / '.venv/bin/python'), '-B', '-m', 'llamasrv.activity.RunLlama', '--config',
                str(self.destination / 'conf/llamasrv.json'), '--check'],
                cwd=self.destination, env=Installation.python_environment(),
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            installer = Installation(hidden, destination=self.destination,
                                     unit_dir=self.unit_dir, sudoers_dir=self.sudoers_dir,
                                     run=self.system, startup_timeout=3)
            installer.services.start()
            from llamasrv.interface.Configuration import Configuration
            installer.services.wait_ready(Configuration(self.destination / 'conf/llamasrv.json'))
            connection = HTTPConnection('127.0.0.1', self.values['network']['http']['port'], timeout=3)
            try:
                connection.request('GET', '/')
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(b'Restart LLM', response.read())
            finally:
                connection.close()
        finally:
            hidden.rename(self.checkout)

    def test_uninstall_repeat_uninstall_and_reinstall_preserve_external_assets(self):
        self.installer().apply('install')
        configuration = self.destination / 'conf/llamasrv.json'
        saved = configuration.read_bytes()
        model = Path(self.values['llama']['model_dir']) / 'model.gguf'
        self.installer().apply('uninstall')
        self.assertEqual(configuration.read_bytes(), saved)
        self.assertEqual(model.read_bytes(), b'fixture model')
        self.assertTrue(Path(self.values['llama']['binary']).exists())
        self.assertFalse((self.destination / VERSION_MARKER).exists())
        self.assertFalse(list(self.unit_dir.iterdir()))
        self.assertFalse((self.sudoers_dir / DService.SUDOERS_FILE).exists())
        self.assertFalse((self.destination / '.venv').exists())
        self.installer().apply('uninstall')
        self.installer().apply('install')
        self.assertEqual(configuration.read_bytes(), saved)
        self.assertTrue((self.destination / VERSION_MARKER).exists())

    def test_missing_assets_invalid_config_and_unowned_units_fail_before_changes(self):
        binary = Path(self.values['llama']['binary'])
        binary.chmod(0o644)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'not executable'):
            self.installer().apply('install')
        self.assertEqual(self.snapshot(), before)
        binary.chmod(0o755)
        unit = self.unit_dir / DService.LLM
        unit.write_text('unrelated')
        with self.assertRaisesRegex(ValueError, 'unowned service'):
            self.installer().apply('install')
        self.assertEqual(unit.read_text(), 'unrelated')
        unit.unlink()
        self.installer().apply('install')
        configuration = self.destination / 'conf/llamasrv.json'
        configuration.write_text('{broken')
        self.system.calls.clear()
        with self.assertRaises(ValueError):
            self.installer().apply('upgrade')
        self.assertFalse(any(call[:2] == ['systemctl', 'stop'] for call in self.system.calls))

    def test_failed_unit_verification_leaves_running_installation_alone(self):
        self.installer().apply('install')
        self.system.calls.clear()
        self.system.fail = 'verify'
        with self.assertRaises(subprocess.CalledProcessError):
            self.installer().apply('upgrade')
        self.assertFalse(any(call[:2] == ['systemctl', 'stop'] for call in self.system.calls))
        self.assertTrue(all(process.poll() is None for process in self.system.processes.values()))

    def test_failed_activation_and_account_access_do_not_advance_version(self):
        self.installer().apply('install')
        self.next_version()
        for failure in ('permission', 'start'):
            with self.subTest(failure=failure):
                self.system.fail = failure
                with self.assertRaises(subprocess.CalledProcessError):
                    self.installer().apply('upgrade')
                self.assertEqual((self.destination / VERSION_MARKER).read_text(), '0.0.0\n')
        self.system.fail = None
        self.installer().apply('upgrade')
        self.assertEqual((self.destination / VERSION_MARKER).read_text(), '0.0.1\n')

    def test_failed_first_install_and_readiness_never_claim_success(self):
        self.system.fail = 'start'
        with self.assertRaises(subprocess.CalledProcessError):
            self.installer().apply('install')
        self.assertFalse((self.destination / VERSION_MARKER).exists())
        self.system.fail = None
        self.health.write_text('loading model')
        installer = self.installer()
        installer.services.startup_timeout = 0.2
        with self.assertRaisesRegex(ValueError, 'did not become ready'):
            installer.apply('install')
        self.assertFalse((self.destination / VERSION_MARKER).exists())
        self.installer().apply('uninstall')

    def test_missing_tools_and_owned_path_symlinks_are_refused(self):
        with patch('scripts.install.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'prerequisite|interpreter'):
                self.installer().apply('install', check=True)
        self.destination.symlink_to(self.base / 'other')
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            self.installer()

    def test_unowned_sudoers_is_never_overwritten_or_removed(self):
        target = self.sudoers_dir / DService.SUDOERS_FILE
        target.write_text('# operator-owned policy\n')
        before = self.snapshot()
        for check in (True, False):
            with self.assertRaisesRegex(ValueError, 'unowned sudoers'):
                self.installer().apply('install', check=check)
            self.assertEqual(self.snapshot(), before)
        self.installer().apply('uninstall')
        self.assertEqual(target.read_text(), '# operator-owned policy\n')

    def test_invalid_sudoers_fails_before_installation_or_service_changes(self):
        (self.checkout / 'systemd/llamasrv.sudoers').write_text('invalid sudoers !!!')
        before = self.snapshot()
        with self.assertRaises(subprocess.CalledProcessError):
            self.installer().apply('install')
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(any(call[:2] == ['systemctl', 'stop'] for call in self.system.calls))

    def test_dependency_failure_and_unowned_venv_do_not_claim_success(self):
        self.system.fail = 'pip'
        with self.assertRaises(subprocess.CalledProcessError):
            self.installer().apply('install')
        self.assertFalse((self.destination / VERSION_MARKER).exists())
        self.system.fail = None
        self.installer().apply('install')
        ownership_path = self.destination / MANIFEST
        ownership = json.loads(ownership_path.read_text())
        ownership['venv_owned'] = False
        ownership_path.write_text(json.dumps(ownership))
        with self.assertRaisesRegex(ValueError, 'unowned virtual environment'):
            self.installer().apply('upgrade', check=True)


if __name__ == '__main__':
    unittest.main()
