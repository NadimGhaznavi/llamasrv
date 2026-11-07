"""Validate configuration and replace this process with the selected llama-server."""

import argparse
from pathlib import Path

from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DText import DText
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Llama import Llama
from llamasrv.interface.Localizer import Localizer


def main(argv=None) -> int:
    localizer = Localizer(Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument("--locale")
    initial, _ = preliminary.parse_known_args(argv)
    locale = localizer.select(explicit=initial.locale)

    def text(key, **values):
        return localizer.text(key, locale=locale, **values)

    parser = argparse.ArgumentParser(description=text(DText.LLAMA_DESCRIPTION))
    parser.add_argument("--config", type=Path, help=text(
        DText.CLI_CONFIG, path=Path(DLlamaSrv.BASE_DIR) / DNetwork.CONFIG_FILE))
    parser.add_argument("--check", action="store_true", help=text(DText.LLAMA_CHECK))
    parser.add_argument("--locale", help=text(DText.CLI_LOCALE))
    args = parser.parse_args(argv)
    try:
        llama = Llama(Configuration(args.config, localizer=localizer, locale=locale))
        if args.check:
            llama.validate_files()
            print(text(DText.LLAMA_VALID))
        else:
            llama.launch()
    except (OSError, ValueError) as error:
        parser.exit(1, text(DText.LLAMA_FAILED, error=error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
