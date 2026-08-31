# Issue 130 blind artifact contract

Review the exact packet candidate without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- Equipment Items occupies `(0, 423, 484, 271)` on the 1536x1024 canvas; Inventory occupies `(0, 701, 484, 303)`.
- Source-owned pixels define the expanded idle Equipment Items window, its nine occupied slots, character art, chrome, minimize control, and close control. Hover, selected, pressed, dragging, drop-target, and available states are deterministic source-derived extensions.
- The prototype is disposable. Its retained authority is only `artifacts/references/ro-desktop-b/equipment-items/prototype-learning-manifest.json`: Behaviour Cards, State Sets, gestures, and manifest decisions.
- No provider generation was used. Cross-window displacement reuses source-owned item imagery and may not retain a visually false pre-transaction item.

## Required observations

1. The 484x271 idle Equipment Items window remains source-coherent at 4x: Japanese title and tabs, nine equipment rows, character art, item label, title controls, spacing, and crop are aligned and legible.
2. Activate and DoubleActivate are real pointer paths. Activate selects one declared slot; DoubleActivate atomically unequips into the selected Inventory slot and advances both public versions once.
3. Inventory to Equipment and Equipment to Inventory DragDrop use at least 30 two-dimensional pointer samples. Source and destination show continuous drag/drop feedback before release.
4. Equip, unequip, and displacement commit both slot maps or neither. Invalid slots and stale versions return named errors and preserve both supplied maps byte-for-byte.
5. A committed displacement visibly updates both windows with source-owned imagery; factual QA state names the logical identity and exact rendered foreign-identity asset.
6. Minimize uses the purpose-built 484x28 plate and restores the exact expanded state. Title Drag, title close, and Escape close are real and reversible.
7. Every Equipment Items control exposes stable IDs, complete declared State Sets, source-owned geometry, and manifest-bound actions. Empty slots remain visible and hit-testable without inventing an item.
8. The Equipment Items Play Log binds to candidate `abed920984ac913c0927d923292aabbf163a333e`, exercises every required action, verifies all frames by hash, and reports zero actionable console or page errors.
9. The native 190-contract Image 79 registry and repository baseline pass on the exact candidate. Options, Skill Tree, Inventory, Storage, and Equipment Card browser Play Logs are rerun against the same SHA after shared SelectionView, ControlRuntime, ControlWindow, and Desktop Action Router changes.
10. The assembled browser frame contains Equipment Items with the five earlier windows. Earlier windows remain coherent; the new window does not crop, partially replace, or permanently stack screenshots over them.

Every finding must name the candidate SHA, expected behavior, actual behavior, evidence path, and violated clause. This review is advisory evidence only and does not approve the final eleven-window assembled desktop.
