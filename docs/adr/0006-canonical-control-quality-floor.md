# Use the Options window's slider as the canonical control quality floor

Status: accepted on 2026-08-29. Ports ADR 0010 of `figma-ui-ux-qwen-pipeline@1d52b78`
and extends it with twelve gates. Supersedes nothing; ADR 0003's paid rules stand.

Numbered 0006 deliberately: the integration line carries three different files
all numbered 0004 (Issue #94), so 0004 and 0005 are unsafe on main.

## Context

Two consecutive attempts at a living replica of a screenshot reported green and
were wrong.

In the predecessor repo, fifteen windows were marked `verified` by weak proxies —
average screenshot scores, centre clicks, declared semantic contracts, and runtime
manifests that could approve their own incomplete mappings. A hands-on review
reproduced visible failures the suite called passes
(`docs/runs/japanese-rpg-false-verification-diagnosis-v001.md`, root cause 1:
*"the pass predicate accepts any change"*).

In this repo, the blind review of the `ro-hud-fullscreen` candidate returned
`verdict: pass` with nine confident positives while its own evidence manifest
recorded the B5 button's before and after frames as the **same file**
(`631de7a5…`) and three "animation" frames as that same file again. The control
it filed as a non-blocking enhancement — the scrollbar thumb — cannot be dragged
at all: `plate_window.gd` sets `_dragging` only for `role == "drag"`.

Both failures share one cause, and it is not the driver. It is the **oracle**: a
verdict that accepts any observable change, and — worse in the second case — no
observable change at all.

The predecessor's cure was a named quality floor: its Options window's BGM and
Effect rows, the one surface built from independent source-derived assets with
continuous values, exact endpoints, reversible state and local pixel invariants.
Naming it as the floor flipped fifteen falsely-green windows red and drove roughly
forty real fixes.

## Decision

**The Options window's slider row is the canonical control quality floor.** A
control of a different type may implement different behaviour, but it must satisfy
the same applicable quality dimensions.

### The seven dimensions (ported)

1. Source-relative visual error no worse than the accepted benchmark.
2. No local connected defect larger than the benchmark's worst defect.
3. Every visible control resolves to an **independent visual authority** — its own
   node with its own artwork, never a region of a flat picture.
4. The visible interaction surface maps to the **correct control**, not merely its
   centre point.
5. Every interaction exposes **idle, pointer-down, pointer-up, settled and
   reversible** evidence.
6. Continuous controls expose at least **five distinct samples and exact
   endpoints**.
7. Window movement, clipping, stacking, minimize, close, reopen, scrolling, tabs,
   menus and selection use **source-specific assertions** when applicable.

### The twelve gates (added)

Each is a line in the Play Log that can only pass with a named frame:

1. Every drag is captured as **≥30 frames**, and the dragged thing's position is
   monotonic with the pointer.
2. Response latency is **≤2 frames** after pointer-down.
3. Endpoints **clamp exactly** — slider at 0 and 100, scrollbar at top and bottom,
   a dragged window at the screen edge — with no overshoot and no bounce.
4. Scrollbars answer **thumb drag, arrow step and wheel**.
5. Reversal restores **byte-identical pixels**.
6. Dragging a window over a neighbour **preserves source z-order**.
7. Rapid or repeated clicks **never wedge** a control.
8. **Zero engine or console errors** across the whole play session.
9. Hover and cursor states appear **where the Source Game shows them**.
10. Text fields accept typing and **render the submission**.
11. Every control shows its **hover, pressed and settled** states on the matching
    gesture.
12. Every generated state passes a **magnified vision fidelity review** against a
    Source Game frame of that state.

### Rules that bind the gates

- **Mechanical metrics never constitute a pass.** Every rendered output is judged
  visually, at ≥4× magnification, against its Behaviour Card and reference, before
  any metric is consulted. Metrics are regression backstops.
- **A pair of frames with no visible change is evidence of failure, not of a pass.**
  The verdict script rejects a log whose frames are byte-identical where the gate
  demands motion.
- **Coverage is part of the verdict.** A catalogued control that was never
  exercised makes the run INCOMPLETE. It never makes it a pass.
- **The builder never produces the evidence that is judged.** Evidence comes from a
  Playtester that drove the artifact itself.
- **A gesture with no Source Game reference is specified from intent, in the open.**
  Issue #115 established that the window drag and the scrollbar's thumb-drag and
  arrow-step gestures are absent from play footage — players never move windows
  (the client restores positions) and use the wheel rather than the bar. Those
  three are specified deliberately and marked as intent-specified on their
  Behaviour Cards, never presented as observed.

## Consequences

- A window is `revision-required` until it passes this floor. Historical green
  never waives a newly learned failure class; adding a correction demotes every
  window it applies to.
- Controls are built from the Control Library, whose entries carry their own
  contract tests. A control that cannot satisfy dimension 3 — an independent
  visual authority — is not a control, it is a picture, and it fails.
- The floor is measured against a Source Game frame, not against taste. Where the
  source is silent, the Behaviour Card says so.

## Alternatives considered

**Keep the deterministic gates and add a stronger reviewer model.** Rejected: the
predecessor's diagnosis is explicit that a different driver would pass the same
broken assertions — *"the driver was never the problem: the oracle was."* The
2026-08-27 round then demonstrated the same with a stronger model.

**Trust the fidelity contract alone.** Rejected: `godot/qa/qa.sh` excludes the
fidelity result from its `hard_fail` expression, so the pixel gate could not fail
the run even when it fired.
