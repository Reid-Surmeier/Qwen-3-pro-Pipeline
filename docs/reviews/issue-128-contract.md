# Issue 128 blind artifact contract

Review the exact packet candidate without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- The Storage Window occupies `(492, 609, 539, 393)` on the 1536x1024 canvas.
- Source-owned pixels define the expanded idle Window, its 35 visible item cells, six category surfaces, item art and counts, scrollbar, search/list/sort/close chrome, and title strip. Hover, pressed, selected, transfer, filtered, list, and scrolling states are deterministic extensions in the same visual language.
- The prototype is disposable. Its retained authority is only `artifacts/references/ro-desktop-b/storage/prototype-learning-manifest.json`: Behaviour Cards, State Set decisions, gesture decisions, and manifest decisions.

## Required observations

1. The 539x393 idle Storage Window remains source-coherent at 4x: category labels, 35 cells, item art and counts, scrollbar, footer count, search/list/sort/close controls, and title chrome are legible and aligned.
2. Storage selection, category choice, sort, list mode, search, scrolling, transfer, close, and title Drag are manifest-driven and report factual QA state through stable Control IDs.
3. Each normalized wheel notch moves exactly three rows; each arrow activation moves one row; both clamp at exact endpoints. Thumb Drag reports continuous motion samples, maps track travel to row offset, and clamps at both ends.
4. Real keyboard input is rendered by the TextField, immediately drives the declared Storage filter, and resets the linked scroll position to the first result row.
5. Control-modified double activation is the only cross-Window transfer gesture. Alt, Shift, Meta, mixed modifiers, and a mixed unmodified/modified click pair cannot impersonate it.
6. Inventory to Storage and Storage to Inventory transfers commit both collections and both versions together. A full target, missing item, duplicate item, invalid modifier, or version drift returns the declared typed error and preserves both prior collections and versions.
7. Every category and item State Set includes all declared semantic and interaction combinations. Malformed ScrollView, TextField, SelectionView, transaction, gesture, and action specifications fail closed with typed errors.
8. The Storage Play Log uses real Chromium pointer, wheel, and keyboard input, covers all required actions, binds to the exact candidate SHA, and reports zero actionable console or page errors.
9. The native 156-contract Image 79 gate and repository baseline pass on the exact candidate. Options, Skill Tree, and Inventory are rerun against the same SHA after the shared SelectionView, ControlRuntime, and ControlWindow changes.
10. The assembled native frame contains Options, Skill Tree, Inventory, and Storage together. Earlier Windows remain visible and coherent; Storage neither crops nor partially replaces them.

Every finding must name the candidate SHA, expected behavior, actual behavior, evidence path, and violated clause. This review is advisory evidence only and does not approve the final eleven-Window assembled desktop.
