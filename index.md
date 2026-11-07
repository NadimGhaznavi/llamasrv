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

![LlamaSrv Architecture](/pages/images/llamasrv-architecture.png)

**LlamaSrv** runs [llama.cpp](https://github.com/ggml-org/llama.cpp) as a managed Linux service with a browser control panel. Applications such as R3el and ND3G can query one shared model endpoint without depending on one another.

![LlamaSrv Control Panel](/pages/images/llamasrv-control-panel.png)

The default setup runs Qwen3.5-4B with a vision projector.

| Component | Default port | Purpose |
| --- | --- | --- |
| Web control panel | `51000` | Configure, restart, and monitor inference |
| `llama-server` | `51001` | Handle inference requests from applications |

## Getting Started

- [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %})
- [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %})
- [Upgrade]({{ site.baseurl }}{% link pages/upgrade.md %})
- [Uninstall]({{ site.baseurl }}{% link pages/uninstall.md %})

## Additional Information

- [Project Structure]({{ site.baseurl }}{% link pages/project-structure.md %})
- [Changelog]({{ site.baseurl }}{% link CHANGELOG.md %})
- [Source repository](https://github.com/NadimGhaznavi/llamasrv)
