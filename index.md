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

The application HTTP server listens on `0.0.0.0:51000`, and a separate systemd
service runs llama-server on `0.0.0.0:51001`. Qwen3.5-4B with its vision
projector is the default. Both services read validated runtime configuration;
the HTTP health endpoint checks inference readiness on demand. Installation,
upgrades and removal preserve operator settings and external model files.
The browser settings interface remains planned.

## Documentation

- [Installation and runtime configuration]({{ site.baseurl }}{% link pages/installation.md %})
- [Development setup]({{ site.baseurl }}{% link pages/development.md %})
- [Maintaining the documentation]({{ site.baseurl }}{% link pages/documentation.md %})
- [Changelog]({{ site.baseurl }}{% link CHANGELOG.md %})
- [Source repository](https://github.com/NadimGhaznavi/llamasrv)
