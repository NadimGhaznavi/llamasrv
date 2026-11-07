---
title: "Upgrade LlamaSrv"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-upgrade
---

Use `upgrade.sh` for an **existing** LlamaSrv installation. It updates the application, Python dependencies, and service definitions while retaining your configuration.

From the repository checkout on the installed host:

```sh
git pull --ff-only
./scripts/upgrade.sh --check
sudo ./scripts/upgrade.sh
```

The upgrade validates settings and model files, updates the installation, restarts inference and HTTP, then waits for both to become ready. It records the new version only after a successful start.

Your `/opt/prod/llamasrv/conf/llamasrv.json`, models, and external llama.cpp installation are preserved. **There is no automatic rollback:** if an upgrade fails, review the error and logs before retrying.

```sh
sudo journalctl -u llamasrv-llm.service -u llamasrv-http.service -n 100 --no-pager
curl --fail http://127.0.0.1:51000/health
```

For a new host, start with [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}).

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
