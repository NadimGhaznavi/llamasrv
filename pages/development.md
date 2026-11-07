---
title: "Development setup"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-development
---

Develop on sally using Python 3.11 or newer. Sally has no GPU or inference
software stack. Wintermute supplies the GPU, llama.cpp and model artifacts;
production inspection is read-only. Git operations, releases and production
installation are performed by the operator.

## Application structure

| Location | Responsibility |
| --- | --- |
| `llamasrv/constants/DLlamaSrv.py` | Identity, literal version, CMDB listeners and owned configuration directory |
| `llamasrv/constants/DLlama.py`, `DQwen.py`, `DService.py` | Launch settings, model defaults and service resource names |
| `llamasrv/interface/Configuration.py` | Shared JSON/default resolution and validation |
| `llamasrv/interface/Network.py` | Listener bindings and local client destinations |
| `llamasrv/interface/Llama.py` | External-file checks, command arguments, process replacement and readiness |
| `llamasrv/interface/Services.py` | Application-owned systemd operations and installation readiness |
| `llamasrv/activity/RunLlama.py` | Launcher CLI orchestration |
| `llamasrv/activity/ManageServices.py` | Sequential start/stop commands |
| `llamasrv/activity/ControlPanel.py` | Settings-update and inference-restart orchestration |
| `llamasrv/server/` | Threaded HTTP listener, Jinja2 templates, static assets and aggregate `/health` |
| `llamasrv/interface/Localizer.py`, `llamasrv/locales/en.json` | Pinned localizer and English source catalogue |
| `systemd/` | Separate HTTP/inference unit templates and the narrowly scoped sudoers policy |
| `scripts/install.py` | Shared install/reinstall/upgrade/uninstall lifecycle |
| `scripts/services` | Installed-service control entry point |
| `tests/` | Configuration, HTTP, process, failure and lifecycle checks |

Default bindings are `0.0.0.0:51000` for HTTP and `0.0.0.0:51001` for inference.
The application owns `/opt/prod/llamasrv`; external llama.cpp and model storage
remain prerequisites. See [installation and runtime configuration]({{ site.baseurl }}{% link pages/installation.md %})
for settings and target-machine operation.

## Pinned engineering contracts

The baseline remains pinned at BMForge revision
`29a100c39997349ecfd40e190319aeb5018ffab8`:

| Skill | Specification |
| --- | --- |
| `bmforge-project` | `0.1.0` |
| `bmforge-constants` | `0.1.0` |
| `bmforge-localization` | `0.1.0` |
| `bmforge-installation` | `0.1.3` |
| `bmforge-http` | `0.5.1` |
| `bmforge-github-pages` | `0.1.0` |

These are project-owned instruction snapshots, not runtime imports. Read
`AGENTS.md` and the selected specifications before editing. Updates require
explicit authorization. Run the offline update check before BMForge-derived
edits, or use local verification when Git commands are prohibited:

```sh
python3 -B .agents/bmforge/manage.py check --project .
python3 -B .agents/bmforge/manage.py verify --project .
```

The check compares a clean local cache without fetching or updating anything.
Verification checks local hashes without Git or an upstream comparison.

## Verify locally

Install the pinned Jinja2 requirements in a development virtual environment.
The suite also needs Bash, `systemd-analyze`, `/usr/sbin/visudo`, Python venv/pip
support, local loopback socket access and normal Linux account-tool executables
for prerequisite discovery. Installation tests simulate account, ownership and
systemctl operations; sudo commands never control real services.

```sh
python3 -B scripts/check-cmdb.py llamasrv/constants/DLlamaSrv.py --name LlamaSrv
python3 -B -m unittest discover -s tests -v
bash -n scripts/install.sh scripts/upgrade.sh scripts/uninstall.sh scripts/services
./scripts/install.sh --help
./scripts/upgrade.sh --help
./scripts/uninstall.sh --help
```

Installation tests use disposable directories, simulated systemd/account
operations and real installed Python processes and isolated virtual environments.
They package the locally installed Jinja2 and MarkupSafe Python sources into
temporary wheels, so dependency installation tests run offline. A CPU-only HTTP fixture
stands in for llama-server; no model is downloaded and no GPU libraries are
required. Coverage includes missing prerequisites, JSON validation, argument
boundaries, health failure/recovery, signals, preserved configuration, repeated
installation/removal, deployment without the checkout, and version markers after
failed activation. These tests do not validate GPU inference or real systemd
activation on wintermute.

## Run individual processes

Start HTTP from the checkout:

```sh
.venv/bin/python -B -m llamasrv
```

It binds to port 51000, serves the control panel at `/`, service information at
`/api`, and reports HTTP 503
from `/health` when no configured LLM is ready. Requests have a bounded read
timeout; SIGTERM and Ctrl+C stop the listener and join request workers.

For explicit development settings, use `--config PATH`; HTTP also accepts
`--host` and `--port` invocation overrides. A missing config uses constants
without creating a file. Both services validate the entire configuration at
startup. The browser reloads saved configuration for each view and mutation;
health probes use the saved inference destination. Listener and inference-process
settings take effect when the corresponding process is restarted.

On a machine with the required external artifacts, validate or launch inference:

```sh
python3 -B -m llamasrv.activity.RunLlama --config /path/to/llamasrv.json --check
python3 -B -m llamasrv.activity.RunLlama --config /path/to/llamasrv.json
```

The launcher replaces itself with llama-server, preserving its PID and native
signal handling under systemd. Human-facing CLI messages use `DText` keys and
the English catalogue. The browser uses the same catalogue with request-scoped
`?lang=` and `Accept-Language` selection; only English is currently published.

## Continue development

Keep orchestration in `activity/`, external bridges in `interface/`, data in
`entity/` when needed, transport in `server/`, and stable identifiers in
`constants/`. The browser reuses configuration validation and installed-service
controls. It uses pinned Jinja2 with autoescaping, plain JavaScript and CSS,
without a frontend build step. Static file access uses an explicit allowlist;
JSON mutations are bounded and reject cross-origin browser requests.

Every logical change updates the single `Unreleased` changelog and its Summary.
Application versions and codenames are assigned by the operator's release
process. Preserve the existing `main`, `dev` and `feat/maint-0.1.0`
branches and attached BMForge mode. Do not run bootstrap branch setup, Git
mutations, release tooling or production deployment without separate explicit
authorization. The lifecycle implementation is enabled, but it does not perform
Git operations or create a release.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
