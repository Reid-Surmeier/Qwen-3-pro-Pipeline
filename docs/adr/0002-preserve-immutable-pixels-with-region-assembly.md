# Preserve immutable pixels with region assembly

Status: accepted on 2026-08-10.

## Context

The object-only golf test showed that a detailed Preservation Invariant can
substantially reduce generative drift, but it cannot make a full-screen Render
Pass byte-identical outside the requested edit. Correcting the output aspect
ratio improved the result materially, yet the model still redrew UI text,
rules, and plant pixels.

ComfyUI also routes GIF input through a video loader that changes many color
values by approximately one 8-bit level. A lossless PNG conversion of the same
Reference Screen does not have that problem.

## Decision

Use a two-stage path for strict reference preservation:

1. Generate a source-ratio batch and select an approved donor image.
2. At the source resolution, copy only the declared edit region from the donor
   onto a lossless PNG Reference Screen.

The `Reference Region Composite` ComfyUI node owns this deterministic Assembly.
A Fidelity Check must prove zero changed pixels outside the declared region
before an output can be called exact-preservation.

## Consequences

- Long Qwen Image 3 instructions remain useful for describing the intended
  object, style, spatial role, and forbidden content, but are not the mechanism
  that guarantees immutable pixels.
- Model-generated UI text is exploratory. Exact Copy remains native Figma or
  application text.
- Multi-region edits require explicit masks or separate region assemblies.
- GIF references must be losslessly normalized to PNG before strict Assembly.
