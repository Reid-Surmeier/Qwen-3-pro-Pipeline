# Host deployment templates

These files reproduce the host-level configuration without storing credentials.

Pinned runtime versions used by the verified installation:

- ComfyUI `v0.31.0`
- `comfyui-mcp@0.50.98`
- Python `3.12.4`
- PyTorch `2.13.0+cu130`

## Files

- `run-comfyui.sh` injects OpenRouter and Alibaba keys through the local
  `stored_bws.sh` Bitwarden Secrets Manager wrapper. It contains secret names,
  never secret values.
- `run-comfyui-pool.sh` starts five independent ComfyUI workers by default and
  one API-compatible router on the existing public port. Each worker loads the
  same custom nodes and uses the same input/output directories; the router only
  selects a worker and never modifies a workflow.
- `systemd/qwen-comfyui.service` runs that wrapper as an enabled user service.
- `codex/comfyui-mcp.toml` is the isolated MCP section to merge into
  `~/.codex/config.toml`; replace `USER` with the local account name.

The verified WSL host uses `10.255.255.254`, a loopback alias, because ordinary
`127.0.0.1` traffic is unreliable in that environment. Override
`QWEN_COMFYUI_LISTEN_ADDRESS` and the matching MCP URL on another host.

The Bitwarden secret names can be changed without editing the script:

```bash
export QWEN_OPENROUTER_SECRET_NAME="OpenRouter"
export QWEN_ALIBABA_SECRET_NAME="Alibaba Singapour"
```

Install the templates after reviewing the paths:

```bash
"$HOME/.local/share/qwen-image-pipeline/ComfyUI/.venv/bin/python" -m pip install -e .
install -m 0755 deploy/run-comfyui.sh \
  "$HOME/.local/share/qwen-image-pipeline/run-comfyui.sh"
install -m 0755 deploy/run-comfyui-pool.sh \
  "$HOME/.local/share/qwen-image-pipeline/run-comfyui-pool.sh"
install -m 0644 deploy/systemd/qwen-comfyui.service \
  "$HOME/.config/systemd/user/qwen-comfyui.service"
systemctl --user daemon-reload
systemctl --user enable --now qwen-comfyui.service
```

The defaults keep the public API at `10.255.255.254:8188` and bind workers to
the same WSL loopback alias at ports `8191` through `8195`. To use a different
pool size or port range, add environment overrides to the service:

```ini
Environment=QWEN_COMFYUI_WORKERS=5
Environment=QWEN_COMFYUI_WORKER_BASE_PORT=8191
```

Workers share ComfyUI's image input and output directories so existing upload,
view, and Save Image behavior is unchanged. Each worker gets a separate SQLite
metadata database under `$QWEN_PIPELINE_ROOT/workers/worker-N/`, avoiding the
database lock that occurs when multiple ComfyUI processes use one state file.

Five workers allow five Codex sessions to have one Render Pass executing in
each local queue. This removes the local FIFO wait but does not raise Alibaba
or OpenRouter account limits; provider throttles and errors still pass back
through the unchanged `Qwen Image 3 Render` node.

The router aggregates `/queue` and `/history`, and keeps
`/history/<prompt_id>` on the worker that accepted the prompt. WebSocket
progress is intentionally rejected so clients fall back to HTTP history
polling; `comfyui-mcp` supports that fallback.
