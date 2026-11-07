"""Bridge validated application settings to llama.cpp's process and health API."""

from http.client import HTTPConnection, HTTPException
import json
import logging
import os
from pathlib import Path

from llamasrv.constants.DHTTP import DHTTP, HealthStatus
from llamasrv.constants.DLlama import DLlama
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DText import DText
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Network import Network


def probe(host: str, port: int, *, components: tuple[str, ...] = ()) -> bool:
    """One bounded, read-only readiness request; never retry or repair."""
    connection = HTTPConnection(host, port, timeout=DLlama.HEALTH_TIMEOUT)
    try:
        connection.request("GET", DHTTP.HEALTH)
        response = connection.getresponse()
        body = response.read(DLlama.HEALTH_RESPONSE_LIMIT + 1)
        if response.status != 200 or len(body) > DLlama.HEALTH_RESPONSE_LIMIT:
            return False
        value = json.loads(body)
        if not isinstance(value, dict) or value.get(DHTTP.STATUS) != HealthStatus.OK:
            return False
        states = value.get(DHTTP.COMPONENTS, {})
        return isinstance(states, dict) and all(states.get(use) == HealthStatus.OK for use in components)
    except (OSError, HTTPException, ValueError) as error:
        logging.warning("health_probe_failed host=%s port=%s error=%s", host, port, error)
        return False
    finally:
        connection.close()


class Llama:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def files(self) -> tuple[Path, Path, Path | None]:
        settings = self.configuration.llama
        directory = Path(settings[DLlama.MODEL_DIR])
        projector = settings[DLlama.MMPROJ]
        return (Path(settings[DLlama.BINARY]), directory / settings[DLlama.MODEL],
                None if projector is None else directory / projector)

    def validate_files(self) -> None:
        binary, model, projector = self.files()
        # External prerequisites may legitimately be symlinks, as on wintermute.
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError(self.configuration.localizer.text(
                DText.LLAMA_BINARY_MISSING, locale=self.configuration.locale, path=binary))
        for artifact in (model, projector):
            if artifact is not None and (not artifact.is_file() or not os.access(artifact, os.R_OK)):
                raise ValueError(self.configuration.localizer.text(
                    DText.LLAMA_MODEL_MISSING, locale=self.configuration.locale, path=artifact))

    def command(self) -> list[str]:
        binary, model, projector = self.files()
        settings = self.configuration.llama
        host, port = Network(self.configuration).binding(DNetwork.LLM)
        arguments = [str(binary), DLlama.MODEL_OPTION, str(model)]
        if projector is not None:
            arguments.extend((DLlama.MMPROJ_OPTION, str(projector)))
        arguments.extend((DLlama.CONTEXT_OPTION, str(settings[DLlama.CONTEXT_SIZE]),
                          DLlama.HOST_OPTION, host, DLlama.PORT_OPTION, str(port)))
        for key, option in ((DLlama.METRICS, DLlama.METRICS_OPTION),
                            (DLlama.JINJA, DLlama.JINJA_OPTION)):
            if settings[key]:
                arguments.append(option)
        return arguments

    def health(self) -> bool:
        return probe(*Network(self.configuration).destination(DNetwork.LLM))

    def launch(self) -> None:
        self.validate_files()
        arguments = self.command()
        os.execv(arguments[0], arguments)
