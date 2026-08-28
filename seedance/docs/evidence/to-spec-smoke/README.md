# $to-spec smoke evidence

Two pre-authorized Seedance 2.0 Mini study clips exercising the `$to-spec` ladder's first
cell (seed pair: identical brief, seed 1 vs seed 7) on the synthetic test mark in
`assets/test-icon/`. The spec under test is `templates/favicon-loop.json` interpreted as a
loop spec with first = last anchor (`play-badge-480.png`, sha256 `0f8d8dfd…`).

Committed here (an exception to the usual runs-stay-local rule, at the owner's request, so
the PR carries reviewable evidence): the sanitized request, plan, capability snapshot,
job records, verification report, and the small output clips with SHA-256 digests. The raw
`request.payload.json` (embedded data URLs) stays local per `docs/run-contract.md`.

## Results (submitted and verified 2026-08-27 UTC)

| Run | Seed | Requested | Delivered | Estimated | Billed | First-anchor RMSE | Last-anchor RMSE | Loop-seam RMSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `seed1/` | 1 | 480x480, 4 s | 640x640, 4.04 s | $0.0756 | $0.05432 | 6.35 | 19.17 | 16.27 |
| `seed7/` | 7 | 480x480, 4 s | 640x640, 4.04 s | $0.0756 | $0.05432 | 6.31 | 21.05 | 18.25 |

## Findings

1. **`size` is not an exact canvas.** Both requests asked for `480x480` (advertised in the
   live profile's `supported_sizes`) and both delivered **640x640** — ByteDance Ark's
   native 480p 1:1 grid. The machine dimension check therefore fails by design honesty:
   treat OpenRouter `size` as resolution/ratio routing, and verify delivered dimensions
   rather than assuming them. Billing also tracked the estimate formula loosely
   ($0.05432 billed vs $0.0756 estimated per clip).
2. **Seed is a weak lever on 2.x, observed.** Both seeds produced the same gesture family
   — a single restrained scale-down "press" pulse returning toward the start pose — with
   near-identical metrics. This matches the upstream warning that 2.x results are
   prompt-dominated; spend study cells on prompt wording, not seed sweeps.
3. **Identity held; loop did not close.** Silhouette, triangle, palette, and corner
   treatment stayed locked in both clips (first-anchor RMSE ≈ 6, compression-level). But
   the final pose lands near, not on, the anchor (last-anchor RMSE 19–21; seam RMSE
   16–18), and the matte's green luminance drifts slightly mid-clip — two of the brief's
   named forbidden-drift modes, caught by exactly the checks the skill prescribes.

These are studies, not accepted outputs: they exist to demonstrate the pipeline and the
clause-by-clause scoring step, not to claim the loop spec is met. Machine verification
recorded `machine_checks_pass: false` (dimension honesty) and both runs still require
human style review by the repo's state rules.
