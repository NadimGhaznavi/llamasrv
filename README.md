# llamasrv

Standalone Linux systemd services for llama-server and its configuration HTTP
server. Qwen3.5-4B with vision is the default model.

Run the HTTP server with Python 3.11 or newer:

```sh
python3 -m llamasrv
```

HTTP listens on `0.0.0.0:51000`; inference listens on `0.0.0.0:51001`.
`/health` returns 503 until inference is ready. Stop HTTP with Ctrl+C or SIGTERM.

On the target machine, run `sudo ./scripts/install.sh` from the checkout.
See [installation and runtime configuration](pages/installation.md) for
prerequisites, settings, upgrades and removal. The browser settings UI is planned.

[Project website and documentation](https://llamasrv.osoyalce.com/)
