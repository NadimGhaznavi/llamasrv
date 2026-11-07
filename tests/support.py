"""Disposable external artifacts and real process helpers for GPU-free tests."""

import json
from pathlib import Path
import shutil
import socket
import time

from llamasrv.interface.Llama import probe


ROOT = Path(__file__).resolve().parents[1]


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
