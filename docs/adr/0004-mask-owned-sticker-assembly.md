# Use mask-owned layers for sticker Assembly

Status: accepted on 2026-08-25.

## Context

Rectangle Assembly proves that pixels outside one bounded edit remain exact,
but a rectangle cannot express a sticker silhouette, white cutline, overlapping
stickers, or a narrow material-contact band. Asking a Render Pass to reproduce
approved artwork and integrate it physically gives the model ownership of too
many pixels and can corrupt type, logos, and line art.

The live ComfyUI already provides core mask operations and
`ImageCompositeMasked`. It does not provide a general image-and-mask
perspective, affine, homography, or displacement warp. The hosted
`QwenImageEditApi` node is also absent from this installation.

## Decision

Keep the existing rectangle `assembly-workflow` unchanged. Add an opt-in
`mask-assembly-workflow` with explicit ownership layers:

1. Project the approved artwork and silhouette together with
   `StickerPerspectiveWarp`.
2. Split the silhouette into artwork interior, white cutline, and contact band
   with `StickerMaskBands`.
3. Composite the white cutline and approved artwork deterministically with
   `ImageCompositeMasked`.
4. Restrict color-matched Qwen/material pixels to the contact band.
5. Fail before `SaveImage` unless `MaskedReferenceFidelityGate` proves that
   pixels outside the union remain exact and `ArtworkFidelityGate` proves that
   the approved artwork and silhouette remain within their configured bounds.

The sticker nodes are a separate custom-node pack. They do not import or alter
provider clients, Render Pass construction, fallback behavior, the concurrent
router, or the original rectangle Assembly node.

## Consequences

- Multiple and non-rectangular ownership regions can be composed without
  granting the model authority over the whole bounding box.
- Feathering and material treatment belong only in the contact band; exact
  artwork remains binary-mask owned.
- Perspective placement is deterministic and keeps artwork and mask geometry
  synchronized.
- Curved-surface displacement remains a future capability. A four-corner warp
  models planar faces, not depth-varying surfaces.
- The API-node alternative remains optional and paid. Installing or enabling it
  is not required for this local mask Assembly path.
