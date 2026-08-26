# ComfyUI mask-node qualification research

Source review and live qualification were completed 2026-08-26 for Issue #2.
This note distinguishes primary-source research, current runtime evidence, and
work that was deliberately not performed. The exact workflows, hashes, costs,
and outputs are preserved under `artifacts/issue-2/`.

## Recommendation

Test two hypotheses separately:

1. A cleaner, explicitly owned mask improves deterministic **Assembly** and
   removes rectangular backgrounds without changing protected pixels.
2. Supplying a mask as an additional visual reference may improve a later
   Qwen **Render Pass**, but only deterministic Assembly decides which of those
   pixels reach the final image.

Start with the first hypothesis. Prefer the already installed project-owned
sticker tooling and ComfyUI core nodes, then compare native BiRefNet. Do not
install a large custom-node pack unless those paths fail a named fixture and
metric. An apparently cleaner edge is not enough: strict preservation still
requires zero changed pixels outside the declared editable mask.

That sequence selected the explicit ownership-mask path. On the frozen fixture,
the project-owned mask node and a core alpha path produced identical decoded
RGB pixels and both matched the independent ground-truth mask with zero false
opaque and zero false transparent pixels. The project-owned path adds named
ownership bands and fail-closed fidelity gates, which the core-only path does
not. BiRefNet was not downloaded or run because its model weight was absent and
the deterministic paths already passed the named fixture.

## Live qualification result

The routed installation at `http://10.255.255.254:8188` reported ComfyUI
`0.31.0`, frontend `1.48.7`, Python `3.12.4`, PyTorch `2.13.0+cu130`, and an
NVIDIA GeForce RTX 4070 SUPER. The aggregate queue was empty before the live
runs.

Codex configuration contained three MCP entries:

- official `comfy-cloud`, configured with OAuth;
- first-party `comfy-local-official`, configured for local runtime work;
- community `comfyui`, already callable in this session.

The two official entries were registered after this Codex session started, so
their tools were not exposed in the session's callable catalog. Official Cloud
MCP discovery informed the research, but no Cloud execution was used. Live
schemas, workflow validation, queue state, submission, and output retrieval for
the five-worker installation were performed through the already callable
community MCP against the routed endpoint. A new Codex session is still needed
to exercise both first-party entries directly; this limitation is not treated
as a failed node qualification.

The installed `qwen_sticker_tooling` source matched commit
`b8e226cb12f7cea8a201da73a852542938fdad9f` exactly. Its only runtime
dependencies are ComfyUI tensors and the PyTorch already supplied by ComfyUI.
All four lightweight contract tests passed, and all five tensor/runtime tests
passed in the actual ComfyUI virtual environment, including deliberate failures
for protected-pixel and artwork changes. Live schemas for
`StickerMaskBands`, `MaskedReferenceFidelityGate`, and `ArtworkFidelityGate`
matched the reviewed source.

Two no-cost workflows then ran successfully:

| Path | Prompt ID | Result |
| --- | --- | --- |
| Project-owned mask bands | `01325c90-2c6d-4b70-9a65-534d04b10989` | success |
| Core alpha path | `a2ed378a-87af-45f3-a372-0eed289d15b9` | success in 157 ms |

Across 932,672 pixels, both explicit mask paths had zero false opaque, zero
false transparent, and zero changed pixels outside the independent mask. Each
recorded silhouette IoU 1.0, zero centroid/scale drift, and zero boundary-band
error. The decoded RGB composites were identical; their PNG hashes differ
because their encodings differ. The RGB result is composited onto a destination
canvas, so transparency is carried and tested as a separate mask rather than
claimed as RGBA `SaveImage` output. A deterministic contact sheet shows two
rows: the actual custom output with its candidate mask and the actual core
output with its candidate mask, each over checker, black, white, gray, and
bright green backgrounds. `StickerMaskBands` intentionally thresholds soft
input at the declared threshold; a tensor test locks the `0.49` versus `0.50`
boundary.
See `artifacts/issue-2/qualification/run.json`, `evaluation.json`, and both
qualification contact sheets for the durable evidence.

The live proof workflow reused the approved mask as the candidate mask in
`ArtworkFidelityGate`. Its exact-artwork check was meaningful, but its reported
silhouette/centroid values were tautological. The repository workflow builder
therefore disables those geometry thresholds and does not claim an independent
candidate-silhouette check. Separate tensor tests prove that the gate rejects a
shifted candidate mask when independent masks are available.

Phase B used OpenRouter and `qwen/qwen-image-3-pro` for two outputs per
condition. The first pre-generation attempt was rejected with HTTP 402 and
completed zero outputs; after the human added credits, all six planned outputs
completed for an actual total of $0.255. No pre-submission estimate was
captured, which remains a documented limitation.

| Condition | References | Outputs | Actual cost | Finding |
| --- | ---: | ---: | ---: | --- |
| B0 reference only | 1 | 2 | $0.083 | baseline |
| B1 reference plus raw mask | 2 | 2 | $0.086 | no consistent improvement |
| B2 reference plus ownership guide | 2 | 2 | $0.086 | scale changed and cyan color shifted |

The run stopped at six outputs, below the effective cap of ten. The mask guides
were RGB references, not native mask inputs or true inpainting. They did not
show a consistent improvement, so deterministic Assembly remains the selected
boundary-control mechanism. Human visual acceptance is still pending. See
`artifacts/issue-2/generation/run.json`, `evaluation.json`, and the generation
contact sheet.

## Discovery is not deployment

The two official MCPs have different jobs.

### Comfy Cloud MCP

The hosted MCP at `https://cloud.comfy.org/mcp` can discover templates,
models, node schemas, graph paths, and prompting guidance with
`search_templates`, `get_template`, `get_template_schema`, `search_models`,
`search_nodes`, `get_node`, `cql`, and `get_prompting_guide`. Its discovery
surface is free, but cloud workflow execution and partner models can consume
credits. A cloud search result does not prove that the node or model exists in
the five-worker local installation.

Primary source: [official Comfy MCP documentation](https://docs.comfy.org/agent-tools/mcp).

### First-party local Comfy MCP

The current first-party [`Comfy-Org/comfy-mcp`](https://github.com/Comfy-Org/comfy-mcp)
is a beta stdio server built on `comfy-cli>=1.14.0`. Its relevant operations
include:

- `server_info` and `system_stats` for the installation and hardware;
- live node, model, and template discovery;
- `search_templates` and `fetch_template`;
- workflow validation and `run_workflow`;
- asynchronous job status/cancel/wait and `fetch_outputs`;
- model/node dependency inspection and installation operations.

Its README states an important remote-target limitation: job submission and
polling can use `COMFYUI_URL`/`COMFYUI_HOST`, but node discovery,
`validate_workflow`, and template `local_check` still describe the local
install. Therefore a validation result from this MCP is runtime proof only if
the MCP process is attached to the actual five-worker installation or to a
catalog-identical installation whose identity is recorded. Otherwise, query
the routed server's live schema through a first-party-supported path before
claiming qualification.

Primary source: [first-party local MCP README](https://github.com/Comfy-Org/comfy-mcp/blob/main/README.md).

The repository currently documents community `comfyui-mcp@0.50.98` as its
local control plane. Its source distinguishes Registry package search from
loaded-node search and live `/object_info` lookup. Inventorying Codex's actual
MCP configuration is therefore required before choosing which surface supplies
each evidence item.

Primary source: [`artokun/comfyui-mcp` v0.50.98](https://github.com/artokun/comfyui-mcp/blob/v0.50.98/README.md).

## Native and core candidates

The deployment documentation pins ComfyUI `v0.31.0`. That release contains
the following relevant node classes.

| Candidate | Intended role | Qualification concern |
| --- | --- | --- |
| `ImageCompositeMasked` | Deterministic source-over-destination Assembly under an optional mask | Image, mask, coordinates, resize behavior, and batch sizes must match |
| `MaskComposite` | Add, subtract, and combine ownership masks | Offset, canvas size, and mask polarity must be explicit |
| `GrowMask` | Small dilation or erosion of a mask | Expansion can consume protected artwork; use only a bounded sweep |
| `ThresholdMask` | Convert a soft mask to a binary mask | Hard thresholds discard fractional alpha |
| `InvertMask` | Convert foreground selection to inverse-alpha convention | A missed inversion can preserve the entire unwanted rectangle |
| `ImageColorToMask` | Exact-color keying diagnostic | Exact equality misses off-white edges and can delete intended white artwork |
| `SplitImageWithAlpha` / `JoinImageWithAlpha` | Move between RGBA and ComfyUI image/mask representation | Core source uses inverse-alpha mask semantics |
| `MaskPreview` / `ImageCompare` | Human inspection | Preview and a slider are not numerical Fidelity Checks |
| `LoadBackgroundRemovalModel` / `RemoveBackground` | Native background-removal inference | Node classes are present, but the required weight is not currently installed |

Primary source files at the deployed version:

- [mask and masked-composite source](https://github.com/Comfy-Org/ComfyUI/blob/v0.31.0/comfy_extras/nodes_mask.py)
- [alpha/compositing source](https://github.com/Comfy-Org/ComfyUI/blob/v0.31.0/comfy_extras/nodes_compositing.py)
- [background-removal source](https://github.com/Comfy-Org/ComfyUI/blob/v0.31.0/comfy_extras/nodes_bg_removal.py)

Core `FeatherMask` should not be selected for general silhouette cleanup. At
this version it fades the outer left, top, right, and bottom edges of the mask
canvas; it does not blur an arbitrary internal contour.

## Native BiRefNet path

ComfyUI's official native workflow uses:

```text
LoadBackgroundRemovalModel
  -> RemoveBackground
  -> InvertMask
  -> JoinImageWithAlpha
```

The subgraph returns a transparent image and a foreground mask. The model file
belongs at `models/background_removal/birefnet.safetensors`. Official guidance
notes that cluttered backgrounds and subjects similar to their backgrounds can
reduce accuracy and that the implementation processes one image at a time.

Primary sources:

- [official BiRefNet tutorial](https://docs.comfy.org/tutorials/utility/remove-background-birefnet)
- [official workflow template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/utility_birefnet_remove_background.json)
- [upstream BiRefNet repository](https://github.com/ZhengPeng7/BiRefNet)

The live node classes are not sufficient qualification. Before testing, record
the exact model URL, license, file size, SHA-256, configured inference device,
and cold/warm memory use. The absent weight is a dependency gap, not evidence
that BiRefNet fails.

## Existing sticker tooling

Live discovery reported these installed project-owned nodes:

- `StickerMaskBands`
- `StickerPerspectiveWarp`
- `MaskedReferenceFidelityGate`
- `ArtworkFidelityGate`

Their identified source is commit
[`b8e226cb12f7cea8a201da73a852542938fdad9f`](https://github.com/ReidSurmeier/maga-sticker-generation-snapshot/commit/b8e226cb12f7cea8a201da73a852542938fdad9f).
At that commit:

- `StickerPerspectiveWarp` transforms approved artwork and its mask together;
- `StickerMaskBands` creates artwork, cutline, contact, editable-union, and
  immutable-outside masks;
- `MaskedReferenceFidelityGate` can fail closed on any outside-mask pixel
  change;
- `ArtworkFidelityGate` checks artwork and silhouette fidelity.

Primary sources:

- [node implementation](https://github.com/ReidSurmeier/maga-sticker-generation-snapshot/blob/b8e226cb12f7cea8a201da73a852542938fdad9f/comfyui_custom_nodes/qwen_sticker_tooling/nodes.py)
- [accepted mask-ownership ADR](https://github.com/ReidSurmeier/maga-sticker-generation-snapshot/blob/b8e226cb12f7cea8a201da73a852542938fdad9f/docs/adr/0004-mask-owned-sticker-assembly.md)
- [workflow at the identified commit](https://github.com/ReidSurmeier/maga-sticker-generation-snapshot/blob/b8e226cb12f7cea8a201da73a852542938fdad9f/workflows/sticker-mask-assembly-v001.api.json)

Previous reports are not current qualification. The implementation must:

1. resolve the installed package to an exact commit and compare it with
   `b8e226c`;
2. review the package source, requirements, and import behavior;
3. rerun its lightweight unit tests;
4. rerun tensor/runtime tests with the actual ComfyUI Python environment;
5. compare every node's live schema with the workflow and source;
6. validate the API workflow against the actual routed installation;
7. execute one no-cost synthetic workflow through the router;
8. prove that each fidelity gate also rejects a deliberately bad fixture;
9. record commands, versions, hashes, output paths, queue state, and memory.

Before making this repository depend on the pack, decide whether it remains a
cross-repository dependency, is ported here, or is generalized into non-sticker
ownership vocabulary. That decision changes a system boundary and needs an ADR.

## Maintained alternative: ComfyUI-RMBG

[`1038lab/ComfyUI-RMBG`](https://github.com/1038lab/ComfyUI-RMBG) is an actively
maintained GPL-3.0 custom pack. Its current source offers several background
removal, segmentation, and matting choices, including BiRefNet variants,
SDMatte, SAM/SAM2, and GroundingDINO.

It is a later experiment, not the first installation candidate. Its
[`requirements.txt`](https://github.com/1038lab/ComfyUI-RMBG/blob/main/requirements.txt)
adds a broad runtime surface including `transparent-background`,
`segment-anything`, `groundingdino-py`, OpenCV, CPU and GPU ONNX Runtime,
Transformers, Diffusers, Hydra, OmegaConf, and IOPAth. The README also supports
automatic model download on first use. Risks include:

- dependency conflicts with the deployed PyTorch/NumPy/ONNX environment;
- duplicate CPU/GPU ONNX packages;
- unplanned network/model downloads;
- multiple model licenses in one pack;
- significant RAM/VRAM growth and long cold starts;
- a large import surface that can prevent ComfyUI startup;
- workflow drift as many unrelated nodes evolve together.

If native/core paths fail, qualify only one pinned pack release or commit in an
isolated copy of the ComfyUI environment. Disable automatic download, review
the exact chosen model's license, hash all weights, inspect startup logs, and
measure cold and warm memory before exposing it to the router.

A smaller alternative for deterministic contour operations is
[`cubiq/ComfyUI_essentials`](https://github.com/cubiq/ComfyUI_essentials), whose
source includes tolerance-based color masking, blur, smooth, fix, and bounding
box operations. It still needs a pinned source/dependency/live-schema review;
it cannot establish subject semantics by itself.

## Candidate experiment matrix

All Phase A rows use frozen existing Render Passes and cost nothing.

| ID | Mask source and Assembly path | Purpose | Advance when |
| --- | --- | --- | --- |
| A0 | Current rectangle Assembly | Baseline and regression control | Always record |
| A1 | Approved geometric mask -> ownership bands -> core composite -> fidelity gates | Strongest deterministic path when shape is known | All preservation gates pass and box leakage is removed |
| A2 | Native BiRefNet continuous mask -> core alpha/composite | No-custom-pack automated baseline | Better alpha metrics without protected-pixel damage |
| A3 | BiRefNet threshold `0.35`, `0.50`, `0.65` | Bound threshold sensitivity | One setting dominates without edge loss |
| A4 | Best A3 result with `GrowMask` `-1`, `0`, `+1` px | Bound leakage/erosion trade-off | It improves boundary error without geometry drift |
| A5 | Exact-white `ImageColorToMask` diagnostic | Determine whether the box is truly a flat color | Never default when intended white pixels are present |
| A6 | Pinned small contour pack or ComfyUI-RMBG model | Escalation only | A1-A5 fail a named criterion |

Phase B tests Qwen separately after a deterministic winner exists:

| ID | Qwen references | Initial outputs |
| --- | --- | ---: |
| B0 | Reference Screen only | 2 |
| B1 | Reference Screen plus raw mask rendered as a labelled RGB guide | 2 |
| B2 | Reference Screen plus selected clean mask/ownership guide | 2 |

The current `QwenImage3Render` has no mask input. It converts references and
provider responses to RGB, so B1/B2 are visual-reference tests, not true
inpainting. A downstream mask node cannot influence a Render Pass that has
already run. Every Phase B candidate must still be clipped to the deterministic
editable union before Assembly.

OpenRouter currently advertises up to four input references and does not
advertise a mask parameter for `qwen/qwen-image-3-pro`. Recheck the
[live endpoint record](https://openrouter.ai/api/v1/images/models/qwen/qwen-image-3-pro/endpoints)
immediately before the experiment. ADR 0003 remains authoritative: target six
outputs, stop when evidence is sufficient, and do not submit a request that
could produce output 11. An ambiguous possibly billed request consumes the
remaining allowance until reconciled.

## Frozen-fixture and measurement requirements

The fixture set should cover opaque white/checker boxes, intended white
artwork, hard silhouettes, soft/translucent edges, a known-good transparent
control, and a deliberately inverted mask. Ground-truth masks must be approved
independently and must not be derived from the candidate under test.

For every variant, record:

- source, donor, mask, workflow, output paths, roles, and SHA-256 values;
- dimensions, channels, and alpha polarity;
- outside-mask changed-pixel count;
- false opaque background and false transparent foreground pixels;
- silhouette IoU, centroid/scale drift, and boundary-band error;
- alpha SAD, MSE, gradient, and connectivity error when ground truth permits;
- cold/warm runtime, peak process RSS, peak VRAM, available system memory, and
  swap growth;
- contact sheets over checker, black, white, gray, magenta, and green
  backgrounds.

SAD, MSE, gradient, and connectivity are established matting measures in the
[perceptually motivated matting benchmark](https://www.microsoft.com/en-us/research/wp-content/uploads/2009/01/cvpr09-matting-Eval.pdf)
and [Deep Image Matting](https://openaccess.thecvf.com/content_cvpr_2017/papers/Xu_Deep_Image_Matting_CVPR_2017_paper.pdf).
Compute boundary measures over a declared edge band as well as globally; a
full-image average can hide a bad halo.

ComfyUI's [first-party test framework](https://github.com/Comfy-Org/ComfyUI-test-framework)
provides tensor-shape, mask-coverage, binary/fuzzy mask, and perceptual-image
assertions. Its dHash comparison is a regression smoke test, not proof of exact
preservation. Exact claims remain byte-level checks outside the editable mask.

## Qualification checklist

- [x] Capture exact ComfyUI, frontend, Python, PyTorch build, GPU, router, and
      MCP configuration details exposed by the live surfaces.
- [x] Identify the official Cloud, first-party local, and community MCP entries,
      including which tools were callable in this session.
- [x] Use the callable MCP against the actual routed five-worker endpoint for
      live schemas, validation, queue state, runs, and outputs.
- [x] Record an empty aggregate queue before the no-cost runs. No restart was
      needed.
- [x] Record live node schemas and the relevant installed-model gap.
- [x] Pin and review the selected non-core source, dependencies, and explicit
      install script. No additional model weight was installed.
- [x] Verify no secret appears in workflow JSON, logs, fixtures, or artifacts.
- [x] Run synthetic inverted-polarity, shape, batch-expansion, soft-alpha,
      shifted-geometry, and deliberate-failure tests.
- [x] Run source tests and actual-ComfyUI-environment tests for sticker tooling.
- [x] Validate the workflows against the actual routed schema.
- [x] Run no-cost synthetic workflows and preserve manifests and hashes.
- [x] Compare the project-owned path with a core-only alternative before
      selecting it; document why BiRefNet and larger packs did not advance.
- [x] Keep the existing rectangle/provider/five-worker path unchanged and make
      the mask path opt-in.
- [x] Keep paid and model-backed evaluation out of ordinary PR CI.
- [x] Record human visual review separately from objective Fidelity Checks.

## Remaining limitations and follow-up

- Restart Codex before directly exercising the newly registered official Cloud
  and local MCP tool catalogs. First-party local discovery must be interpreted
  carefully when its process is not catalog-identical to the remote target.
- Native BiRefNet remains unbenchmarked. Qualifying it later requires choosing
  and hashing a weight revision, reviewing its license, and measuring cold/warm
  time and memory. It is not required for the selected deterministic fixture.
- The Phase B pre-submission price estimate was not captured. Actual provider
  costs and every request/output are recorded.
- Objective checks passed, but the generated comparison and selected contact
  sheet still require human visual acceptance.
- Remote Mac access to the Pugnet ComfyUI interface and Partner-compatible local
  Qwen node inputs are tracked separately in Issue #32.

The selected path is now project-owned by this repository under accepted ADR
0004. Research alone did not make that selection: reviewed source and
dependencies, current live schemas, no-cost routed executions, frozen-fixture
metrics, and preservation failures all contributed to the decision.
