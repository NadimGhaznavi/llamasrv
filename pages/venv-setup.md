---
title: "Set up the Python venv"
layout: single
classes: wide
author_profile: true
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-venv-setup
---

After [building llama.cpp]({{ site.baseurl }}{% link pages/build-llama-cpp.md %}), create the Python environment and install the converter dependencies for both 4B and 9B models. Run these commands from the llama.cpp source checkout:

```sh
cd "$HOME/llamasrv-work/llama.cpp"
python3 -m venv "$HOME/llamasrv-work/.venv"
"$HOME/llamasrv-work/.venv/bin/python" -m pip install \
  -r requirements/requirements-convert_hf_to_gguf.txt
"$HOME/llamasrv-work/.venv/bin/python" -m pip check
```

Both model guides call this environment's Python by its full path. LlamaSrv's installer creates a separate venv for running the services.

---

[Previous: Build llama.cpp]({{ site.baseurl }}{% link pages/build-llama-cpp.md %}) · [Next: Choose a model]({{ site.baseurl }}{% link pages/environment-setup.md %}#models)

[Documentation index]({{ site.baseurl }}{% link index.md %})
