---
title: "llamasrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-home
permalink: /
---

![{{ site.title }} logo]({{ site.logo | relative_url }})

Linux systemd service to run llama-server.

## Project status

The application HTTP server listens on `0.0.0.0:51000` and provides JSON service
information and an on-demand health endpoint. The repository also contains the
BMForge application and documentation scaffolds, version metadata, and prepared
release and installation tooling. The llama-server service and browser interface
remain to be implemented.

## Documentation

- [Development setup]({{ site.baseurl }}{% link pages/development.md %})
- [Maintaining the documentation]({{ site.baseurl }}{% link pages/documentation.md %})
- [Changelog]({{ site.baseurl }}{% link CHANGELOG.md %})
- [Source repository](https://github.com/NadimGhaznavi/llamasrv)
