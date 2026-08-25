# ComfyUI sticker-tooling validation

Validated against the live routed ComfyUI service on 2026-08-25.

## Confirmed live

- ComfyUI `0.31.0`, frontend `1.48.7`, Python `3.12.4`, PyTorch
  `2.13.0+cu130`, RTX 4070 SUPER.
- `comfyui-mcp` is registered and can read health, queue, node schemas, and
  workflow validation through `http://10.255.255.254:8188`.
- Core mask/composite nodes: `LoadImage` mask output, `ImageToMask`,
  `ImageColorToMask`, `ThresholdMask`, `InvertMask`, `MaskComposite`,
  `GrowMask`, `FeatherMask`, `CropMask`, `MaskPreview`, and
  `ImageCompositeMasked`.
- Geometry/finishing nodes: `ImageRotate`, `ResizeImageMaskNode`, `ImageScale`,
  `ImageCropV2`, `ColorTransfer`, `ImageBlur`, `ImageSharpen`, and `Canny`.
- Existing pipeline node: `ReferenceFidelityGate`.

## Corrections to the research

- `ImageRotate` is limited to its installed rotation choices; it is not a
  projective transform.
- Searches for perspective, affine, homography, and displacement image nodes
  returned no matching live node. The only `warp` match was latent video noise,
  not sticker geometry.
- `QwenImageEditApi` is implemented by current upstream ComfyUI, but it is not
  present on this live server. The MCP API-node catalog returned zero Qwen
  partner nodes. The local provider-backed `Qwen Image 3 Render` node remains a
  separate integration and must not be described as that hosted API node.

Official upstream references:

- <https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_api_nodes/nodes_qwen.py>
- <https://github.com/Comfy-Org/docs/blob/main/tutorials/image/qwen/qwen-image-edit.mdx>

## Added capability

The `qwen_sticker_tooling` custom-node pack supplies only the missing
deterministic seams:

- `StickerMaskBands`
- `StickerPerspectiveWarp`
- `MaskedReferenceFidelityGate`
- `ArtworkFidelityGate`

Everything else is expressed with the existing live core nodes. The original
rectangle Assembly path remains available and unchanged.
