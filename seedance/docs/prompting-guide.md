# Prompting guide — what the model is actually given

Owner request (2026-08-27): expose the inputs, not just the outputs. This guide records,
for every run in `docs/evidence/board-icons-test/`, the exact text prompt and the exact
image inputs sent to `bytedance/seedance-2.0-mini`.

## How a prompt is built

`seedance-icons plan` compiles the motion brief through `compile_prompt`
(`src/seedance_icons/brief.py`) into labeled blocks, always in this order:

```
SOURCE AUTHORITY:  what is identity-exact
LOCKED STYLE:      what may never change
MOTION:            the one gesture (batch 2: cites an era idiom)
TIMING:            holds and settle
CAMERA:            static-camera lock
BACKGROUND / MATTE: the key matte contract
MUST NOT:          negative constraints
```

Sprite-grammar rules applied since the retro gate (docs/retro-conformance-gate.md): no
style tokens ("pixel art", "8-bit", "glow" — they trigger re-rendering), one small
stepped motion, stop-motion vocabulary, hard containment negatives.

## Image-input chain (identical for every run)

1. Board screenshot: FigJam `SWuBeRWPrhVZ6GW2kqGz1o` node `0:4` exported at max
   dimension 2048 (rendered 1617x1577) via the repo Figma helper.
2. Crop: 104x104 box per icon (coordinates below) → `source/crop-<icon>-tight.png`.
3. Anchor: crop upscaled **4x NEAREST** (no smoothing) to 416x416, centered on a solid
   `#00FF00` matte at **640x640** → `anchors/<icon>-anchor-640.png`.
4. The anchor is sent **twice** — as `first_frame` and as `last_frame` (base64 data
   URLs in `frame_images`). No other image reference is sent.

Request config, every run: duration 4 s · `size 480x480` (provider delivers 640x640) ·
seed 1 · `generate_audio false`.

| Icon | Crop box in node 0:4 (x0,y0,x1,y1) | Crop sha256 (12) | Anchor sha256 (12) |
| --- | --- | --- | --- |
| heal | (656, 182, 760, 286) | `1efa74253e97` | `f93ff9e4b060` |
| protect | (136, 448, 240, 552) | `4b9fe09ac9f8` | `62cfada47418` |
| blessing | (1392, 186, 1496, 290) | `2e20124aa2a2` | `68bd97bf9347` |
| holy-light | (136, 186, 240, 290) | `6a01fec2d9f3` | `5a12d2f5080f` |
| resurrection | (396, 186, 500, 290) | `2ca0ac3eb177` | `49151ff05fdb` |
| aqua-benedicta | (916, 186, 1020, 290) | `ae175d46f5c4` | `c29104e1b839` |
| sanctuary | (656, 448, 760, 552) | `51c6ee5090f5` | `74f6f739344e` |
| angelus | (656, 712, 760, 816) | `75b4b2f43386` | `17871d2eff08` |
| gloria | (136, 1246, 240, 1350) | `35eb1ee0ec53` | `9555ca258027` |

## Exact compiled prompts, per run

### heal — batch 1 (rejected grammar)

```
SOURCE AUTHORITY:
The supplied Ragnarok-style Heal skill icon (pink pixel-art heart marked 'AB' in a red beveled tile) is the exact identity authority. Preserve its silhouette, pixel structure, palette, and tile frame.

LOCKED STYLE:
- 24px-origin pixel-art skill icon inside a beveled rounded-square tile, as captured (already upscaled with soft pixel edges)
- the tile frame, bevel, and background stay perfectly rigid and static for the entire clip
- no smoothing, no vector redraw, no repainting; the pixel structure and limited palette are the identity
- no added text, particles, objects, glow halos outside the tile, or style modernization
- icon tile stays exactly centered; all motion is contained inside the tile

MOTION:
The heart glyph alone performs one soft heartbeat pulse: a slight scale-up of about 5 percent and back, like a single gentle beat. The tile frame does not move.

TIMING:
Hold the exact start pose for the first 8%, perform one gesture, settle by 88%, and hold the identical pose through the end frame.

CAMERA:
Locked orthographic front view. No pan, zoom, roll, perspective, reframing, or depth-of-field.

BACKGROUND / MATTE:
Uniform #00FF00 key matte with no gradient, spill, texture, or shadow. Transparency is produced and inspected separately.

MUST NOT:
- do not redraw or reinterpret the icon or its frame
- do not change palette, stroke, bevel, or corner treatment
- do not introduce edge shimmer, color pulsing, or background drift
- do not leave a visible loop seam; final frame returns exactly to the first frame
```

### protect — batch 1 (rejected grammar)

```
SOURCE AUTHORITY:
The supplied Ragnarok-style Protect skill icon (silver-blue pixel-art shield on a dark beveled tile) is the exact identity authority. Preserve its silhouette, pixel structure, palette, and tile frame.

LOCKED STYLE:
- 24px-origin pixel-art skill icon inside a beveled rounded-square tile, as captured (already upscaled with soft pixel edges)
- the tile frame, bevel, and background stay perfectly rigid and static for the entire clip
- no smoothing, no vector redraw, no repainting; the pixel structure and limited palette are the identity
- no added text, particles, objects, glow halos outside the tile, or style modernization
- icon tile stays exactly centered; all motion is contained inside the tile

MOTION:
A single narrow diagonal gleam of light sweeps once across the shield face from upper-left to lower-right, respecting the pixel style. Nothing else moves.

TIMING:
Hold the exact start pose for the first 8%, perform one gesture, settle by 88%, and hold the identical pose through the end frame.

CAMERA:
Locked orthographic front view. No pan, zoom, roll, perspective, reframing, or depth-of-field.

BACKGROUND / MATTE:
Uniform #00FF00 key matte with no gradient, spill, texture, or shadow. Transparency is produced and inspected separately.

MUST NOT:
- do not redraw or reinterpret the icon or its frame
- do not change palette, stroke, bevel, or corner treatment
- do not introduce edge shimmer, color pulsing, or background drift
- do not leave a visible loop seam; final frame returns exactly to the first frame
```

### blessing — batch 1 (rejected grammar)

```
SOURCE AUTHORITY:
The supplied Ragnarok-style Blessing skill icon (small blue potion bottle with golden sparkles in an amber beveled tile) is the exact identity authority. Preserve its silhouette, pixel structure, palette, and tile frame.

LOCKED STYLE:
- 24px-origin pixel-art skill icon inside a beveled rounded-square tile, as captured (already upscaled with soft pixel edges)
- the tile frame, bevel, and background stay perfectly rigid and static for the entire clip
- no smoothing, no vector redraw, no repainting; the pixel structure and limited palette are the identity
- no added text, particles, objects, glow halos outside the tile, or style modernization
- icon tile stays exactly centered; all motion is contained inside the tile

MOTION:
The bottle gives one gentle tilt of a few degrees to the left and returns upright while the existing golden sparkles twinkle once. The tile frame does not move.

TIMING:
Hold the exact start pose for the first 8%, perform one gesture, settle by 88%, and hold the identical pose through the end frame.

CAMERA:
Locked orthographic front view. No pan, zoom, roll, perspective, reframing, or depth-of-field.

BACKGROUND / MATTE:
Uniform #00FF00 key matte with no gradient, spill, texture, or shadow. Transparency is produced and inspected separately.

MUST NOT:
- do not redraw or reinterpret the icon or its frame
- do not change palette, stroke, bevel, or corner treatment
- do not introduce edge shimmer, color pulsing, or background drift
- do not leave a visible loop seam; final frame returns exactly to the first frame
```

### holy-light — batch 1 (rejected grammar)

```
SOURCE AUTHORITY:
The supplied Ragnarok-style Holy Light skill icon (golden pixel-art cross with rays in a cream beveled tile) is the exact identity authority. Preserve its silhouette, pixel structure, palette, and tile frame.

LOCKED STYLE:
- 24px-origin pixel-art skill icon inside a beveled rounded-square tile, as captured (already upscaled with soft pixel edges)
- the tile frame, bevel, and background stay perfectly rigid and static for the entire clip
- no smoothing, no vector redraw, no repainting; the pixel structure and limited palette are the identity
- no added text, particles, objects, glow halos outside the tile, or style modernization
- icon tile stays exactly centered; all motion is contained inside the tile

MOTION:
The cross and its existing rays brighten softly in one gentle bloom and dim back to the start, keeping the same pixels lit. No new rays or halo appear.

TIMING:
Hold the exact start pose for the first 8%, perform one gesture, settle by 88%, and hold the identical pose through the end frame.

CAMERA:
Locked orthographic front view. No pan, zoom, roll, perspective, reframing, or depth-of-field.

BACKGROUND / MATTE:
Uniform #00FF00 key matte with no gradient, spill, texture, or shadow. Transparency is produced and inspected separately.

MUST NOT:
- do not redraw or reinterpret the icon or its frame
- do not change palette, stroke, bevel, or corner treatment
- do not introduce edge shimmer, color pulsing, or background drift
- do not leave a visible loop seam; final frame returns exactly to the first frame
```

### resurrection — batch 2 (era-corpus grammar)

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the resurrection icon and its square frame must remain as captured except the one described movement.

LOCKED STYLE:
- the object keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame and its border stay perfectly still for the entire clip
- nothing is redrawn, repainted, sharpened, or reinterpreted
- subtle, small movement only; stop-motion feel with held poses

MOTION:
The bright core of the circular orb alternates between two brightness states in visible held steps, like a slow blink. Nothing moves and nothing else changes.

TIMING:
Hold the exact start image for the first quarter, make the small stepped change, and return to exactly the start image for the final quarter.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects
- no smooth fades or continuous motion; every change happens in visible held steps
- do not change any color or redraw any part of the image
```

### aqua-benedicta — batch 2 (era-corpus grammar)

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the aqua benedicta icon and its square frame must remain as captured except the one described movement.

LOCKED STYLE:
- the object keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame and its border stay perfectly still for the entire clip
- nothing is redrawn, repainted, sharpened, or reinterpreted
- subtle, small movement only; stop-motion feel with held poses

MOTION:
A tiny spark of light steps across the water surface from left to right in three separate held positions, one visible jump at a time. Everything else is frozen.

TIMING:
Hold the exact start image for the first quarter, make the small stepped change, and return to exactly the start image for the final quarter.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects
- no smooth fades or continuous motion; every change happens in visible held steps
- do not change any color or redraw any part of the image
```

### sanctuary — batch 2 (era-corpus grammar)

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the sanctuary icon and its square frame must remain as captured except the one described movement.

LOCKED STYLE:
- the object keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame and its border stay perfectly still for the entire clip
- nothing is redrawn, repainted, sharpened, or reinterpreted
- subtle, small movement only; stop-motion feel with held poses

MOTION:
The golden tones of the figure flash one step brighter and settle back, a slow two-state blink. Zero movement anywhere; only the gold shades change.

TIMING:
Hold the exact start image for the first quarter, make the small stepped change, and return to exactly the start image for the final quarter.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects
- no smooth fades or continuous motion; every change happens in visible held steps
- do not change any color or redraw any part of the image
```

### angelus — batch 2 (era-corpus grammar)

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the angelus icon and its square frame must remain as captured except the one described movement.

LOCKED STYLE:
- the object keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame and its border stay perfectly still for the entire clip
- nothing is redrawn, repainted, sharpened, or reinterpreted
- subtle, small movement only; stop-motion feel with held poses

MOTION:
The two wing tips shift up by one tiny step, return, then down by one tiny step, each pose held, like a slow sprite wing flap. The skull and frame are frozen.

TIMING:
Hold the exact start image for the first quarter, make the small stepped change, and return to exactly the start image for the final quarter.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects
- no smooth fades or continuous motion; every change happens in visible held steps
- do not change any color or redraw any part of the image
```

### gloria — batch 2 (era-corpus grammar)

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the gloria icon and its square frame must remain as captured except the one described movement.

LOCKED STYLE:
- the object keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame and its border stay perfectly still for the entire clip
- nothing is redrawn, repainted, sharpened, or reinterpreted
- subtle, small movement only; stop-motion feel with held poses

MOTION:
The four outer ray tips of the emblem blink on and off together while the small center switches to its brightest shade, a simple two-state twinkle in held steps.

TIMING:
Hold the exact start image for the first quarter, make the small stepped change, and return to exactly the start image for the final quarter.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects
- no smooth fades or continuous motion; every change happens in visible held steps
- do not change any color or redraw any part of the image
```

## Why batch 1 and batch 2 prompts differ

Batch 1 briefs described continuous gestures ("gleam sweeps", "bloom") with pixel-art
style tokens in the style lock — the model answered with smooth VFX and, once, a full
redraw. Batch 2 briefs are translations of cited era idioms
(`docs/research/era-ui-animation-reference-corpus.md` §prescriptions; each brief JSON in
`briefs-v2/` records its `era_idiom_basis`) using stop-motion vocabulary and zero style
tokens. Structural failures went from 2/4 to 0/5.

