# Issue 126 blind artifact contract

Review candidate `9d63fc8cc10e2b0a3de442be379a8d5f435a7eae` without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- The Skill Tree Window occupies `(492, 0, 611, 595)` on the 1536x1024 canvas.
- Source-owned pixels define the expanded tree view. The list view, detail panel, selected/hover/pressed treatments, and purpose-built minimized strip are deterministic extensions in the same visual language.

## Required observations

1. The expanded idle Window is source-coherent at 4x inspection; live Stepper text is legible and does not overlap source-baked digits or arrows.
2. Left activation changes the selected skill; distinct right-button `ContextActivate` opens the selected skill's detail without changing gesture meaning.
3. Every one of the 26 Steppers is exercised. One accepted step updates `current / target`, marks one Window transaction pending, and hides every Stepper arrow in the same frame.
4. Use commits pending targets; Cancel discards pending targets. Both clear the transaction and restore every arrow.
5. View reverses between tree and list presentation, and the description Toggle reverses on a second activation.
6. Minimize swaps to a purpose-built 611x28 title strip and restores in place. Title Drag follows the pointer continuously; Close hides the Window.
7. All stable Control IDs and manifest actions are covered, the Play Log has no console error, and the previously accepted Options Window regression remains PASS.

Every finding must name the candidate SHA, expected behavior, actual behavior, evidence path, and violated clause. This review is advisory evidence only and does not approve the final eleven-Window assembled desktop.
