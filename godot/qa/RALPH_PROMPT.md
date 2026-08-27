# Ralph iteration — RO-HUD replica convergence (#86)

You are one iteration of a continuous convergence loop on the Godot replica
in this worktree (`godot/`). Reference authority: `artifacts/references/
ro-hud-fullscreen/reference-native.png`. Contract: figma-ui-ux-qwen-pipeline
`1d52b78` (layered contracts ADR 0009 + autonomous convergence loop).

## Non-negotiable rules
- **Vision first.** Mechanical metrics NEVER constitute a pass. Every claim
  of "fixed" requires you to Read the actual rendered frame and judge it
  against the reference visually, magnifying crops 3-4x for detail work.
- The reference screenshot is the immutable visual authority. The untouched
  frame must stay pixel-exact to it; changed regions must change; declared
  invariant regions must stay stable.
- Every control must be exercised through a real gesture and produce its
  intended visible state change. Pointer-down shows feedback; action fires
  on release. All interactions must be reversible.
- Deterministic assembly owns geometry, restoration, interaction, state.
  Derived assets are built by `godot/tools/build_derived_plates.py`.
- No paid Qwen generation unless strictly required by an isolated failure;
  if required, follow the #86 ledger procedure (cap 200, record exact cost
  in the generation ledger, smallest source-locked batch, fail closed on
  provider ambiguity).

## One iteration
1. Read `godot/qa/BACKLOG.md`. Pick the single highest-impact open item
   (or a defect you find in step 2 that outranks it).
2. Build + playtest: export the Web build, run
   `node godot/qa/web/playtest.mjs`, then **Read the key frames** in
   `godot/qa/web/out/play/` and vision-review each against the reference.
   Record any NEW defect you see in BACKLOG.md.
3. Fix the chosen item. Re-render, re-playtest, and **visually verify the
   fix in the frames** (crop + magnify the changed region).
4. Backstops (only after visual verification): `bash godot/qa/qa.sh` must
   end green; playtest must report 0 console errors.
5. Update BACKLOG.md (mark done, add found), commit everything with a
   descriptive message ending in the standard co-author trailer, and push
   `release/v0.2.0`.
6. If and only if BACKLOG.md has no open items, every gate is green, and a
   final full-frame vision review finds nothing off: write the file
   `godot/qa/RALPH_DONE` containing a one-paragraph completion summary,
   then post a final evidence comment on issue #86 (embed round images via
   raw.githubusercontent URLs at the pushed commit SHA).

Work on exactly ONE backlog item per iteration. Keep every fix small and
verified. Never delete evidence. Never force-push.
