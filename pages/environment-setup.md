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

This is a complete example of preparing a **Debian 13** host to run LlamaSrv with **llama.cpp and Qwen3.5-4B**. It is based on the Ax3l deployment, which used an NVIDIA Quadro M4000 and CUDA 12.4. Use compatible versions for your own hardware.

**LlamaSrv does not install drivers, compile llama.cpp, or download models.** Its first installation expects a working `llama-server` binary and the default Qwen model files at the paths below. Once installed, you can select a different model in the control panel.

## 1. Prepare Linux

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

**CPU-only host?** Skip the NVIDIA driver and CUDA steps, and use the CPU build in the next section.

## 2. Build llama.cpp

Keep source code and model-conversion files in a writable workspace:

```sh
mkdir -p "$HOME/llamasrv-work"
cd "$HOME/llamasrv-work"
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
```

Choose **one** build:

```sh
# NVIDIA CUDA
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build build -j 4
```

```sh
# CPU only
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
```

Install the binary where LlamaSrv expects it:

```sh
sudo cmake --install build --prefix /opt/prod/llama.cpp
/opt/prod/llama.cpp/bin/llama-server --version
```

If the binary reports missing shared libraries, register the installed library path:

```sh
echo '/opt/prod/llama.cpp/lib' | sudo tee /etc/ld.so.conf.d/llama.cpp.conf
sudo ldconfig
```

For additional backends and build options, see the [llama.cpp build guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md).

## 3. Download Qwen3.5-4B

The default model uses two GGUF files: a quantized **language model** and an **F16 vision projector**. Download the original model into the same workspace. The Ax3l download was approximately 18 GB; conversion needs substantial additional free space.

```sh
cd "$HOME/llamasrv-work"
git lfs install
git clone --depth 1 https://huggingface.co/Qwen/Qwen3.5-4B
mkdir -p models/intermediate models/quantized
```

Create an isolated conversion environment and install the dependencies provided by llama.cpp:

```sh
python3 -m venv "$HOME/llamasrv-work/.venv"
"$HOME/llamasrv-work/.venv/bin/python" -m pip install \
  -r "$HOME/llamasrv-work/llama.cpp/requirements.txt"
```

## 4. Convert and install the model

From the llama.cpp checkout, convert the **language model** to BF16:

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

## 5. Install and verify LlamaSrv

Follow [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}) to clone its repository and install the two services. LlamaSrv starts inference on port `51001` and the control panel on port `51000`.

When the services are running:

```sh
curl -fsS http://127.0.0.1:51000/health
curl -fsS http://127.0.0.1:51001/props
```

Check the `/props` response for `"vision": true` in `modalities`. Open `http://HOST:51000/` to manage the service. Restrict access to the control panel, which has no login.

The model conversion commands are an example from a particular working setup. As llama.cpp evolves, its conversion options and hardware support may change. For model/projector usage, see the [llama.cpp multimodal guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md).

---

Adapted from Ax3l's [environment](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/env-setup.md), [driver](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/driver-setup.md), [llama.cpp](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/llama-cpp.md), and [Qwen3.5](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/qwen-3.5-model-setup.md) guides.

[Documentation index]({{ site.baseurl }}{% link index.md %})
