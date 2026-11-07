"""Service control must preserve order and distinguish missing units from errors."""

from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock

from llamasrv.constants.DService import DService
from llamasrv.interface.Services import Services


class ServiceTests(unittest.TestCase):
    def test_start_stop_order_and_absent_units(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, 'loaded\n', ''))
        services = Services(run=runner)
        services.start()
        self.assertEqual([call.args[0] for call in runner.call_args_list], [
            ['systemctl', 'start', DService.LLM], ['systemctl', 'start', DService.HTTP]])
        runner.reset_mock()
        services.stop()
        self.assertEqual([call.args[0] for call in runner.call_args_list if 'stop' in call.args[0]], [
            ['systemctl', 'stop', DService.HTTP], ['systemctl', 'stop', DService.LLM]])
        runner.reset_mock()
        runner.return_value = subprocess.CompletedProcess([], 1, 'not-found\n', '')
        services.stop()
        self.assertFalse(any('stop' in call.args[0] for call in runner.call_args_list))
        runner.return_value = subprocess.CompletedProcess([], 1, '', 'systemd bus unavailable')
        with self.assertRaises(subprocess.CalledProcessError):
            services.stop()

    def test_new_account_is_created_but_lookup_errors_are_fatal(self):
        runner = Mock(side_effect=[subprocess.CompletedProcess([], 2, '', ''),
                                   subprocess.CompletedProcess([], 0, '', '')])
        services = Services(run=runner)
        services.ensure_account()
        self.assertEqual(runner.call_args_list[1].args[0], [
            DService.USERADD, '--system', '--user-group', '--no-create-home',
            '--shell', '/usr/sbin/nologin', DService.ACCOUNT])
        runner.side_effect = None
        runner.return_value = subprocess.CompletedProcess([], 1, '', 'lookup failed')
        with self.assertRaisesRegex(ValueError, 'lookup failed'):
            services.ensure_account()

    def test_unit_directives_and_command_arguments_use_correct_quoting(self):
        units = Services().render(Path(__file__).resolve().parents[1],
                                  Path('/opt/prod/app path'), Path('/usr/bin/python3'),
                                  Path('/opt/prod/app path/conf/llamasrv.json'))
        for content in units.values():
            self.assertIn('User=llamasrv\n', content)
            self.assertIn('WorkingDirectory=/opt/prod/app path\n', content)
            self.assertIn('--config "/opt/prod/app path/conf/llamasrv.json"', content)
            self.assertNotIn('@', content)


if __name__ == '__main__':
    unittest.main()
