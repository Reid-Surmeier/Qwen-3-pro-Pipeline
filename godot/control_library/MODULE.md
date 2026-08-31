# Control Library module

## Interface

`control_spec.gd` is the construction seam. It loads and validates schema-version 3 ControlSpec manifests and returns either the complete manifest or factual typed errors. No runtime Window is constructed from an invalid manifest. Window-level Gesture-to-Action bindings are part of the same seam as Control bindings; `ControlWindow` routes them and reports the last routed Gesture, Action, and error through `qa_state()`. A `SelectionView` may read displayed values only through its manifest-owned `value_control_ids` mapping. `ControlWindow.qa_state()` is the observation seam; adapters may add rendered facts through `rendered_facts()`, which the Window merges into the corresponding public Control state.

`ScrollView.interact()` accepts normalized Wheel, Activate, and Drag payloads and owns row offsets and exact clamps; a manifest may instead declare a zero-range unavailable visual authority, which rejects every gesture without mutation. `TextField.edit()` accepts or rejects complete candidate text atomically. `ControlWindow.action_emitted` publishes accepted Window Actions to the Desktop Action Router without granting it access to private adapter nodes.

A manifest-owned chat TextField may additionally submit its complete draft with
one declared modifier scope. `ControlWindow` anchors delayed delivery to engine
frame numbers, so coroutine or browser scheduling cannot accelerate the exact
three-frame state transition. Web QA publication preserves the complete public
state while sending only the changed Window after the initial snapshot; the
browser exposes payload counters in `window.godotQaMetrics` for regression
evidence.

`Meter.project()` is the read-only Meter interface. A Meter declares ordered bounds, a current value, fill axis, and source-owned fill extent; it exposes no Gesture Capability and `MeterControl` renders its State Set without making the source plate interactive.

`SelectionViewControl` owns real press/move/release recognition. It publishes
cross-Window drag phases through `ControlWindow.action_emitted`, while the
Desktop Action Router remains the only owner of the two-Window transaction.
`ControlRuntime.selection_slots()` and `apply_selection_slots()` are the public
snapshot/apply seam. Empty equipment slots may remain visible and hit-testable
through `show_empty_slots`; foreign logical identities use manifest-owned
source assets so a committed displacement visibly changes both Windows. The
construction seam validates `show_empty_slots`, `identity_surfaces`, and every
`foreign_identity_assets` resource before construction. The observation seam
reports the visibility and `resource_path` of the actual TextureRect nodes,
not a predicted manifest path. Conditional `context_actions` are explicit
manifest bindings resolved from same-Window choice state before local action
handling; the Inventory Equip tab uses this to own `EquipInventoryItem`
without opening stale item detail.

## Errors

`control_errors.gd` owns the stable error codes named by spec #124. Callers branch on `code`; `path` and `detail` are evidence, not alternate error types.

## Acceptance tests

`res://tests/run_control_spec_contracts.gd` tests this seam from issue literals. Runtime controls and Windows are tested through their manifest actions and QA-state results, never through private node structure.
The Equipment Items contracts additionally drive real 31-sample pointer paths
across Inventory and Equipment Items and inspect only public QA state.
They include invalid-destination rejection frames, explicit Equip-tab
DoubleActivate ownership, and adversarial foreign-asset validation.
`res://tests/run_chat_room_window_contracts.gd` drives actual text and modifier
input, exact accepted/third-frame observations, F10, Alt+F10, and clamped Wheel
input through the same public seam.

## Implementation freedom

The validator, constructors, render nodes, Gesture Capabilities, and adapters may change behind the seam. Schema version, named errors, stable manifest IDs, two-axis State Sets, and acceptance behavior require a new Issue to change.
