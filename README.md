# LlamaSrv

LlamaSrv provides systemd-managed llama.cpp inference and a browser control panel. Qwen3.5-4B with vision is the default model.

On a Linux host with the llama.cpp binary and model files already installed:

```sh
git clone https://github.com/NadimGhaznavi/llamasrv.git
cd llamasrv
./scripts/install.sh --check
sudo ./scripts/install.sh
```

The control panel listens on port `51000`, and inference on port `51001`. By default both bind to all IPv4 interfaces; restrict control-panel access to a trusted network.

[Installation and usage guides](https://llamasrv.osoyalce.com/) · [Project structure](pages/project-structure.md)
