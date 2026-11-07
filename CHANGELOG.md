---
title: "Changelog"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-changelog
---

# Changelog

All changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Changed

- Rewrote the project documentation for readers: separate install, upgrade and uninstall guides, runtime examples, a clearer installation inventory, and a shorter project-structure page.

## [0.2.0] - 2026-11-07 @ 04:52

### Summary

Manage local inference through a browser control panel, with validated settings,
live readiness and narrowly authorized service restarts. Honor explicit Jinja
disable settings and keep installation tests reliable across releases.

### Added

- Dark, responsive HTTP control panel based on the configuration/status sketch,
  using the project logo, installed GGUF and projector selectors, English message
  keys, atomic settings updates, restart confirmation and live readiness.
- Passwordless start/stop grants for exactly the HTTP and LLM systemd units in
  `/etc/sudoers.d/llamasrv`, validated before installation and tracked for removal
  during uninstall. The LLM restart uses sequential noninteractive stop/start.
- Isolated production Jinja2 runtime and writable service-owned configuration,
  while keeping application code and the sudoers policy owned by root.
- HTTP and offline installation acceptance coverage for configuration validation,
  exact sudo commands, policy ownership/removal and isolated deployed rendering;
  operator documentation for the browser and service permissions.

### Fixed

- Explicitly disable llama.cpp chat templating with `--no-jinja` when runtime
  `jinja` is false; omitting `--jinja` left it enabled on builds such as wintermute's.
- Keep disposable lifecycle-test versions independent of the repository's
  current release metadata.

### Changed

- Updated site logo, again.

## [0.1.0] - 2026-11-07 @ 03:28

### Summary

Run a configurable standalone llama-server on port 51001 alongside LlamaSrv's
HTTP service on port 51000. Defaults match ax3l's Qwen3.5-4B vision setup;
operator-owned runtime settings survive installation and upgrades.

### Added

- Shared, validated runtime configuration for both listeners and the selected
  GGUF model, optional vision projector, context size, metrics and Jinja flags.
- llama-server launcher with fatal checks for missing or unusable external
  binaries and model files, and on-demand inference readiness in `/health`.
- Separate hardened systemd units, sequential service controls, and completed
  install/reinstall/upgrade/uninstall operations with configuration preservation,
  deployed-code checks and readiness-gated successful-version bookkeeping.
- GPU-free process/lifecycle tests and operator documentation for development
  on sally and manual installation on wintermute; Git and release operations
  remain operator-controlled.
- Standard-library threaded HTTP server started with `python3 -m llamasrv`,
  defaulting to `0.0.0.0:51000` from CMDB metadata, with JSON service information,
  `/health`, HEAD support, local-time request logs, bounded request timeouts,
  and graceful shutdown.
- Validated production JSON listener settings and CLI overrides, English CLI
  message catalogue, startup documentation, and HTTP/configuration/lifecycle
  acceptance checks.
- Pinned `bmforge-github-pages` skill with the local BMForge manager and lock file.
- Dark-themed Jekyll configuration for `llamasrv.osoyalce.com`, with English
  metadata, multilingual support, and the project's MyCount identifier.
- Documentation homepage, maintenance guide, and original SVG project logo.
- GitHub Actions workflow to build and deploy the documentation from `main`.
- Ignore rules for generated Jekyll output and caches.
- Pinned `bmforge-http` skill for the planned application web interface.
- Pinned `bmforge-project`, `bmforge-constants`, `bmforge-localization`, and
  `bmforge-installation` baseline skills at BMForge revision `29a100c39997`.
- Project engineering instructions and canonical `LlamaSrv` metadata, with
  initial version `0.0.0`, subtype `Application`, and base directory
  `/opt/prod/llamasrv`.
- Standard BMForge release script, CMDB checker, and install, upgrade, and
  uninstall entry points.
- Development guide covering the scaffold, verification, and remaining
  application implementation work.

### Changed

- Updated site logo.
- Keep the README focused on the project overview and documentation link.
- Exclude the application package from the documentation site output.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
