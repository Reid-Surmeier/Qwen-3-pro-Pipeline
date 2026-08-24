---
name: qwen-source-locked-image-generation
description: Generate or edit production raster assets in this repository through the mandatory Qwen Image 3 Pro and ComfyUI single-decision workflow. Use for stickers, source-locked image edits, visual donors, correction passes, and generated FigJam review candidates; do not use the generic OpenAI-first image-generation route for these artifacts.
---

# Qwen Source-Locked Image Generation

Use the named workflow profile
`qwen-source-locked-single-decision-v1`. It is the production contract for this
repository, not a prompt suggestion.

## Provider and runtime boundary

- Render only with Alibaba Qwen Image 3 Pro through the existing ComfyUI
  `QwenImage3Render` node.
- Never call built-in OpenAI `image_gen`, an OpenAI image CLI, or the pipeline's
  direct-provider command for a production candidate.
- Do not fall back to another provider when preflight, ComfyUI, credentials, or
  Qwen fails. Report the failure and preserve the stage state.
- A user can explicitly request an exploratory provider comparison, but that
  output stays outside an approved production run and cannot become a donor or
  FigJam candidate without changing the repository contract.

## Prepare one stage

Read `schemas/edit-brief.schema.json` and
`docs/research/qwen-image-3-prompt-method.md` when authoring the Edit Brief.
Every stage must declare:

- the workflow profile, `runtime: comfyui`, Alibaba provider, and Qwen Image 3
  Pro model;
- one immutable reference path and verified SHA-256;
- one stage ID, one visual decision, and one approval state;
- exactly one bounded edit region as `[x, y, width, height]`;
- source geometry, an explicit source-ratio `width*height`, four candidates,
  and a fixed seed;
- ordered preservation, layout, style, negative, and quality constraints;
- Exact Copy character-for-character whenever the decision changes text.

The long structured brief may use Qwen's available instruction budget, but do
not add low-priority prose merely to fill it. Reference roles and invariants
come before style language.

Run the fail-closed preflight from the repository root before any paid or local
render call:

```bash
python3 -m qwen_ui_pipeline preflight path/to/brief.json \
  --reference path/to/immutable-reference.png
```

Do not continue unless it returns `status: ready_for_comfyui` with the expected
profile, provider, model, source hash, decision count, candidate count, seed,
and prompt metrics.

## Render, freeze, and assemble

1. Generate the ComfyUI graph with `python3 -m qwen_ui_pipeline workflow ...`
   and queue that exact graph in the existing ComfyUI runtime.
2. Save all four raw candidates, compiled prompt, source hash, seed, provider,
   model, ComfyUI prompt ID, response metadata, and contact sheet beneath the
   current stage.
3. Review only the stage's one decision. Mark attempts as rejected or freeze
   one selected donor; do not start the next stage while selection is open.
4. Set `stage.status` to `approved` and record
   `stage.approved_output_sha256` before deterministic assembly.
5. Assemble only the approved bounded region over the immutable source with
   `ReferenceRegionComposite`. Record this as assembly, not as model fidelity.
6. Verify the exact source hash, output hash, Exact Copy, dimensions, alpha,
   and zero outside-region pixel error before FigJam placement.

Use this artifact hierarchy so retries do not create muddy parallel run trees:

```text
artifacts/runs/<run-id>/
  stage-01-<decision>/
    brief.json
    attempt-01/
    attempt-02/
    approved/
  assembly/
  run.json
```

A new top-level `vNNN` is appropriate only for a genuinely new run definition
or an approved assembled successor—not for switching providers, revising the
same prompt, or retrying the same stage.

## FigJam boundary

After verification, load the Figma/FigJam skill and upload a named sibling.
Never replace the immutable source node. Include the stage manifest and focused
readback with the placement record.
