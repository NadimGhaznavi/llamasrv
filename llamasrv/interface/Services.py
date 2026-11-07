"""Application-owned systemd operations; inference and HTTP stay separate."""

import json
from pathlib import Path
import subprocess
import tempfile
import time

from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DService import DService
from llamasrv.constants.DText import DText
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import probe
from llamasrv.interface.Localizer import Localizer
from llamasrv.interface.Network import Network


class Services:
    def __init__(self, *, run=None, unit_dir: Path | None = None,
                 sudoers_dir: Path | None = None,
                 startup_timeout: float = DService.STARTUP_TIMEOUT):
        self.run = run if run is not None else subprocess.run
        self.unit_dir = Path(unit_dir if unit_dir is not None else DService.UNIT_DIR)
        self.sudoers_dir = Path(sudoers_dir if sudoers_dir is not None else DService.SUDOERS_DIR)
        self.startup_timeout = startup_timeout
        self.localizer = Localizer(Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)

    def text(self, key: DText, **values) -> str:
        return self.localizer.text(key, **values)

    def command(self, *arguments: str, check: bool = True):
        return self.run(list(arguments), check=check, capture_output=True,
                        text=True, timeout=DService.COMMAND_TIMEOUT)

    def render(self, checkout: Path, application: Path, python: Path,
               configuration: Path) -> dict[str, str]:
        # WorkingDirectory consumes a path, while ExecStart tokenizes arguments.
        values = {"APP": str(application).replace("%", "%%"),
                  "USER": DService.ACCOUNT,
                  "PYTHON": json.dumps(str(python), ensure_ascii=False).replace("%", "%%"),
                  "CONF_DIR": json.dumps(str(configuration.parent), ensure_ascii=False).replace("%", "%%"),
                  "CONFIG": json.dumps(str(configuration), ensure_ascii=False).replace("%", "%%")}
        units = {}
        for name in DService.START_ORDER:
            content = (checkout / "systemd" / name).read_text(encoding="utf-8")
            for key, value in values.items():
                content = content.replace("@" + key + "@", value)
            if "@" in content:
                raise ValueError(self.text(DText.SERVICE_TEMPLATE, setting=name))
            units[name] = content
        return units

    def verify(self, units: dict[str, str]) -> None:
        with tempfile.TemporaryDirectory(prefix="llamasrv-units-") as directory:
            paths = []
            for name, content in units.items():
                path = Path(directory) / name
                path.write_text(content, encoding="utf-8")
                paths.append(str(path))
            self.command("systemd-analyze", "verify", *paths)

    def ensure_account(self) -> None:
        result = self.command("getent", "passwd", DService.ACCOUNT, check=False)
        if result.returncode == 2:
            self.command(DService.USERADD, "--system", "--user-group", "--no-create-home",
                         "--shell", "/usr/sbin/nologin", DService.ACCOUNT)
        elif result.returncode:
            raise ValueError(self.text(DText.SERVICE_ACCOUNT_FAILED,
                                       setting=DService.ACCOUNT, error=result.stderr))

    def loaded(self, name: str) -> bool:
        result = self.command("systemctl", "show", "--property=LoadState", "--value", name,
                              check=False)
        if result.stdout.strip() == "not-found":
            return False
        result.check_returncode()
        return True

    def start(self) -> None:
        for name in DService.START_ORDER:
            self.command("systemctl", "start", name)

    def restart_llm(self) -> None:
        """Use the exact passwordless commands granted by our installed sudoers file."""
        try:
            for action in ("stop", "start"):
                self.command(DService.SUDO, "-n", DService.SYSTEMCTL, action, DService.LLM)
        except subprocess.SubprocessError as error:
            raise RuntimeError(self.text(DText.UI_OPERATION_FAILED)) from error

    def sudoers(self, checkout: Path | None = None) -> str:
        root = checkout if checkout is not None else Path(__file__).resolve().parents[2]
        return (root / DService.SUDOERS_SOURCE).read_text(encoding="utf-8")

    def verify_sudoers(self, checkout: Path | None = None) -> None:
        with tempfile.NamedTemporaryFile(mode="w", prefix="llamasrv-sudoers-") as stream:
            stream.write(self.sudoers(checkout))
            stream.flush()
            self.command(DService.VISUDO, "-cf", stream.name)

    def install_sudoers(self, checkout: Path | None = None) -> None:
        with tempfile.NamedTemporaryFile(dir=self.sudoers_dir, prefix=".llamasrv-",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(self.sudoers(checkout).encode("utf-8"))
                stream.flush()
                temporary.chmod(0o440)
                temporary.replace(self.sudoers_dir / DService.SUDOERS_FILE)
            finally:
                temporary.unlink(missing_ok=True)

    def stop(self, units: tuple[str, ...] | list[str] = DService.START_ORDER) -> None:
        for name in reversed(DService.START_ORDER):
            if name in units and self.loaded(name):
                self.command("systemctl", "stop", name)

    def install(self, units: dict[str, str]) -> None:
        for name, content in units.items():
            # These files are outside BASE_DIR; never chmod their ancestor directories.
            with tempfile.NamedTemporaryFile(dir=self.unit_dir, prefix=".llamasrv-",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    stream.write(content.encode("utf-8"))
                    stream.flush()
                    temporary.chmod(0o644)
                    temporary.replace(self.unit_dir / name)
                finally:
                    temporary.unlink(missing_ok=True)
        self.command("systemctl", "daemon-reload")
        for name in DService.START_ORDER:
            self.command("systemctl", "enable", name)

    def uninstall(self, units: list[str]) -> None:
        self.stop(units)
        for name in reversed(DService.START_ORDER):
            if name in units:
                if self.loaded(name):
                    self.command("systemctl", "disable", name)
                (self.unit_dir / name).unlink(missing_ok=True)
        if units:
            self.command("systemctl", "daemon-reload")

    def wait_ready(self, configuration: Configuration) -> None:
        address = Network(configuration).destination(DNetwork.HTTP)
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            for name in DService.START_ORDER:
                result = self.command("systemctl", "is-active", "--quiet", name, check=False)
                if result.returncode:
                    raise ValueError(self.text(DText.SERVICE_INACTIVE, setting=name))
            if probe(*address, components=(DNetwork.HTTP, DNetwork.LLM)):
                return
            time.sleep(DService.POLL_INTERVAL)
        raise ValueError(self.text(DText.SERVICE_NOT_READY, seconds=f"{self.startup_timeout:g}",
                                   llm_unit=DService.LLM, http_unit=DService.HTTP))
