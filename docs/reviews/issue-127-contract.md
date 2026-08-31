# Issue 127 blind artifact contract

Review the exact packet candidate without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- The Inventory Window occupies `(0, 701, 484, 303)` on the 1536x1024 canvas.
- Source-owned pixels define the expanded idle Window, all 28 visible item cells, five tab labels, scrollbar/search chrome, and resize grip. Selected, modifier-selected, dragging, drop-target, detail, resized, and purpose-built minimized states are deterministic extensions in the same visual language.

## Required observations

1. The 484x303 idle Window is source-coherent at 4x; all 28 source item cells, quantities, tabs, chrome, and resize grip remain legible and aligned.
2. Each of the five source-owned tab surfaces routes `Activate` to `SelectInventoryTab`, changes only the selected tab and declared tab content state, and reverses when Item is reselected.
3. One primary activation selects exactly one declared slot. One shared `DoubleActivate` opens the same item detail without emitting duplicate `Activate` actions.
4. Control-modified activation toggles independent item membership and reverses. Alt, Shift, Meta, or mixed modifiers return `InvalidModifierError` and change no semantic state.
5. Dragging crosses the four-pixel threshold before recognition, exposes factual source/target/motion state, and swaps the two declared item values once. The trailing pointer release emits no extra `Activate`.
6. A drop outside a declared slot returns `InvalidDropTargetError`; version drift returns `GestureConflictError`. Both preserve item values, selection, detail, and transaction version.
7. Resize follows real pointer motion, clamps exactly at 332x220 and 734x512, keeps the grip under the pointer until clamped, and preserves every grid cell's Window-local visual/hit alignment.
8. Minimize uses a purpose-built 484x28 strip and restores the prior size and position. Title Drag remains continuous; title Close and focused Escape Close route through manifest Window actions.
9. Tabs, SelectionView item states, resize geometry, modifier policy, drop targets, and action bindings fail closed with their declared typed errors when malformed.
10. All stable Inventory Control IDs and every Control- and Window-level manifest action are covered. Inventory, Skill Tree, and Options Play Logs contain no console errors and have separate candidate-bound evidence manifests.

Every finding must name the candidate SHA, expected behavior, actual behavior, evidence path, and violated clause. This review is advisory evidence only and does not approve the final eleven-Window assembled desktop.
