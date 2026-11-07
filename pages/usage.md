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

LlamaSrv loads **one model at a time** from its configured model directory; it does not download models.

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

These OpenAI-compatible endpoints come from llama.cpp, not the LlamaSrv control panel. If `/v1/models` reports a different model identifier, use that identifier in the chat request.

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
