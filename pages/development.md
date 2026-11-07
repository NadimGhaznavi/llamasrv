---
title: "Development setup"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-development
---

The canonical Python application name is `LlamaSrv`, its package is `llamasrv`,
and its CMDB subtype is `Application`. The repository contains the application
scaffold, documentation, and a standard-library HTTP server. llama-server service
management and the browser interface remain future implementation work.

## Scaffold

| Location | Purpose |
| --- | --- |
| `AGENTS.md` | Project engineering instructions and authorization boundaries |
| `.agents/skills/` | Project-local BMForge contracts, templates, and references |
| `.agents/bmforge/lock.json` | Pinned revisions and integrity hashes |
| `llamasrv/constants/DLlamaSrv.py` | Literal version, CMDB identity, and installation base directory |
| `llamasrv/server/` | Threaded HTTP listener, JSON routes, and CLI startup |
| `llamasrv/interface/Network.py` | Validated listener defaults and configuration overrides |
| `llamasrv/interface/Localizer.py`, `llamasrv/locales/en.json` | English source catalogue and locale selection |
| `tests/` | HTTP, lifecycle, and configuration acceptance checks |
| `scripts/check-cmdb.py` | Read-only validation of the application metadata |
| `scripts/new-release.sh` | Standard BMForge release publication workflow |
| `scripts/install.py` | Shared installation lifecycle template |
| `scripts/install.sh`, `scripts/upgrade.sh`, `scripts/uninstall.sh` | Executable lifecycle entry points |

The initial version is `0.0.0`, with codename `Initial development` and
installation base directory `/opt/prod/llamasrv`. The declared HTTP listener is
`0.0.0.0:51000`; persistent components and databases are not yet used.

The baseline is pinned from BMForge revision
`29a100c39997349ecfd40e190319aeb5018ffab8`:

| Skill | Specification | Purpose |
| --- | --- | --- |
| `bmforge-project` | `0.1.0` | Engineering, architecture, and changelog discipline |
| `bmforge-constants` | `0.1.0` | Typed identifiers and application metadata |
| `bmforge-localization` | `0.1.0` | English message catalogues and request-local language selection |
| `bmforge-installation` | `0.1.3` | Owned install, upgrade, and uninstall lifecycle |
| `bmforge-http` | `0.5.1` | Application HTTP UI/API and health endpoint |
| `bmforge-github-pages` | `0.1.0` | Static project documentation |

These skills provide instructions and application-owned reference templates.
The application has no runtime dependency on BMForge.

## Verify the scaffold

Use Python 3.11 or newer for application development. The scaffold checks need
only Python's standard library, Bash, and Git. From the repository root:

```sh
python3 .agents/bmforge/manage.py check --project .
python3 -B scripts/check-cmdb.py llamasrv/constants/DLlamaSrv.py --name LlamaSrv
python3 -B -m unittest discover -s tests -v
bash -n scripts/new-release.sh scripts/install.sh scripts/upgrade.sh scripts/uninstall.sh
scripts/new-release.sh --help
scripts/install.sh --help
scripts/upgrade.sh --help
scripts/uninstall.sh --help
```

The BMForge check compares installed hashes against the clean local cache and
does not fetch or upgrade skills. `verify --project .` verifies local integrity
without Git or an upstream comparison.

## Run the HTTP server

From the repository root, run:

```sh
python3 -B -m llamasrv
```

The default listener is `0.0.0.0:51000`, covering all IPv4 interfaces. Use a
server IP address to connect remotely. For a local check:

```sh
curl http://127.0.0.1:51000/
curl http://127.0.0.1:51000/health
```

`GET /` returns the application name, version, and health URL. `GET /health`
returns `{"status":"ok","components":{"http":"ok"}}` while the HTTP
component is usable, or HTTP 503 with the failed component identified. HTTP is
currently the only component; this does not check an unimplemented llama-server
service. Both routes support `HEAD`. Unknown routes return 404 and mutation
methods on known routes return 405. No browser UI or additional Python package
is needed for this stage.

Ctrl+C and SIGTERM stop the listener and join request workers. Request sockets
have a five-second timeout so idle clients cannot hold shutdown indefinitely.
A failed bind exits with an error before reporting that the listener is ready.

### Listener configuration

The single source of listener defaults is `DLlamaSrv.CMDB_NETWORK`. Startup
reads optional overrides from `/opt/prod/llamasrv/conf/llamasrv.json`, regardless
of the caller's working directory. For example:

```json
{
  "network": {
    "http": {
      "interface": "0.0.0.0",
      "port": 51000
    }
  }
}
```

The root and `network` values must be JSON objects. The only supported role is
`http`, with optional `interface` (numeric IPv4 string) and `port` (integer from
1 to 65535). A missing file or omitted settings use CMDB defaults. Explicit
values remain deployment choices even if a later release changes defaults.
Malformed JSON, unknown keys, incorrect types, and unreadable files fail startup.

`--host` and `--port` override the validated configuration for one invocation.
`--config PATH` selects another JSON file for development or testing:

```sh
python3 -B -m llamasrv --config /tmp/llamasrv.json --host 0.0.0.0 --port 51000
```

Configuration is resolved once at startup; restart the process after edits.
The JSON describes persistent deployment choices, while CLI overrides apply
only to the running invocation. `Network.destination("http")` maps wildcard
bindings to `127.0.0.1` for local clients. CLI messages use stable localization
keys and the bundled English catalogue; `--locale` selects a published locale,
falling back to English. No translations are currently published.

## Continue application development

Read the pinned project skill and each selected component's specification.
Put use-case orchestration in `activity/`, external-system bridges in
`interface/`, and domain values in `entity/` as implementations require them.
Keep HTTP transport in `server/` and stable identifiers in `constants/`.
Create packages when they have a responsibility to implement.

When implementing the UI, extend the English catalogue with its actual message
keys. The HTTP component uses Python's
standard-library server, Jinja2 for HTML, and application-owned CSS and browser
JavaScript. The existing HTTP API and CLI require only the Python standard
library. Add required component probes to the existing health endpoint as
dependencies are implemented.

Complete the llama-server service lifecycle, configuration preservation,
startup verification, and all three installation operations before enabling
`DEPLOYMENT_READY` in `scripts/install.py`. The initial value is `False`;
each lifecycle script's `--check` deliberately fails with
`Deployment is not configured` until that work is complete.

## Release preparation

Update the single `Unreleased` changelog section and its summary for every
completed change. Use the existing `main`, `dev`, and `feat/maint-0.1.0`
branches; the repository retains its attached BMForge mode. Running `init` or
`setup-branches` here would conflict with the existing setup.

The release script is prepared for `LlamaSrv` and the `origin`, `dev`, and
`main` workflow. Read the pinned project's release guides before use. Commits,
release publication, and production deployment require separate authorization.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
