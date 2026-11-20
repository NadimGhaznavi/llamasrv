---
title: "Build and Install Qwen3.5-9B with Vision"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-qwen35-9b-setup
---

Use this procedure on the **PROD host** to convert the original Qwen3.5-9B
weights, install the two resulting model files, and try them with LlamaSrv.
It complements the [4B environment procedure]({{ site.baseurl }}{% link pages/environment-setup.md %}).
The 4B files remain available for switching back, and LlamaSrv's application
defaults remain Qwen3.5-4B.

This guide assumes LlamaSrv is already installed and serving the 4B model. For
initial host preparation, drivers and the existing llama.cpp installation,
follow the 4B environment procedure and [installation guide]({{ site.baseurl }}{% link pages/install.md %}).
There is no LlamaSrv release or application upgrade in this procedure.

## 1. Check the host and choose the workspace

Run the commands in order in the **same Bash session**, as your normal operator
account. Use `sudo` only where shown, and stop if a command fails. Adjust the
source, model directory and server paths to match the existing installation before
continuing.

```bash
QWEN9B_WORK="$HOME/llamasrv-work/qwen3.5-9b"
QWEN9B_LLAMA_CPP="$HOME/llamasrv-work/llama.cpp"
QWEN9B_MODEL_DIR="/opt/prod/models"
QWEN9B_SERVER="/opt/prod/llama.cpp/bin/llama-server"

mkdir -p "$QWEN9B_WORK/models/intermediate" "$QWEN9B_WORK/models/quantized"
df -h "$QWEN9B_WORK" "$QWEN9B_MODEL_DIR"
free -h
nvidia-smi
"$QWEN9B_SERVER" --version
git -C "$QWEN9B_LLAMA_CPP" status --short
git -C "$QWEN9B_LLAMA_CPP" rev-parse HEAD
```

Use a clean llama.cpp source checkout corresponding to the installed server's
build commit. It must support **Qwen3.5 language and vision conversion**. Keep
the working server, CUDA toolkit and drivers in place. In particular, an older
card such as the documented Quadro M4000 needs a compatible llama.cpp/CUDA
combination; do not pull and install a newer server as part of model conversion.
If the checkout is missing or does not match, obtain the matching source before
continuing. An unsupported-model error requires resolving that compatibility
first.

You need Git LFS, Python with `venv`, CMake and a C++ compiler, as in the 4B
procedure. Plan for **at least 80 GiB of free disk space** across the workspace
and model filesystem: the original model is about 19.3 GB, Git LFS also stores
objects, and conversion produces a large BF16 intermediate plus the finished
files and installed copies. Python dependencies and build files need space too.
Conversion and quantization use system RAM; check memory and swap availability
and schedule this work away from busy inference periods.

For a CPU-only host, omit all `nvidia-smi` commands and the GPU-specific settings in section 7.
Inference speed and memory placement will differ from the 8 GiB GPU trial.

### What the trial will load

| Setting | Value |
| --- | --- |
| Language model | `Qwen3.5-9B-Q4_K_M.gguf` |
| Vision projector | `mmproj-Qwen3.5-9B-F16.gguf` |
| Initial context size | `16384` |
| Initial cache types | F16 K and V |
| Initial parallel slots | `1` |
| Jinja chat template | Enabled |

As a size reference, the [published Unsloth artifacts](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main)
are about **5.29 GiB** for Q4_K_M and **0.85 GiB** for the F16 projector.
Your own conversion can differ. From the [official model configuration](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/config.json),
the full-attention F16 KV allocation at 16,384 tokens is approximately
**0.5 GiB**: 8 layers × 4 KV heads × 256 dimensions × K/V × 2 bytes per value.
That puts these three items near **6.65 GiB**, before recurrent state, compute
buffers and other GPU users. Treat 8 GiB as a trial budget and measure actual
use, including an image request. Q4_K_M describes the weights, not the KV cache.

## 2. Download and record the original 9B model

Clone the [official Qwen3.5-9B repository](https://huggingface.co/Qwen/Qwen3.5-9B)
into a new directory. The first command skips automatic weight downloads so
Git LFS can be configured locally to this clone.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 \
  https://huggingface.co/Qwen/Qwen3.5-9B \
  "$QWEN9B_WORK/Qwen3.5-9B"
git -C "$QWEN9B_WORK/Qwen3.5-9B" lfs install --local
git -C "$QWEN9B_WORK/Qwen3.5-9B" lfs pull
git -C "$QWEN9B_WORK/Qwen3.5-9B" lfs fsck

git -C "$QWEN9B_WORK/Qwen3.5-9B" rev-parse HEAD > "$QWEN9B_WORK/model-source.commit"
git -C "$QWEN9B_LLAMA_CPP" rev-parse HEAD > "$QWEN9B_WORK/llama-source.commit"
"$QWEN9B_SERVER" --version > "$QWEN9B_WORK/server-version.txt" 2>&1
```

If a download is interrupted, resume with `git lfs pull` and run `git lfs fsck`
again in this same clone. Keep the revision records with the generated files.

## 3. Prepare conversion tools

Create a separate conversion environment using the requirements from the
matching llama.cpp checkout. This environment belongs to the workspace; it is
separate from LlamaSrv's installed runtime environment.

```bash
python3 -m venv "$QWEN9B_WORK/.venv"
"$QWEN9B_WORK/.venv/bin/python" -m pip install \
  -r "$QWEN9B_LLAMA_CPP/requirements.txt"
"$QWEN9B_WORK/.venv/bin/python" \
  "$QWEN9B_LLAMA_CPP/convert_hf_to_gguf.py" --help
```

Confirm the converter supports `--outtype bf16`, `--outtype f16` and `--mmproj`.
Build the quantizer in a separate CPU build directory; quantizing the model
does not require a CUDA build or installation of another server binary.

```bash
cmake -S "$QWEN9B_LLAMA_CPP" -B "$QWEN9B_WORK/quantizer-build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF
cmake --build "$QWEN9B_WORK/quantizer-build" --target llama-quantize -j 4
```

## 4. Convert the language model and vision projector

Convert the language weights to BF16:

```bash
"$QWEN9B_WORK/.venv/bin/python" \
  "$QWEN9B_LLAMA_CPP/convert_hf_to_gguf.py" \
  "$QWEN9B_WORK/Qwen3.5-9B" \
  --outfile "$QWEN9B_WORK/models/intermediate/Qwen3.5-9B-BF16.gguf" \
  --outtype bf16
```

Export the **9B model's own projector** in F16:

```bash
"$QWEN9B_WORK/.venv/bin/python" \
  "$QWEN9B_LLAMA_CPP/convert_hf_to_gguf.py" \
  "$QWEN9B_WORK/Qwen3.5-9B" --mmproj \
  --outfile "$QWEN9B_WORK/models/quantized/mmproj-Qwen3.5-9B-F16.gguf" \
  --outtype f16
```

Do not pair the 9B language model with the 4B projector. Both files here come
from the same downloaded 9B snapshot.

## 5. Quantize and checksum the finished files

Quantize only the language model; leave the projector in F16.

```bash
"$QWEN9B_WORK/quantizer-build/bin/llama-quantize" \
  "$QWEN9B_WORK/models/intermediate/Qwen3.5-9B-BF16.gguf" \
  "$QWEN9B_WORK/models/quantized/Qwen3.5-9B-Q4_K_M.gguf" \
  Q4_K_M

ls -lh "$QWEN9B_WORK/models/quantized/"*.gguf
(
  cd "$QWEN9B_WORK/models/quantized" || exit 1
  sha256sum Qwen3.5-9B-Q4_K_M.gguf mmproj-Qwen3.5-9B-F16.gguf \
    > "$QWEN9B_WORK/Qwen3.5-9B.sha256"
)
```

Proceed only after both conversions and quantization finish successfully.
The checksums record your generated artifacts; they are not expected to match
a third-party quantization made with different tools or metadata.

## 6. Install the two files alongside 4B

Copy the finished files into LlamaSrv's configured model directory. Use real
files under `/opt/prod`, rather than links into your home workspace: the
systemd service protects home directories.

```bash
sudo install -d -m 755 "$QWEN9B_MODEL_DIR"
sudo install -o root -g root -m 644 \
  "$QWEN9B_WORK/models/quantized/Qwen3.5-9B-Q4_K_M.gguf" \
  "$QWEN9B_MODEL_DIR/"
sudo install -o root -g root -m 644 \
  "$QWEN9B_WORK/models/quantized/mmproj-Qwen3.5-9B-F16.gguf" \
  "$QWEN9B_MODEL_DIR/"
(
  cd "$QWEN9B_MODEL_DIR" || exit 1
  sha256sum --check "$QWEN9B_WORK/Qwen3.5-9B.sha256"
)
sudo -u llamasrv test -r "$QWEN9B_MODEL_DIR/Qwen3.5-9B-Q4_K_M.gguf"
sudo -u llamasrv test -r "$QWEN9B_MODEL_DIR/mmproj-Qwen3.5-9B-F16.gguf"
```

Both checksum results must say `OK`, and both readability checks must succeed.
Installing these files does not change the running model. Keep the original 4B
model and projector in this directory.

## 7. Save the current settings and select 9B

Arrange a maintenance window for the inference restart. Record the existing
model, projector, context size and Jinja setting, and back up the live JSON:

```bash
QWEN9B_CONFIG_BACKUP="$QWEN9B_WORK/llamasrv-before-9b-$(date +%Y%m%d-%H%M%S).json"
sudo cp -a /opt/prod/llamasrv/conf/llamasrv.json "$QWEN9B_CONFIG_BACKUP"
sudo systemctl cat llamasrv-llm.service
"$QWEN9B_SERVER" --help
```

### Set a repeatable GPU trial

The panel does not expose llama.cpp's GPU-layer, slot or cache-type options.
For the single-slot CUDA trial, confirm the installed server's help lists
`LLAMA_ARG_N_GPU_LAYERS`, `LLAMA_ARG_N_PARALLEL`, `LLAMA_ARG_CACHE_TYPE_K` and
`LLAMA_ARG_CACHE_TYPE_V`. If it does not, stop and check that build's supported
options before setting an override.

Create a dedicated systemd drop-in. If this filename already exists, save and
review it first; also check for existing overrides of the same variables.

```bash
sudo systemctl edit --drop-in=90-qwen35-9b-trial.conf llamasrv-llm.service
```

Enter this content in the editor:

```ini
[Service]
Environment=LLAMA_ARG_N_GPU_LAYERS=99
Environment=LLAMA_ARG_N_PARALLEL=1
Environment=LLAMA_ARG_CACHE_TYPE_K=f16
Environment=LLAMA_ARG_CACHE_TYPE_V=f16
```

This requests all model layers on the GPU and one slot, with F16 K and V caches.
It deliberately tests the intended GPU placement; inspect startup logs to
confirm actual placement. A single slot also avoids dividing the context among
several concurrent requests. On CPU-only hosts, omit the GPU-layer line.

```bash
sudo systemctl daemon-reload
sudo systemctl show llamasrv-llm.service --property=Environment
```

### Select the model in the panel

Refresh `http://HOST:51000/` and set:

| Panel setting | Value |
| --- | --- |
| Model directory | The value of `QWEN9B_MODEL_DIR` |
| Model | `Qwen3.5-9B-Q4_K_M.gguf` |
| Vision projector | `mmproj-Qwen3.5-9B-F16.gguf` |
| Context size | `16384` |
| Jinja | Enabled |

Keep the existing binary path, listener settings and metrics choice. Click
**Update** to save. Before restarting, check the selected files as the service
account:

```bash
sudo -u llamasrv sh -c 'cd /opt/prod/llamasrv && .venv/bin/python -B -m llamasrv.activity.RunLlama --config conf/llamasrv.json --check'
```

This checks configuration and readable/executable paths; it does not load the
model or prove that it fits in VRAM. Click **Restart LLM** and confirm the
restart. The control panel stops the old process before starting the new one.

## 8. Verify loading, text and vision

These examples use the default inference port. Substitute the installed port
if it differs.

```bash
systemctl status llamasrv-llm.service --no-pager
sudo journalctl -u llamasrv-llm.service -n 150 --no-pager
curl -fsS http://127.0.0.1:51001/health
curl -fsS http://127.0.0.1:51001/props
curl -fsS http://127.0.0.1:51001/v1/models
nvidia-smi
```

During loading, health may return HTTP 503. Wait for `{"status":"ok"}`;
`systemctl` reporting an active process alone is insufficient. Check that
`/props` names the 9B model, reports `"vision": true` in `modalities`, and has
one slot. Inspect startup logs for the resolved 16,384-token context, F16
caches, GPU layer placement and memory allocation. An 8 GiB fit is confirmed
only after requests also complete successfully.

Use the model identifier returned by `/v1/models` in the following requests.
Replace the example identifier if your build reports another one.

```bash
curl -fsS http://127.0.0.1:51001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen3.5-9B-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": "Reply with one short greeting."}],
    "max_tokens": 512,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

For the vision check, use a local PNG loss chart with known labels and a clear
trend. Set the image path below to an existing file. This sends the image as
base64 in the request; no external image hosting is needed.

```bash
QWEN9B_CHART="$HOME/loss-chart.png"
python3 - "$QWEN9B_CHART" <<'PY' > "$QWEN9B_WORK/vision-request.json"
import base64
import json
from pathlib import Path
import sys

encoded = base64.b64encode(Path(sys.argv[1]).read_bytes()).decode("ascii")
json.dump({
    "model": "Qwen3.5-9B-Q4_K_M.gguf",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Read the chart's axis labels and legend. Describe the loss trend and any divergence. Do not invent unreadable values."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + encoded}},
    ]}],
    "max_tokens": 1024,
    "chat_template_kwargs": {"enable_thinking": False},
}, sys.stdout)
PY
curl -fsS http://127.0.0.1:51001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary "@$QWEN9B_WORK/vision-request.json"
nvidia-smi
```

Use `nvidia-smi -l 1` in a second terminal while sending the requests to observe
peak memory, then press Ctrl-C to stop that display. Test representative chart
sizes and prompts, and compare correctness and latency with your 4B results.
The smoke checks disable thinking to keep their output bounded; test the
application's intended reasoning settings separately. A short request does not
validate a prompt that fills the entire context window.

## 9. If the trial fails or you want to return to 4B

For allocation failures, stop a repeatedly failing inference process before
investigating:

```bash
sudo systemctl stop llamasrv-llm.service
sudo journalctl -u llamasrv-llm.service -n 150 --no-pager
```

First check competing GPU processes, actual offload, slot count and image size.
Reducing context to `8192` is a separate smaller trial; lower GPU offload moves
work to system RAM and changes latency. Keep F16 cache as the baseline. Q8 KV
is a separate backend-dependent experiment, and LlamaSrv has no JSON cache-type
setting. Do not assume that an older GPU supports every quantized-cache or
Flash Attention combination.

To restore the previous setup:

1. In the panel, select the recorded 4B model, its matching projector, previous
   context size and Jinja setting, then click **Update**.
2. Remove only the trial drop-in created in section 7. If it replaced an
   existing file, restore that saved file instead. Leave other overrides alone.

   ```bash
   sudo rm /etc/systemd/system/llamasrv-llm.service.d/90-qwen35-9b-trial.conf
   sudo systemctl daemon-reload
   ```

3. Click **Restart LLM**. Check `/health`, `/props` and a text/image request
   again to confirm that 4B is serving.

If the panel is unavailable, restore from the terminal. The following assumes
the trial drop-in was newly created; if it replaced an existing file, restore
that saved file instead of removing it:

```bash
sudo systemctl stop llamasrv-llm.service
sudo cp -a "$QWEN9B_CONFIG_BACKUP" /opt/prod/llamasrv/conf/llamasrv.json
sudo rm -f /etc/systemd/system/llamasrv-llm.service.d/90-qwen35-9b-trial.conf
sudo systemctl daemon-reload
sudo systemctl start llamasrv-llm.service
```

The JSON backup does not include systemd drop-ins. Keep the 9B files and build
records while evaluating the trial; switching models does not
require deleting either model pair.

## References

- [Official Qwen3.5-9B model and source weights](https://huggingface.co/Qwen/Qwen3.5-9B)
- [llama.cpp converter](https://github.com/ggml-org/llama.cpp/blob/master/convert_hf_to_gguf.py)
- [llama.cpp multimodal input](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)
- [llama.cpp server options and API](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
- [Debian 13 systemctl manual, including named drop-ins](https://manpages.debian.org/trixie/systemd/systemctl.1.en.html)
- [Using LlamaSrv]({{ site.baseurl }}{% link pages/usage.md %})

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
