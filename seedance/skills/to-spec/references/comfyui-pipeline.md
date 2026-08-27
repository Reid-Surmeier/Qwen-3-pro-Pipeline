# ComfyUI Seedance pipeline

How to iterate the same spec contract in ComfyUI. Full citations and the complete provider
survey live in `docs/research/seedance-comfyui-research.md` (observed 2026-08-26); this
page is the operating guide.

## Three integration routes

| Route | Billing / auth | When to use |
| --- | --- | --- |
| **This repo's planning nodes** (`SeedanceIconPrompt` → `SeedancePlanRequest`) | none — planning only | Default. Compile the brief, validate against a live profile, and price a request inside the graph; paid submission stays at the CLI cost gate (`docs/figma-comfyui-workflow.md`). |
| **ComfyUI built-in ByteDance API nodes** (`comfy_api_nodes/nodes_bytedance.py`) | Comfy account + prepaid credits (proxies BytePlus via `api.comfy.org`) | Best-maintained execution path in-graph: nodes ship in ComfyUI core, track model releases, and need no key management. Note this bypasses the repo's run contract — see "Evidence discipline" below. |
| **Custom key-owning packs** (kookliu/ComfyUI-Custom-Nodes for a direct BytePlus Ark key; gokayfem/ComfyUI-fal-API for fal billing) | your own provider key | Only when billing must go to your own Ark/fal account. Reseller-middleman packs are not recommended. |

Install ComfyUI only via `scripts/install_comfyui.sh` into an isolated checkout; never
modify or restart a shared runtime without ownership checks.

## Built-in node map (when executing in-graph)

- **Seedance 1.x** (inline `--resolution … --ratio … --seed … --camerafixed` flags appended
  to the prompt): `ByteDanceTextToVideoNode`, `ByteDanceImageToVideoNode`,
  `ByteDanceFirstLastFrameNode`, `ByteDanceImageReferenceNode`. 1.x uniquely offers
  `camera_fixed`, meaningful seeds, 2-second floors, and (1.0 pro) fractional-second
  `frames` control — relevant when a spec needs a very short clip.
- **Seedance 2.x** (structured request): `ByteDance2TextToVideoNode`,
  `ByteDance2FirstLastFrameNode`, `ByteDance2ReferenceNodeV2`. No camera flag — camera
  lock is prompt language only; the nodes warn results are non-deterministic regardless
  of seed.
- **Post-processing**: `ByteDanceVideoEnhanceNode` (vCube upscale / frame-rate to 120 fps),
  or OSS RIFE/FILM interpolation (Fannovel16/ComfyUI-Frame-Interpolation) plus per-frame
  model upscaling. Seedance always generates 24 fps; post-steps are the only frame-rate
  lever and must be recorded as separate evidence on the run.

**I2V shape:** `Load Image` → Seedance I2V / first-last node → `Save Video` (native
`VIDEO` socket chains into post nodes).

## Iteration patterns worth copying

1. **Draft-then-finalize (Seedance 1.5 pro only):** `draft: true` renders a cheap 480p
   preview, then a `draft_task` item finalizes with the same inputs/seed — the provider's
   own cheap-study ladder.
2. **Last-frame chaining:** `return_last_frame: true` hands back a watermark-free PNG of
   the final frame; feed it as the next task's `first_frame` to sequence longer motion.
   Seedance 2.5 also has a true `extend` task type.
3. **Loop approximation:** identical first + last frame (documented as allowed) starts and
   ends on the icon still; a perfect seam still needs `verify --loop` plus trim/cross-fade
   as a post-step. No native loop flag exists on any surface.
4. **Seed sweeps are a 1.x tool:** on 2.x, spend the same money on prompt-wording cells
   instead.

## Evidence discipline

Executing in ComfyUI (built-in or key-owning nodes) does not suspend the run contract:
capture the request JSON, canonical model, price badge or estimate, job ID, output hash,
and verification into a `runs/`-style evidence directory before comparing candidates. The
graph is an iteration surface, not an approval surface — the explicit cost acknowledgement
still happens with a human before anything paid.
