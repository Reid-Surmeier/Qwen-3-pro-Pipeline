# Separate generative rendering from deterministic assembly

Status: accepted on 2026-08-10.

Use image models for controlled Render Passes and isolated visual assets, but keep Figma and application code authoritative for final layout, Exact Copy, and interaction. ComfyUI coordinates model calls and image operations; it does not turn generated raster text into the source of truth. This preserves the speed and stylistic range of Qwen Image 3 while avoiding irreversible dependence on probabilistic typography and layout.
