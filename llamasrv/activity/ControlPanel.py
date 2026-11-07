"""Coordinate saved settings and the installed inference-service restart."""

from threading import Lock

from llamasrv.constants.DControl import DControl
from llamasrv.constants.DLlama import DLlama
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DText import DText
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import Llama
from llamasrv.interface.Services import Services


class ControlPanel:
    def __init__(self, configuration: Configuration, *, services: Services | None = None):
        self.configuration = configuration
        self.services = services if services is not None else Services()
        self.lock = Lock()

    def read(self, locale: str) -> Configuration:
        return Configuration(self.configuration.path, localizer=self.configuration.localizer,
                             locale=locale)

    def snapshot(self, locale: str) -> dict:
        configuration = self.read(locale)
        models, projectors = Llama(configuration).available_files()
        settings = {key: configuration.llama[key] for key in (
            DLlama.MODEL, DLlama.MMPROJ, DLlama.CONTEXT_SIZE, DLlama.METRICS, DLlama.JINJA)}
        settings.update({DControl.HTTP_PORT: configuration.network[DNetwork.HTTP][1],
                         DControl.LLM_PORT: configuration.network[DNetwork.LLM][1]})
        return {DControl.SETTINGS: settings, DControl.MODELS: models,
                DControl.PROJECTORS: projectors}

    def update(self, values: dict, locale: str) -> None:
        with self.lock:
            configuration = self.read(locale)
            expected = {DControl.HTTP_PORT, DControl.LLM_PORT, DLlama.MODEL, DLlama.MMPROJ,
                        DLlama.CONTEXT_SIZE, DLlama.METRICS, DLlama.JINJA}
            if set(values) != expected:
                raise ValueError(configuration.text(DText.UI_INVALID_SETTINGS))
            models, projectors = Llama(configuration).available_files()
            for key, available in ((DLlama.MODEL, models), (DLlama.MMPROJ, projectors)):
                if values[key] != configuration.llama[key] and not (
                        key == DLlama.MMPROJ and values[key] is None):
                    if not isinstance(values[key], str) or values[key] not in available:
                        raise ValueError(configuration.text(DText.UI_UNKNOWN_MODEL))
            candidate = configuration.as_dict()
            for use, key in ((DNetwork.HTTP, DControl.HTTP_PORT), (DNetwork.LLM, DControl.LLM_PORT)):
                candidate[DNetwork.NETWORK][use][DNetwork.PORT] = values[key]
            candidate[DLlama.SECTION].update({key: values[key] for key in expected
                                             if key not in (DControl.HTTP_PORT, DControl.LLM_PORT)})
            configuration.resolve(candidate)
            http_host, http_port = configuration.network[DNetwork.HTTP]
            llm_host, llm_port = configuration.network[DNetwork.LLM]
            if http_port == llm_port and (http_host == llm_host or DNetwork.WILDCARD in (
                    http_host, llm_host)):
                raise ValueError(configuration.text(DText.UI_PORT_CONFLICT))
            Llama(configuration).validate_files()
            configuration.save()

    def restart(self, locale: str) -> None:
        with self.lock:
            configuration = self.read(locale)
            Llama(configuration).validate_files()
            self.services.restart_llm()
