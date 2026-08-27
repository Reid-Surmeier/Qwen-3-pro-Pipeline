# Issue #34: ComfyUI node experiment research

Status: completed experiment. One deterministic Assembly method qualified; the
focused-crop Render arm ended in an ambiguous paid timeout and was not retried.

## Result

The direct Qwen baseline succeeded at the semantic edit in both outputs: the
complete Effect row is gone, one BGM slider remains, and one Skin dropdown
remains. It also redrew the complete screen, so it could not preserve the
source-owned Japanese and exterior pixels exactly.

The useful node path is a hard `ReferenceRegionComposite` after the Render
Pass. It uses each successful baseline output as a donor only inside
`x=160, y=130, width=1350, height=350`. The first planned rectangle was
rejected because it cut the right-side `on` label and dropdown; the corrected
rectangle was derived from the visible source bounds and then frozen for both
candidates. This no-cost graph produced the intended edit twice and measured:

- candidate 1: 378,801 changed RGBA pixels inside; **0 outside**;
- candidate 2: 471,742 changed RGBA pixels inside; **0 outside**;
- source size and output size: 1572 x 718 RGBA;
- exact source alpha outside the rectangle in both outputs.

The existing node needed one opt-in addition: accept `LoadImage`'s source mask
and reconstruct the source alpha before `SaveImage`. Without it, the otherwise
correct hard composite preserved RGB but lost 54,952 source alpha values. A
core `JoinImageWithAlpha` follow-up improved that count but still changed
48,205 alpha values, so it was rejected. The new opt-in path reaches zero and
does not change the default public workflow behavior.

`FeatherMask` was also rejected. It adds a visible horizontal seam and does
not improve Qwen's structural edit. The focused-crop Qwen arm timed out after
180.352 seconds with no returned outputs; billing is unknown, the attempt was
counted as spent, and no retry or conditional paid arm was submitted.

The saved, GUI-auditable ComfyUI workflow is
`issue-34-japanese-hard-region-assembly-v003.json`. The contact sheet, exact
hashes, prompt IDs, cost, and measurements are under
`artifacts/issue-34/japanese-node-experiment-v003/`.

## What the previous "masking" did

The earlier green selection-guide experiment was harmful for this UI case. In
the human review, only the unmarked baseline donor made the intended edit; the
green-guide outputs targeted the wrong pixels, retained or damaged the wrong
lettering, and introduced visible guide/patch artifacts. It is rejected
evidence, not a weaker version of the winning method. No green guide was used
as a Qwen input in the experiment documented here.

The previous assisted graph did not select an internal edit area. It resized
`LoadImage`'s transparency-mask output, resized the complete Qwen candidate,
and joined them with `JoinImageWithAlpha`. This restored the transparent
exterior after resizing. The mask never entered Qwen, never selected the Effect
row, and never improved copy or layout. It was delivery Assembly.

The live `QwenImage3Render` schema accepts an Edit Brief and an optional `IMAGE`
batch, but no `MASK`. Its implementation converts up to four batched images
into provider references. Therefore a mask can make an exact post-Qwen Assembly
change, but cannot guide this provider-backed Qwen node. A future local Qwen
edit workflow could use masking only if its sampler or conditioning graph
explicitly consumes a mask. See
[`QwenImage3Render`](../../qwen_ui_pipeline/comfyui_node.py) and
[`build_openrouter_request`](../../qwen_ui_pipeline/providers/openrouter.py).

## Guardrails and test target

- Authority: `artifacts/issue-34/alpha-window-2x/source/options-window-source.png`
- SHA-256: `7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16`
- Source: 1572 x 718 RGBA.
- Qwen Image 3 Pro remains the main generator.
- Preserve `オプション` and `スナップ` character-for-character, plus the
  magenta frame, tabs, BGM state, Skin dropdown, checkbox states, bevels,
  palette, and transparent exterior outside a declared edit.
- Primary fixed-canvas edit: remove the complete Effect row and reflow the
  remaining controls without translation. Test 1572 x 1436 height extension
  separately only after a fixed-canvas node method proves useful.

GitNexus was bound to the current Issue-worktree index at commit
`5ac269112123dc8a8f7df77d6ee9ffb92ca7fe49`. It found two existing production
seams: whole-screen Qwen rendering and rectangular
`ReferenceRegionComposite`. The latter is an existing exact-preservation
control, not a new workflow to reimplement.

A read-only live `/object_info` check on 2026-08-26 confirmed the node schemas
used below. ComfyUI builds this endpoint from loaded node mappings
([official server source](https://github.com/Comfy-Org/ComfyUI/blob/master/server.py)).

The current ComfyUI MCP discovery surfaces were checked explicitly:

- `list_packs` reported 56 bundled local/free workflow packs. The Qwen edit
  guidance and workflows target a local Qwen Image Edit 2511 stack, so they are
  not interchangeable with the required provider-backed Qwen Image 3 Pro node.
- `list_templates` returned zero custom-node-registered templates and warned
  that this endpoint cannot enumerate ComfyUI core frontend templates. An empty
  result was therefore recorded as a scope limitation, not proof that no core
  template exists.
- The subgraph/blueprint guidance recommends saved subgraphs for reusable large
  graph sections. The winning graph has only two loaders, one composite, and
  one save node; wrapping it in an extra subgraph would not improve auditability.
  The complete graph was saved directly to the workflow library instead.
- The Qwen edit prompting guide states that it has no official vendor prompt
  source and describes the different local 2511 model. The generic prompting
  guide is CLIP/sampler-oriented and does not control the provider-backed node.
  Therefore this test retained the repository's structured Edit Brief, exact
  Japanese copy, negative constraints, fixed seed, and explicit output fields
  rather than importing unrelated CLIP weights or sampler settings.

## Ranked experiment matrix

### 1. Focused source crop -> Qwen donor -> post-stitch

**Hypothesis:** Qwen will identify and remove the Effect row more reliably when
its only reference is the actual body crop instead of the complete window.
Stitching only that donor region back preserves everything outside the edit.
This follows the official Crop-and-Stitch pattern: crop before sampling and
stitch afterward without changing unmasked areas
([official comfyorg project](https://github.com/comfyorg/comfyui-crop-and-stitch)).
The custom Crop-and-Stitch pack itself is **not installed**; only the installed
core-node equivalent below has been schema-validated, without execution.

- **Nodes:** `LoadImage(reference)` -> `ImageCropV2(body rectangle)` ->
  `QwenImage3Render` -> `ResizeImageMaskNode(exact crop size)` ->
  `ImageCompositeMasked(destination=reference, source=donor, x, y, mask)`.
  Create hard `SolidMask` and `FeatherMask` variants from the same raw donor;
  they are no-cost Assembly variants. `JoinImageWithAlpha` is not required for
  this opaque interior edit and should be added only if a later alpha Fidelity
  Check identifies a real deficit.
- **Changes:** Qwen renders only the body crop. Assembly changes only the hard
  rectangle or its explicitly recorded feather edge.
- **Cannot change:** anything outside the declared composite rectangle. The
  chosen rectangle excludes both `オプション` and `スナップ`, so those source
  pixels remain untouched. Feathering changes pixels only inside the same hard
  rectangle; it does not broaden the edit boundary.
- **Objective check:** matched baseline and focused Render settings; 2/2 focused
  donors remove the complete Effect row and retain one BGM slider and one Skin
  dropdown. Hard composite: zero changed pixels outside the rectangle.
  Feathered composite: zero outside rectangle plus recorded feather width.
  Report perimeter seam error for both; do not credit feathering for Qwen's
  internal edit.
- **Likely failure:** too little context yields a floating control fragment;
  too much recreates full-screen ambiguity. Hard stitching may seam; feathering
  may contaminate nearby source pixels.

Node contracts:
[ImageCropV2](https://docs.comfy.org/built-in-nodes/ImageCropV2),
[ImageCompositeMasked](https://docs.comfy.org/built-in-nodes/ImageCompositeMasked),
[FeatherMask](https://docs.comfy.org/built-in-nodes/FeatherMask).

### 2. Exact Japanese text-lock Assembly

**Hypothesis:** restoring the two Japanese source regions will visibly and
provably improve the same raw candidate when Qwen misspells them.

- **Nodes:** `LoadImage(source/raw)` -> `ResizeImageMaskNode(raw to source
  size)`; build a 0-valued full mask with `SolidMask`, add 1-valued
  `オプション` and `スナップ` rectangles with `MaskComposite`, then
  `ImageCompositeMasked(destination=raw, source=reference, mask=combined)`.
  Apply exterior alpha separately at the end.
- **Changes:** only the two declared text rectangles and exterior alpha.
- **Cannot change:** row removal, spacing, slider state, or Qwen selection.
  This is Assembly, not generation guidance.
- **Objective check:** zero RGB error against the source inside both rectangles;
  zero differences from raw outside them and the alpha operation; exact bounds
  and changed-pixel count recorded. Any visible patch seam disqualifies it.
- **Likely failure:** source text boxes look pasted on if Qwen moved the
  surrounding title or bottom row. A larger source-owned band may be required.

Node contracts:
[SolidMask](https://docs.comfy.org/built-in-nodes/SolidMask),
[MaskComposite](https://docs.comfy.org/built-in-nodes/MaskComposite),
[ImageCompositeMasked](https://docs.comfy.org/built-in-nodes/ImageCompositeMasked).

### 3. Actual source-detail crop as a second Qwen reference

**Hypothesis:** a magnified crop of the BGM/Effect/Skin controls can improve
selection without painting a green guide over the authority image.

- **Nodes:** `LoadImage` -> `ImageCropV2(three control rows)` ->
  `ResizeAndPadImage(1572x718, nearest-exact, black)` -> `BatchImagesNode`
  combining unmodified source first and crop second -> `QwenImage3Render`.
- **Changes:** Qwen receives two genuine source references rather than one.
- **Cannot change:** it cannot guarantee attention, exact Japanese copy, or
  deterministic selection. It needs matched new Render Passes.
- **Objective check:** hold Edit Brief, model, provider, count, seed, and output
  settings constant; record both input hashes and crop bounds. It qualifies
  only if 2/2 candidates beat the matched baseline on complete row removal,
  retained BGM state, and retained Skin dropdown without losing another
  invariant. Apply hypothesis 2 equally to both arms so text restoration is
  not credited to the crop.
- **Likely failure:** duplicated controls, a zoomed crop instead of a full
  window, or black padding copied into the interface.

Node contracts:
[ResizeAndPadImage](https://docs.comfy.org/built-in-nodes/ResizeAndPadImage) and
[official BatchImagesNode source](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_post_processing.py).

### 4. Conditional height-outpaint stress test

**Hypothesis:** `ImagePadForOutpaint` can provide a real 1572 x 1436 reference
canvas so Qwen extends the window rather than merely rescaling it.

- **Nodes:** `LoadImage` -> `ImagePadForOutpaint(718 total vertical padding)`
  -> padded `IMAGE` into `QwenImage3Render`; retain the output `MASK` for audit;
  post-composite declared source bands with `ImageCompositeMasked`.
- **Changes:** reference canvas and marked extension area.
- **Cannot change:** the outpaint mask does not guide the current Qwen node,
  because that node has no mask input. Feeding the padded image is image
  conditioning only. It cannot preserve the whole original body while also
  deleting its Effect row.
- **Objective check:** exact 1572 x 1436 output, nonempty new pixels, zero error
  in restored bands, and continuous magenta side-frame edges across the old/new
  boundary versus a matched source-only height baseline.
- **Likely failure:** second window, desktop continuation, or a padding seam.

Sources:
[official outpainting workflow](https://docs.comfy.org/tutorials/basic/outpaint)
and [ImagePadForOutpaint](https://docs.comfy.org/built-in-nodes/ImagePadForOutpaint).

## Controls and exclusions

- Prior exact-size/source-alpha graph: delivery control only; it did not improve
  selection, copy, or layout.
- Existing `ReferenceRegionComposite`: zero-outside-rectangle control already
  in production.
- `ColorTransfer` and `ImageSharpen`: low-value conditional controls. Existing
  measurements show selection/structure is the dominant failure, not a large
  palette mismatch. Test only after a structurally correct donor and only for
  a predeclared color/edge deficit
  ([ColorTransfer](https://docs.comfy.org/built-in-nodes/ColorTransfer),
  [ImageSharpen](https://docs.comfy.org/built-in-nodes/ImageSharpen)).
- Traditional resize: changes dimensions/interpolation, not semantics
  ([ImageScale](https://docs.comfy.org/built-in-nodes/ImageScale)).
- Model upscale: `ImageUpscaleWithModel` is registered, but the live
  `UpscaleModelLoader` has no model choices. Do not submit it.
- Latent inpaint nodes: incompatible with provider-backed `QwenImage3Render`,
  which exposes neither latent nor conditioning inputs.

## Bounded run and stop rule

First validate API JSON against live schemas without a provider call. Then:

1. Source-only baseline: 2 outputs, fixed seed.
2. Hypothesis 1 focused-crop Render: 2 outputs with identical model, provider,
   Edit Brief, seed, count, resolution, and aspect ratio.
3. Apply hard, feathered, and Japanese text-lock Assembly to the same two
   focused donors at no model cost.

The existing run cost $0.083 for two outputs; four would be approximately
$0.166 only if the live OpenRouter quote is unchanged. Recalculate and record
the current estimate before submission.

Stop if hypothesis 1 produces a repeatable, pre-explained improvement and one
Assembly variant passes its pixel/seam checks. If not, run one pre-recorded
conditional two-output hypothesis-3 arm and reuse the baseline. Run hypothesis
4 only if fixed-canvas work has first proven useful and height extension remains
an unresolved named question. Stop when one method qualifies or the matrix is
exhausted; never retry an ambiguous paid request.

For every arm retain API JSON, input/output hashes, provider/model, prompt ID,
seed, requested/completed count, estimate/actual cost, dimensions, node-specific
measurements, and stopping reason. Failed and neutral arms remain evidence.
Human visual approval remains separate.
