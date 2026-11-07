"""Disposable external artifacts and real process helpers for GPU-free tests."""

import json
from importlib import import_module, metadata
from pathlib import Path
import shutil
import socket
import time
from zipfile import ZipFile

from llamasrv.interface.Llama import probe


ROOT = Path(__file__).resolve().parents[1]


def dependency_wheels(directory: Path):
    """Package the real locally installed dependencies for offline venv tests.

    MarkupSafe's Python implementation is sufficient; omit host-specific binary
    extensions so these test wheels are portable across local interpreters.
    """
    for distribution, package in (('Jinja2', 'jinja2'), ('MarkupSafe', 'markupsafe')):
        version = metadata.version(distribution)
        name = distribution.lower()
        info = f'{name}-{version}.dist-info'
        source = Path(import_module(package).__file__).parent
        with ZipFile(directory / f'{name}-{version}-py3-none-any.whl', 'w') as wheel:
            records = []
            for path in source.rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py', '.typed'):
                    target = package + '/' + str(path.relative_to(source))
                    wheel.write(path, target)
                    records.append(target)
            description = metadata.distribution(distribution).metadata
            meta = f'Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n'
            for requirement in description.get_all('Requires-Dist', []):
                meta += f'Requires-Dist: {requirement}\n'
            wheel.writestr(info + '/METADATA', meta + '\n')
            wheel.writestr(info + '/WHEEL', 'Wheel-Version: 1.0\nGenerator: LlamaSrv-offline-tests\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
            records.extend((info + '/METADATA', info + '/WHEEL', info + '/RECORD'))
            wheel.writestr(info + '/RECORD', ''.join(f'{path},,\n' for path in records))


def free_port():
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        return reservation.getsockname()[1]


def fixture_configuration(directory: Path):
    binary = directory / 'external bin/llama server'
    binary.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'tests/fixtures/llama-server', binary)
    binary.chmod(0o755)
    models = directory / 'external models'
    models.mkdir()
    (models / 'model.gguf').write_bytes(b'fixture model')
    (models / 'projector.gguf').write_bytes(b'fixture projector')
    http_port, llm_port = free_port(), free_port()
    while http_port == llm_port:
        llm_port = free_port()
    return {
        'network': {
            'http': {'interface': '127.0.0.1', 'port': http_port},
            'llm': {'interface': '127.0.0.1', 'port': llm_port}},
        'llama': {'binary': str(binary), 'model_dir': str(models),
                  'model': 'model.gguf', 'mmproj': 'projector.gguf',
                  'context_size': 12288, 'metrics': True, 'jinja': True}}


def write_configuration(path: Path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2) + '\n')


def wait_for_health(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f'Process exited before readiness: {process.returncode}')
        if probe('127.0.0.1', port):
            return
        time.sleep(0.02)
    raise AssertionError('Fixture did not become ready')
