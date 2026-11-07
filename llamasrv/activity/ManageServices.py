"""Run the two installed services sequentially, without dependency machinery."""

import argparse
import os
from pathlib import Path
import subprocess

from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DText import DText
from llamasrv.interface.Localizer import Localizer
from llamasrv.interface.Services import Services


def main(argv=None) -> int:
    localizer = Localizer(Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)
    parser = argparse.ArgumentParser(description=localizer.text(DText.SERVICES_DESCRIPTION))
    parser.add_argument("action", choices=("start", "stop"),
                        help=localizer.text(DText.SERVICES_ACTION))
    args = parser.parse_args(argv)
    if os.geteuid() != 0:
        parser.exit(1, localizer.text(DText.SERVICES_ROOT) + "\n")
    try:
        services = Services()
        if args.action == "start":
            services.start()
        else:
            services.stop()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, localizer.text(DText.SERVICES_FAILED, error=error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
