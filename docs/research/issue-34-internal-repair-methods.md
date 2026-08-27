# Issue 34: node-assisted internal UI repair methods

Date: 2026-08-26

Status: research only. This note records no paid submission and does not approve one.

## Question and fixed guardrails

The useful comparison is not whether a node can preserve the outside alpha. It is whether a node changes the flawed **inside** of an existing Qwen Image 3 Pro candidate in a visible, repeatable, measurable way.

The Reference Screen remains `options-window-source.png`, SHA-256 `7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16`, 1572 x 718 RGBA. Every experiment must:

- preserve `オプション` and `スナップ` byte-for-byte;
- preserve the pixel-era type, palette, magenta frame, title bar, tabs, dropdown, checkbox states, bevels, borders, shadows, and transparent exterior;
- remove the complete Effect row;
- leave exactly one BGM slider and one Skin dropdown;
- keep Qwen Image 3 Pro as the main generator; and
- treat a Render Pass as probabilistic and final Assembly as deterministic.

The green-guide arm is already harmful evidence. The exact-size/source-alpha arm is delivery Assembly only: it changes dimensions and alpha ownership but does not guide Qwen or repair internal copy or layout.

## Primary-source findings

ComfyUI's official guidance uses a mask to localize inpainting and an inpainting-aware model path to generate the replacement. It does not imply that a post-generation mask can improve content that a model already drew. The official tutorial connects the mask to `VAEEncodeForInpainting`; the installed `QwenImage3Render` exposes only `edit_brief_json` and an optional `IMAGE` batch, so `ConditioningSetMask`, `InpaintModelConditioning`, and `SetLatentNoiseMask` cannot connect to this provider node. A real mask-guided provider arm would require a new provider/node interface, not another downstream composite. [Official inpainting tutorial](https://docs.comfy.org/tutorials/basic/inpaint)

The installed official `Image Inpainting (Qwen-image)` blueprint confirms that distinction. Its subgraph uses `ControlNetInpaintingAliMamaApply`, `VAEEncode`, `SetLatentNoiseMask`, `KSampler`, and a grow/blur mask subgraph. That is a local Qwen-Image + ControlNet generator, not the required OpenRouter `qwen/qwen-image-3-pro` generator, so it is useful pattern evidence but is out of scope for execution here. [Official Qwen inpainting blueprint](https://github.com/Comfy-Org/ComfyUI/blob/master/blueprints/Image%20Inpainting%20%28Qwen-image%29.json)

Official core provides the primitives needed for a deterministic internal-repair graph. `ImageCropV2` takes an image plus a bounding box and returns that exact slice. `ImageCompositeMasked` places a source at explicit `x,y` coordinates, optionally through a mask; `resize_source=false` avoids an implicit full-canvas resize. [Installed-version crop source](https://github.com/Comfy-Org/ComfyUI/blob/43cb4fffc89bba20ab7bd61467a36d0339338dab/comfy_extras/nodes_images.py#L59), [installed-version composite source](https://github.com/Comfy-Org/ComfyUI/blob/43cb4fffc89bba20ab7bd61467a36d0339338dab/comfy_extras/nodes_mask.py#L80), [official node documentation](https://docs.comfy.org/built-in-nodes/ImageCompositeMasked)

The current official Crop Images 2x2 blueprint uses `GetImageSize`, `PrimitiveBoundingBox`, `ImageCropV2`, and `BatchImagesNode`, which is direct first-party precedent for packaging crop logic as a reusable subgraph. ComfyUI documents subgraphs as reusable node combinations with promoted inputs and outputs. [Official crop blueprint](https://github.com/Comfy-Org/Subgraph-Blueprints/blob/main/Crop%20Images%202x2.json), [official subgraph guide](https://docs.comfy.org/interface/features/subgraph)

`ResizeImageMaskNode` supports exact dimensions, aspect-preserving modes, center crop, and `nearest-exact`, `bilinear`, `area`, `bicubic`, or `lanczos`. Its installed tooltip identifies `nearest-exact` for pixel art, `area` for downscaling, and `lanczos` for upscaling. `ResizeAndPadImage` preserves aspect ratio while fitting an image into a target canvas and adding centered white or black padding. [Installed-version resize source](https://github.com/Comfy-Org/ComfyUI/blob/43cb4fffc89bba20ab7bd61467a36d0339338dab/comfy_extras/nodes_post_processing.py#L412), [installed-version pad source](https://github.com/Comfy-Org/ComfyUI/blob/43cb4fffc89bba20ab7bd61467a36d0339338dab/comfy_extras/nodes_images.py#L445), [official ResizeAndPadImage documentation](https://docs.comfy.org/built-in-nodes/ResizeAndPadImage)

Current upstream ComfyUI has a first-party Qwen Image 3 API edit node with explicit multi-image roles, but the live 0.31.0 installation does not expose that class. It therefore cannot be the implementation basis for this Issue without a separate upgrade/migration decision. [Current upstream Qwen API-node source](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_api_nodes/nodes_qwen.py)

## Installed live evidence

Read-only checks were made against the configured live ComfyUI target on 2026-08-26 while the aggregate queue was empty.

- `/system_stats`: ComfyUI `0.31.0`, commit `43cb4fffc89bba20ab7bd61467a36d0339338dab`, workflow templates `0.11.34`, embedded docs `0.5.9`.
- `/object_info/QwenImage3Render`: required `edit_brief_json: STRING`; optional `reference_images: IMAGE`; outputs `IMAGE, STRING`. There is no mask, conditioning, crop, or region input.
- The deployed custom-node source serializes at most the first four tensors in the `reference_images` batch as separate PNG references.
- `/object_info/BatchImagesNode`: 1-50 `IMAGE` inputs. Its installed implementation resizes every later image to the first image's size with bilinear center crop when dimensions differ. A detail reference must therefore be explicitly padded to the first image's size before batching; otherwise the batching node silently changes it.
- `/object_info/ImageCropV2`: `image: IMAGE`, `crop_region: BOUNDING_BOX` -> `IMAGE`.
- `/object_info/PrimitiveBoundingBox`: integer `x,y,width,height` -> `BOUNDING_BOX`.
- `/object_info/ImageCompositeMasked`: `destination`, `source`, `x`, `y`, `resize_source`, optional `mask` -> `IMAGE`.
- `/object_info/ResizeImageMaskNode`: `IMAGE|MASK`, dynamic resize mode, scale method -> same type.
- `/object_info/ResizeAndPadImage`: `image`, target width/height, white/black padding, interpolation -> `IMAGE`.
- `/object_info/ImageStitch`: two images, direction, size matching, spacing -> `IMAGE`; it uses Lanczos when matching the second image's size.
- `/object_info/UpscaleModelLoader`: `model_name` options are empty. Model-backed super-resolution is not runnable on the present host and must not be represented as an installed experiment.
- `/global_subgraphs` exposes the official Qwen inpainting, Qwen edit, Crop Images 2x2/3x3, and Video Stitch blueprints. Only their installed node classes are eligible; the local Qwen inpainting blueprint changes the generator and is excluded.
- `InpaintCrop` and `InpaintStitch` are not present in `/object_info`. The official-community Crop and Stitch pattern is relevant background, but installing another node pack is outside this Issue. [ComfyOrg Crop and Stitch source](https://github.com/comfyorg/comfyui-crop-and-stitch/blob/main/inpaint_cropandstitch.py)

GitNexus found only two current production workflow seams: `build_comfyui_api_workflow` builds `LoadImage -> QwenImage3Render -> SaveImage`, and `build_comfyui_assembly_workflow` builds `LoadImage(reference + donor) -> ReferenceRegionComposite -> SaveImage`. No component-level crop/reflow workflow exists. The new seam, if an experiment qualifies, should extend deterministic Assembly rather than duplicate the provider node or redefine the existing one-rectangle Assembly.

## Ranked experiment matrix

The order below prioritizes an internal visible change, ability to reuse the already-paid raw donors, and clean attribution of the node's contribution.

### 1. Source-locked component repair and row reflow

**Hypothesis.** A component-level Assembly can use the authoritative source for tiny exact-copy controls and the existing Qwen donor for the redesigned body, while moving the Skin row into the removed Effect row's space. This should visibly fix malformed BGM/Skin glyphs and the excessive vertical gap without claiming that a mask improved Qwen's raw generation.

**Exact graph.** `LoadImage(source)` + `LoadImage(raw donor)` -> `ResizeImageMaskNode(raw donor, scale dimensions 1572x718, crop=center, nearest-exact)` -> repeated `PrimitiveBoundingBox -> ImageCropV2` for accepted donor and source-owned micro-components -> repeated `ImageCompositeMasked(destination, source patch, x, y, resize_source=false, optional hard mask)` -> `ReferenceRegionComposite` for final exterior ownership -> `SaveImage`.

The first trial should use hard rectangular ownership only. A mask is added only when a patch contains pixels that must remain donor-owned; it is not called guidance. Source-owned patches must remain small enough that Qwen is still visibly responsible for the edited body.

**Expected visible effect.** Correct source-faithful label/control pixels; one BGM row and one Skin row; Skin moved upward into a deliberate two-row layout; no Effect row; less empty internal space. The candidate should still visibly retain Qwen's generated inner panel rather than becoming a reconstruction of the source.

**Objective checks.** Record every source and destination bounding box. Compare source-owned patch bytes after translation. Count BGM sliders, Skin dropdowns, and Effect rows. Measure the two row centerlines and the inter-row gap. Attribute the node-induced diff only to the union of component rectangles. Require zero RGBA changes outside the declared final Assembly region and byte equality for `オプション` and `スナップ`.

**Likely failure.** Rectangular seams, background mismatch, copied components at an incompatible scale, or a repair footprint so large that Qwen is no longer meaningfully the generator. Reject rather than feather if feathering visibly softens one-pixel borders.

### 2. Aspect-preserving donor normalization before Assembly

**Hypothesis.** The paid candidates are 2:1, while the source is about 2.19:1. Resizing directly to 1572 x 718 stretches them vertically. Center-crop normalization should preserve the generated control proportions and produce less squashed labels, handles, and dropdown arrows before any component repair.

**Exact graph.** `LoadImage(raw donor)` -> `ResizeImageMaskNode(scale dimensions, width=1572, height=718, crop=center, scale_method=nearest-exact)` -> the same hard `ReferenceRegionComposite` geometry used for the matched control. A separate `lanczos` arm is allowed only as an interpolation comparison, not as a semantic repair claim.

**Expected visible effect.** Rounder handles, less vertical stretching, more source-like line and control aspect ratios. This arm should not be credited for correcting text or row counts.

**Objective checks.** Compare aspect ratios of the BGM handle, checkbox, and dropdown arrow against the source; compare edge sharpness and one-pixel line retention; require the exact output canvas and zero outside-region changes. The node-induced diff is the full donor-owned rectangle, so the report must not describe it as a localized text fix.

**Likely failure.** Center crop removes useful top/bottom context, while nearest-exact can alias a non-integer scale and Lanczos can blur pixel art. Even a geometry win remains neutral if the same malformed glyphs and large gap remain.

### 3. Full-source plus padded-detail Qwen references

**Hypothesis.** Giving Qwen both the immutable full screen and an enlarged, unmodified detail crop may keep global layout context while making the two retained rows occupy more of the model's visual input. This is the only generator-facing arm available through the current provider node without changing generator families.

**Exact graph.** `LoadImage(source)` -> `PrimitiveBoundingBox -> ImageCropV2(detail)` -> `ResizeAndPadImage(detail, target_width=1572, target_height=718, padding_color=white, interpolation=nearest-exact)` -> `BatchImagesNode(full source first, padded detail second)` -> `QwenImage3Render`. The pre-pad is required to prevent `BatchImagesNode` from silently bilinear-resizing and center-cropping the second image.

**Expected visible effect.** Better BGM/Skin glyph structure, a more deliberate two-row reflow, and fewer duplicated controls in the raw Qwen output before any Assembly.

**Objective checks.** Use the existing full-source baseline as Arm A. A new donor qualifies only if it improves the named internal defect before compositing and then survives the same outside-region Fidelity Check. Record the exact reference order and hashes. Both requested outputs must remove Effect, contain one BGM slider and one Skin dropdown, preserve named states, and improve at least one predeclared copy/layout measure over the existing two direct donors.

**Likely failure.** Qwen may interpret the padded crop as another composition, duplicate controls, or still redraw copy. The method cannot guarantee character-for-character copy because the provider generates RGB pixels probabilistically.

### 4. Second-pass local donor refinement

**Hypothesis.** A crop of the better existing donor, paired with the corresponding source detail, may let Qwen repair a smaller internal failure while retaining the successful row removal.

**Exact graph.** `LoadImage(raw donor) -> ImageCropV2(donor detail)`, `LoadImage(source) -> ImageCropV2(source detail)`, pad both with `ResizeAndPadImage`, batch them in explicit donor-then-authority order with `BatchImagesNode`, then call `QwenImage3Render`; normalize the resulting patch once with `ResizeImageMaskNode` and place it with `ImageCompositeMasked(resize_source=false)`.

**Expected visible effect.** Repair of a specific malformed label/control without regenerating the full screen.

**Objective checks.** Predeclare one defect and its crop. Compare the repaired crop against the original donor crop for OCR/copy, control count, and geometry. Demand zero changes outside the crop after Assembly.

**Likely failure.** Reference-role bleed, another full redesign, or insufficient evidence from one remaining pair. This method is lower than Arm 3 because it consumes the last allowance while losing a clean same-call full-screen control.

## Methods not eligible as winning arms

- **Hard `ReferenceRegionComposite` alone:** useful containment, but it does not improve the pixels inside the rectangle.
- **FeatherMask:** already produced a visible seam in this case; soft ownership also weakens exact one-pixel UI edges.
- **JoinImageWithAlpha / Porter-Duff alone:** alpha delivery only; neither repairs copy or layout.
- **Model upscale:** node class is present but no upscale model is installed.
- **Official Qwen local inpainting or Qwen-2511 subgraphs:** materially different generator/model path, contrary to the Issue boundary.
- **Current upstream Qwen Image 3 API edit node:** absent from the live catalog; adopting it is an upgrade/migration decision, not a current installed-node experiment.

## Execution order and stopping rule

1. Run Arms 1 and 2 on both saved raw Japanese donors with no provider call.
2. Keep failed/neutral graphs and measurements. A method qualifies only if the improvement is visible in both donors and described by the predeclared checks.
3. Stop if Arm 1 qualifies; package it as an opt-in reusable component-repair Assembly/subgraph with public-interface tests.
4. If Arm 1 fails and Arm 2 only improves geometry, do not combine weak claims. Arm 3 is the only remaining generator-facing experiment worth considering.
5. Arm 4 is conditional only if Arm 3 exposes one sharply localized unresolved defect and the paid allowance permits it; with the current allowance it should normally remain unrun.

Issue 34 has already spent 8 of its 10 possible paid output images. No paid calls are authorized during this research phase. The only possible future batch is at most two OpenRouter `qwen/qwen-image-3-pro` outputs, estimated at approximately $0.083 from the preceding measured two-output run. Before submission, the Issue body must name the selected arm, exact references and hashes, seed/settings, estimate, and stop condition. An ambiguous request counts as spent and must not be retried.

## Recommendation for the first experiment

Start with Arm 1 against both saved donors. It is the only installed method that can correct a visible internal error and reflow the two rows without spending the final two outputs. Arm 2 should run beside it as a geometry control. Do not describe either as mask-guided generation: both are deterministic post-generation Assembly, and their value must be proven by the exact pixels and row geometry they change.
