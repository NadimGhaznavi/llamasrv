---
title: "Install LlamaSrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-installation
---

For a first installation, [prepare the host]({{ site.baseurl }}{% link pages/environment-setup.md %})
and [install the default 4B model]({{ site.baseurl }}{% link pages/models.md %}).
The installer checks for these files:

- `/opt/prod/llama.cpp/bin/llama-server`
- `/opt/prod/models/Qwen3.5-4B-Q4_K_M.gguf`
- `/opt/prod/models/mmproj-Qwen3.5-4B-F16.gguf`

## Install

Run on the target host with systemd, sudo, and Python 3.11+ with venv. The
installer needs access to the Python packages in `requirements.txt`.

If you already have the checkout, start at `cd`.

```sh
sudo install -d /opt/dev
sudo install -d -o "$(id -un)" -g "$(id -gn)" /opt/dev/llamasrv
git clone https://github.com/NadimGhaznavi/llamasrv.git /opt/dev/llamasrv
cd /opt/dev/llamasrv
./scripts/install.sh --check
sudo ./scripts/install.sh
```

The installer deploys to `/opt/prod/llamasrv`, creates its runtime venv and
`conf/llamasrv.json`, then starts the inference and control-panel services.

## Verify

```sh
curl -fsS http://127.0.0.1:51000/health
curl -fsS http://127.0.0.1:51001/health
```

Open `http://HOST:51000/` to manage LlamaSrv. Both services bind to all IPv4
interfaces by default. Restrict port `51000` to trusted hosts because the
control panel has no login.

[Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
