# Issue 126 blind artifact contract

Review candidate `13fca40e2e28491aa259d82b00692475760443aa` without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- The Skill Tree Window occupies `(492, 0, 611, 595)` on the 1536x1024 canvas.
- Source-owned pixels define the expanded tree view. The list view, detail panel, selected/hover/pressed treatments, and purpose-built minimized strip are deterministic extensions in the same visual language.

## Required observations

1. The expanded idle Window is source-coherent at 4x inspection; live Stepper text is legible and the complete left and right source arrows render without overlapping the values.
2. Left activation changes the selected skill; distinct right-button `ContextActivate` opens detail text for that item from the manifest, without changing gesture meaning.
3. Every one of the 26 Steppers is exercised. One accepted step updates `current / target`, marks one Window transaction pending, and leaves no rendered Stepper-arrow pixels anywhere in the Window in that same frame.
4. A Stepper click beyond either bound is rejected with `TransactionRejectedError`, does not change the target, and does not start a transaction.
5. Use commits pending targets; Cancel discards pending targets. Both clear the transaction and restore every arrow.
6. View reverses between tree and list presentation; list values reflect committed runtime values rather than their construction-time snapshot. The description Toggle reverses on a second activation.
7. Minimize swaps to a purpose-built 611x28 title strip and restores in place. Title Drag follows the pointer continuously; Close hides the Window.
8. `plates.list`, `drag_geometry`, and `minimized_controls` fail closed when malformed; SelectionView and Stepper semantics route the manifest-declared actions rather than hardcoded action names.
9. All stable Control IDs and manifest actions are covered, the Play Log has no console error, and the previously accepted Options Window regression remains PASS.

Every finding must name the candidate SHA, expected behavior, actual behavior, evidence path, and violated clause. This review is advisory evidence only and does not approve the final eleven-Window assembled desktop.
