---
title: "Download Qwen3.5-4B"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-download-qwen35-4b
---

The default model uses two GGUF files: a quantized **language model** and an **F16 vision projector**. Download the original model into the same workspace. The Ax3l download was approximately 18 GB; conversion needs substantial additional free space.

```sh
cd "$HOME/llamasrv-work"
git lfs install
git clone --depth 1 https://huggingface.co/Qwen/Qwen3.5-4B
mkdir -p models/intermediate models/quantized
```

Before converting the model, complete the shared [Python venv setup]({{ site.baseurl }}{% link pages/venv-setup.md %}).

---

[Previous: Set up the Python venv]({{ site.baseurl }}{% link pages/venv-setup.md %}) · [Environment Setup]({{ site.baseurl }}{% link pages/environment-setup.md %}) · [Next: Convert and install the model]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-4b.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
