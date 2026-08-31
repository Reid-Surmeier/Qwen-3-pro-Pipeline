# Figma and ComfyUI workflow

## Figma source authority

1. Record file key, node ID, export settings, export hash, and style-guide revision.
2. Preserve the source node. Put first-frame, last-frame, and generated contact sheets beside it.
3. Export at a larger square size with a locked safe area; review again at favicon sizes.
4. Add notes for intended motion, timing, and rejected variations without replacing history.

## ComfyUI execution

The custom nodes expose request building and explicit cost planning. The workflow template does not
auto-submit a paid request. Use the CLI cost gate or a deliberately configured execution node after
approval. MCP automation should upload references, queue a named workflow, read back the history,
and attach output/job hashes to the run—not hide provider state.

The installer uses a dedicated ComfyUI checkout. Never install into or restart an unknown shared
runtime. See `scripts/install_comfyui.sh`.
