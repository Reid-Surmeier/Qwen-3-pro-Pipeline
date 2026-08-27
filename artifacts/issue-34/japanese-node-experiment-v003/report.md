# Issue 34 result: hard region Assembly is the useful node path

The direct Qwen outputs successfully removed the Effect row, but they redrew the whole interface. The implemented node path uses that successful output only as a donor inside `160,130,1350,350` and keeps the original source everywhere else.

## Measured result

- Two independent node outputs completed successfully.
- Candidate 1 changed 378,801 pixels inside the declared edit rectangle.
- Candidate 1 changed **0 RGBA pixels outside** the rectangle.
- Against the matched full-canvas donor, the node restored 601,136 exterior RGBA pixels and changed **0 pixels inside** the edit rectangle. This isolates the node contribution from Qwen's edit.
- Original Japanese title `オプション` and footer `スナップ` are source-owned, not regenerated.
- Feathered Assembly was rejected because it adds a visible horizontal seam.
- The focused-crop paid arm timed out ambiguously after 180.352 seconds. It was counted as possibly billed and was not retried.
- Confirmed direct-baseline cost: **$0.083**. Focused-crop billing remains unknown.

## What the node changes

`ReferenceRegionComposite` now has an opt-in source-alpha input. It replaces only the chosen rectangle and copies the source alpha exactly outside it. The default workflow behavior is unchanged.

The GUI-auditable workflow is saved in the ComfyUI library as `issue-34-japanese-hard-region-assembly-v003.json`. A read-back confirmed its four-node graph and source-mask connection. A dependency lock could not be generated because the MCP process does not have a local `COMFYUI_PATH`; this is recorded as a limitation, not treated as verification.

Candidate 1 is the selected comparison candidate because its BGM and Skin spacing is more even. Human visual approval is still required before merge.
