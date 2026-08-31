# Memorized-brand reversion: not observed (Issue #70)

This Issue began from a finding that was itself retracted mid-session: the
Issue #18 "brand reversion" instance turned out to be a mislabeled source
(the genuine ENERGY STAR sticker, not the parody), with the model behaving
source-faithfully. The redesigned experiment below tested the reversion
hypothesis against the repository's two **verified approved parody outputs**.

## Design

Two sources, one benign recolor edit each (never touching the parody
lettering), four protection arms per source with the protection as the only
changed input; seed `2026070001`, 1K, explicit OpenRouter via live ComfyUI:

- `bare` — no brand-specific protection
- `exact-copy` — exact_copy blocks quoting the parody text
- `negative` — negative constraint naming the real brand and forbidding it
- `wordmark-ref` — the parody wordmark crop as natural Reference 2

Outcome: 8 requested, **5 completed, 3 provider read-timeouts** (palantir
exact-copy and wordmark-ref, truthsocial exact-copy), all ambiguous, counted
as spent, never retried. $0.218 actual for 5 outputs.

## Results — reversion incidence 0/5

| Source | Arm | Edit executed | Real-brand element reappeared? |
| --- | --- | --- | --- |
| palantir | bare | field → deep green (band left blue) | **none** — script, star, band text intact |
| palantir | negative | field and band → deep green | **none** |
| truthsocial | bare | band → deep red | **none** — oval and both lines intact |
| truthsocial | negative | band → deep red | **none** |
| truthsocial | wordmark-ref | band → deep red | **none** |

Both bare arms — the condition the hypothesis predicted would fail —
preserved the parody identity completely. No element of the genuine
ENERGY STAR or Intel Inside marks appeared in any output.

## Conclusions

1. **T33 remains theoretical.** Across this session's entire evidence
   (the retracted #18 instance plus 5/5 clean outputs here), the pipeline's
   source-locked regime — authoritative reference image plus strong
   preservation language — shows no memorized-brand pull, even unprotected.
   The taxonomy entry stays as a watch-for class with incidence 0 observed.
2. **Secondary observation** (single-seed): the palantir edit's ambiguous
   "background field" wording split behavior — the bare arm recolored only
   the upper field, the negative-constraint arm recolored field and band.
   Consistent with PR #68's theme: ambiguity, not protection level, is where
   arms diverge.
3. **Operational**: 3 of 8 requests died as read-timeouts inside the node's
   180-second client window — the session-wide ambiguous rate is now 6 of 35
   (~17%) and rising with source complexity. Issue #71's configurable
   timeout is the highest-leverage operational fix available.

## Evidence

- Contact sheet: `artifacts/benchmarks/issue-70-t33-mitigation/contact-sheet.png`
- Outputs + SHA-256: `.../outputs/`, `.../collection-manifest.json`
- Attempt records with prompt IDs: `.../attempts/`; wordmark crops in `.../refs/`
- Runner: `scripts/issue70_t33_mitigation.py`

## Limitations

One seed, benign recolor edits only. Reversion may still occur under
heavier edits (relayout, regeneration of the wordmark region itself) or
text-free generation without an authoritative source; those are different
experiments. The exact-copy arm completed for neither source, so its
protective value is unmeasured.
