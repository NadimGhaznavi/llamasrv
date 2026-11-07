---
title: "Install, Upgrade, Uninstall"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-scripts
---

The LlamaSrv repository includes three service-lifecycle scripts. Run them from a checkout on the target Linux host.

| Task | Guide | Command |
| --- | --- | --- |
| First installation | [Install]({{ site.baseurl }}{% link pages/install.md %}) | `sudo ./scripts/install.sh` |
| Existing installation | [Upgrade]({{ site.baseurl }}{% link pages/upgrade.md %}) | `sudo ./scripts/upgrade.sh` |
| Removal | [Uninstall]({{ site.baseurl }}{% link pages/uninstall.md %}) | `sudo ./scripts/uninstall.sh` |

Each script supports `--check` to validate without making changes, and `--help` for command usage.

For models, configuration, and runtime controls, see [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %}).

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
