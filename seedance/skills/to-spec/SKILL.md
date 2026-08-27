---
name: to-spec
description: "Drive an icon, logo, or favicon animation from a written design spec to a spec-compliant, evidence-backed Seedance deliverable. Use when a Figma/brand/motion spec exists and the goal is iterating studies until the output demonstrably meets it. Guide only: it changes how you plan and judge runs, it does not submit anything."
---

# Bring an icon animation to spec

The spec is the acceptance authority. A run is "to spec" only when every spec clause is
either demonstrated by evidence or explicitly waived by the spec owner. Machine-verified
is not accepted; accepted is a human decision recorded against the spec.

This skill is a guide. It does not add commands, does not submit paid requests, and never
overrides the cost gate in `docs/run-contract.md`.

## Procedure

### 1. Lock the spec

1. Read `CONTEXT.md`, `docs/run-contract.md`, `docs/model-routing.md`, and
   `docs/verification.md`.
2. Capture the spec as a file in the repo (or a hash + citation when it cannot be copied):
   source asset, style rules, motion intent, timing, delivery format, and review scale.
3. Hash the source asset and spec revision. Iteration against a moving spec is not
   iteration; renegotiate the spec first, then restart the ladder.

### 2. Translate spec → motion brief

Map every spec clause into a brief field so nothing lives only in prose:

| Spec clause | Brief field |
| --- | --- |
| Identity / do-not-alter rules | `source_authority`, `negative_constraints` |
| Geometry, stroke, palette, type, safe area | `style_lock` |
| The animation idea | `motion` |
| Beats, holds, easing, loop requirement | `timing` |
| Framing and camera rules | `camera` |
| Background / transparency / matte | `background` (ADR 0003: matte, never native alpha) |

A spec clause with no brief field is a gap: extend the brief, do not leave the clause
implicit. Unmapped clauses are the most common reason a "finished" render fails review.

### 3. Choose the control variables

Read `references/control-variables.md` for the full set (request-level, prompt-level,
conditioning, cost, and out-of-request variables). For each spec clause, name the variable
that controls it and the check that will prove it. Refresh the live capability snapshot
first (`seedance-icons capabilities`); never plan from a stale or remembered profile —
run `$research-seedance-capabilities` when facts are missing.

### 4. Iterate studies on Mini

Follow `docs/research/experiment-matrix.md`: one paid run per cell, one material variable
changed per cell, rejected evidence kept. The default ladder for a spec:

1. **Seed pair** — same brief, two seeds, cheapest supported size/duration. Separates
   prompt-driven behavior from seed luck before any prompt surgery.
2. **Motion wording screen** — 2–3 `motion`/`timing` phrasings, everything else fixed.
3. **Conditioning cell** — first-only vs first+last, if the spec requires endpoints or a
   loop.
4. Score every study against the spec clause it targets, not against general appeal.
   Record pass/fail per clause in the run's notes before planning the next cell.

Each cell is `seedance-icons plan …` (free) → show model, canonical slug, request, and
estimate → explicit approval → `submit --acknowledge-cost` with the exact estimate →
`wait` → `verify`. One approval covers one submission.

### 5. Transfer to 2.5 and close

1. Re-run the winning brief on `final` (Seedance 2.5). Seeds and motion behavior do not
   transfer; treat the first 2.5 run as a confirmation cell, not a formality.
2. `seedance-icons verify` with anchors (and `--loop` when the spec demands a loop), then
   `$verify-icon-animation` for independent review.
3. Walk the spec clause by clause against the verification report and playback at delivery
   scale. Produce a spec-compliance table: clause → evidence → pass/fail/waived.
4. Only the spec owner marks the run accepted. Store the compliance table with the run.

### ComfyUI route

For visual, node-based iteration of the same contract, read
`references/comfyui-pipeline.md`. The graph plans and prices; the paid boundary stays at
the CLI gate.

## Guardrails

- Do not start paid iteration before the spec, source hash, and brief mapping are locked.
- Do not change two variables in one paid cell, and do not resubmit on an ambiguous
  timeout — poll the existing job.
- Do not report "meets spec" from memory: every clause needs pointed evidence (frame,
  metric, or reviewed playback).
- Do not blur generated / verified / reviewed / accepted; they are distinct states.
- Do not commit API keys, payload data URLs, private specs, or run contents that the spec
  owner has not cleared for the repository.
