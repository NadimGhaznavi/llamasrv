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

    def test_restart_submits_one_exact_nonblocking_systemd_job(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, '', ''))
        services = Services(run=runner)
        services.restart_llm()
        runner.assert_called_once_with([
            '/usr/bin/sudo', '-n', '/usr/bin/systemctl', '--no-block', 'restart', DService.LLM],
            check=True, capture_output=True, text=True, timeout=DService.COMMAND_TIMEOUT)
        for error in (subprocess.CalledProcessError(1, ['sudo'], stderr='denied'),
                      subprocess.TimeoutExpired(['sudo'], DService.COMMAND_TIMEOUT)):
            with self.subTest(error=type(error).__name__):
                runner.reset_mock()
                runner.side_effect = error
                with self.assertRaises(RuntimeError) as caught:
                    services.restart_llm()
                self.assertIs(caught.exception.__cause__, error)
                self.assertEqual(runner.call_count, 1)

    def test_sudoers_grants_only_exact_service_commands_without_wildcards(self):
        content = Services().sudoers()
        rules = [line for line in content.splitlines() if line and not line.startswith('#')]
        self.assertEqual(len(rules), 1)
        commands = rules[0].split('NOPASSWD: ', 1)[1].split(', ')
        self.assertEqual(set(commands), {
            f'/usr/bin/systemctl {action} {name}'
            for name in (DService.HTTP, DService.LLM) for action in ('start', 'stop')
        } | {f'/usr/bin/systemctl --no-block restart {DService.LLM}'})
        self.assertEqual(len(commands), 5)
        self.assertNotIn('*', content)
        self.assertTrue(rules[0].startswith('llamasrv ALL=(root) NOPASSWD:'))


if __name__ == '__main__':
    unittest.main()
