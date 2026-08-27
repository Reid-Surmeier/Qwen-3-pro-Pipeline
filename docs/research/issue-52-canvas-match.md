# Canvas-match ablation: does output geometry drive drift? (Issue #52)

One frozen task (the Issue #18 localized-replacement canonical brief), one
seed (`2026052001`), arms varying only `output.aspect_ratio`/`resolution`.
Explicit OpenRouter / `qwen/qwen-image-3-pro` via live ComfyUI; source
plantstudio `c9ddeaa3…` (474x403 ≈ 1.176:1). Run 2026-08-26; pre-submission
record on the Issue. 5 requested, 4 completed, 1 provider read-timeout
(`e-close-5x4-2k`, ambiguous, counted as spent, not retried). $0.172 actual.

## Per-arm results

| Arm | Delivered | Aspect drift vs source | Vision verdict |
| --- | --- | --- | --- |
| a-close-5x4-1k | 1024x820 (1.249) | +6% | Layout held; exact title; mild top/bottom clipping; clean club |
| b-mismatch-4x3-1k | 1024x768 (1.333) | +13% | Layout held; **title corrupted** ("Libraly of wildnowers"), top clipped, selection marker recolored black |
| c-mismatch-16x9-1k | 1024x576 (1.778) | +51% | **Uniform vertical squash** of the whole window; complete UI inventory incl. full tab row; exact title; one list-glyph error ("Soloman's seal"); marker black; hooked club hosel |
| d-mismatch-1x1-1k | 1024x1024 (1.000) | -15% | **Uniform vertical stretch** of the canvas region; complete UI; exact title; correct red marker; clean iron — arguably the cleanest output of the four |
| e-close-5x4-2k | — | — | provider read-timeout, no output |

## Findings

1. **The strong hypothesis is not supported on this route.** Aspect
   mismatch did not cause global redraw (T20) or content cropping collapse
   in any arm. The model adapts by *anisotropic scaling*: it renders the
   complete window and stretches or squashes it to fill the requested
   canvas. The historical golf-club v001 collapse (4:3) does not reproduce
   from aspect alone under the current canonical brief; its failures likely
   came from the brief/provider/settings of that run, not geometry per se.
2. **What geometry mismatch actually costs** is proportion fidelity: at
   16:9 every element is visibly squat, at 1:1 visibly elongated. For a UI
   whose pixel proportions matter, that is still a rejection — but it is a
   *predictable, uniform* distortion, not chaos, and deterministic
   downstream resizing can partially correct it.
3. **Text damage did not cleanly track aspect.** The 4:3 arm corrupted the
   title while 16:9 and 1:1 kept it exact; given Issue #53 measured ~30%
   per-seed incidence for copy corruption, a single seed cannot attribute
   arm b's damage to geometry. A follow-up would need ≥4 seeds per arm.
4. **Practical guidance**: prefer the nearest supported aspect (5:4 here)
   to minimize proportion distortion, but do not expect aspect choice alone
   to prevent or cause fine-grained failures. The taxonomy's
   failure-to-guidance map is updated to cite this measured result instead
   of the earlier v001-vs-v002 anecdote.

## Evidence

- Contact sheet: `artifacts/benchmarks/issue-52-canvas-match/contact-sheet.png`
- Outputs + SHA-256: `.../outputs/`, `.../collection-manifest.json`
- Attempt records with prompt IDs: `.../attempts/`
- Runner: `scripts/issue52_canvas_match.py`

## Limitations

One task, one brief, one seed per arm (justified for layout-level claims by
Issue #53's stability finding, insufficient for the text-damage question);
the 2K resolution arm never completed, so the resolution effect remains
unmeasured. Scored unblinded by the designing agent.
