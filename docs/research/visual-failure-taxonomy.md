# Visual failure taxonomy — v0.1.0

Issue: [#26 — When results look "AI"](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/26)

This taxonomy names the observable defect classes that make a generated
candidate "look AI" or clearly failed **relative to its Reference Screen and
Edit Brief**. It is a task-relative failure vocabulary, not an AI-origin
detector: appearance alone cannot prove model origin, and intentional
pixelation, collage, or stylization must never be rejected merely for looking
synthetic.

Every class below is grounded in at least one preserved repository artifact.
The seed corpus lives in `artifacts/issue-26/annotations/` as machine-readable
records with SHA-256 identity, defect classes, approximate regions, and
dispositions. Annotation regions produced by model vision are advisory;
deterministic gates (hashes, dimensions, outside-region pixel counts) remain
the only hard-reject authority, and final visual acceptance stays human-owned.

## The three-layer gate

1. **Deterministic hard gates** — dimensions, channel/alpha checks, SHA-256
   identity of protected regions, zero changed pixels outside declared edit
   regions, duplicate-count invariants. These may hard-reject automatically.
2. **Advisory visual critique** — a model-vision pass that must cite a
   taxonomy class, an approximate region, and the violated contract clause.
   It may recommend rejection and a bounded next experiment; it may not
   approve, submit paid requests, or broaden masks.
3. **Human decision** — final acceptance, rejection, and next-direction
   authority. Silence is not approval.

## Failure classes

Severity guidance: `hard` classes are deterministically checkable and should
gate automatically once instrumented; `strong` classes are visually
unambiguous to a sighted reviewer; `weak` classes need corroboration before
rejection.

### Text and copy

| ID | Class | Signal | Severity | Seed evidence |
| --- | --- | --- | --- | --- |
| T01 | `exact-copy-corruption` | Glyphs in a preserve-exactly region are garbled, respelled, or re-kerned ("PlantStudo - Librarv of wildflnuwers"). | hard (OCR/pixel diff where reliable), else strong | golf-club v001 images 02 and 04 title bars |
| T02 | `semantic-text-mismatch` | Legible text whose meaning contradicts the depicted object or brief (a marble bust captioned フクロペンギン, "sack penguin"). | strong, `context_missing` until source/brief known | Issue #26 attached example |
| T03 | `logotype-corruption` | A wordmark or script logo re-drawn with malformed ligatures, stray apostrophes, or wrong letterforms while remaining superficially plausible. | strong | palantir v001 candidate 4 |

### Object structure

| ID | Class | Signal | Severity | Seed evidence |
| --- | --- | --- | --- | --- |
| T10 | `topology-melt` | Adjacent parts merge into one mass; a club hosel becomes an L-block; part boundaries lose meaning. | strong | golf-club v001 image-02 club head |
| T11 | `object-identity-drift` | The requested object is replaced by a near-neighbor (a rounded putter blob instead of a seven-iron). | strong | golf-club v001 image-03 |
| T12 | `anatomy-support-incoherence` | Anatomy or supporting structure cannot exist in 3D: shelf-like protruding chest cross-section on a bust, impossible occlusion. | strong | Issue #26 attached example |
| T13 | `duplicated-ghost-geometry` | Semi-transparent duplicates, doubled stems/edges, echo silhouettes. | strong | golf-club v001 image-04 right plant group |

### Layout and geometry

| ID | Class | Signal | Severity | Seed evidence |
| --- | --- | --- | --- | --- |
| T20 | `global-redraw` | The whole Reference Screen is re-interpreted when the brief confined the edit to one region: every plant re-rendered, chrome re-set. | strong (hard once outside-region diff is instrumented) | golf-club v001 all four candidates |
| T21 | `aspect-ratio-drift` | Output aspect differs from the source contract (474x403 ≈ 1.18:1 rendered at 4:3). | hard | golf-club v001 (1152x864) vs reference |
| T22 | `crop-composition-drift` | Content cut at canvas edges that the source shows in full (title bar, tab row truncated). | strong | golf-club v001 images 01 and 04 |
| T23 | `frame-content-misalignment` | Inner content offset within its own frame; uneven margins the source does not have. | strong | palantir v001 candidate 4 |
| T24 | `element-boundary-collision` | A drawn element runs into or through a border it should terminate before. | strong | palantir v001 candidate 3 arc; maga v003 swoosh into border |

### Surface and style

| ID | Class | Signal | Severity | Seed evidence |
| --- | --- | --- | --- | --- |
| T30 | `style-smoothing` | Pixel-era aliased artwork returned as smooth anti-aliased or photoreal rendering. | strong | golf-club v001 club shaft gradient |
| T31 | `micro-texture-worms` | Halftone or grain replaced by worm-like repeating micro-glyph noise, visible at 100%. | weak | maga v003 flag/field texture |
| T32 | `template-remnant` | A structural element of the style-donor template survives into the new design where it has no role. | strong | maga v003 retained XP swoosh |

### Assembly and alpha (deterministically checkable today)

| ID | Class | Signal | Severity | Seed evidence |
| --- | --- | --- | --- | --- |
| T40 | `opaque-rectangle-leakage` | A sticker/icon ships with an opaque bounding rectangle instead of silhouette alpha. | hard | Issue #2 history (truth-social raw vs final) |
| T41 | `mask-seam` | Visible seam at a composite boundary (feathered or hard). | strong | Issue #34 FeatherMask rejection |
| T42 | `vacated-region-patch` | A removed element leaves a visibly foreign fill patch (pale/gray oval where a glyph was). | strong | Issue #2 `precise-guided-v005` history |
| T43 | `outside-region-change` | Any changed pixel outside the declared edit region when exact preservation is claimed. | hard | Issue #34 JoinImageWithAlpha rejection (48,205 px) |

## Failure-to-guidance map

The owner's framing in Issue #26: artifacts mean the model was not guided
enough. Observed mappings from the seed corpus:

- T21/T22 (aspect and crop) → **match the source canvas**. Issue #52 measured
  this with one frozen PlantStudio edit, seed, and Qwen Image 3 Pro model over
  four OpenRouter arms. Exact `size: 948x806` had 0% aspect error and only mild
  bottom cropping; nearest `5:4` had 6.17% aspect error and moderate bottom
  truncation at both 1K and 2K; mismatched `16:9` had 51.15% aspect error and
  severe teal pillarboxing. Its outside-region and edge-strip pixel indicators
  were respectively 1.97x and 1.69x the exact arm. Prefer exact explicit pixel
  size, otherwise the closest supported aspect. Increasing resolution does not
  repair a mismatched canvas.
- T20 (global redraw) → **canvas match reduces disturbance but is not a
  preservation mechanism**. Issue #52 bounded independent review found T20 in
  every arm: typography, icons, plants, graph, and controls were regenerated
  outside the licensed edit region. Exact size and the nearest aspect reduced
  the raw changed-pixel fraction, while mismatched `16:9` was 1.97x the exact
  arm, but even the lowest arm changed 28.42% of normalized outside-region
  pixels above the luma threshold. Use deterministic Assembly plus Fidelity
  Check when the contract requires zero outside-region changes.
- T01/T03 (copy/logotype corruption) → shrink the generation surface
  (focused crop), or move text into source-owned pixels via deterministic
  Assembly (ADR 0002); regenerate only non-text regions.
- T10/T11/T12 (topology/identity/anatomy) → add object-reference images,
  name the object subtype and part inventory in the brief, or accept per-part
  Assembly from a better donor.
- T30/T31 (style smoothing, texture worms) → name the raster character
  explicitly ("aliased edges, limited palette, no anti-aliasing"), keep
  resolution near source scale, and review at 100%.
- T32 (template remnant) → enumerate donor-template elements to drop in the
  negative constraints.
- T40–T43 → deterministic Assembly and Fidelity Check; these are pipeline
  contracts, not prompt problems.

## Versioning

- `v0.2.0` (2026-08-27): replaced the anecdotal combined T20/T21/T22 canvas
  guidance with the measured Issue #52 four-arm result; canvas match reduces
  T21/T22 severity but does not satisfy strict T20 preservation.
- `v0.1.0` (2026-08-26): initial 18 classes from the zero-cost audit of 8
  preserved runs plus the Issue #26 attached example. Annotated by Claude
  (Fable 5) model vision as the advisory layer; every record carries
  `annotator` and `evidence_strength` so later blind tests can score misses
  and false rejects by class.

New classes append; renames supersede with a note. A class may only be
promoted from advisory to hard-gate when a deterministic check exists for it
and a blinded holdout shows it does not reject source-faithful stylization.
