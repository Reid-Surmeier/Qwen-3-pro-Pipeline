---
name: figma-qwen-ui-pipeline
description: Fast, repeatable Figma and FigJam operations for the Qwen UI pipeline. Use when Codex needs to inspect the Draw Over Software board, map notes and arrows, upload generated raster or SVG assets, replace an existing image fill, edit FigJam notes/connectors, create or update Figma UI screens, or implement a Figma screen as working web code without rediscovering authentication, file IDs, node IDs, and MCP call shapes.
---

# Figma Qwen UI Pipeline

Keep FigJam research, editable Figma design, generated assets, and working code as distinct layers with explicit provenance. Reuse the connected hosted Figma MCP server and the stable board targets in [references/targets.json](references/targets.json).

## Route the request

- Inspect or annotate the existing FigJam board: load `$figma-use` and `$figma-use-figjam`.
- Upload PNG, JPEG, WebP, or SVG assets: use `upload_assets`; do not use `figma.createImage()` in FigJam.
- Create or update a composed Figma screen: load `$figma-use` and `$figma-generate-design`.
- Create a new Figma file: load `$figma-create-new-file` before calling `create_new_file`.
- Implement an approved Figma frame as application code: load `$figma-implement-design`.
- Extract design context for code generation: load `$figma-design-to-code`.

Read [references/workflow.md](references/workflow.md) before the first mutation in a task.

## Fast path

1. Resolve the target from `references/targets.json`; do not search Figma by filename when the file key is known.
2. Call `get_figjam` once for the root or smallest relevant subtree. Cache the XML locally for the turn.
3. Use node IDs from that XML. Do not infer connections from proximity when connector endpoints are available.
4. Make one bounded mutation: upload an asset, edit a text node, add a connector, or create one screen section.
5. Return every created or mutated node ID.
6. Capture a focused screenshot of the changed node and compare it with the source before continuing.

Prefer native Figma MCP tools when they are exposed. If the tool wrapper is unavailable or deferred, use the bundled helper instead of rebuilding an HTTP client:

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs tools
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs get-figjam \
  --target draw-over-software-board --out /tmp/draw-over-software-board.xml
```

The helper reads the existing Codex Figma OAuth credential without printing it. Never pass tokens on the command line or place them in project files.

## Upload an image

Upload a new board asset without changing an existing node:

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs upload \
  --target draw-over-software-board --asset /absolute/path/variant.png
```

Replace the raster fill of an existing node only when replacement is explicitly intended:

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs upload \
  --target draw-over-software-board --asset /absolute/path/variant.png \
  --node-id 1:41 --scale-mode FIT
```

For experiments, preserve the PlantStudio source node and place named variants beside it. Use names that encode role and iteration, such as `golf-ui/club-preview/v001`.

## Edit native FigJam content

Before every `use_figma` call, read `$figma-use`; for board operations also read `$figma-use-figjam`. Follow their font-loading, page, atomicity, and return-ID rules.

Put JavaScript in a temporary file to avoid shell escaping:

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs use \
  --target draw-over-software-board --code-file /tmp/figma-edit.js \
  --description "Edit the selected FigJam note" \
  --skills figma-use,figma-use-figjam
```

Keep each call below ten logical operations. Stop on an error, inspect state, then issue a targeted correction; failed `use_figma` scripts are atomic.

## Performance rules

- Do not repeat OAuth setup while the authenticated `whoami` check succeeds.
- Batch independent reads and uploads.
- Use one root inspection, then focused node screenshots.
- Persist stable non-secret IDs in `references/targets.json`; refresh only when Figma returns a missing-node error.
- Preserve source images and add variants during exploration. Destructive replacement is a later, explicit step.
- Report the Figma URL, node IDs, screenshot validation, and any remaining drift after each iteration.
