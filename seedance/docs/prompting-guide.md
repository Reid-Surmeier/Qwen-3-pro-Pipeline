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

## Batch 3 — beat-by-beat, era-grounded, reference-paired (submitted 2026-08-27)

Redesign per owner feedback: references became visible evidence (real-game GIFs in
`../evidence/board-icons-test/references/`, provenance with sha256s and cadence
citations), prompts grew to 406–543 compiled words, and four of six cells left the
subtle-idle layer (Tier B cooldown wipe and press-fire; transition-layer coin spin and
item-get).

### Image-input chain changes vs batches 1–2

- **Crisp anchors**: each 104 px source crop is snapped to its 26 px native grid,
  16-color quantized, then 4x NEAREST upscaled — the model now receives hard pixels
  instead of soft screenshot texture. Files: `anchors/<icon>-anchor-crisp-640.png`,
  hashes in `source/hashes.json` (`crisp_anchor_sha256`).
- The crisp anchor is still sent twice (first_frame + last_frame, base64 data URLs).
- Config unchanged: mini · 4 s · `size 480x480` (delivered 640x640) · seed 1 · silent.

### Cell 7 (experimental): video-reference conditioning

`gloria` runs a second time with the real TCG coin-spin clip supplied as
`input_references[0].video_url` alongside both frame anchors
(`--experimental-mixed-inputs`). **API finding:** OpenRouter's `input_references`
accept only HTTPS URLs — a base64 data URL is rejected with
`400 "Only HTTPS URLs are allowed"` (frame_images accept data URLs; references do
not). The clip is therefore fetched from the repo's raw URL
(`references/ref-coin-spin.mp4`). Estimate $0.0454 vs $0.0756 for the anchor-only
cells.

### heal — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the heal icon — the white heart glyph and its red beveled square frame — must remain exactly as captured except the one described repeating movement.

LOCKED STYLE:
- the heart keeps its exact shape, colors, and soft blocky texture exactly as captured
- the square frame, its bevel, and the tile background stay perfectly rigid and still for the entire clip
- nothing is redrawn, repainted, sharpened, smoothed, or reinterpreted
- all movement is a whole-glyph position change between fixed poses; the glyph never deforms, stretches, or morphs
- stop-motion feel: every visible state is a held pose, and the picture jumps between poses with no in-between blending

MOTION:
The white heart runs a continuous two-pose idle loop for the whole clip, exactly like a handheld-game party icon. Pose A is the image exactly as captured. Pose B is the identical heart shifted up by one small step of its own blocky grid, with its bottom edge sitting one step higher. The clip alternates A, B, A, B without ever stopping: each pose is held for about a tenth of a second, then the picture snaps to the other pose. There are roughly twenty A-B rounds across the clip. Nothing accelerates, decelerates, eases, or drifts — the two poses are the only two pictures that ever exist, traded at a metronome-steady rate. The frame and background hold perfectly still through every swap.

TIMING:
Begin on pose A, the exact start image. Alternate A and B at a steady beat of about one tenth of a second per pose for the entire duration, with crisp instant swaps. Time the final swaps so the clip ends holding pose A, pixel-identical to the first frame.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, shadows, or added objects
- no smooth motion, no fades, no motion blur; only instant swaps between the two held poses
- no third pose: the heart is only ever in pose A or pose B
- do not change any color or redraw any part of the image
- the loop must not slow down, pause mid-clip, or change rhythm
```

### angelus — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the angelus icon — the small winged skull and its beveled square frame — must remain exactly as captured except the one described repeating movement.

LOCKED STYLE:
- the skull and both wings keep their exact shapes, colors, and soft blocky texture exactly as captured
- the square frame, its bevel, and the tile background stay perfectly rigid and still for the entire clip
- nothing is redrawn, repainted, sharpened, smoothed, or reinterpreted
- wing movement is a tiny position shift of the outer wing tips only, in whole steps of the image's own blocky grid; the wing shapes never bend, stretch, or morph
- stop-motion feel: every visible state is a held pose, and the picture jumps between poses with no in-between blending

MOTION:
The two outer wing tips run a continuous four-beat flap cycle for the whole clip while the skull and everything else stay frozen. The cycle has exactly three poses used in the order 1-2-3-2: pose 1 is the image exactly as captured; pose 2 has each outer wing tip shifted up by one small step of the blocky grid; pose 3 has each tip up by two steps. The clip walks 1, 2, 3, 2, 1, 2, 3, 2 continuously, each pose held for about an eighth of a second, snapping between poses with no blending. Both wings move together in perfect mirror symmetry. The inner wing roots next to the skull never move — only the outermost tip region rises and falls. Roughly eight full flap cycles fit across the clip at a steady, unhurried rhythm.

TIMING:
Begin on pose 1, the exact start image. Step through the 1-2-3-2 cycle at a steady beat of about one eighth of a second per pose for the entire duration. Time the final beats so the clip ends holding pose 1, pixel-identical to the first frame.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, shadows, or added objects
- no smooth motion, no fades, no motion blur; only instant swaps between the three held poses
- the skull, the frame, and the wing roots never move; only the outer wing tips shift
- do not change any color or redraw any part of the image
- the flap must not slow down, pause mid-clip, or change rhythm
```

### protect — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the protect icon — the silver-blue shield and its beveled square frame — must remain exactly as captured underneath the described overlay effect. The shield art itself is never altered, only covered and uncovered.

LOCKED STYLE:
- the shield keeps its exact shape, colors, and soft blocky texture exactly as captured; it never moves, scales, or redraws
- the square frame, its bevel, and the tile background stay perfectly rigid and still for the entire clip
- the cooldown effect is a flat dark cover layer ON TOP of the icon, like a piece of dark glass — the icon pixels underneath are unchanged and reappear exactly as captured when uncovered
- the cover's edge is a hard straight radius line from the center, aliased and crisp, never soft or feathered
- stop-motion feel: the sweep advances in small visible increments, each briefly held, never as one continuous smear

MOTION:
A skill-cooldown sweep plays once, exactly like a 2004 MMO action bar. Beat 1: the icon holds exactly as captured for a moment. Beat 2: a flat dark semi-transparent cover snaps on instantly over the whole square tile, darkening the shield to about forty percent brightness — the shield is still recognizable underneath, merely dimmed. Beat 3: the cover is eaten away clockwise, starting from the twelve o'clock position: a hard straight edge line from the tile center sweeps clockwise like a clock hand, and everything the line passes is uncovered back to full captured brightness, while everything not yet reached stays dimmed. The sweep advances in about twelve visible held increments, taking most of the clip, so the bright wedge grows from a sliver at twelve o'clock through three o'clock, six o'clock, nine o'clock, until the last dark sliver just before twelve vanishes. Beat 4: the instant the cover is fully gone, a small bright white-gold flat flash overlay appears across the shield at full strength and fades out in three visible held steps, each dimmer than the last, within half a second. Beat 5: the tile holds exactly as captured to the end.

TIMING:
Hold the exact start image briefly, snap the dark cover on, spend most of the clip on the stepped clockwise sweep, play the three-step end flash right as the sweep completes, and hold the exact start image again for the final portion so the last frame is pixel-identical to the first.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill; the dark cover and the flash exist only inside the square tile.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, soft light rays, particles, or added objects; the flash is a flat overlay, not a bloom
- the shield art is never redrawn, recolored, or moved — dimming comes only from the flat cover above it
- the sweep edge is never blurred, curved, or feathered
- no smooth continuous rotation; the sweep advances in distinct held increments
- do not leave a visible loop seam; the final frame returns exactly to the first frame
```

### resurrection — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the resurrection icon — the circular orb and its beveled square frame — must remain exactly as captured underneath the described overlay effects. The orb art itself is never altered, only overlaid.

LOCKED STYLE:
- the orb keeps its exact shape, colors, and soft blocky texture exactly as captured; it never moves, scales, or redraws
- the tile background stays in place; the only frame change is the described instant bevel press state
- overlay effects are flat layers ON TOP of the icon; the pixels underneath are unchanged and reappear exactly as captured when an overlay hides
- every state change is an instant snap between held states; nothing eases or glides
- stop-motion feel: the clip is a sequence of a few distinct held pictures

MOTION:
A button press-and-fire plays once, exactly like clicking a skill on a 2004 MMO action bar. Beat 1: the tile holds exactly as captured. Beat 2, the press: the beveled frame snaps instantly to a pressed state — the bevel highlight and shadow edges swap places so the tile reads as pushed one step inward; the orb itself does not move or change. Beat 3, the fire: a flat white overlay square covers the icon area at about sixty percent strength for just one brief held instant — a single blink — then vanishes, and the bevel snaps back to the captured state in the same instant. Beat 4, the queued blink: a flat red overlay border frame, sitting just inside the tile edge and about two grid steps thick, snaps fully on and holds for about four tenths of a second, snaps fully off for four tenths, on again for four tenths, off again — exactly two on-off rounds, with the orb and frame unchanged underneath and clearly visible through the open center of the red frame. Beat 5: the tile holds exactly as captured to the end.

TIMING:
Hold the exact start image for the first stretch, play the instant press and the single white blink near the one-third mark, run the two red on-off rounds at a steady four-tenths-of-a-second beat, and hold the exact start image again for the final stretch so the last frame is pixel-identical to the first.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill; the press state, white blink, and red frame exist only inside the square tile.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, or added objects; the white blink and red frame are flat overlays, not glows
- the orb art is never redrawn, recolored, or moved
- no fading: the white blink and the red frame turn fully on and fully off instantly
- the red frame's edges are hard and straight, never soft, and it never fills the tile center
- do not leave a visible loop seam; the final frame returns exactly to the first frame
```

### gloria — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the gloria icon's beveled square frame and background must remain exactly as captured; the rayed emblem in the center performs the described turn and returns to exactly its captured appearance.

LOCKED STYLE:
- the emblem keeps its exact colors and soft blocky texture in every pose; poses are drawn with the same limited palette and chunky structure as the captured art
- the square frame, its bevel, and the tile background stay perfectly rigid and still for the entire clip
- nothing is repainted, sharpened, smoothed, or style-modernized
- the turn is shown as a handful of distinct held poses, exactly like a flipped game coin — never a smooth 3D rotation
- stop-motion feel: each pose is held briefly, and the picture snaps from pose to pose with no in-between blending

MOTION:
The central emblem performs exactly one full spin about its vertical axis, shown the way a Game Boy duel coin shows a toss — as a short cycle of flat held poses, not a smooth rotation. Beat 1: the emblem holds exactly as captured. Beat 2, the spin, about eight held poses in sequence: the full face as captured; the face narrowed to about two thirds of its width; narrowed to a slim upright oval; collapsed to a thin vertical edge line a couple of grid steps wide; the slim oval again, now showing the back of the turn; two thirds width again; and finally the full face exactly as captured. Each pose is a flat picture held for roughly a tenth of a second, snapping to the next with no blending, no perspective, and no shading change — the narrowing poses simply compress the emblem's blocky forms horizontally around its vertical centerline while keeping its palette. The emblem stays centered the whole time; its height never changes; only its width steps through the cycle. Beat 3: after the single spin completes, the emblem holds exactly as captured for the rest of the clip.

TIMING:
Hold the exact start image for roughly the first third, play the one eight-pose spin cycle at a steady beat of about a tenth of a second per pose, and hold the exact start image again through the final third so the last frame is pixel-identical to the first.

CAMERA:
Static camera. No zoom, no pan, no rotation of the camera, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, particles, shadows, or added objects
- no smooth continuous rotation, no 3D shading, no perspective foreshortening, no motion blur — only flat held poses
- the emblem never leaves the tile center, never changes height, and never changes palette
- exactly one spin: the cycle must not repeat
- do not leave a visible loop seam; the final frame returns exactly to the first frame
```

### blessing — batch 3

```
SOURCE AUTHORITY:
The supplied image is the exact identity authority. Every pixel of the blessing icon — the small bottle and its beveled square frame — must remain exactly as captured except the one described presentation, which adds only the small sparkle shapes explicitly licensed below.

LOCKED STYLE:
- the bottle keeps its exact shape, colors, and soft blocky texture exactly as captured; it never deforms, stretches, or morphs
- the square frame, its bevel, and the tile background stay perfectly rigid and still for the entire clip
- nothing is redrawn, repainted, sharpened, smoothed, or reinterpreted
- the licensed sparkles are tiny flat blocky shapes in the same chunky structure as the captured art — plus-shaped four-block twinkles, pure white, at most a few grid steps across
- stop-motion feel: every visible state is a held pose, and the picture jumps between poses with no in-between blending

MOTION:
An item-get presentation plays once, exactly like a Game Boy Advance treasure reveal. Beat 1: the tile holds exactly as captured. Beat 2, the pop: the whole bottle jumps up by two small steps of its own blocky grid in one instant snap, holds that raised pose briefly, then snaps down to one step below its captured position for one brief held pose, then snaps back to exactly its captured position — a two-position quantized bounce, three snaps in all, with no easing and no stretching. Beat 3, the twinkle: right as the bottle lands, two tiny white plus-shaped sparkles appear in the empty tile area above the bottle, one upper-left and one upper-right of the bottle neck; each sparkle steps through a small grow-shrink cycle of three held poses — a single dot, the full plus shape, back to a dot — and vanishes completely, the pair offset so one twinkles a beat after the other. The sparkle cycle takes under a second in total. Beat 4: the tile holds exactly as captured, with no trace of the sparkles, through to the end.

TIMING:
Hold the exact start image for roughly the first third, play the three-snap bounce, run the short two-sparkle twinkle immediately after the landing, and hold the exact start image again through the final third so the last frame is pixel-identical to the first.

CAMERA:
Static camera. No zoom, no pan, no rotation, no perspective, no depth-of-field.

BACKGROUND / MATTE:
Plain still uniform #00FF00 background with no gradient, texture, shadow, or spill; the sparkles exist only inside the square tile, never on the background.

MUST NOT:
- nothing may cross the edge of the square onto the background
- no glow, bloom, light rays, halos, or soft particles; the two plus-shaped sparkles are the only added elements, and they are flat, hard-edged, and temporary
- the bottle is never redrawn, recolored, tilted, squashed, or stretched — it only changes position in whole steps
- no smooth motion, no fades, no motion blur; only instant snaps between held poses
- the sparkles must be gone well before the clip ends, leaving the image exactly as captured
- do not leave a visible loop seam; the final frame returns exactly to the first frame
```

### gloria (video-reference cell) — batch 3

Same compiled prompt as gloria above; the request additionally carries the real
coin-spin clip as a video reference (see Cell 7 notes).
