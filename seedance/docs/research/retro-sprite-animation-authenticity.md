# Retro Sprite Animation Authenticity — Research

**Date:** 2026-08-27
**Scope:** How authentic 8/16-bit game icon animation actually works; whether Seedance
(text prompt + first/last frame + duration + seed, fixed 24 fps, no negative prompt, no CFG)
can be steered toward that look prompt-side; and the deterministic post-processing +
gate metrics that guarantee it.

---

## 1. The mechanics of authentic retro sprite/icon animation

### 1.1 Hardware constraints that created the look

- **Tiny fixed palettes, no alpha blending.** On the NES, "backgrounds and sprites each
  have 4 palettes of 4 colors"; a sprite uses a single 4-color palette, entry 0 of each
  palette is transparent, and there is **no alpha blending capability** — only a hard
  priority system between background and sprite pixels
  ([NESdev wiki: PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)).
  Consequence: every retro "glow", "fade", or "shine" is a *palette trick*, never a
  translucent bloom. Any intermediate blended color at a sprite edge is an anachronism.
- **Indexed color everywhere.** VGA-era art was 8-bit indexed: "video cards could only
  render 256 colors at a time, so a palette of selected colors was used"; each pixel
  stores an index into the palette
  ([EffectGames, "Old School Color Cycling with HTML5"](https://www.effectgames.com/effect/article-Old_School_Color_Cycling_with_HTML5.html)).
- **Palette cycling instead of redrawn frames.** Animation was often achieved by
  *rotating palette entries*, not by drawing new frames: "change this palette at will,
  and all the onscreen colors would instantly change to match … It was fast, and took
  virtually no memory." Mark Ferrari produced "rain, snow, ocean waves, moving fog,
  clouds, smoke, waterfalls … without any layers or alpha channels — just one single
  flat image with one 256 color palette"
  ([EffectGames article](https://www.effectgames.com/effect/article-Old_School_Color_Cycling_with_HTML5.html);
  [Mark Ferrari, GDC 2016, "8 Bit & '8 Bitish' Graphics — Outside the Box"](https://www.gdcvault.com/play/1023586/8-Bit-8-Bitish-Graphics),
  [video](https://www.youtube.com/watch?v=aMcJ1Jvtef0);
  [Q&A with Mark J. Ferrari](https://www.effectgames.com/effect/article-Q_A_with_Mark_J_Ferrari.html)).
  This is the primary-source basis for the classic **"shine" effect**: a band of
  lighter palette indices marching across the sprite in discrete steps — the *colors
  step through indices*; pixels never blend.

### 1.2 Frame counts and timing (the sprite-animation grammar)

- **Very low unique-frame counts.** Practitioner pixel-VFX work documents effects built
  from "3 frames at 300ms," "4 frames at 200ms," and "6 frames and 100ms per frame";
  a comparatively lavish idle is "an 8-frame cycle" where "the body pose is 8 frames
  animated on twos over the whole animation"
  ([VFX Apprentice, "Pixel Art Meets VFX"](https://www.vfxapprentice.com/blog/pixel-art-game-effects-animated)).
  Translated: **2–8 unique frames, each held 100–300 ms ≈ 3–10 fps effective.**
- **Holds ("on twos"/"on threes") are the aesthetic**, not a defect: key poses are held
  for multiple ticks while transitions get 1–2 ticks; varying hold duration — not
  adding frames — is how pixel artists control pace and weight
  ([VFX Apprentice, ibid.](https://www.vfxapprentice.com/blog/pixel-art-game-effects-animated);
  Pedro Medeiros' free animation tutorials — Fundamentals, Idle, Squash, Sub-pixel,
  Outlines, Motion Blur — at [saint11.art](https://saint11.art/blog/pixel-art-tutorials/)
  and mirrored on [Lospec](https://lospec.com/pixel-art-tutorials/author/pedro-medeiros)).
- **Ragnarok Online's own timing unit confirms the coarseness:** in ACT files "the
  delay is given in units of 25ms each, so an animationDelay of 1 means 25ms in
  between each frame" — real sprites use multi-unit delays (e.g. 4 units = 100 ms =
  10 fps effective)
  ([RagnarokFileFormats ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)).

### 1.3 Motion rules

- **Whole-pixel displacement only.** Sprite layers in RO ACT frames move by integer
  X/Y offsets per frame ([ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)).
  Sub-pixel *implied* motion exists as a drawing technique (redrawing edge pixels /
  shifting color weight — Medeiros has a dedicated "Sub-pixel" tutorial,
  [saint11.art](https://saint11.art/blog/pixel-art-tutorials/)), but the pixel grid
  itself never slides fractionally.
- **Squash/stretch and motion blur are redrawn pixels, not filters.** Medeiros'
  "Squash" and "Motion Blur" tutorials show these as hand-placed pixel clusters
  (smears/multiples), not scaling or Gaussian blur
  ([saint11.art](https://saint11.art/blog/pixel-art-tutorials/)). Hardware could not
  scale NES sprites at all, and RO's **2D UI layer "does not implement sprite
  scaling"** even though the 3D world layer does
  ([ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)).
- **Stable outlines.** Sprites keep a consistent (often selectively colored) outline;
  "selective outlining … replace[s] a lot of the black outline with lighter colors"
  but the outline ring itself persists frame to frame
  ([Derek Yu, Pixel Art Tutorial: Basics](https://www.derekyu.com/makegames/pixelart.html)).
- **Blink/flash = palette swap or visibility toggle.** With no alpha, damage flashes
  and blinks were done by swapping the sprite's palette to white/inverted for held
  frames, or toggling sprite visibility — both are instantaneous index operations
  ([NESdev PPU palettes](https://www.nesdev.org/wiki/PPU_palettes);
  [EffectGames color-cycling article](https://www.effectgames.com/effect/article-Old_School_Color_Cycling_with_HTML5.html)).

### 1.4 How Ragnarok Online specifically animates — and the icon caveat

- RO entities are **SPR + ACT** pairs: SPR is a texture atlas of **indexed-color
  bitmaps with their palettes** (plus optional truecolor TGA frames)
  ([SPR.MD](https://github.com/Duckwhale/RagnarokFileFormats/blob/master/SPR.MD);
  [Ragnarok Research Lab: SPR](https://ragnarokresearchlab.github.io/file-formats/spr/)),
  and ACT defines actions → frames → layers with per-layer offset, mirror, tint,
  rotation, scale, and the 25 ms delay units
  ([ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)).
- **Critical finding: RO's item and skill icons do not animate.** The ACT
  documentation states item and spell icons are "completely static," using a single
  idle action that never animates; animated visuals in RO are the *cast/skill effects
  in the world*, not the UI icons
  ([ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)).
  So "an animated RO-style skill icon" is a *stylistic extrapolation*: the authentic
  reference grammar comes from RO's sprite animation system and 8/16-bit item/effect
  animation generally, not from RO's icon UI itself. Design implication: the most
  authentic animations for such icons are the ones a palette-era engine could do —
  palette cycling/shine sweeps, 2–4 frame redraw loops, whole-pixel bobs, flash
  frames — applied to an otherwise stable icon.

### The extracted grammar (summary table)

| Property | Authentic value | Source |
|---|---|---|
| Unique frames | 2–8 (icons/effects: 2–4 typical) | VFX Apprentice; saint11 |
| Effective rate | ~3–10 fps (100–300 ms holds) | VFX Apprentice; RO ACT 25 ms units |
| Color count | 4 (NES sprite) … ≤256 (VGA); fixed set | NESdev; EffectGames |
| Glow/shine | palette-index stepping, no alpha | Ferrari GDC; EffectGames |
| Motion | integer-pixel offsets; sub-pixel only via redraw | RO ACT; saint11 |
| Squash/blur | redrawn pixels, never filters/scaling | saint11; RO ACT (UI no scaling) |
| Outline | persistent, selectively colored | Derek Yu |
| Flash/blink | palette swap / visibility toggle, held frames | NESdev; EffectGames |

---

## 2. Prompt-side steering of Seedance: partially useful, not sufficient

### 2.1 What the model actually offers

- Seedance 1.0 pro I2V: "Generates a target video based on your input first-frame
  image + new last-frame image (optional) + text prompt (optional)"; output is fixed
  **24 fps**, 2–12 s, 480p/720p/1080p MP4. The docs list **no negative prompt and no
  CFG**; fidelity language is about *subject consistency* ("enhances face retention …
  between the first and last frames"), not exact pixel preservation
  ([BytePlus ModelArk: seedance-1.0-pro](https://docs.byteplus.com/en/docs/ModelArk/1587798);
  official prompt guide index: [ModelArk 1631633](https://docs.byteplus.com/en/docs/ModelArk/1631633)).
- Marketing/derivative guides describe first/last-frame mode as the model
  "synthesiz[ing] the frames in between … keeping subjects, colors, and composition
  coherent" — i.e., it is an *interpolator by design*
  ([Seedance first/last frame guide](https://www.seedance.tv/blog/seedance-first-and-last-frame)).

### 2.2 What prompt vocabulary is documented to do

- The fal.ai Seedance prompting guide's core advice is "Motion is what the model
  animates, so spend your words on verbs" with a Subject/Motion/Environment/Look/
  Camera structure — it documents **no mechanism for stepped, held, low-frame-rate,
  or stop-motion cadence**
  ([fal.ai Seedance prompting guide](https://fal.ai/learn/tools/seedance-2-0-prompting-guide)).
  No primary source found documents any Seedance control over temporal cadence;
  output cadence is architecturally fixed at 24 fps smooth interpolation
  ([BytePlus docs](https://docs.byteplus.com/en/docs/ModelArk/1587798)).
- Community workflows that do get game sprites out of video models treat the video as
  **raw material to post-process**: generate, then "scrub through the rendered video
  and identify frames representing essential stages of motion" and rebuild the sheet
  from ~8 extracted frames
  ([chongdashu/ai-game-spritesheets](https://github.com/chongdashu/ai-game-spritesheets)).
  Community experience with neural interpolation of pixel art reports the failure
  mode directly: interpolation "introduces color blending which isn't suitable for
  pixel art," plus alpha loss
  ([ResetEra: Interpolating pixel art animation with neural networks](https://www.resetera.com/threads/interpolating-pixel-art-animation-with-neural-networks.168281/)).
- **"Pixel art" as a style keyword is a re-render trigger, not a preservation
  instruction.** I2V guides describe style keywords as generation targets (the model
  re-synthesizes toward the described look while "preserving … subject, composition,
  and style" only loosely). This matches the observed blessing failure — the model
  redrew the icon as modern crisp pixel art. No documented Seedance control asserts
  "do not repaint the input." (Inference from
  [BytePlus docs](https://docs.byteplus.com/en/docs/ModelArk/1587798) +
  [fal.ai guide](https://fal.ai/learn/tools/seedance-2-0-prompting-guide); flagged in
  §4d as a gap — no vendor statement either way.)

### 2.3 Verdict

Prompt-side steering can **reduce the damage** (less camera motion, less invented
effect animation, motion confined to the subject) but **cannot produce** held frames,
locked palettes, or pixel-grid alignment, because the model has no cadence or palette
controls and its first/last-frame mode is explicitly a smooth interpolator. Prompting
is a *variance reducer*; the deterministic post pipeline (§3) is the *guarantee*.

Practical prompt rules that follow from the documented behavior:

1. **Describe motion, not style.** Never say "pixel art," "8-bit," "retro," or
   "crisp pixels" in the video prompt — style words invite re-rendering; the style is
   already fully specified by the anchor frames. Spend words on the *single* motion
   ("the sword icon's blade glints; a band of light passes diagonally across it").
2. **Anchor both ends with the same locked icon.** First and last frame = the exact
   source crop (or source + one hand-authored variant) so the interpolation is forced
   to return home; the docs confirm last-frame anchoring is supported and optional
   ([BytePlus](https://docs.byteplus.com/en/docs/ModelArk/1587798)).
3. **Forbid the camera.** "Static camera, no zoom, no pan, background completely
   still" — camera vocabulary is one of the few levers the prompt guides document
   ([fal.ai guide](https://fal.ai/learn/tools/seedance-2-0-prompting-guide)).
4. **One effect per clip, small amplitude.** "Subtle," "small movement," "the icon
   itself does not change shape" — verbs drive animation, so minimize verb count.
5. **Ask for holds anyway ("stop-motion, held poses, choppy low-frame-rate sprite
   animation")** — undocumented, occasionally helps, never rely on it; treat as a
   seed-search heuristic scored by the gate, not a control.

---

## 3. Deterministic post-processing: the reliable path

Every primitive below is a documented tool feature; chained, they *guarantee* the
grammar of §1 regardless of what the model emits.

### 3.1 Temporal quantization (holds)

Subsample the 24 fps output to N effective fps and re-hold. ffmpeg's `fps` filter
converts to a constant rate by duplicating/dropping frames
([ffmpeg-filters: fps](https://ffmpeg.org/ffmpeg-filters.html#fps-1)):

```bash
# 6 fps effective cadence, re-held to 24 fps container timing
ffmpeg -i raw.mp4 -vf "fps=6" -r 24 held.mp4
```

Better: extract frames at N fps, dedupe/select the K most distinct as the "sprite
sheet," then rebuild with explicit per-frame holds (mirroring RO's 25 ms-unit delay
model, [ACT.MD](https://github.com/rdw-archive/RagnarokFileFormats/blob/master/ACT.MD)) —
this yields an inspectable frame list the gate can count. Do **not** use `minterpolate`
(motion interpolation), `tmix`, or `tblend` (temporal averaging/blending) anywhere in
the chain — those are the smoothness generators
([ffmpeg-filters](https://ffmpeg.org/ffmpeg-filters.html)).

### 3.2 Palette locking

Quantize every frame to the **exact palette extracted from the source icon crop**,
with dithering off (dither = intermediate-color speckle = anachronism at 24–32 px):

- **ffmpeg:** `palettegen` (options `max_colors`, `stats_mode`, `use_alpha`) run on the
  *source still*, then `paletteuse` with `dither=none`
  ([ffmpeg-filters: palettegen/paletteuse](https://ffmpeg.org/ffmpeg-filters.html#palettegen-1);
  workflow and dither trade-offs by the filter's author:
  [pkh.me, "High quality GIF with FFmpeg"](https://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html)):

  ```bash
  ffmpeg -i source_icon.png -vf "palettegen=max_colors=32:stats_mode=single" pal.png
  ffmpeg -i held.mp4 -i pal.png -lavfi "paletteuse=dither=none" locked.mp4
  ```

- **PIL:** `Image.quantize(palette=palette_image, dither=Dither.NONE)` — the `palette`
  parameter means "quantize to the palette of given PIL.Image.Image", giving exact
  per-pixel nearest-index mapping under full programmatic control
  ([Pillow: Image.quantize](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize)).
  PIL is preferred for the gate because the same palette object drives both the
  transform and the measurement.

### 3.3 Pixel-grid re-snapping

Video generation happens at 480p+; the icon's native grid is ~24–26 px. Re-snap:

1. Downscale each frame to the native grid (e.g. 26×26) — use **mode/majority
   filtering** (most-common color per cell, implementable in numpy) or PIL
   `Resampling.NEAREST` ("use nearest neighbour")
   ([Pillow: resize/Resampling](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.resize)).
2. Palette-lock at native size (§3.2).
3. Upscale back with NEAREST only (integer factor), so every output "pixel" is a
   uniform k×k block — the definition of grid alignment.

This single step deletes sub-pixel motion, alpha-blended edges, and interpolated
smears, because none of them survive a mode-filtered downsample + palette lock.

### 3.4 Optional grammar synthesis (beyond conformance)

Because RO icon animation is an extrapolation anyway (§1.4), the pipeline can go
further and *synthesize* authentic effects deterministically instead of trusting the
model at all: take 2–4 gate-passing unique frames as poses, then add a palette-cycled
shine (rotate the light ramp indices, per Ferrari's technique
[GDC 2016](https://www.gdcvault.com/play/1023586/8-Bit-8-Bitish-Graphics)) or a
white-palette flash frame. This turns Seedance into a pose generator and moves all
"effects" into index arithmetic that is authentic by construction.

---

## 4. Recommended enforcement design

### (a) Sprite-grammar prompt rewrite rules

Rewrite every user/system animation prompt before submission:

1. Strip style tokens: `pixel art, 8-bit, 16-bit, retro, sprite, crisp, HD, detailed,
   glow, bloom, particles, cinematic` → removed (style comes from anchors; glow/bloom
   are the failure modes).
2. Template: `"{single concrete motion clause}. The object keeps its exact shape and
   colors. Static camera, no zoom, no pan. Plain still background. Subtle, small
   movement. Stop-motion feel, held poses."`
3. Anchors: first frame = source crop upscaled NEAREST to model resolution on a flat
   background; last frame = same image (loops) or one authored variant frame.
4. Duration minimal (2 s — smallest documented, [BytePlus](https://docs.byteplus.com/en/docs/ModelArk/1587798));
   seed-sweep and let the gate pick.

### (b) Deterministic retro-conformance post pipeline (order matters)

```
raw 24fps mp4
  → temporal subsample to N_fps (fps filter / frame extraction; no minterpolate/tmix/tblend)
  → dedupe near-identical frames → K unique frames (K ≤ 8)
  → per frame: downscale to native grid (mode filter, fallback NEAREST)
  → per frame: quantize to source palette, dither=NONE (PIL quantize(palette=…))
  → outline/background reconciliation vs source frame 0 (copy source pixels where
    outside allowed-change mask, optional)
  → NEAREST integer upscale to delivery size
  → reassemble at held cadence (each unique frame × hold count at 24fps, e.g. 4 → 6fps)
```

### (c) Gate metrics and suggested thresholds

Measured on the *native-grid, pre-upscale* frames; the gate runs on both the raw
model output (to score seeds) and the post-pipeline output (to certify):

| Metric | Definition | Threshold (certify) |
|---|---|---|
| Unique-frame count | frames with any pixel diff after grid-snap | 2 ≤ K ≤ 8 (icons: 2–4 preferred) |
| Effective fps | K × loops / duration | ≤ 10 fps |
| Palette conformance | % pixels whose RGB ∉ source palette (exact match) | 0% post-pipeline; raw-output seed score = fraction within ΔE < 8 of palette |
| Palette size | unique colors per frame | ≤ source palette size (≤ 32) |
| Grid alignment error | after k× NEAREST upscale, % of k×k blocks that are non-uniform | 0% post; raw score = mean intra-block variance |
| Blended-edge detector | count of boundary pixels whose color is a convex combination (within tolerance) of both neighbors' palette colors but ∉ palette | 0 post; raw score for seed ranking |
| Silhouette stability | IoU of alpha/background mask vs frame 0 | ≥ 0.90 (bob/shake allowed via integer-shift-compensated IoU) |
| Displacement integrality | best cross-correlation shift between consecutive frames | integer pixels only (post guarantees; raw score = sub-pixel residual) |
| Identity anchor | frame 0 vs source crop, per-pixel match after snap | ≥ 97% pixels identical |

Post-pipeline, the first six are guaranteed by construction; the gate's real
decisions are silhouette stability and identity (did the model redraw the icon?) —
fail → next seed / next prompt rewrite tier.

### (d) Confidence & gaps

- **High confidence:** hardware constraints and palette mechanics (NESdev, EffectGames,
  Ferrari GDC); RO ACT/SPR mechanics incl. 25 ms delay units and static UI icons
  (RagnarokFileFormats); ffmpeg/PIL primitive behavior (official docs + filter
  author's writeup); Seedance control surface (BytePlus official docs).
- **Medium confidence:** typical frame counts/holds — drawn from one detailed
  practitioner VFX source plus Medeiros' tutorial corpus (tutorials are published as
  GIF images; exact numbers were confirmed only from the VFX Apprentice text). The
  "2–4 frames for item icons" figure is a synthesis, not a single citable table.
- **Low confidence / gaps:**
  - No primary source documents Seedance's response to cadence vocabulary
    ("stop-motion", "choppy", "low frame rate") — treat as unverified heuristic; our
    own seed-sweep telemetry should become the evidence.
  - The official BytePlus Seedance prompt guide page
    ([ModelArk 1631633](https://docs.byteplus.com/en/docs/ModelArk/1631633)) could not
    be fetched (JS-rendered); its content may contain style-preservation guidance we
    haven't seen. Worth a manual read.
  - One documented community "pixel art with Seedance" attempt
    ([aawea.org](https://aawea.org/prompts/pixel-art-animation-attempt-with-seedance-2-0))
    was inaccessible (403); no verified claims taken from it.
  - Whether RO renders skill *icons* with any animation in modern clients was
    confirmed only via the ACT.MD statement ("completely static"); a client-side
    check (GRF inspection of `texture/…/item/*.bmp`) would make it airtight.
