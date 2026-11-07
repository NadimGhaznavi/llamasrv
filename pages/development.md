---
title: "Development setup"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-development
---

The canonical Python application name is `LlamaSrv`, its package is `llamasrv`,
and its CMDB subtype is `Application`. The repository contains the application
scaffold and documentation. Service management and the web interface are the
next implementation work.

## Scaffold

| Location | Purpose |
| --- | --- |
| `AGENTS.md` | Project engineering instructions and authorization boundaries |
| `.agents/skills/` | Project-local BMForge contracts, templates, and references |
| `.agents/bmforge/lock.json` | Pinned revisions and integrity hashes |
| `llamasrv/constants/DLlamaSrv.py` | Literal version, CMDB identity, and installation base directory |
| `scripts/check-cmdb.py` | Read-only validation of the application metadata |
| `scripts/new-release.sh` | Standard BMForge release publication workflow |
| `scripts/install.py` | Shared installation lifecycle template |
| `scripts/install.sh`, `scripts/upgrade.sh`, `scripts/uninstall.sh` | Executable lifecycle entry points |

The initial version is `0.0.0`, with codename `Initial development` and
installation base directory `/opt/prod/llamasrv`. Persistent components,
databases, and network listeners are empty until implemented and declared.

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
bash -n scripts/new-release.sh scripts/install.sh scripts/upgrade.sh scripts/uninstall.sh
scripts/new-release.sh --help
scripts/install.sh --help
scripts/upgrade.sh --help
scripts/uninstall.sh --help
```

The BMForge check compares installed hashes against the clean local cache and
does not fetch or upgrade skills. `verify --project .` verifies local integrity
without Git or an upstream comparison.

## Continue application development

Read the pinned project skill and each selected component's specification.
Put use-case orchestration in `activity/`, external-system bridges in
`interface/`, and domain values in `entity/` as implementations require them.
Keep HTTP transport in `server/` and stable identifiers in `constants/`.
Create packages when they have a responsibility to implement.

Before implementing the UI, adapt the pinned localization assets with the
application's actual English message keys. The HTTP component uses Python's
standard-library server, Jinja2 for HTML, and application-owned CSS and browser
JavaScript. Declare actual listeners and configuration when those are selected.

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
