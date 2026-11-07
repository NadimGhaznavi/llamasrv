#!/usr/bin/env bash
# Provision and deploy the project from a separate source checkout.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec /usr/bin/python3 -B -m scripts.install install "$@"
