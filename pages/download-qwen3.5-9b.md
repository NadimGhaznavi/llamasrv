---
title: "Download Qwen3.5-9B"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-download-qwen35-9b
---

Qwen3.5-9B uses two GGUF files: a quantized **language model** and an **F16 vision projector**. Allow at least 80 GiB of free space across the workspace and model filesystem for the download, conversion and installed copies. Use a llama.cpp checkout that matches the installed server and supports Qwen3.5 language and vision conversion.

```sh
cd "$HOME/llamasrv-work"
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://huggingface.co/Qwen/Qwen3.5-9B
git -C Qwen3.5-9B lfs install --local
git -C Qwen3.5-9B lfs pull
git -C Qwen3.5-9B lfs fsck
mkdir -p models/intermediate models/quantized
```

If a download is interrupted, resume with `git -C Qwen3.5-9B lfs pull`.

Before converting the model, complete the shared [Python venv setup]({{ site.baseurl }}{% link pages/venv-setup.md %}). The same environment supports both 4B and 9B.

---

[Previous: Set up the Python venv]({{ site.baseurl }}{% link pages/venv-setup.md %}) · [Environment Setup]({{ site.baseurl }}{% link pages/environment-setup.md %}) · [Next: Convert and install the model]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-9b.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
