---
title: "Install, Upgrade, Uninstall"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-installation
---

LlamaSrv runs two independent systemd services on one Linux host:

| Service | Responsibility | Default listener |
| --- | --- | --- |
| `llamasrv-llm.service` | llama.cpp inference with one selected model | `0.0.0.0:51001` |
| `llamasrv-http.service` | Browser control panel, configuration and aggregate readiness | `0.0.0.0:51000` |

## Target prerequisites

Development and CPU-only tests run on sally. The initial deployment target is
wintermute, which supplies the GPU and software stack. The application requires
Python 3.11 or newer with venv/ensurepip support, systemd, `systemd-analyze`,
`getent`, `useradd`, `runuser`, `chown`, `/usr/bin/sudo` and `/usr/sbin/visudo`.
The installer deploys the pinned Jinja2/MarkupSafe requirements into
`/opt/prod/llamasrv/.venv`. Both services and the installed service helper use
that environment and the installed application directory. Python package
installation needs access to the pinned requirements, via a package index or
an operator-configured offline wheel source.

The following externally managed files must already be installed:

- `/opt/prod/llama.cpp/bin/llama-server`, executable by the service account.
- `/opt/prod/models/Qwen3.5-4B-Q4_K_M.gguf`, readable by the service account.
- `/opt/prod/models/mmproj-Qwen3.5-4B-F16.gguf`, readable by the service account.

The installer and launcher fail with the affected path if a required file is
missing or unusable. Symlinks in these external paths are supported. Their
download, conversion, compilation, CUDA configuration and ownership are outside
LlamaSrv's scope; installation and removal never manage those directories.
The application-owned directory `/opt/prod/llamasrv` must be a real directory.

## Install and update

The operator manages Git and release operations. From the checkout on
wintermute, the normal operator workflow is:

```sh
git pull
sudo ./scripts/install.sh
```

`install.sh` supports a first installation and repeated installation. It
validates prerequisites and settings, verifies rendered unit syntax, creates
the dedicated `llamasrv` system account if absent, installs application files,
installs `/etc/sudoers.d/llamasrv`, enables both services and starts inference
followed by HTTP. Startup must become
healthy within 120 seconds before `.deployment-version` records success.

For an explicit upgrade of an existing installation:

```sh
sudo ./scripts/upgrade.sh
```

Before either operation, use `--check` to validate without writing files,
creating accounts, or stopping/starting services:

```sh
./scripts/install.sh --check
./scripts/upgrade.sh --check
```

These checks use the same configuration and file checks as the real operation.
They cannot prove service-account access on a first installation or validate
GPU inference. The real operation also checks the deployed launcher as the
service account and verifies both services through aggregate HTTP readiness.
All three lifecycle scripts support `--help` without privilege.

## Runtime settings

The installer creates `/opt/prod/llamasrv/conf/llamasrv.json` from application
constants only when the file is absent. Reinstallation and upgrades preserve
an existing file byte for byte. `DLlamaSrv.CMDB_NETWORK` owns listener defaults;
`DLlama` and `DQwen` own llama.cpp and default-model settings.

```json
{
  "network": {
    "http": {"interface": "0.0.0.0", "port": 51000},
    "llm": {"interface": "0.0.0.0", "port": 51001}
  },
  "llama": {
    "binary": "/opt/prod/llama.cpp/bin/llama-server",
    "model_dir": "/opt/prod/models",
    "model": "Qwen3.5-4B-Q4_K_M.gguf",
    "mmproj": "mmproj-Qwen3.5-4B-F16.gguf",
    "context_size": 12288,
    "metrics": true,
    "jinja": true
  }
}
```

Omitted fields use constant defaults. Unknown fields, malformed JSON, invalid
IPv4 addresses, ports outside 1–65535, nonpositive context sizes and incorrect
types are fatal configuration errors. `binary` and `model_dir` must be absolute
paths. Model and projector names resolve against `model_dir`; absolute artifact
paths are also accepted. Set `mmproj` to JSON `null` for a model without a vision
projector. Changing `model` selects another already-provisioned GGUF; only one
model is loaded by this service at a time. No shell evaluates configured paths.

`jinja` selects llama.cpp's Jinja chat-template engine for formatting messages
and tool definitions into the model's prompt. It passes `--jinja` when true and
`--no-jinja` when false, independently of the binary's default. This does not
require the Python Jinja2 package. `metrics` enables llama.cpp's Prometheus-format
`/metrics` endpoint on the inference port, including token throughput and active
or deferred request counts. It does not install a monitoring collector.

Settings are read at each process start. After editing, either rerun the
installer, which validates before stopping the existing services, or run:

```sh
sudo ./scripts/services stop
sudo ./scripts/services start
```

The helper runs installed code. It stops HTTP before inference and starts
inference before HTTP. It has no dependency discovery or readiness wait. The
systemd units themselves have no dependency on ax3l services.

## Browser control panel

Open `http://HOST:51000/` to edit listener ports, context size, metrics, Jinja,
the provisioned GGUF model and its optional vision projector. The model list
comes from `model_dir`; the panel does not download model files. **Update**
validates settings and external files, then saves the JSON atomically. It does
not restart either service. **Restart LLM** asks for confirmation and runs the
saved inference settings through sequential noninteractive stop/start commands.
Unsaved edits disable restart until saved or discarded by reloading the page.
Changing the control-panel port requires a separate HTTP-service restart; the
browser displays a reminder and continues using the current listener.

The installer makes `conf/` and its JSON file writable by `llamasrv`; installed
code and privileged policy stay root-owned. `/etc/sudoers.d/llamasrv` is mode
`0440` and grants the `llamasrv` account passwordless access to only these commands:

```sh
/usr/bin/systemctl stop llamasrv-http.service
/usr/bin/systemctl start llamasrv-http.service
/usr/bin/systemctl stop llamasrv-llm.service
/usr/bin/systemctl start llamasrv-llm.service
```

There are no command wildcards or general sudo grants. The HTTP unit allows
setuid execution for `sudo` (`NoNewPrivileges=false`); inference keeps
`NoNewPrivileges=true`. Both retain filesystem hardening, with only `conf/`
writable by HTTP. `visudo` checks the policy before any service changes, and
installation refuses an existing policy that the manifest does not own.
The application has no login screen; access to the control-panel listener grants
configuration and inference-restart control. Bind its HTTP interface to the
intended trusted network.

Status checks real readiness every five seconds while the page is visible.
The displayed timestamp uses server-local time and identifies its timezone.
Machine-readable service information is available at `/api`; `/health` keeps
its existing readiness response.

## Verify and diagnose

```sh
curl --fail http://127.0.0.1:51000/health
curl --fail http://127.0.0.1:51001/health
curl --fail http://127.0.0.1:51001/props
journalctl -u llamasrv-llm.service -u llamasrv-http.service
```

Aggregate health returns HTTP 200 with
`{"status":"ok","components":{"http":"ok","llm":"ok"}}` only when inference
reports ready. A loading, unreachable or failed LLM produces HTTP 503 and an
`llm` error. Probes are bounded and read-only; they do not restart services.
Inspect `/props` on the real target to verify the expected vision capability.

Failed installation or upgrade does not advance the last-successful version
marker or claim success. File replacement is not a whole-installation rollback:
an interrupted operation can leave new files or stopped services. Inspect the
reported error and journal, correct the prerequisite or setting, and rerun
`install.sh`. Ownership records allow retry and removal of partial installs.

## Uninstall

```sh
sudo ./scripts/uninstall.sh
```

Removal stops HTTP then inference, disables and removes only application-owned
units, removes its manifest-owned `/etc/sudoers.d/llamasrv` policy and virtual
environment, and removes managed code and the successful-version marker. Runtime
configuration, unowned files, external binaries/models and the system account
are retained. An ownership record remains with retained state so repeated
uninstall and later reinstall are safe. No data purge is performed.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
