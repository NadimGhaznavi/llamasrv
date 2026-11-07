#!/usr/bin/env python3
"""Install, update or remove LlamaSrv; external llama.cpp and models stay untouched."""

import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DService import DService
from llamasrv.constants.DText import DText
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import Llama
from llamasrv.interface.Services import Services


BMFORGE_COMPONENT = {"id": "bmforge.installation", "spec_version": "0.1.3"}

PROJECT_NAME = "LlamaSrv"
DEPLOYMENT_READY = True
COPY_TREES = ("llamasrv", "scripts", "systemd")
COPY_FILES = ()
# Set to "requirements.txt" for Python applications requiring a production venv.
# Keep None for applications without Python package dependencies.
REQUIREMENTS_FILE = "requirements.txt"
VENV_DIR = ".venv"
# Use the host interpreter, never an activated development checkout venv.
SYSTEM_PYTHON = "/usr/bin/python3"
# Adapt to the deployed application's service/client imports when enabling deployment.
RUNTIME_IMPORTS = ("llamasrv.server.LlamaSrvServer", "llamasrv.activity.RunLlama", "jinja2")
MANIFEST = ".installation-manifest.json"
VERSION_MARKER = ".deployment-version"
SERVICE_UNITS = "service_units"
SUDOERS_OWNED = "sudoers_owned"


def relative_path(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Managed paths must be strings")
    path = PurePosixPath(name)
    if not name or path.is_absolute() or '..' in path.parts or path.as_posix() != name or name == '.':
        raise ValueError(f"Invalid managed path: {name}")
    if name in (MANIFEST, VERSION_MARKER):
        raise ValueError(f"Reserved bookkeeping path: {name}")
    return name


def reject_symlinks(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f"Refusing a symbolic link in deployment path: {candidate}")


class Installation:
    def __init__(self, checkout: Path, *, destination: Path | None = None,
                 run=None, unit_dir: Path | None = None,
                 sudoers_dir: Path | None = None,
                 startup_timeout: float = DService.STARTUP_TIMEOUT) -> None:
        self.services = Services(run=run, unit_dir=unit_dir, sudoers_dir=sudoers_dir,
                                 startup_timeout=startup_timeout)
        self.checkout = checkout.resolve()
        self.run = run or subprocess.run
        self.version_file = f"{PROJECT_NAME.lower()}/constants/D{PROJECT_NAME}.py"
        spec = importlib.util.spec_from_file_location('cmdb_checker', self.checkout / 'scripts/check-cmdb.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        self.metadata = checker.validate((self.checkout / self.version_file).read_text(),
                                         PROJECT_NAME, self.version_file)
        self.destination = Path(destination if destination is not None else self.metadata['BASE_DIR']).absolute()
        reject_symlinks(self.destination)
        if (self.checkout.is_relative_to(self.destination)
                or self.destination.is_relative_to(self.checkout)):
            raise ValueError("Run deployment from a separate checkout outside the installation")

    def installed_files(self) -> list[str] | None:
        manifest = self.destination / MANIFEST
        reject_symlinks(manifest)
        if not manifest.exists():
            if self.destination.exists():
                raise ValueError("Installation directory exists without an ownership manifest; inspect it before proceeding")
            return None
        data = json.loads(manifest.read_text())
        if (not isinstance(data, dict) or data.get('project') != PROJECT_NAME
                or not isinstance(data.get('files'), list)):
            raise ValueError("Installation ownership manifest does not match this project")
        if type(data.get('venv_owned', False)) is not bool:
            raise ValueError("Installation manifest has invalid virtual environment ownership")
        if type(data.get(SUDOERS_OWNED, False)) is not bool:
            raise ValueError("Installation manifest has invalid sudoers ownership")
        units = data.get(SERVICE_UNITS, [])
        if (not isinstance(units, list) or any(name not in DService.START_ORDER for name in units)
                or len(units) != len(set(units))):
            raise ValueError(self.services.text(DText.INSTALL_SERVICE_OWNERSHIP))
        names = [relative_path(name) for name in data['files']]
        if (len(names) != len(set(names))
                or self.version_file not in names and not (not names and data.get('removed') is True)):
            raise ValueError("Installation ownership manifest has invalid files")
        for name in [*names, VERSION_MARKER]:
            path = self.destination / name
            reject_symlinks(path)
            if path.exists() and not path.is_file():
                raise ValueError(f"Managed file is no longer a regular file: {path}")
        return names

    def source_files(self) -> list[str]:
        names = {relative_path(name) for name in COPY_FILES}
        if REQUIREMENTS_FILE is not None:
            names.add(relative_path(REQUIREMENTS_FILE))
        for name in COPY_TREES:
            folder = self.checkout / relative_path(name)
            reject_symlinks(folder)
            if not folder.is_dir():
                raise ValueError(f"Missing source directory: {name}")
            for path in folder.rglob('*'):
                if '__pycache__' in path.parts or VENV_DIR in path.parts or path.suffix in ('.pyc', '.pyo'):
                    continue
                reject_symlinks(path)
                if path.is_file():
                    names.add(relative_path(path.relative_to(self.checkout).as_posix()))
        if self.version_file not in names:
            raise ValueError("Deployment must include readable CMDB constants")
        for name in names:
            source = self.checkout / name
            reject_symlinks(source)
            if not source.is_file():
                raise ValueError(f"Missing source file: {name}")
            target = self.destination / name
            reject_symlinks(target)
            if target.exists() and not target.is_file():
                raise ValueError(f"Managed file target is not a regular file: {target}")
        return sorted(names)

    def plan(self, action: str) -> tuple[list[str] | None, list[str]]:
        if not DEPLOYMENT_READY:
            raise ValueError("Deployment is not configured: implement provisioning, lifecycle, and health checks before enabling it")
        previous = self.installed_files()
        if action == 'upgrade' and not previous:
            raise ValueError("No installation found; run install.sh first")
        current = [] if action == 'uninstall' else self.source_files()
        if previous is not None:
            for name in set(current) - set(previous):
                if (self.destination / name).exists():
                    raise ValueError(f"New managed file would overwrite an unowned file: {name}")
        self.preflight_python(action)
        self.preflight_services(action)
        return previous, current

    def venv_owned(self) -> bool:
        manifest = self.destination / MANIFEST
        return manifest.is_file() and json.loads(manifest.read_text()).get('venv_owned') is True

    @staticmethod
    def python_environment() -> dict[str, str]:
        environment = os.environ.copy()
        for variable in ('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV',
                         'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
            environment.pop(variable, None)
        environment['PYTHONNOUSERSITE'] = '1'
        return environment

    def preflight_python(self, action: str) -> None:
        venv = self.destination / VENV_DIR
        reject_symlinks(venv)
        if venv.exists() and not venv.is_dir():
            raise ValueError(f'Virtual environment path is not a directory: {venv}')
        if action == 'uninstall':
            return
        if REQUIREMENTS_FILE is None:
            if (not Path(SYSTEM_PYTHON).is_absolute() or '/opt/dev/' in SYSTEM_PYTHON
                    or not os.access(SYSTEM_PYTHON, os.X_OK)):
                raise ValueError(f'Missing host Python interpreter: {SYSTEM_PYTHON}')
            self.run([SYSTEM_PYTHON, '-B', '-c',
                      'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'],
                     check=True, env=self.python_environment(), capture_output=True,
                     text=True, timeout=DService.COMMAND_TIMEOUT)
            return
        requirements = self.checkout / relative_path(REQUIREMENTS_FILE)
        if not requirements.is_file():
            raise ValueError(f'Missing Python dependency manifest: {REQUIREMENTS_FILE}')
        for entry in requirements.read_text().splitlines():
            entry = entry.strip()
            if (entry.startswith(('-e ', '--editable')) or '/opt/dev/' in entry):
                raise ValueError('Production Python dependencies must not use editable or /opt/dev installs')
        if venv.exists():
            if not self.venv_owned():
                raise ValueError(f'Refusing an unowned virtual environment: {venv}')
            configuration = venv / 'pyvenv.cfg'
            binary = venv / 'bin/python'
            reject_symlinks(configuration)
            reject_symlinks(binary.parent)
            if (not configuration.is_file() or not binary.is_file()
                    or '/opt/dev/' in configuration.read_text()
                    or '/opt/dev/' in str(binary.resolve())):
                raise ValueError(f'Production virtual environment is incomplete or references /opt/dev: {venv}')
        host_python = Path(SYSTEM_PYTHON)
        if (not host_python.is_absolute() or '/opt/dev/' in SYSTEM_PYTHON
                or host_python.is_relative_to(self.destination)
                or host_python.is_relative_to(self.checkout)
                or host_python.resolve().is_relative_to(self.checkout)
                or host_python.resolve().is_relative_to(self.destination)
                or '/opt/dev/' in str(host_python.resolve())
                or (host_python.parent.parent / 'pyvenv.cfg').exists()):
            raise ValueError('SYSTEM_PYTHON must be a host interpreter outside development and deployed environments')
        if shutil.which(SYSTEM_PYTHON) is None:
            raise ValueError(f'Missing host Python interpreter: {SYSTEM_PYTHON}')
        self.run([SYSTEM_PYTHON, '-B', '-c', 'import venv, ensurepip'],
                 check=True, env=self.python_environment(), capture_output=True,
                 text=True, timeout=30)

    def prepare_python(self) -> None:
        if REQUIREMENTS_FILE is None:
            return
        venv = self.destination / VENV_DIR
        python = venv / 'bin/python'
        environment = self.python_environment()
        if not venv.exists():
            self.run([SYSTEM_PYTHON, '-m', 'venv', str(venv)],
                     check=True, env=environment, timeout=120)
        self.run([str(python), '-m', 'pip', 'install', '--upgrade',
                  '-r', str(self.destination / REQUIREMENTS_FILE)],
                 check=True, cwd=self.destination, env=environment, timeout=300)
        self.run([str(python), '-m', 'pip', 'check'],
                 check=True, cwd=self.destination, env=environment, timeout=30)
        if RUNTIME_IMPORTS:
            # Imports run from deployed files, without a checkout or PYTHONPATH.
            self.run([str(python), '-B', '-c',
                      'from importlib import import_module; from sys import argv; '
                      '[import_module(name) for name in argv[1:]]',
                      *RUNTIME_IMPORTS],
                     check=True, cwd=self.destination, env=environment, timeout=30)

    def atomic_write(self, path: Path, content: bytes, mode: int = 0o644) -> None:
        if not path.is_relative_to(self.destination):
            raise ValueError(self.services.text(DText.INSTALL_OUTSIDE_PATH, path=path))
        path.parent.mkdir(parents=True, exist_ok=True)
        for directory in (path.parent, *path.parent.parents):
            if directory == self.destination.parent:
                break
            directory.chmod(0o755)
        descriptor, name = tempfile.mkstemp(prefix='.bmforge-install-', dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content)
                os.fchmod(stream.fileno(), mode)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def remove_files(self, names: list[str]) -> None:
        for name in names:
            path = self.destination / name
            path.unlink(missing_ok=True)
            for directory in path.parents:
                if directory == self.destination:
                    break
                try:
                    directory.rmdir()
                except OSError:
                    break

    def owned_units(self) -> list[str]:
        manifest = self.destination / MANIFEST
        return json.loads(manifest.read_text()).get(SERVICE_UNITS, []) if manifest.is_file() else []

    def owns_sudoers(self) -> bool:
        manifest = self.destination / MANIFEST
        return manifest.is_file() and json.loads(manifest.read_text()).get(SUDOERS_OWNED) is True

    def preflight_services(self, action: str) -> None:
        owned = self.owned_units()
        if action == 'uninstall' and not owned and not self.owns_sudoers():
            return
        commands = ('systemctl',) if action == 'uninstall' else (
            'systemctl', 'systemd-analyze', 'getent', DService.USERADD, DService.RUNUSER,
            DService.SUDO, DService.VISUDO, 'chown')
        for command in commands:
            if shutil.which(command) is None:
                raise ValueError(self.services.text(DText.INSTALL_PREREQUISITE, setting=command))
        reject_symlinks(self.services.unit_dir)
        if not self.services.unit_dir.is_dir():
            raise ValueError(self.services.text(DText.INSTALL_UNIT_DIRECTORY, path=self.services.unit_dir))
        sudoers = self.services.sudoers_dir / DService.SUDOERS_FILE
        reject_symlinks(sudoers)
        if self.owns_sudoers():
            if sudoers.exists() and not sudoers.is_file():
                raise ValueError(f'Sudoers target is not a regular file: {sudoers}')
        elif action != 'uninstall' and sudoers.exists():
            raise ValueError(f'Refusing to replace an unowned sudoers file: {sudoers}')
        if action != 'uninstall' and not self.services.sudoers_dir.is_dir():
            raise ValueError(f'Missing sudoers include directory: {self.services.sudoers_dir}')
        for name in DService.START_ORDER:
            target = self.services.unit_dir / name
            reject_symlinks(target)
            if target.exists() and (name not in owned or not target.is_file()):
                raise ValueError(self.services.text(DText.INSTALL_UNOWNED_UNIT, path=target))
        if action == 'uninstall':
            return
        self.services.verify_sudoers(self.checkout)
        self.configuration_path = self.destination / DNetwork.CONFIG_FILE
        reject_symlinks(self.configuration_path)
        self.configuration = Configuration(self.configuration_path)
        Llama(self.configuration).validate_files()
        self.runtime_python = (self.destination / VENV_DIR / 'bin/python'
                               if REQUIREMENTS_FILE is not None else Path(SYSTEM_PYTHON))
        self.units = self.services.render(self.checkout, self.destination,
                                          self.runtime_python, self.configuration_path)

    def verify_runtime(self) -> None:
        self.run([str(self.runtime_python), '-B', '-c',
                  'from importlib import import_module; from sys import argv; '
                  '[import_module(name) for name in argv[1:]]',
                  'llamasrv.server.LlamaSrvServer', 'llamasrv.activity.RunLlama'],
                 check=True, cwd=self.destination, env=self.python_environment(),
                 capture_output=True, text=True, timeout=DService.COMMAND_TIMEOUT)
        # Root's file access is insufficient evidence for the service account.
        self.run([DService.RUNUSER, '-u', DService.ACCOUNT, '--', str(self.runtime_python),
                  '-B', '-m', 'llamasrv.activity.RunLlama', '--config',
                  str(self.configuration_path), '--check'],
                 check=True, cwd=self.destination, env=self.python_environment(),
                 capture_output=True, text=True, timeout=DService.COMMAND_TIMEOUT)

    def apply(self, action: str, *, check: bool = False) -> None:
        previous, names = self.plan(action)
        if check:
            print(f"{action}: checks passed for {self.destination}; no files changed.")
            return
        if action == 'uninstall':
            if previous is not None:
                self.services.uninstall(self.owned_units())
                if self.owns_sudoers():
                    (self.services.sudoers_dir / DService.SUDOERS_FILE).unlink(missing_ok=True)
                self.remove_files(previous)
                venv = self.destination / VENV_DIR
                reject_symlinks(venv)
                if venv.is_dir() and self.venv_owned():
                    shutil.rmtree(venv)
                (self.destination / VERSION_MARKER).unlink(missing_ok=True)
                (self.destination / MANIFEST).unlink()
                try:
                    self.destination.rmdir()
                except OSError:
                    removed = {'project': PROJECT_NAME, 'files': [], 'removed': True}
                    self.atomic_write(self.destination / MANIFEST,
                                      (json.dumps(removed, indent=2) + '\n').encode())
            print(f"Removed managed {PROJECT_NAME} services and files; configuration and data retained.")
            return
        # Validate unit syntax before stopping an existing installation.
        # The production venv does not exist on a fresh installation. Validate
        # syntax with the known host interpreter before changing services, then
        # verify the actual deployed command once its environment is prepared.
        self.services.verify(self.services.render(
            self.checkout, self.destination, Path(SYSTEM_PYTHON), self.configuration_path))
        self.services.ensure_account()
        self.services.stop(self.owned_units())
        self.destination.mkdir(parents=True, exist_ok=True)
        self.destination.chmod(0o755)
        ownership = {'project': PROJECT_NAME, 'files': sorted(set(previous or ()) | set(names)),
                     'venv_owned': REQUIREMENTS_FILE is not None or self.venv_owned(),
                     SUDOERS_OWNED: True,
                     SERVICE_UNITS: list(DService.START_ORDER)}
        self.atomic_write(self.destination / MANIFEST,
                          (json.dumps(ownership, indent=2) + '\n').encode())
        for name in names:
            source = self.checkout / name
            mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
            self.atomic_write(self.destination / name, source.read_bytes(), mode)
        if not self.configuration_path.exists():
            self.atomic_write(self.configuration_path,
                              (json.dumps(self.configuration.as_dict(), indent=2) + '\n').encode())
        self.services.command('chown', DService.ACCOUNT + ':' + DService.ACCOUNT,
                              str(self.configuration_path.parent), str(self.configuration_path))
        self.prepare_python()
        self.services.verify(self.units)
        self.verify_runtime()
        self.remove_files(sorted(set(previous or ()) - set(names)))
        self.services.install(self.units)
        self.services.install_sudoers(self.checkout)
        self.services.start()
        self.services.wait_ready(self.configuration)
        ownership['files'] = names
        self.atomic_write(self.destination / MANIFEST,
                          (json.dumps(ownership, indent=2) + '\n').encode())
        # Advance the authoritative version only after both services are ready.
        self.atomic_write(self.destination / VERSION_MARKER,
                          (self.metadata['VERSION'] + '\n').encode())
        print(f"{action}: {PROJECT_NAME} {self.metadata['VERSION']} deployed to {self.destination}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'upgrade', 'uninstall'))
    parser.add_argument('--check', action='store_true', help='Validate the operation without changing files')
    args = parser.parse_args()
    if not args.check and os.geteuid() != 0:
        parser.error('Run deployment as root; --check and --help do not require root')
    try:
        Installation(Path(__file__).resolve().parents[1]).apply(args.action, check=args.check)
    except (OSError, ValueError, TypeError, SyntaxError, subprocess.SubprocessError) as error:
        detail = getattr(error, 'stderr', None) or str(error)
        parser.exit(1, f"Deployment failed: {detail}\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
