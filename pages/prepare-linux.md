---
title: "Prepare Linux"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-prepare-linux
---

Install Git, the build tools, and Python's virtual-environment support:

```sh
sudo apt update
sudo apt install git git-lfs build-essential cmake libssl-dev python3-dev python3-venv
```

For an **NVIDIA GPU**, enable the `contrib`, `non-free` and `non-free-firmware` components in your Debian APT sources (either `/etc/apt/sources.list` or the `Components:` field of `/etc/apt/sources.list.d/debian.sources`). Then install the driver and CUDA toolkit:

```sh
sudo apt update
sudo apt install linux-headers-amd64 nvidia-driver nvidia-cuda-dev nvidia-cuda-toolkit
```

Reboot after installing the driver and confirm it is working:

```sh
lspci | grep -i nvidia
nvidia-smi
nvcc --version
```

The original Ax3l machine reported driver `550.163.01` and CUDA toolkit `12.4`. Older cards such as the Quadro M4000 need a compatible CUDA toolkit **and** llama.cpp version. A current release may no longer support every older GPU.

**CPU-only host?** Skip the NVIDIA driver and CUDA steps, and use the CPU build in [Build llama.cpp]({{ site.baseurl }}{% link pages/build-llama-cpp.md %}).

---

[Environment Setup]({{ site.baseurl }}{% link pages/environment-setup.md %}) · [Next: Build llama.cpp]({{ site.baseurl }}{% link pages/build-llama-cpp.md %})

[Documentation index]({{ site.baseurl }}{% link index.md %})
