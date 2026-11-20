---
title: "Prepare the Host"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-environment
---

Set up a Debian 13 host once. Build under `/opt/dev` and deploy to `/opt/prod`.

| Path | Contents |
| --- | --- |
| `/opt/dev/llama.cpp` | llama.cpp source, build, and converter venv |
| `/opt/dev/models` | Model downloads, intermediate files, and finished GGUFs |
| `/opt/dev/llamasrv` | LlamaSrv source checkout |
| `/opt/prod/llama.cpp` | Link to the deployed llama.cpp build |
| `/opt/prod/models` | GGUFs served by LlamaSrv |
| `/opt/prod/llamasrv` | Deployed LlamaSrv services and configuration |

## 1. Install dependencies

```sh
sudo apt update
sudo apt install git git-lfs build-essential cmake libssl-dev python3-dev python3-venv curl sudo
```

For NVIDIA on Debian amd64, enable `contrib`, `non-free`, and
`non-free-firmware` in your APT sources. Then install the driver and toolkit.

```sh
sudo apt update
sudo apt install linux-headers-amd64 nvidia-driver nvidia-cuda-toolkit
```

Reboot after installing the driver, then run `nvidia-smi` and `nvcc --version`.
The Ax3l deployment used a Quadro M4000 with CUDA 12.4. Choose a llama.cpp
revision that supports both your GPU/toolkit and the model you plan to serve.

## 2. Build and deploy llama.cpp

If you already have a compatible deployment, use the matching source checkout
for conversion and continue to step 3. On a new host, create the build
directories for your build account.

```sh
sudo install -d /opt/dev /opt/prod
sudo install -d -o "$(id -un)" -g "$(id -gn)" /opt/dev/llama.cpp /opt/dev/models
git clone https://github.com/ggml-org/llama.cpp.git /opt/dev/llama.cpp
cd /opt/dev/llama.cpp
```

If you use a specific llama.cpp tag or commit, check it out before building.
Set `cuda=ON` for NVIDIA CUDA or leave it `OFF` for CPU.

```sh
cuda=OFF
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA="$cuda" \
  -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_INSTALL_RPATH='$ORIGIN/../lib'
cmake --build build --parallel 4
```

Install under a versioned path. Check the binary before pointing the stable
production path at it.

```sh
prefix="/opt/prod/llama.cpp-$(git rev-parse --short HEAD)"
sudo cmake --install build --prefix "$prefix"
"$prefix/bin/llama-server" --version &&
  sudo ln -sfnT "$prefix" /opt/prod/llama.cpp
```

Other backends and CUDA options are covered in the [llama.cpp build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md).

## 3. Set up the converter

Run once per llama.cpp checkout to convert models from their original weights.
You can skip this step if you already have the finished GGUFs.

```sh
cd /opt/dev/llama.cpp
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements/requirements-convert_hf_to_gguf.txt
.venv/bin/python -m pip check
```

Next, [install a model]({{ site.baseurl }}{% link pages/models.md %}).

[Documentation index]({{ site.baseurl }}{% link index.md %})
