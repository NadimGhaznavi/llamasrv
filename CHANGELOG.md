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

### Summary

Establish the BMForge application and documentation scaffolds for LlamaSrv,
with an HTTP server listening on all IPv4 interfaces at port 51000, on-demand
health checks, and prepared release and installation tooling.

### Added

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
- Standard BMForge release script, CMDB checker, and deployment-disabled
  install, upgrade, and uninstall templates.
- Development guide covering the scaffold, verification, and remaining
  application implementation work.

### Changed

- Updated site logo.
- Keep the README focused on the project overview and documentation link.
- Exclude the application package from the documentation site output.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
