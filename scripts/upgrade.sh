#!/usr/bin/env bash
# Upgrade an installation while retaining configuration, credentials, and data.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec /usr/bin/python3 -B -m scripts.install upgrade "$@"
