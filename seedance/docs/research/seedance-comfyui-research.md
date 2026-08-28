# Seedance × ComfyUI × OpenRouter — Research (verified against primary sources)

**Date:** 2026-08-26.
**Scope:** (1) Every Seedance control variable; (2) best ComfyUI pipeline + iteration patterns; (3) OpenRouter availability; (4) icon-animation notes.
**Method note:** The canonical parameter reference is BytePlus ModelArk's "Create a video generation task" API doc. That page is a JS SPA that WebFetch cannot render, so its full body text was extracted from the embedded content JSON of the raw HTML (`curl` + parsing the Quill deltas). The doc's own `UpdatedTime` stamp in the page payload is `2026-08-24`, so it is current. All quotes below are from that extracted text unless another source is cited.

---

## 1. The Seedance family and where it is hosted (as of Aug 2026)

Seedance is ByteDance Seed's video-generation family. Weights are **not open** — every integration is an API. Current line-up on the first-party API (BytePlus ModelArk, a.k.a. Volcano Engine Ark internationally):

| Model | Ark model ID | Modes | Output |
|---|---|---|---|
| Dreamina Seedance 2.5 | `dreamina-seedance-2-5-260628` | T2V, I2V (first frame / first+last), omni reference-to-video (ref images/videos/audio), video edit, video extend | 480p/720p/1080p, 4–30 s (or auto), audio |
| Dreamina Seedance 2.0 | `dreamina-seedance-2-0-260128` | T2V, I2V, omni reference, edit, extend | 480p/720p/1080p/4k, 4–15 s, audio |
| Dreamina Seedance 2.0 fast | `dreamina-seedance-2-0-fast-260128` | same as 2.0 | 480p/720p only |
| Dreamina Seedance 2.0 mini | `dreamina-seedance-2-0-mini` | same as 2.0 | 480p/720p only |
| Dreamina Seedance 1.5 pro | `seedance-1-5-pro-251215` | T2V, I2V (first / first+last), draft mode, return_last_frame, audio | 480p/720p/1080p, 4–12 s |
| Seedance 1.0 pro | `seedance-1-0-pro-250528` | T2V, I2V (first / first+last) | 480p/720p/1080p, 2–12 s, 24 fps, silent |
| Seedance 1.0 pro fast | `seedance-1-0-pro-fast-251015` | T2V, I2V (first frame only) | 480p/720p/1080p, 2–12 s |
| Seedance 1.0 lite (t2v/i2v) | `seedance-1-0-lite-t2v-250428` / `seedance-1-0-lite-i2v-250428` | T2V / I2V | deprecated in ComfyUI's node list |

Model-ID sources: ComfyUI's ByteDance API-node source, which pins these exact strings ([nodes_bytedance.py](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy_api_nodes/nodes_bytedance.py), `SEEDANCE_MODELS` dict at ~L114 and the video-node combo lists); Seedance 1.0 pro model card ([BytePlus ModelArk model card](https://docs.byteplus.com/en/docs/modelark/1587798)); mode/duration/resolution matrix from the [Create a video generation task API doc](https://docs.byteplus.com/en/docs/ModelArk/1520757) ("Model capabilities" and "Supported models and values" sections, quoted throughout §2). Deprecation of the 1.0-lite IDs: `nodes_bytedance.py` marks `["seedance-1-0-lite-t2v-250428", "seedance-1-0-lite-i2v-250428"]` as deprecated.

Technical reports: [Seedance 1.0: Exploring the Boundaries of Video Generation Models (arXiv 2506.09113)](https://arxiv.org/abs/2506.09113) and [Seedance 2.0: Advancing Video Generation for World Complexity (arXiv 2604.14148)](https://arxiv.org/pdf/2604.14148); ByteDance Seed's [tech-report announcement](https://seed.bytedance.com/en/blog/tech-report-of-seedance-1-0-is-now-publicly-available).

**Hosting surfaces:** BytePlus ModelArk (first-party, `POST https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks`), [fal.ai](https://fal.ai/models/bytedance/seedance-2.5/image-to-video/api), [Replicate](https://replicate.com/bytedance/seedance-1-pro/api/schema), [OpenRouter](https://openrouter.ai/bytedance) (since 2026-04-15), and ComfyUI's built-in API nodes (proxying BytePlus via `api.comfy.org`).

### Pricing (documented)

- **ModelArk:** token-billed. Seedance 1.0 pro: "2.5 USD/M Tokens" for both T2V and I2V ([model card](https://docs.byteplus.com/en/docs/modelark/1587798)). The API doc's Aug-2026 promo box gives real-world anchors: Seedance 2.5 1080p "prices starting at approximately USD 0.41 per second" (at the 72% promo rate, 2026-08-14→09-17); Seedance 2.0 mini 720p "starts at approximately USD 0.03 per second" (40% promo); Seedance 2.0 fast 720p "starts at approximately USD 0.09 per second" (75% promo) ([API doc](https://docs.byteplus.com/en/docs/ModelArk/1520757)). `service_tier: "flex"` (offline queue) is "priced at 50% of online inference" but is **not** available for 2.x models (same doc).
- **OpenRouter** (per-second, from [openrouter.ai/bytedance](https://openrouter.ai/bytedance) and the [seedance-2.0 model page](https://openrouter.ai/bytedance/seedance-2.0)): `seedance-1-5-pro` $0.02306/s; `seedance-2.0` $0.06726/s (480p) up to $0.7776/s (4K); `seedance-2.0-fast` $0.04035/s; `seedance-2.0-mini` $0.01345/s; `seedance-2.5` $0.1028/s. (List prices shown at the lowest tier; 2.0 scales by resolution.)
- **ComfyUI API nodes:** prepaid Comfy credits; the nodes carry live price badges computed from resolution/ratio/duration (the JSONata price expressions are in `nodes_bytedance.py`, e.g. 2.5 at 1080p ≈ $0.016731 per 1k tokens-equivalent unit in `_SEEDANCE2_PRICE_EXPR_TEMPLATE`). Credits: "Partner Nodes require credits for API calls to closed-source models, so they do not support free usage" ([API-nodes overview](https://docs.comfy.org/tutorials/api-nodes/overview)).

---

## 2. Complete control-variable reference (canonical = ModelArk API)

Endpoint: `POST https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks` — asynchronous; poll `Retrieve a video generation task` (`GET .../tasks/{id}`) or use `callback_url`. "This API supports only API Key authentication." All statements in this section are from the [Create a video generation task doc](https://docs.byteplus.com/en/docs/ModelArk/1520757) unless noted.

### 2.1 Top-level request fields

| Field | Type / range | Default | Notes (verbatim where quoted) |
|---|---|---|---|
| `model` | string | — | Ark model ID or endpoint ID (table in §1). |
| `content` | object[] | — | Mixed list of `text`, `image_url`, `video_url`, `audio_url`, `draft_task` items. Supported combos: "Text", "Text (optional) + image", "+ video", "+ audio (2.5 supports audio-only)", and image+video+audio mixes. |
| `resolution` | string | 2.5/2.0/1.5: `720p`; 1.0 pro & pro-fast: `1080p` | 2.5: 480p/720p/1080p. 2.0: 480p/720p/1080p/**4k**. 2.0 fast & mini: 480p/720p. 1.5 pro & 1.0 pro(+fast): 480p/720p/1080p. 2.5@1080p and 2.0@4K are 10-bit H.265/HEVC. |
| `ratio` | string | 2.5/2.0/1.5: `adaptive`; 1.0 pro T2V: `16:9`, I2V: `adaptive` | Values: `16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive`. For 2.5 first/first-last I2V, edit, and extend, ratio "only supports adaptive" (first-frame image's AR is preserved). Exact pixel tables per ratio/resolution are in the doc (e.g. 720p 16:9 = 1280×720; 1:1 = 960×960; 480p 1:1 = 640×640). |
| `duration` | integer (seconds) | see right | "Dreamina Seedance 2.5: Default -1; supports [4, 30] or -1. Seedance 2.0 series: Default 5; supports [4, 15] or -1. Seedance 1.5 pro: Default 5; supports [4, 12] or -1. Seedance 1.0 pro: Default 5; supports [2, 12]. Seedance 1.0 pro fast: Default 5; supports [2, 12]." `-1` = model picks a whole-second length; for 2.5 video-editing, duration must be `-1` (output ≈ source length). |
| `frames` | integer | — | **1.0 pro / pro fast only.** Overrides `duration`; frame count = duration × 24; valid values are integers `25 + 4n` in `[29, 289]` — enables fractional-second clips (e.g. 57 frames = 2.375 s). |
| `seed` | integer `[-1, 2147483647]` | `-1` (random) | Listed as supported for **1.5 pro, 1.0 pro, 1.0 pro fast**. Same seed → "similar results will be generated, but complete consistency is not guaranteed." |
| `camera_fixed` | boolean | `false` | Supported by **1.5 pro, 1.0 pro, 1.0 pro fast**; "Reference-image scenarios are not supported." `true`: "ModelArk will append the fixed camera instruction to the user's prompt, but the actual result is not guaranteed." |
| `watermark` | boolean | `false` | `true` adds an "AI Generated" watermark bottom-right. |
| `generate_audio` | boolean | `true` | **2.5, 2.0 series, 1.5 pro.** "Put dialogue content in double quotes to optimize the audio generation effect." Output audio is always mono. |
| `return_last_frame` | boolean | `false` | Returns the final frame as a **watermark-free PNG** at video resolution via the retrieve API. Doc tip: "Use the last frame of the previously generated video as the first frame of the next video task to quickly generate a sequence of videos." (Listed under 1.5 pro support in the doc.) |
| `draft` | boolean | `false` | **1.5 pro only.** Draft mode renders a cheap 480p preview "to quickly verify whether the scene structure, shot scheduling, subject motion match the prompt intent"; finalize by submitting a `draft_task` content item with the draft's task ID (model/text/image/audio/seed/ratio/duration/camera_fixed are reused). |
| `omni_reference_task_type` | string: `auto` \| `reference` \| `edit` \| `extend` | `auto` | **2.5 only.** Pre-validates task constraints at submit time (edit ⇒ ≥1 `reference_video`, source 4–30 s, `ratio: adaptive`, `duration: -1`; extend ⇒ ≥1 `reference_video`, `ratio: adaptive`). |
| `output_format` | string: `mp4` \| `mov` | `mp4` | **2.5 only.** MOV = H.264 YUV 4:4:4 + PCM for pro post workflows. |
| `priority` | integer `[0, 9]` | `0` | **2.5 & 2.0 series.** Queue-jump within the same endpoint; FIFO otherwise. |
| `service_tier` | `default` \| `flex` | `default` | `flex` = offline inference at 50% price; **not supported for 2.5/2.0**. |
| `callback_url` | string (HTTPS) | — | POST callback on state change; statuses `queued/running/succeeded/failed/expired`; 3 retries on delivery failure. |
| `execution_expires_after` | integer s `[3600, 259200]` | `172800` (48 h) | Task auto-expires past this. |
| `safety_identifier` | string ≤64 chars | — | Hashed end-user ID for abuse detection. |

**Not exposed anywhere:** no `negative_prompt`, no CFG/guidance scale, no sampler/steps — none of ModelArk, fal, Replicate, OpenRouter, or the ComfyUI nodes expose them for Seedance. **FPS is fixed at 24** for generation (model card: "frame rate of 24 fps"; task responses return `framespersecond=24`); the only frame-rate levers are 1.0-pro's `frames` count and post-processing.

### 2.2 `content` items and conditioning roles

- `{"type": "text", "text": "..."}` — the prompt. "Recommended prompt length: no more than 500 Chinese characters or 1,000 English words." All models take English; 2.5 adds ES/ID/PT/JA/MS/TH/AR/VI/KO; 2.0 adds ES/ID/PT/JA.
- `{"type": "image_url", "image_url": {"url": ...}, "role": ...}` — URL, `data:image/<fmt>;base64,...`, or `asset://<ASSET_ID>`. Roles:
  - `first_frame` (or omitted) — I2V first-frame conditioning, **all models**, exactly 1 image.
  - `last_frame` — with a `first_frame` image for first+last-frame I2V (2.5, 2.0 series, 1.5 pro, 1.0 pro; 2 images, role required). "The first-frame and last-frame images can be identical." If ARs differ, the first frame wins and the last frame is center-cropped.
  - `reference_image` — omni reference (2.5: 1–30 images; 2.0 series: 1–9).
  - Image constraints: jpeg/png/webp/bmp/tiff/gif (heic/heif from 1.5 pro on), AR 0.4–2.5, 300–6000 px per side, <30 MB each, request body ≤64 MB.
  - The three conditioning families — first-frame I2V, first+last I2V, and omni-reference — "are mutually exclusive scenarios and cannot be mixed."
- `{"type": "video_url", ..., "role": "reference_video"}` — 2.5 (≤10 clips, each 2–30 s, total ≤30 s) / 2.0 series (≤3 clips, 2–15 s, total ≤15 s); mp4/mov, 24–60 fps, ≤200 MB.
- `{"type": "audio_url", ..., "role": "reference_audio"}` — wav/mp3; 2.5: ≤10 clips 2–30 s (total ≤30 s), audio-only input allowed; 2.0: ≤3 clips 2–15 s, audio-only not allowed. ≤15 MB each.
- `{"type": "draft_task", "draft_task": {"id": ...}}` — finalize a 1.5-pro draft.
- 2.x restriction: "models do not support directly uploading reference images or videos that contain real human faces" — portrait assets go through ModelArk's verified digital-character/asset flow.

### 2.3 Inline prompt-flag syntax (the "--ratio 16:9 --dur 5" convention)

The doc's "Parameter input methods" section: "For resolution, ratio, duration, frames, seed, camera_fixed, and watermark, all models support both passing parameters directly in the request body and appending `--[parameters]` after the text prompt." Body fields are the "Conventional method (recommended)" with strict validation; inline flags are the "Legacy method" with weak validation. The doc's own weak-validation example (verbatim):

```json
{
    "model": "seedance-1-5-pro-251215",
    "content": [
        {
            "type": "text",
            "text": "The kitten is yawning at the camera. --rs 720p --rt 16:9 --dur 5 --seed 11 --cf false --wm true"
        }
    ]
}
```

So the short flags are `--rs` (resolution), `--rt` (ratio), `--dur` (duration), `--seed`, `--cf` (camera_fixed), `--wm` (watermark); long forms also work — ComfyUI's own nodes append `--resolution … --ratio … --duration … --seed … --camerafixed … --watermark …` ([nodes_bytedance.py](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy_api_nodes/nodes_bytedance.py), `ByteDanceTextToVideoNode.execute`, ~L1676).

### 2.4 Response / task object

Create returns `{"id": "cgt-…"}`; retrieve returns status (`queued/running/succeeded/failed/expired`), `content.video_url` (and `last_frame_url` when requested), `usage.completion_tokens/total_tokens`, plus echoed `seed`, `resolution`, `ratio`, `duration`, `framespersecond: 24`, `generate_audio`. Task records live 7 days; returned `duration` = floor(frames/24). (All from the same API doc, including a captured sample `ContentGenerationTask(... framespersecond=24 ... seed=33608 ...)`.)

### 2.5 Third-party schema deltas (first-party API surfaces for the same model)

- **fal.ai — Seedance 1.0 Pro I2V** ([schema](https://fal.ai/models/fal-ai/bytedance/seedance/v1/pro/image-to-video/api)): `prompt`, `image_url` (required); `end_image_url` (last frame); `aspect_ratio` enum `21:9, 16:9, 4:3, 1:1, 3:4, 9:16, auto` (default `auto`); `resolution` `480p/720p/1080p` (default `1080p`); `duration` 2–12 (default `"5"`); `camera_fixed` bool; `seed` int (−1 = random); `enable_safety_checker` (default true); `num_frames` (overrides duration). Output: `video` file + used `seed`.
- **fal.ai — Seedance 2.5 I2V** ([schema](https://fal.ai/models/bytedance/seedance-2.5/image-to-video/api)): `prompt`, `image_url` (≤30 MB) required; `end_image_url`; `resolution` `480p/720p/1080p` default `720p`; `duration` `auto | 4–30` default `auto`; `aspect_ratio` default `auto`; `generate_audio` default `true`; `bitrate_mode` `standard|high`; `end_user_id`. No `camera_fixed` on 2.5 (matches Ark, where camera_fixed is 1.x-only). Other fal slugs: `bytedance/seedance-2.0/{text-to-video, image-to-video, reference-to-video}` and `/fast/` variants ([fal search results/model pages](https://fal.ai/models/bytedance/seedance-2.0/image-to-video/api)).
- **Replicate — `bytedance/seedance-1-pro`** ([schema](https://replicate.com/bytedance/seedance-1-pro/api/schema)): "text-to-video and image-to-video support for 5s or 10s videos, at 480p and 1080p"; inputs `prompt, image, last_frame_image, duration, resolution, aspect_ratio, fps, camera_fixed, seed`.

---

## 3. Best ComfyUI pipeline

### 3.1 Built-in API nodes (recommended; best maintained)

Seedance ships **in ComfyUI core** as API/partner nodes — no custom pack needed. Source of truth: [`comfy_api_nodes/nodes_bytedance.py`](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy_api_nodes/nodes_bytedance.py) (≈3,900 lines, actively maintained in the main repo alongside `nodes_bytedance_llm.py`). Auth is your **Comfy account + prepaid credits** (Settings → User login; nodes call `api.comfy.org` which proxies BytePlus — endpoints `"/proxy/byteplus/api/v3/contents/generations/tasks"` and `"/proxy/byteplus-seedance2/..."` in the source). "API nodes require you to be logged into your ComfyUI with a Comfy account… credits greater than 0" ([API-nodes overview](https://docs.comfy.org/tutorials/api-nodes/overview)). No ByteDance API key or env var is involved for the built-ins.

**Seedance 1.x nodes** (category `partner/video/ByteDance`, each outputs a `VIDEO`):

| Node ID | Display name | Key inputs |
|---|---|---|
| `ByteDanceTextToVideoNode` | ByteDance Text to Video | model (`seedance-1-5-pro-251215`, `seedance-1-0-pro-250528`, `seedance-1-0-lite-t2v-250428`, `seedance-1-0-pro-fast-251015`; default pro-fast), prompt, resolution 480p/720p/1080p, aspect_ratio `16:9,4:3,1:1,3:4,9:16,21:9`, duration 3–12 (default 5; ≥4 enforced for 1.5 pro), seed 0–2147483647, camera_fixed (default false), watermark (default false), generate_audio ("ignored for any model except seedance-1-5-pro") |
| `ByteDanceImageToVideoNode` | ByteDance Image to Video | same + `image` (first frame) |
| `ByteDanceFirstLastFrameNode` | ByteDance First-Last-Frame to Video | same + `first_frame`, `last_frame` (no pro-fast model) |
| `ByteDanceImageReferenceNode` | ByteDance Reference Images to Video | 1–4 reference `images`, 480p/720p only, models 1.0 pro / 1.0 lite i2v |

These nodes serialize the settings as inline prompt flags (`--resolution … --ratio … --duration … --seed … --camerafixed … --watermark`) into the Ark task request — i.e., they use the legacy text-command convention documented by BytePlus (§2.3).

**Seedance 2.x nodes** (structured JSON request via `Seedance2TaskCreationRequest` — fields `model, content, generate_audio, resolution, ratio, duration, seed, watermark, output_format, omni_reference_task_type`):

| Node ID | Display name | Key inputs |
|---|---|---|
| `ByteDance2TextToVideoNode` | ByteDance Seedance 2.5 Text to Video | model combo (Seedance 2.5 / 2.0 [480p–4k] / 2.0 Fast / 2.0 Mini [480p/720p]); per-model dynamic inputs: prompt, resolution (2.5 default 720p), ratio `16:9,4:3,1:1,3:4,9:16,21:9,adaptive`, duration (2.5: 4–30 default 5; 2.0: 4–15 default 7), generate_audio (default true), output_format `mp4`; plus seed (note: "results are non-deterministic regardless of seed") and watermark |
| `ByteDance2FirstLastFrameNode` | ByteDance Seedance 2.5 First-Last-Frame to Video | + optional `first_frame`/`last_frame` images or `first_frame_asset_id`/`last_frame_asset_id` |
| `ByteDance2ReferenceNodeV2` (+ legacy `ByteDance2ReferenceNode`) | ByteDance Seedance 2.5 Reference to Video | + autogrow `reference_images` (≤30), `reference_videos` (≤10), `reference_audios`; `video_editing` toggle; `task_type` `auto/reference/edit/extend` |
| `ByteDanceCreateImageAsset` / `ByteDanceCreateVideoAsset` | Create Image/Video Asset | uploads portrait assets, returns `asset_id`/`group_id` (real-person liveness verification path — see [partner-node tutorial](https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0)) |
| `ByteDanceVideoEnhanceNode` | ByteDance vCube Video Enhance | post-step: upscale/frame-rate enhance; fps up to 120 (`source` keeps rate; >30 fps costs 2×, >60 fps 4×), resolution 720p–2K |

Official tutorial + downloadable workflow templates: [Seedance 2.0 partner-node tutorial](https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0), [supported-models page](https://comfy.org/p/supported-models/seedance-bytedance/), and ready T2V/R2V/FLF workflows on [comfy.org/workflows](https://comfy.org/workflows/model/seedance/).

**Typical workflow shape (I2V):** `Load Image` → `ByteDanceImageToVideoNode` (or `ByteDance2FirstLastFrameNode` with only `first_frame` connected) → `Save Video`. The video output is a native ComfyUI `VIDEO` socket, so it chains directly into save/preview or post nodes.

**Why the built-ins are the best-maintained path:** they live in the core repo (updated with each model release — 1.5-pro, 2.0, 2.5, price badges, deprecations are already tracked), require no key management, expose every Ark control that matters, and are documented on docs.comfy.org.

### 3.2 Custom-node alternatives (if you want your own API key / different billing)

- [kookliu/ComfyUI-Custom-Nodes](https://github.com/kookliu/ComfyUI-Custom-Nodes) — direct **BytePlus Ark key** nodes for Seedream 4.0 + Seedance (Text2Video, Image2Video, Refs2Video, FirstLastFrame; supports `seedance-1-5-pro-251215`). Choose this to bill straight to your own ModelArk account.
- [FloyoAI/ComfyUI-Seed-API](https://github.com/FloyoAI/ComfyUI-Seed-API) — BytePlus foundation-model nodes incl. `seedance-1-0-pro-250528`, `seedance-1-0-pro-fast-251015`.
- [gokayfem/ComfyUI-fal-API](https://github.com/gokayfem/ComfyUI-fal-API) — wraps 1,400+ fal.ai models (incl. Seedance endpoints) with a fal key; useful if you're already on fal billing.
- [Anil-matcha/seedance2-comfyui](https://github.com/Anil-matcha/seedance2-comfyui) — Seedance 2.0/2.5/Mini via the third-party MuAPI reseller (key via node or `~/.muapi/config.json`); small (38★) and adds a middleman — not recommended over the built-ins.

### 3.3 Iteration patterns

- **Seed sweeps:** meaningful only on 1.x (Ark: same seed ⇒ "similar results…, but complete consistency is not guaranteed"); the 2.x ComfyUI nodes explicitly warn "results are non-deterministic regardless of seed" — for 2.x, iterate on prompt/draft instead. ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757); [nodes_bytedance.py](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy_api_nodes/nodes_bytedance.py))
- **Cheap iteration via draft mode (1.5 pro):** `draft: true` renders a low-token 480p preview; finalize with `draft_task` reusing the exact inputs/seed. ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757))
- **First-frame conditioning from a still render:** the core I2V flow (`role: first_frame`); with `ratio: adaptive` the model preserves the still's aspect ratio.
- **Last-frame chaining for longer clips:** set `return_last_frame: true` and feed the returned watermark-free PNG as the next task's `first_frame` — the doc's own recommended pattern ("Generate multiple consecutive videos"). On fal, the same chain uses `end_image_url`/output frames; Seedance 2.5 additionally has a true `extend` task type that continues a source clip.
- **Post-steps in ComfyUI:** ByteDance's own `ByteDanceVideoEnhanceNode` (vCube) for upscale + frame-interpolation to up to 120 fps in-graph; or the standard OSS pair — RIFE/FILM frame interpolation via [Fannovel16/ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation) and video upscalers (e.g. `Upscale Image (using Model)` per-frame) — since Seedance always outputs 24 fps.

---

## 4. OpenRouter — yes, Seedance is on it

OpenRouter launched video generation on **April 15, 2026**: "On day one, we're supporting text-to-video and image-to-video on Seedance 2.0 / 1.5, Veo 3.1, Wan 2.7 / 2.6, and Sora 2 Pro" ([announcement](https://openrouter.ai/blog/announcements/video-generation/)).

- **Endpoint:** dedicated async `POST https://openrouter.ai/api/v1/videos` (NOT chat/completions); poll `GET /api/v1/videos/{jobId}` until `completed`, download from `unsigned_urls[0]`. Capability discovery: `GET /api/v1/videos/models` (fields like `supported_resolutions`, `supported_durations`, `supported_aspect_ratios`, `supported_frame_images`, `pricing_skus`, `allowed_passthrough_parameters`). ([Video-generation docs](https://openrouter.ai/docs/features/multimodal/video-generation); [cookbook](https://openrouter.ai/docs/cookbook/video-generation/choose-video-model); [announcement](https://openrouter.ai/blog/announcements/video-generation/))
- **Slugs & pricing** ([openrouter.ai/bytedance](https://openrouter.ai/bytedance)): `bytedance/seedance-1-5-pro` ($0.02306/s, added 2026-03-23), `bytedance/seedance-2.0` ($0.06726/s→$0.7776/s by resolution, 4–15 s, 480p–4K, audio; 2026-04-15), `bytedance/seedance-2.0-fast` ($0.04035/s), `bytedance/seedance-2.0-mini` ($0.01345/s, 2026-08-12), `bytedance/seedance-2.5` ($0.1028/s, 2026-08-07). No Seedance 1.0 slugs. Provider is "Seed" ([seedance-2.0 page](https://openrouter.ai/bytedance/seedance-2.0)).
- **Request fields** ([docs](https://openrouter.ai/docs/features/multimodal/video-generation)): `model`, `prompt` (required); `duration`, `resolution`, `aspect_ratio`, `size` (WxH), `frame_images` (first/last-frame image-to-video), `input_references`, `generate_audio` (default true where supported), `seed` ("Not guaranteed by all providers"), `callback_url`, `provider` (passthrough). Note: video jobs are ZDR-ineligible.
- **Minimal curl** (docs' example, with a Seedance slug substituted):

```bash
curl -X POST "https://openrouter.ai/api/v1/videos" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bytedance/seedance-2.0-mini",
    "prompt": "A flat vector rocket icon gently lifts off, subtle flame flicker, static camera",
    "duration": 4,
    "resolution": "720p",
    "aspect_ratio": "1:1"
  }'
# then poll: curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/videos/{id}
```

*(The verbatim docs example uses `google/veo-3.1` with only `model` + `prompt`; the extra fields are documented body params. For image-to-video, add `frame_images` with a first-frame entry per the docs.)*

---

## 5. Icon-animation notes (small UI icons/logos → short clips)

- **Use I2V first-frame from a clean still** (`role: first_frame`) with `ratio` left at `adaptive` — Ark then "automatically preserves the aspect ratio of the first-frame image", so a square icon stays 1:1; otherwise pick `1:1` explicitly (native 1:1 outputs: 640×640 @480p, 960×960 @720p, 1440×1440 @1080p). ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757))
- **Lock the camera:** on 1.x models set `camera_fixed: true` (appends a fixed-camera instruction; "actual result is not guaranteed"); on 2.x there is no flag — write "static camera, fixed shot" in the prompt. ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757); fal 2.5 schema has no camera_fixed either)
- **Short durations:** 1.0 pro supports 2–12 s (only model family going down to 2 s; 1.5 pro/2.x floor is 4 s); for sub-/fractional-second control use 1.0 pro's `frames` (`25+4n`, 29–289 → 1.2–12 s). ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757))
- **Loop-friendliness:** no native loop flag anywhere. The documented approximation is **first+last-frame I2V with the same image in both roles** — "The first-frame and last-frame images can be identical" — which starts and ends the clip on your icon still. Alternatively chain with `return_last_frame`. Cross-fade/trim for a perfect loop is a post-step. ([Ark doc](https://docs.byteplus.com/en/docs/ModelArk/1520757))
- **Silence & cleanliness:** set `generate_audio: false` on 1.5/2.x (audio also changes billing SKUs), `watermark: false` (default), and prefer 720p+ so small glyph edges survive; Seedance 1.0's stylization strengths ("3D cartoon, sketch" etc. per the [model card](https://docs.byteplus.com/en/docs/modelark/1587798)) suit flat-design icons.
- **Cheapest sweep path:** OpenRouter `bytedance/seedance-2.0-mini` at $0.01345/s or ComfyUI 1.0-pro-fast node; iterate at 480p, finalize at 1080p (1.0 pro defaults to 1080p).

---

## 6. Confidence & gaps

**High confidence (direct primary sources):** ModelArk parameter table, inline-flag syntax (`--rs/--rt/--dur/--seed/--cf/--wm` example verbatim), roles, per-model resolution/duration/ratio defaults (extracted from the live doc payload, UpdatedTime 2026-08-24); ComfyUI node names/params/endpoints (read from `nodes_bytedance.py` source, grepped locally); OpenRouter endpoint, slugs, launch date.

**Gaps / lower confidence:**
1. **BytePlus doc extraction caveat:** content was reconstructed from the SPA's embedded JSON; table cell ordering (pixel-dimension matrix) was scrambled, so per-cell pixel values I quoted were cross-read carefully but a few ratio↔resolution pairings could be mis-attributed. The parameter prose is verbatim.
2. **`seed`, `camera_fixed`, `return_last_frame` "Supported models" lists** in the Ark doc were adjacent-line reads in the reconstructed text; I'm confident about camera_fixed (1.5-pro/1.0-pro/pro-fast, matches ComfyUI omitting camera_fixed from 2.x nodes) but `return_last_frame`'s exact model coverage (1.5-pro-only vs. also 1.0) is uncertain.
3. **OpenRouter numbers** (per-second prices, dates) came via WebFetch summaries of openrouter.ai pages, which are rendered client-side; values are plausible and internally consistent but were not double-sourced. The curl example beyond `model`+`prompt` is composed from documented fields, not copied verbatim.
4. **fal pricing per clip** was not shown in the fetched schema pages; not reported.
5. **Replicate schema enums** (exact duration/resolution/fps values) were only partially rendered; the "5s or 10s, 480p and 1080p" line is from the model description, and Replicate per-second pricing was not visible.
6. **Dreamina Seedance 2.x prompt guides** ([2.0 guide](https://docs.byteplus.com/en/docs/ModelArk/2222480), [2.5 guide](https://docs.byteplus.com/en/docs/ModelArk/2607689)) did not render and were not payload-extracted — camera-movement prompt vocabulary for 2.x is therefore not enumerated here.
7. **Seedance 2.0-mini Ark model ID** `dreamina-seedance-2-0-mini` has no date suffix in ComfyUI's source; that may be an alias rather than the full versioned ID.
8. `frames`' documented lower bound is "[29, 289]" while the formula text says `25 + 4n` — 29 = 25+4·1, consistent, but the doc's example also cites 57 which is 25+4·8: both fit; range quoted as printed.
