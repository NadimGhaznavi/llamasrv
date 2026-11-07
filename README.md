# llamasrv

Linux systemd service to run llama-server.

Run the HTTP server with Python 3.11 or newer:

```sh
python3 -m llamasrv
```

It listens on all IPv4 interfaces at `0.0.0.0:51000`. Check it with
`curl http://127.0.0.1:51000/health`. Stop it with Ctrl+C or SIGTERM.

[Project website and documentation](https://llamasrv.osoyalce.com/)
