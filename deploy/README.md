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
install -m 0755 deploy/run-comfyui.sh \
  "$HOME/.local/share/qwen-image-pipeline/run-comfyui.sh"
install -m 0644 deploy/systemd/qwen-comfyui.service \
  "$HOME/.config/systemd/user/qwen-comfyui.service"
systemctl --user daemon-reload
systemctl --user enable --now qwen-comfyui.service
```
