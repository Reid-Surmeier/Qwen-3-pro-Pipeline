# Verification

Verification has three independent layers.

## Media checks

`seedance-icons verify` uses `ffprobe` and `ffmpeg` to record codec/container streams, dimensions,
duration, audio presence, first frame, and last frame. Duration tolerance is 0.35 seconds.

## Pixel evidence

Compression-aware RMSE is recorded between supplied anchors and extracted frames. For a loop, the
first/last seam RMSE is also recorded. RMSE is diagnostic, not a universal acceptance threshold:
edge contamination and perceptual drift still require inspection.

## Human style review

Review a contact sheet and real-time playback at delivery scale. Confirm:

- silhouette, proportions, negative space, stroke weight, palette, and typography remain locked;
- no unrequested morphing, object invention, texture, camera motion, lighting drift, or wobble;
- the motion path, easing, anticipation, overshoot, squash/stretch, holds, and loop seam match the
  brief;
- a keyed matte does not contaminate antialiased edges;
- the favicon remains legible at 16, 32, 48, and 64 pixels;
- any audio is intentional and synchronized.

Record review separately from machine verification. Only a human can mark a run accepted.
