---
title: "Build llama.cpp"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-build-llama-cpp
---

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

---

[Previous: Prepare Linux]({{ site.baseurl }}{% link pages/prepare-linux.md %}) · [Next: Choose a model]({{ site.baseurl }}{% link pages/environment-setup.md %}#models)

[Documentation index]({{ site.baseurl }}{% link index.md %})
