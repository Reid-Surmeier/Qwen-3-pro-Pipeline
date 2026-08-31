## Blind artifact review — Assembly v003

Candidate: `9c36e3712964a9a59b1fbfb08805de7037f9db8e`
Baseline: `b2e4f594f6fb23e0dcc4e2a3395d492585a35c9b`
Contract: `docs/reviews/issue-118-v003-contract.md`
Verdict: **PASS**

### Clause findings

- C1: Assembly v001's dimensions, crop, frame, panel, controls, states, ordering, spacing, and stripe band are preserved.
- C2: Assembly v001's header gradient and rules remain intact; the right blue bead and close button are byte-identical and unshifted. No rectangular patch or seam is visible.
- C3: The predeclared mask is glyph-shaped: 4,831 native mask pixels contain all 4,207 actual changes. Maximum per-box fill is 0.364804965.
- C4: All 19 strings are exact and legible at full and native scale. No broken, merged, doubled, clipped, or haloed glyphs or mismatched background patches were found.
- C5: `object` remains active and `material` inactive; the v001 tab silhouettes, fills, stepped notch, placement, and orientation remain intact.
- C6: Independent reproduction found zero changed pixels and zero maximum channel error outside the mask, zero right-control differences, an exact nearest-neighbor 4x enlargement, matching pinned font hashes, and no new provider request.

All packet reference hashes and all candidate evidence blobs matched. The 2576x1856 contact sheet contains four complete, unclipped panels and captions.

No specified defect was found.

This verdict is advisory evidence only and is not owner approval.
