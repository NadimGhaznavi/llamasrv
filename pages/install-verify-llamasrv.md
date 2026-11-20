---
title: "Install and verify LlamaSrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-install-verify
---

Follow [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}) to clone its repository and install the two services. The first installation requires the [default 4B model and projector]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-4b.md %}), even if you plan to use 9B. LlamaSrv starts inference on port `51001` and the control panel on port `51000`.

When the services are running:

```sh
curl -fsS http://127.0.0.1:51000/health
curl -fsS http://127.0.0.1:51001/props
```

Check the `/props` response for `"vision": true` in `modalities`. Open `http://HOST:51000/` to manage the service. Restrict access to the control panel, which has no login.

## Use Qwen3.5-9B

After [installing the 9B files]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-9b.md %}), save the current configuration:

```sh
sudo cp -a /opt/prod/llamasrv/conf/llamasrv.json \
  "$HOME/llamasrv-before-9b-$(date +%Y%m%d-%H%M%S).json"
```

In the control panel, set:

| Setting | Value |
| --- | --- |
| Model directory | `/opt/prod/models` |
| Model | `Qwen3.5-9B-Q4_K_M.gguf` |
| Vision projector | `mmproj-Qwen3.5-9B-F16.gguf` |
| Context size | `16384` |
| Jinja | Enabled |

Click **Update**, then check the selected files:

```sh
sudo -u llamasrv sh -c 'cd /opt/prod/llamasrv && .venv/bin/python -B -m llamasrv.activity.RunLlama --config conf/llamasrv.json --check'
```

Click **Restart LLM** and confirm. Check readiness and the selected model:

```sh
curl -fsS http://127.0.0.1:51001/health
curl -fsS http://127.0.0.1:51001/props
curl -fsS http://127.0.0.1:51001/v1/models
```

While the model loads, health may return HTTP 503. Wait for `{"status":"ok"}` and confirm that `/props` reports the 9B model and `"vision": true`. Use the returned model identifier in the [query example]({{ site.baseurl }}{% link pages/usage.md %}#query-the-model).

If loading fails, check the logs:

```sh
sudo journalctl -u llamasrv-llm.service -n 100 --no-pager
```

To return to 4B, select `Qwen3.5-4B-Q4_K_M.gguf` and `mmproj-Qwen3.5-4B-F16.gguf`, restore the previous context and Jinja settings, then click **Update** and **Restart LLM**.

---

[Environment Setup]({{ site.baseurl }}{% link pages/environment-setup.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
