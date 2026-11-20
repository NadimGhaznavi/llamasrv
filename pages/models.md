---
title: "Install a Model"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-models
---

Use the same procedure for either model. Start with **4B** on a fresh LlamaSrv
installation. On an existing installation, you can add either model and select it
after deployment.

| Model | Hugging Face repo | Starting context |
| --- | --- | --- |
| Qwen3.5-4B (default) | [`Qwen/Qwen3.5-4B`](https://huggingface.co/Qwen/Qwen3.5-4B) | `12288` |
| Qwen3.5-9B | [`Qwen/Qwen3.5-9B`](https://huggingface.co/Qwen/Qwen3.5-9B) | `16384` for a trial, lower if memory is tight |

For conversion, use the [llama.cpp build and converter]({{ site.baseurl }}{% link pages/environment-setup.md %})
under `/opt/dev/llama.cpp`. Allow room for the download, BF16 intermediate,
and finished files. For 9B, budget at least 80 GiB across `/opt/dev` and
`/opt/prod`.

## 1. Download

Set `repo` to the model you want. Use the same shell for all three steps and
stop if a command fails.

```sh
repo=Qwen/Qwen3.5-4B
model=${repo##*/}
source_dir="/opt/dev/models/$model"
build_dir=/opt/dev/models

mkdir -p "$build_dir/intermediate" "$build_dir/quantized"
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "https://huggingface.co/$repo" "$source_dir"
git -C "$source_dir" lfs pull
```

For an existing checkout, set `source_dir` to its path and skip the clone.
If a download was interrupted, rerun `git lfs pull` in that checkout.

## 2. Convert

Convert the language model to BF16, quantize it to Q4_K_M, and export the
matching vision projector in F16.

```sh
cd /opt/dev/llama.cpp
.venv/bin/python convert_hf_to_gguf.py "$source_dir" --outtype bf16 \
  --outfile "$build_dir/intermediate/$model-BF16.gguf"
build/bin/llama-quantize "$build_dir/intermediate/$model-BF16.gguf" \
  "$build_dir/quantized/$model-Q4_K_M.gguf" Q4_K_M
.venv/bin/python convert_hf_to_gguf.py "$source_dir" --mmproj --outtype f16 \
  --outfile "$build_dir/quantized/mmproj-$model-F16.gguf"
```

## 3. Deploy

If you already have the two finished GGUFs, set `model` and `build_dir` as
above and place the files in `/opt/dev/models/quantized` with the names below.

```sh
sudo install -d -m 0755 /opt/prod/models
sudo install -m 0644 "$build_dir/quantized/$model-Q4_K_M.gguf" \
  "$build_dir/quantized/mmproj-$model-F16.gguf" /opt/prod/models/
```

On a new host, [install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}).
On an existing server, [switch models]({{ site.baseurl }}{% link pages/usage.md %}#switch-models).

To document another model supported by this conversion recipe, add its source
repo and starting context to the table. For a text-only model, skip the projector
conversion and copy only the language GGUF.

[Documentation index]({{ site.baseurl }}{% link index.md %})
