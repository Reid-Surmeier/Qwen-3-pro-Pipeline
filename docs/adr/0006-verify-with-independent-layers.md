# 6. Verify with independent layers, and never let a builder grade itself

Date: 2026-08-26

Status: accepted on 2026-08-26.

## Context

Reconstruction runs repeatedly reached a state where the generating agent
reported success while the output was visibly misaligned with the source. The
project owner then had to act as the verification layer, re-prompting and
pointing out the same classes of defect run after run.

Two distinct causes produced that outcome.

First, the oracle was too weak. Interaction checks accepted any observable
change as proof a control worked, and visual checks scored whole screenshots,
where a large correct area masks a small wrong one.

Second, the builder graded its own work. An agent evaluating its own output
shares every blind spot that produced the output, and a weak vision judgement
is exactly the blind spot that matters here.

The predecessor repository (`figma-ui-ux-qwen-pipeline`) had already worked out
the deterministic half of the answer. That work was not migrated with the
package.

## Decision

Verification is layered, and the layers have different authority.

1. **Deterministic gates hold authority.** A fidelity contract names the
   rectangles a Render Pass may change; every pixel outside them must be byte
   identical to the approved baseline. Interaction contracts require four
   facts — real gesture path, intended region changed, invariants stable,
   source-approved and reversible. Anything else is `uncontracted-evidence` and
   fails closed.

2. **Exploratory review may find, never waive.** Correction replay runs the
   corpus of the owner's recurring corrections against a run. It can open a
   finding; it cannot overturn a gate or mark a run verified.

3. **The verifier is a separate agent on a different model family from the
   builder**, and judges bounded region crop pairs rather than whole
   screenshots. It returns structured findings; a defect it cannot localise is
   a fail.

4. **Every finding is promoted to a reproducible test before it is fixed.**

## Consequences

A run cannot be declared verified by the agent that produced it, and a passing
whole-image impression cannot hide a small unlicensed change.

Contracts must be authored per target, which is real work up front. That cost
is deliberate: it is the same work the owner was previously doing by hand on
every iteration, paid once and then reused.

Verification costs a second model call per reviewed region. Deterministic gates
run first and are free, so the paid layer only ever sees runs that already
passed everything a machine could measure.

The corpus grows. Each new correction the owner makes is added, so the loop
learns defects instead of repeating them.
