# Own mask-aware sticker tooling in this repository

Status: accepted on 2026-08-26.

## Context

Issue #2 qualifies an opt-in mask-aware Assembly path. The live ComfyUI
installation already contained four project-owned nodes copied from
`maga-sticker-generation-snapshot` commit
`b8e226cb12f7cea8a201da73a852542938fdad9f`, but this repository could not
reproduce that runtime from its own checkout. A workflow referring to those
node classes without owning or pinning their source would hide a cross-repo
dependency.

## Decision

Port the exact four-node pack into this repository and preserve the originating
commit and hashes in the Issue #2 qualification record. This repository now
owns the active source, tests, and install procedure for:

- `StickerMaskBands`;
- `StickerPerspectiveWarp`;
- `MaskedReferenceFidelityGate`; and
- `ArtworkFidelityGate`.

The pack remains opt-in and deterministic. It operates after a Render Pass and
does not select a provider, submit a paid request, replace Qwen Image 3 Pro, or
change the five-worker router. Installation is explicit and does not restart
ComfyUI automatically.

## Consequences

- A checkout can reproduce the selected workflow without reading another
  repository at run time.
- Changes to these nodes require lightweight contract tests, Torch tests in the
  ComfyUI environment, live schema validation, and a no-cost workflow test.
- The originating commit remains provenance, not a second active source of
  truth.
- Perspective support remains a planar four-corner transform. Curved-surface
  displacement is still outside this node pack.
