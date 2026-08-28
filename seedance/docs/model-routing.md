# Model routing

## Seedance 2.0 Mini

Use `bytedance/seedance-2.0-mini` for motion studies, prompt comparisons, easing exploration,
matte tests, and low-cost seed sweeps. The live profile observed on 2026-08-22 supported 480p and
720p, 4–15 second clips, first/last frames, seed, generated audio, and image/video/audio references.

## Seedance 2.5

Use `bytedance/seedance-2.5` for final candidates, 16–30 second work, and cases where richer
multimodal fidelity matters. The live profile observed on 2026-08-22 supported 480p and 720p,
4–30 second clips, first/last frames, seed, generated audio, and multimodal references.

## Routing rules

- `study` selects Mini; `final` selects 2.5.
- An exact model ID is also allowed.
- Unsupported duration fails. A study longer than 15 seconds does not silently become a final.
- Store both model ID and canonical slug, because an alias can move.
- Re-run studies on 2.5 before final acceptance; model behavior is not assumed equivalent.
- Use `size` when exact canvas dimensions matter. Avoid supplying both `size` and
  `resolution + aspect_ratio`.

Live OpenRouter metadata remains authority over this dated note.

