---
title: "Environment Setup"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-environment
---

Before installing LlamaSrv, prepare a Linux host with **llama.cpp**, a model, and (optionally) NVIDIA GPU acceleration. The example below uses Debian 13, a Quadro M4000, and Qwen3.5-4B. Other hardware and models may need different packages or build options.

## Linux and NVIDIA drivers

Install the basic build tools:

```sh
sudo apt update
sudo apt install git git-lfs build-essential cmake libssl-dev python3-dev python3-venv
```

For NVIDIA hardware, enable Debian's `contrib`, `non-free`, and `non-free-firmware` repository components, then install the driver and CUDA toolkit:

```sh
sudo apt install linux-headers-amd64 nvidia-driver nvidia-cuda-dev nvidia-cuda-toolkit
```

Reboot after installing the driver, then check:

```sh
nvidia-smi
nvcc --version
```

For the Quadro M4000, the Ax3l setup used NVIDIA driver 550.163.01 and CUDA toolkit 12.4. Check that your driver, CUDA toolkit, and GPU architecture are compatible before building.

## Build llama.cpp

```sh
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build build --config Release -j "$(nproc)"
sudo cmake --install build --prefix /opt/prod/llama.cpp
```

For a CPU-only build, omit `-DGGML_CUDA=ON`. If the installed binary requires shared libraries from the installation prefix, register them:

```sh
echo '/opt/prod/llama.cpp/lib' | sudo tee /etc/ld.so.conf.d/llama.cpp.conf
sudo ldconfig
```

Confirm that `/opt/prod/llama.cpp/bin/llama-server` exists and runs. LlamaSrv expects that path by default; it does **not** build llama.cpp itself.

## Prepare Qwen3.5-4B

The default LlamaSrv configuration uses a quantized language model and a separate F16 vision projector. The following commands reproduce the preparation described in Ax3l. Run them from a development workspace with enough disk space and memory for the conversion.

```sh
git lfs install
mkdir -p /opt/dev/models/intermediate /opt/dev/models/quantized /opt/prod/models
cd /opt/dev
git clone --depth 1 https://huggingface.co/Qwen/Qwen3.5-4B
```

Install the conversion requirements in a Python virtual environment:

```sh
python3 -m venv /opt/dev/qwen-convert-venv
. /opt/dev/qwen-convert-venv/bin/activate
cd /opt/dev/llama.cpp
pip install -r requirements.txt
```

If you cloned llama.cpp elsewhere, use that checkout instead of `/opt/dev/llama.cpp`.

Convert the language model and vision projector:

```sh
python convert_hf_to_gguf.py /opt/dev/Qwen3.5-4B \
  --outfile /opt/dev/models/intermediate/Qwen3.5-4B-BF16.gguf --outtype bf16

python convert_hf_to_gguf.py /opt/dev/Qwen3.5-4B \
  --mmproj \
  --outfile /opt/dev/models/intermediate/mmproj-Qwen3.5-4B-F16.gguf \
  --outtype f16
```

Quantize the language model, leaving the projector in F16:

```sh
/opt/dev/llama.cpp/build/bin/llama-quantize \
  /opt/dev/models/intermediate/Qwen3.5-4B-BF16.gguf \
  /opt/dev/models/quantized/Qwen3.5-4B-Q4_K_M.gguf Q4_K_M
```

Install the two GGUF files:

```sh
sudo cp /opt/dev/models/quantized/Qwen3.5-4B-Q4_K_M.gguf /opt/prod/models/
sudo cp /opt/dev/models/intermediate/mmproj-Qwen3.5-4B-F16.gguf /opt/prod/models/
```

Ensure the files are readable by the `llamasrv` service account. The model and projector must both be present for vision support.

## Continue with LlamaSrv

Now follow [Install LlamaSrv]({{ site.baseurl }}{% link pages/install.md %}). The installer checks the external binary and model files, then manages the two systemd services.

Once running, verify the model's capabilities:

```sh
curl -fsS http://127.0.0.1:51001/props
```

For vision, check for `"vision": true` in the reported modalities. See [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %}) for configuration and client requests.

---

Adapted from the [Ax3l environment setup](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/env-setup.md), [driver setup](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/driver-setup.md), [llama.cpp setup](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/llama-cpp.md), and [Qwen3.5 model setup](https://github.com/NadimGhaznavi/ax3l/blob/main/pages/qwen-3.5-model-setup.md).

[Documentation index]({{ site.baseurl }}{% link index.md %})
