---
title: "Environment Setup"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-environment
---

Prepare a **Debian 13** host to run LlamaSrv with **llama.cpp and Qwen3.5**. The 4B example is based on the Ax3l deployment, which used an NVIDIA Quadro M4000 and CUDA 12.4. Use compatible versions for your own hardware.

**LlamaSrv does not install drivers, compile llama.cpp, or download models.** Its first installation expects a working `llama-server` binary and the default Qwen model files at the paths documented in these steps. Once installed, you can select a different model in the control panel.

Follow these steps in order:

## Prepare Linux

1. [Prepare Linux]({{ site.baseurl }}{% link pages/prepare-linux.md %})

## Build Llama

2. [Build llama.cpp]({{ site.baseurl }}{% link pages/build-llama-cpp.md %})

## Set up the Python venv

3. [Set up the Python venv]({{ site.baseurl }}{% link pages/venv-setup.md %})

## Models

The instructions below are for building different models.

### Qwen 3.5 4B

A. [Download Qwen3.5-4B]({{ site.baseurl }}{% link pages/download-qwen3.5-4b.md %})

B. [Convert and install the model]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-4b.md %})

### Qwen 3.5 9B

A. [Download Qwen3.5-9B]({{ site.baseurl }}{% link pages/download-qwen3.5-9b.md %})

B. [Convert and install the model]({{ site.baseurl }}{% link pages/convert-install-qwen3.5-9b.md %})

## Install and Verify LlamaSrv

4. [Install and verify LlamaSrv]({{ site.baseurl }}{% link pages/install-verify-llamasrv.md %})

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
