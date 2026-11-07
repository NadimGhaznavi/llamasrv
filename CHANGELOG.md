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

- Updated site logo.

### Summary

Establish the standard BMForge GitHub Pages documentation scaffold for llamasrv.

### Added

- Pinned `bmforge-github-pages` skill with the local BMForge manager and lock file.
- Dark-themed Jekyll configuration for `llamasrv.osoyalce.com`, with English
  metadata, multilingual support, and the project's MyCount identifier.
- Documentation homepage, maintenance guide, and original SVG project logo.
- GitHub Actions workflow to build and deploy the documentation from `main`.
- Ignore rules for generated Jekyll output and caches.

### Changed

- Keep the README focused on the project overview and documentation link.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
