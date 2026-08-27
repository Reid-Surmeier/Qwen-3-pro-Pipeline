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
- `verify-node-source.sh` asserts that the running ComfyUI serves node code
  from the intended checkout. `run-comfyui.sh` calls it before the pool starts.
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

## Node source drift

Two host-side links decide which code the pool actually serves, and they drift
independently of the repository:

1. the editable install of `qwen_ui_pipeline` inside `ComfyUI/.venv`, and
2. the `custom_nodes/qwen_image_3_openrouter` symlink.

On 2026-08-26 both pointed at stale worktrees, one of them a branch whose pull
request had been closed unmerged. The service reported healthy, the nodes
loaded, and every change merged to `main` was invisible to the running server.
Nothing in the pipeline output distinguished that state from a correct one.

`verify-node-source.sh` makes it loud instead:

```bash
deploy/verify-node-source.sh
```

It resolves the package through the ComfyUI interpreter from a neutral working
directory, since running inside the repository would let the current directory
shadow the installed mapping and report a false pass. It exits non-zero naming
both the expected and actual paths and the command that repairs them.

It reports and stops; it never repairs on its own, because reinstalling
silently could discard work an operator deliberately placed on the host.

Point it at a different checkout with `QWEN_PIPELINE_REPO`.
