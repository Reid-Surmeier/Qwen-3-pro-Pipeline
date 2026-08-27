---
name: verify-icon-animation
description: "Independently verify generated icon animations for media validity, endpoint fidelity, loop seams, temporal drift, style-guide compliance, and favicon-scale readability. Use after generation or when auditing a candidate."
---

# Verify an icon animation

Review without modifying the candidate. Machine checks, visual review, and final acceptance are
separate evidence layers.

## Procedure

1. Read the run brief, sanitized request, live capability snapshot, plan, job record, and output
   hash. Confirm they describe one submission and exact canonical model.
2. Run `seedance-icons verify` with all available first/last anchors and `--loop` when applicable.
3. Inspect ffprobe evidence: playable video stream, expected dimensions, duration within tolerance,
   and expected audio presence.
4. Inspect extracted first/last frames and a contact sheet at full size and delivery sizes.
5. Compare silhouette, proportions, negative space, strokes, joins, palette, typography, matte,
   framing, and safe area against source authority.
6. Inspect real-time and frame-stepped playback for edge shimmer, color pulsing, unwanted morphs,
   camera drift, duplicated elements, motion discontinuity, and loop seam.
7. Record each requirement as pass, fail, or needs human judgment with evidence paths. Do not tune a
   threshold after seeing the result merely to make it pass.
8. Mark the run verified only if machine gates pass. A human must separately mark it accepted.

## Guardrails

- Do not repair or replace the output while claiming independent verification.
- RMSE is compression-aware diagnostic evidence, not perceptual proof.
- A matching endpoint cannot prove intermediate style consistency or seamless velocity.
- If the background must become transparent, separately review keyed edge contamination at small
  sizes and on light/dark checkerboards.
