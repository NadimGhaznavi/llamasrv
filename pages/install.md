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

LlamaSrv runs two independent systemd services: a browser control panel and a `llama-server` inference process.

For a host that does not yet have llama.cpp or a model, follow the [Environment Setup guide]({{ site.baseurl }}{% link pages/environment-setup.md %}) first.

## Requirements

On the Linux host where LlamaSrv will run, you need:

- Python 3.11 or newer with `venv`/`ensurepip`, systemd, sudo, and standard Linux account tools.
- An executable llama.cpp server at `/opt/prod/llama.cpp/bin/llama-server`.
- A readable model at `/opt/prod/models/Qwen3.5-4B-Q4_K_M.gguf` and its vision projector at `/opt/prod/models/mmproj-Qwen3.5-4B-F16.gguf`.
- Access to the Python dependencies listed in `requirements.txt` (online or through an offline wheel source).

The first installation checks for these default files. Once installed, you can select another provisioned model or change the binary path. LlamaSrv does not download models or build llama.cpp.

## Install

Clone the repository on the target host, outside `/opt/prod/llamasrv`:

```sh
git clone https://github.com/NadimGhaznavi/llamasrv.git
cd llamasrv
./scripts/install.sh --check
sudo ./scripts/install.sh
```

The check validates prerequisites without changing files. Installation starts inference first, then the control panel, and waits for both services to become ready.

## What gets installed

| Location | Purpose |
| --- | --- |
| `/opt/prod/llamasrv/` | Application code, scripts, templates, and requirements |
| `/opt/prod/llamasrv/.venv/` | Python runtime dependencies |
| `/opt/prod/llamasrv/conf/llamasrv.json` | Persistent configuration |
| `/etc/systemd/system/llamasrv-llm.service` | Inference server, port `51001` |
| `/etc/systemd/system/llamasrv-http.service` | Web control panel, port `51000` |
| `/etc/sudoers.d/llamasrv` | Restricted permission to start/stop these services |
| `llamasrv` system account | Runs both services |

LlamaSrv also tracks its managed files and last successful deployment version. External models and the llama.cpp executable remain untouched.

## First run

Open `http://HOST:51000/` in a browser and confirm the service status. From the host:

```sh
curl --fail http://127.0.0.1:51000/health
curl --fail http://127.0.0.1:51001/health
```

**Security:** Both listeners bind to `0.0.0.0` by default. The control panel has no login, so restrict port `51000` to trusted hosts. Anyone who can reach it can change settings and restart inference.

Next: [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %}), [Upgrade]({{ site.baseurl }}{% link pages/upgrade.md %}), or [Uninstall]({{ site.baseurl }}{% link pages/uninstall.md %}).

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
