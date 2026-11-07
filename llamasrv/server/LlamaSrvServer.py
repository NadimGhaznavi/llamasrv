"""Application-owned HTTP listener and command entry point."""

import argparse
from http.server import ThreadingHTTPServer
import logging
from pathlib import Path
import signal

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from llamasrv.activity.ControlPanel import ControlPanel
from llamasrv.constants.DControl import DControl
from llamasrv.constants.DHTTP import DHTTP, HealthStatus
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DText import DText
from llamasrv.interface.Localizer import Localizer
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import Llama
from llamasrv.interface.Network import Network
from llamasrv.server.LlamaSrvHandler import LlamaSrvHandler


BMFORGE_COMPONENT = {"id": "bmforge.http-server", "spec_version": "0.5.1"}


class LlamaSrvServer(ThreadingHTTPServer):
    # Join request workers on close; each socket has a bounded read timeout.
    daemon_threads = False
    block_on_close = True

    def __init__(self, address: tuple[str, int], *, llama: Llama | None = None,
                 configuration: Configuration | None = None):
        configuration = configuration if configuration is not None else (
            llama.configuration if isinstance(llama, Llama) else Configuration())
        self.llama = llama if llama is not None else Llama(configuration)
        self.control = ControlPanel(configuration)
        self.localizer = configuration.localizer
        self.templates = Environment(
            loader=FileSystemLoader(Path(__file__).resolve().parent / "templates"),
            autoescape=select_autoescape(("html", "xml")), undefined=StrictUndefined)
        self.templates.get_template(DControl.TEMPLATE)
        super().__init__(address, LlamaSrvHandler)

    def health(self) -> dict:
        state = HealthStatus.OK if self.fileno() >= 0 else HealthStatus.ERROR
        try:
            llama = (Llama(self.control.read(self.localizer.default_language))
                     if isinstance(self.llama, Llama) else self.llama)
            inference = HealthStatus.OK if llama.health() else HealthStatus.ERROR
        except ValueError:
            logging.exception("health_configuration_failed")
            inference = HealthStatus.ERROR
        healthy = state == HealthStatus.OK and inference == HealthStatus.OK
        return {DHTTP.STATUS: HealthStatus.OK if healthy else HealthStatus.ERROR,
                DHTTP.COMPONENTS: {DNetwork.HTTP: state, DNetwork.LLM: inference}}


def main(argv=None) -> int:
    localizer = Localizer(Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument("--locale")
    initial, _ = preliminary.parse_known_args(argv)
    locale = localizer.select(explicit=initial.locale)

    def text(key, **values):
        return localizer.text(key, locale=locale, **values)

    parser = argparse.ArgumentParser(description=text(DText.SERVER_DESCRIPTION))
    parser.add_argument("--host", help=text(DText.CLI_HOST))
    parser.add_argument("--port", type=int, help=text(DText.CLI_PORT))
    parser.add_argument("--config", type=Path, help=text(
        DText.CLI_CONFIG, path=Path(DLlamaSrv.BASE_DIR) / DNetwork.CONFIG_FILE))
    parser.add_argument("--locale", help=text(DText.CLI_LOCALE))
    args = parser.parse_args(argv)
    try:
        configuration = Configuration(args.config, localizer=localizer, locale=locale)
        network = Network(configuration)
        address = network.binding(DNetwork.HTTP, host=args.host, port=args.port)
    except ValueError as error:
        parser.error(str(error))

    def stop(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, stop)
    try:
        with LlamaSrvServer(address, llama=Llama(configuration)) as server:
            print(text(DText.SERVER_READY, host=server.server_address[0],
                       port=server.server_port), flush=True)
            server.serve_forever(poll_interval=DHTTP.POLL_INTERVAL)
    except KeyboardInterrupt:
        print(text(DText.SERVER_STOPPED), flush=True)
    except OSError as error:
        logging.error(text(DText.SERVER_FAILED, error=error))
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
