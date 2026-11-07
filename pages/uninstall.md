---
title: "Uninstall LlamaSrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-uninstall
---

From the repository checkout on the installed host:

```sh
./scripts/uninstall.sh --check
sudo ./scripts/uninstall.sh
```

Uninstall stops and disables both services, removes LlamaSrv-owned systemd units and sudoers rules, and deletes the deployed application code and managed Python virtual environment.

**Retained:** `/opt/prod/llamasrv/conf/llamasrv.json`, external llama.cpp and model files, the `llamasrv` system account, and any unowned files. Uninstall does not purge data.

If retained files remain, `/opt/prod/llamasrv/` may remain. A later [reinstallation]({{ site.baseurl }}{% link pages/install.md %}) can reuse the saved settings.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
