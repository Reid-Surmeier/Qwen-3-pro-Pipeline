# Interaction contracts

## Why generic evidence is not a verdict

The earlier suite clicked control centres successfully and then accepted any
observable change as proof the control worked. A decorative hover filter, a
hidden status string, or a preselected radio all satisfied that bar. Swapping
the browser driver would not have helped, because the driver was never the
problem: the oracle was.

An interaction contract replaces "something changed" with four facts that must
all hold.

## The four facts

An interaction passes only when its contract proves:

1. **The real gesture path ran.** The recorded pointer or key sequence reached
   the element that owns the pixels, confirmed by hit ownership
   (`elementFromPoint` at the gesture coordinates resolves to the control, not
   to an overlay or an ancestor). A synthetic state mutation is not a gesture.
2. **The intended region changed.** The rectangle the contract names for this
   interaction differs from its pre-gesture capture.
3. **Declared invariant regions stayed stable.** Every pixel outside the named
   rectangles is byte identical, judged by
   [`qwen_ui_pipeline.fidelity.verify_against_baseline`](../../qwen_ui_pipeline/fidelity.py).
4. **The behaviour is source-approved and reversible.** The resulting state is
   one the reference authorises, and the documented reverse gesture returns the
   surface to its prior state.

Any interaction that produces an observable effect without satisfying all four
is recorded as `uncontracted-evidence` and **fails closed**. It is never
promoted to a pass.

## Required checkpoints

Where a control supports them, a contract captures: `idle`, `pointer-down`,
`pointer-up`, `settled`, `reversal`, `cancel`, and for window chrome
`minimize`, `restore`, and `extreme-drag`. A missing applicable checkpoint is a
gap, not a pass.

## Layer authority

| Layer | Answers | Cannot answer |
| --- | --- | --- |
| Fidelity contract (deterministic) | Did unlicensed pixels change? How much changed inside each licensed region? | Whether the licensed change is *correct* |
| Interaction contract (deterministic) | Did the real gesture produce the authorised, reversible result? | Whether the result reads as the same UI |
| Correction replay (exploratory) | Does this reconstruction repeat a defect the owner has corrected before? | Nothing on its own — it may find, never waive |

Deterministic layers hold authority. The exploratory layer can open a finding
but can never overturn a deterministic verdict, and can never mark a run
verified by itself.

## Promotion rule

A correction-replay finding is not a loop result. Before any fix is applied the
finding must be minimised and promoted to a reproducible test in the owning
layer. Only then is the correction implemented and the same gesture and visual
checkpoint replayed.

This is what stops the same class of defect being reported in prose run after
run: once promoted, the pipeline catches it without a human present.
