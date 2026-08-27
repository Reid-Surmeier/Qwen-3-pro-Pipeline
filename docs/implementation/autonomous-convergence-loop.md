# Autonomous convergence loop

## Outcome

A reconstruction is not `verified` because it resembles one screenshot.
Verification requires two layers with different authority:

1. **deterministic gates** for canvas geometry, licensed-region change,
   invariant-pixel stability, interaction behaviour, hit ownership, and
   provider provenance;
2. **correction replay**, an exploratory pass driven by
   [`qa/correction-replay.json`](../../qa/correction-replay.json) — every
   recurring correction the project owner has made, encoded as a review prompt
   with required evidence and a promotion rule.

The second layer is intentionally exploratory. It may find a failure. It can
never waive, override, or substitute for a gate.

A finding is not a completed loop result. The runner must route it back to the
owning production stage, add a regression contract, apply the correction, and
replay the same gesture and visual checkpoint. `revision-required` is an
intermediate state, never a successful outcome.

## Loop

```text
Reference authority (checksum, canvas, source-ownership masks)
  -> deterministic component extraction (component-workflow)
  -> Qwen Render Pass, only where a crop cannot serve
  -> region assembly (ReferenceRegionComposite)
  -> interactive build over independent components
  -> Gate 1: fidelity contract + interaction contracts
  -> Gate 2: correction replay by an independent verifier
  -> finding?
       yes -> minimise -> promote to a reproducible test -> revise
              -> restart from the owning stage
       no  -> full suite -> verified
```

## Routing table

Every finding belongs to exactly one production stage:

| Finding | Owning stage |
| --- | --- |
| Missing, incorrect, or contaminated visual state | Qwen Render Pass and its bounded assembly |
| Missing component or wrong asset ownership | Component extraction and the runtime manifest |
| Wrong bounds, clipping, overlap, or z-order | Assembly geometry |
| Dead, generic, non-reversible, or choppy interaction | Interactive build behaviour and timing |
| Passes locally but not in the delivered runtime | Runtime export integration |

## Independent verification

Gate 2 runs in a **separate agent on a different model family from the
builder**, for one reason: an agent that grades its own output shares its own
blind spots. The verifier receives region crop pairs rather than whole
screenshots, because a bounded crop pair is a far more reliable visual
judgement than a full-screen comparison, and the component manifest already
supplies the crop list.

The verifier returns structured findings — region, verdict, defect class,
coordinates. A finding it cannot localise is a fail, not a pass. It never
returns prose approval.

## Required evidence per reconstruction

- immutable reference identity and crop geometry;
- component manifest with stable identifiers and edit authority;
- Render Pass request artifacts and exact charged cost for every paid pass;
- fidelity-contract result showing zero invariant violations;
- interaction checkpoints for every enabled control
  (see [interaction contracts](interaction-contracts.md));
- correction-replay bundle with a verdict for every applicable prompt;
- local region comparisons rather than a single whole-window score.

## Cost discipline

Paid verification is OpenRouter-only and stops before image eleven for one
linked Issue (ADR 0003). Run the smallest source-locked batch that can resolve
the isolated failure, retain the exact charged cost in `run.json`, and reject
drifting candidates rather than re-rolling blindly. Provider ambiguity after
submission fails closed so a timeout cannot trigger a duplicate paid request.
