---
title: "Using LlamaSrv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-usage
---

LlamaSrv separates **service control** from **inference**. The web panel manages the process; applications call the shared `llama-server` endpoint.

## Control panel

Open `http://HOST:51000/`. Choose a provisioned GGUF model and optional vision projector, adjust the context size and ports, or enable metrics and Jinja chat templates.

**Update** saves configuration without restarting the services. **Restart LLM** applies saved inference settings. Changing the control-panel port requires an HTTP-service restart.

## Switch models

[Deploy the model files]({{ site.baseurl }}{% link pages/models.md %}), then open
the control panel at `http://HOST:51000/`.

1. Select the GGUF in **Model** and its matching file in **Vision projector**.
   Choose **None** for a text-only model.
2. Set **Context size** for the model and the available memory.
3. Click **Update**, then **Restart LLM** and confirm.

Selecting a vision projector automatically sets a minimum of 1024 tokens per
image to support accurate grounding with Qwen vision models. Choosing **None**
omits this option. Larger image token budgets can increase processing time and
memory use.

When inference is ready, confirm the selected model. For a vision model, check
that `/props` shows `"vision": true` under `modalities`.

```sh
curl -fsS http://127.0.0.1:51001/v1/models
curl -fsS http://127.0.0.1:51001/props
```

If the model fails to load, [check the service logs](#check-status) or switch
back to the previous model, projector, and context size.

## Configuration

Settings live in `/opt/prod/llamasrv/conf/llamasrv.json` and survive upgrades. For example, a minimal configuration for a text-only model is:

```json
{
  "llama": {
    "model": "my-text-model.gguf",
    "mmproj": null
  }
}
```

If you edit an existing file, keep your other settings and change only the fields you need. The selected GGUF must already exist in `model_dir` (default `/opt/prod/models`).

## Query the model

Independent applications such as R3el and ND3G send requests to port `51001`. For example:

```sh
curl http://127.0.0.1:51001/v1/models

curl http://127.0.0.1:51001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen3.5-4B-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
```

Use the model identifier returned by llama.cpp's `/v1/models` in the chat request.

## Check status

```sh
systemctl status llamasrv-llm.service llamasrv-http.service
curl http://127.0.0.1:51000/health
curl http://127.0.0.1:51001/health
journalctl -u llamasrv-llm.service -u llamasrv-http.service -n 100
```

Start or stop both services with the installed helper:

```sh
sudo /opt/prod/llamasrv/scripts/services stop
sudo /opt/prod/llamasrv/scripts/services start
```

The control panel has no authentication. Keep port `51000` on a trusted network.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
