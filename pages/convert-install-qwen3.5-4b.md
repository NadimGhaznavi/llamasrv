---
title: "Convert and install the model"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-convert-install-qwen35-4b
---

From the llama.cpp checkout, use the [Python venv]({{ site.baseurl }}{% link pages/venv-setup.md %}) to convert the **language model** to BF16:

```sh
cd "$HOME/llamasrv-work/llama.cpp"
"$HOME/llamasrv-work/.venv/bin/python" convert_hf_to_gguf.py \
  "$HOME/llamasrv-work/Qwen3.5-4B" \
  --outfile "$HOME/llamasrv-work/models/intermediate/Qwen3.5-4B-BF16.gguf" \
  --outtype bf16
```

Export the separate **vision projector** in F16:

```sh
"$HOME/llamasrv-work/.venv/bin/python" convert_hf_to_gguf.py \
  "$HOME/llamasrv-work/Qwen3.5-4B" --mmproj \
  --outfile "$HOME/llamasrv-work/models/intermediate/mmproj-Qwen3.5-4B-F16.gguf" \
  --outtype f16
```

Quantize only the language model to Q4_K_M; keep the projector in F16:

```sh
"$HOME/llamasrv-work/llama.cpp/build/bin/llama-quantize" \
  "$HOME/llamasrv-work/models/intermediate/Qwen3.5-4B-BF16.gguf" \
  "$HOME/llamasrv-work/models/quantized/Qwen3.5-4B-Q4_K_M.gguf" \
  Q4_K_M
```

Copy the two finished files into the default model directory:

```sh
sudo install -d -m 755 /opt/prod/models
sudo install -m 644 \
  "$HOME/llamasrv-work/models/quantized/Qwen3.5-4B-Q4_K_M.gguf" \
  /opt/prod/models/
sudo install -m 644 \
  "$HOME/llamasrv-work/models/intermediate/mmproj-Qwen3.5-4B-F16.gguf" \
  /opt/prod/models/
```

Check the prerequisites before proceeding:

```sh
ls -lh /opt/prod/llama.cpp/bin/llama-server
ls -lh /opt/prod/models/{Qwen3.5-4B-Q4_K_M,mmproj-Qwen3.5-4B-F16}.gguf
```

The model files must be readable by the `llamasrv` service account that the installer creates. A projector is needed for vision support; loading only the language-model GGUF will not enable images.

---

[Previous: Download Qwen3.5-4B]({{ site.baseurl }}{% link pages/download-qwen3.5-4b.md %}) · [Environment Setup]({{ site.baseurl }}{% link pages/environment-setup.md %}) · [Next: Install and verify LlamaSrv]({{ site.baseurl }}{% link pages/install-verify-llamasrv.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
