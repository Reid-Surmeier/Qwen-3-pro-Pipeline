# Domain context

## Purpose

Produce small, style-locked icon animations through an inspectable OpenRouter/Seedance workflow.

## Language

- **Source authority**: the exact icon or frame whose identity must be preserved.
- **Style lock**: geometry, silhouette, stroke, palette, typography, material, negative space,
  and background constraints that must not drift.
- **Motion brief**: intent, path, easing, timing, holds, secondary motion, and exclusions.
- **Study**: a disposable Seedance 2.0 Mini iteration used to learn about motion/prompt behavior.
- **Final**: a Seedance 2.5 candidate intended for acceptance review.
- **Anchor**: an exact first or last frame supplied to the model.
- **Reference**: image, video, or audio guidance that is not an exact frame anchor.
- **Matte**: a deliberate solid background used when the delivery format has no native alpha.
- **Run**: immutable request/evidence directory for one paid submission.
- **Verified**: machine checks completed; not the same as visually accepted.
- **Accepted**: a human explicitly approved the visual result.

## State flow

`briefed -> planned -> cost-approved -> submitted -> generated -> verified -> reviewed -> accepted`

Failed or rejected candidates remain as evidence. They are not overwritten.

