# Seed variance for a fixed Edit Brief (Issue #53)

Eight pre-registered seeds, one fixed brief (the Issue #18 localized-
replacement canonical brief), byte-identical settings otherwise. Explicit
OpenRouter / `qwen/qwen-image-3-pro` via live ComfyUI, 1K, 5:4, source
plantstudio `c9ddeaa3…`. Run 2026-08-26 under ADR 0007's standing
authorization; pre-submission record on the Issue.

Outcome: 8 requested, 7 completed, 1 provider read-timeout (seed 555,
ambiguous, counted as spent, not retried). Actual cost $0.301.

## Per-seed vision scores

Classes from the Issue #26 taxonomy. "clean" = no visible instance.

| Seed | Edit success | T01 copy corruption | T11 object identity | T22 crop drift | Note |
| --- | --- | --- | --- | --- | --- |
| 11 | yes | clean | clean (grooved iron) | mild top+bottom | small glyph noise near Parameters tab |
| 733 | yes | clean | **hollow putter-like head** | mild bottom | |
| 4242 | yes | **title glyphs degraded** | hooked/merged head | **top clipped** | worst of set |
| 90210 | yes | clean | clean (grooved iron) | top clipped | |
| 314159 | yes | clean | clean (iron; tiny mid-shaft blob) | none — full tab row | **best of set** |
| 777001 | yes | trace ("fleabane" first list item blurred) | clean (grooved iron) | mild bottom | |
| 20260826 | yes | clean | **driver/wood head, not an iron** | mild bottom | |
| 555 | — | — | — | — | provider timeout, no output |

## Findings

1. **Macro-structure is seed-stable.** 7/7 completed seeds performed the
   requested replacement, kept the window layout, chrome, list, graph, and
   controls, and confined obvious change to the selection region. Global
   redraw (T20) occurred in 0/7. The canvas-match lever (5:4 near-source)
   held across every seed.
2. **Fine-grained defects are seed-volatile.** Object subtype fidelity
   failed in 3/7 (putter, hooked, driver instead of a seven-iron); copy
   corruption appeared in 2/7 (one moderate title degradation, one trace);
   top-edge crop clipping in 3/7. Roughly a 30-45% per-seed incidence for
   each fine-grained class.
3. **Practical rule of thumb** (exploratory, one task, one brief): a
   single-seed A/B is acceptable evidence for layout/canvas-level effects,
   and unacceptable for Exact Copy or object-subtype claims — batch at
   least 4 seeds when those dimensions decide the comparison. This
   retroactively bounds the Issue #18 conclusion: its rejected max-length
   hypothesis rested on layout-level parity (seed-stable), but its per-task
   "winners" turned on exactly the volatile dimensions.
4. **Provider reliability datum:** 1 of 8 sequential requests failed with a
   read timeout on an otherwise healthy route; the ~12% ambiguous-failure
   rate is worth assuming in batch cost planning.

## Evidence

- Contact sheet: `artifacts/benchmarks/issue-53-seed-variance/contact-sheet.png`
- Outputs + SHA-256: `.../outputs/`, `.../collection-manifest.json`
- Attempt records with prompt IDs: `.../attempts/`
- Runner: `scripts/issue53_seed_variance.py`; sheet: `scripts/issue53_contact_sheet.py`

## Limitations

One task, one brief, one provider route, 7 effective samples; scored by the
same agent that designed the run (no blinding — variance measurement, not an
A/B). Class incidences are coarse rates, not calibrated probabilities.
