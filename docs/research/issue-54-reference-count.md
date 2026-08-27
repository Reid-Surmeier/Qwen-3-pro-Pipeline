# Does a natural second reference improve edit fidelity? (Issue #54)

Two frozen tasks, two arms each (source-only vs source + one natural,
repository-owned detail reference), same seed (`2026054001`) and settings
within each pair; the added reference — batched via core `ImageBatch` into
`QwenImage3Render` — is the only changed generation input, plus one sentence
in `reference_role` naming its role. Explicit OpenRouter /
`qwen/qwen-image-3-pro`, 1K. Run 2026-08-26; pre-submission record on the
Issue. 4 requested, 4 completed, $0.178 actual.

Historical context: the repository's prior second-reference experiments used
*synthetic* guides (green selection rectangles in Issue #2, masks-as-images
in Issue #34) and both failed. This tests *natural* references instead.

## Results

### club-insertion (plantstudio, 5:4; reference 2 = 3x pixel-art crop of the accepted assembly v003 club)

Both arms succeeded with exact titles and held layout. The with-reference
club's head geometry tracks the reference crop's compact grooved iron and
hosel curve slightly more closely; the source-only head is chunkier and more
faceted. The margin is small and within the same-seed similarity that
dominates matched pairs (Issue #18/#53). Importantly, the model did **not**
copy the red selection border present in the reference crop — the role
sentence was honored. No drift increase.

**Call: marginal, inconclusive for object-identity improvement.**

### material-change (xp-badge, 3:4, brushed silver foil; reference 2 = maga v001 metallic sticker photo)

A clear, interpretable difference:

- source-only converted the *entire* badge to monochrome silver — flag panes
  included (permitted by the brief's "may take on silver-tinted shading").
- with-reference reproduced the swatch's material convention: **colored
  printed artwork on a brushed-silver substrate** — the four flag panes kept
  saturated glossy inks exactly as the reference sticker's colored art sits
  on its metallic field.

Both are brief-compliant; the reference did not raise render quality (both
are excellent, text exact, geometry preserved) — it **resolved an ambiguity**
in the style instruction toward the reference's convention.

**Call: a natural material reference visibly steers interpretation; it is a
disambiguation tool, not a quality booster.**

## Recommendation for Issue #32's image_1..image_3 guidance

- Use additional natural references to pin down *underspecified* aspects
  (material behavior, object subtype morphology), stating each reference's
  role in one sentence.
- Do not expect extra references to rescue well-specified edits, and do not
  use synthetic guides (both prior attempts failed; this experiment's
  natural references caused no such harm).
- Same-seed pairs remain near-twins; reference effects show up exactly where
  the brief is ambiguous.

## Evidence

- Outputs + SHA-256: `artifacts/benchmarks/issue-54-reference-count/outputs/`,
  `.../collection-manifest.json`; attempt records with prompt IDs in
  `.../attempts/`; the constructed club reference in `.../refs/`.
- Runner: `scripts/issue54_reference_count.py`.

## Limitations

Two tasks, one seed per pair (sufficient for the material-interpretation
claim, which is a categorical difference well above #53's seed noise;
insufficient for the marginal club-morphology claim). Scored unblinded by
the designing agent.
