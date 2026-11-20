---
title: "LlamaSrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-home
permalink: /
---

**LlamaSrv** runs llama.cpp under systemd with a browser control panel. The
control panel listens on port `51000` and inference on port `51001`.

## First installation

1. [Prepare the host]({{ site.baseurl }}{% link pages/environment-setup.md %}).
2. [Install Qwen3.5-4B]({{ site.baseurl }}{% link pages/models.md %}), the default model.
3. [Install and verify LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}).

## Existing installations

- [Install another model]({{ site.baseurl }}{% link pages/models.md %}) or [switch to one you already installed]({{ site.baseurl }}{% link pages/usage.md %}#switch-models).
- [Upgrade]({{ site.baseurl }}{% link pages/upgrade.md %}) or [uninstall]({{ site.baseurl }}{% link pages/uninstall.md %}) LlamaSrv.

## Reference

- [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %})
- [Project structure]({{ site.baseurl }}{% link pages/project-structure.md %})
- [Changelog]({{ site.baseurl }}{% link CHANGELOG.md %})
- [Source repository](https://github.com/NadimGhaznavi/llamasrv)

![LlamaSrv control panel]({{ '/pages/images/llamasrv-control-panel.png' | relative_url }})

![LlamaSrv architecture]({{ '/pages/images/llamasrv-architecture.png' | relative_url }})
