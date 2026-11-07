---
title: "Project Structure"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-development
---

LlamaSrv has two independent processes. The HTTP service manages configuration and systemd controls; the inference service launches llama.cpp with the selected model. Applications connect directly to the inference endpoint, without going through the web interface.

## Application structure

| Location | Purpose |
| --- | --- |
| `llamasrv/constants/DLlamaSrv.py` | Project identity, installation path, and default ports |
| `llamasrv/constants/DLlama.py`, `DQwen.py`, `DService.py` | Inference settings, default model, and systemd names |
| `llamasrv/interface/Configuration.py` | Load and validate persistent JSON settings |
| `llamasrv/interface/Network.py` | Resolve listener and client addresses |
| `llamasrv/interface/Llama.py` | Build the llama.cpp command and check readiness |
| `llamasrv/interface/Services.py` | Start, stop, install, and check systemd services |
| `llamasrv/activity/RunLlama.py` | Launch the selected model |
| `llamasrv/activity/ManageServices.py` | Control both installed services |
| `llamasrv/activity/ControlPanel.py` | Save browser settings and restart inference |
| `llamasrv/server/` | HTTP endpoints, control-panel templates, and static assets |
| `llamasrv/locales/` | Interface text and translations |
| `systemd/` | Unit templates and restricted sudoers policy |
| `scripts/` | Install, upgrade, uninstall, and helper commands |
| `tests/` | Configuration, HTTP, runtime, and deployment tests |
| `pages/` | Website and user documentation |

The installed code and JSON configuration live in `/opt/prod/llamasrv`. The llama.cpp binary and models remain external, so the service can be shared with applications such as R3el and ND3G.

## Local development

Use Python 3.11 or newer. Automated tests do not require a GPU:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Installation tests also expect Linux tools such as Bash, `systemd-analyze`, and `visudo`; they simulate systemd operations. Engineering conventions are pinned under `.agents/` using BMForge skills.

For deployment, see [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}).

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
