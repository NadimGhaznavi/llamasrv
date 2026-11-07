---
title: "Project Structure"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-development
---

LlamaSrv is a Python application with two independent systemd services. The HTTP service provides the control panel. The inference service launches the external `llama-server` executable. Both read the same JSON configuration.

## Repository layout

| Location | Purpose |
| --- | --- |
| `llamasrv/constants/` | Project settings, model defaults, listener ports, and service names |
| `llamasrv/interface/` | Configuration validation, llama.cpp integration, and systemd operations |
| `llamasrv/activity/` | Launch and service-control workflows |
| `llamasrv/server/` | HTTP API, control-panel templates, JavaScript, and CSS |
| `llamasrv/locales/` | Interface strings and translations |
| `scripts/` | Installation, upgrade, uninstall, and service helpers |
| `systemd/` | Unit templates and restricted sudoers policy |
| `tests/` | Configuration, HTTP, process, and installation tests |
| `pages/` | Website and user documentation |

For example, `Configuration.py` validates settings, `RunLlama.py` launches the selected model, and `ControlPanel.py` handles browser-driven configuration and restart operations.

The installed application lives in `/opt/prod/llamasrv`. The llama.cpp binary and model files stay outside the application so other projects can use the same inference endpoint without depending on LlamaSrv's implementation.

## Local development

Use Python 3.11 or newer. A GPU is not required for the automated tests:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Deployment tests also expect Linux tools such as Bash, `systemd-analyze`, and `visudo`; service operations are simulated. The project uses pinned BMForge skills in `.agents/` for its development conventions.

For deployment instructions, see [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}).

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
