# Control Library module

## Interface

`control_spec.gd` is the construction seam. It loads and validates schema-version 3 ControlSpec manifests and returns either the complete manifest or factual typed errors. No runtime Window is constructed from an invalid manifest. Window-level Gesture-to-Action bindings are part of the same seam as Control bindings; `ControlWindow` routes them and reports the last routed Gesture, Action, and error through `qa_state()`. A `SelectionView` may read displayed values only through its manifest-owned `value_control_ids` mapping. `ControlWindow.qa_state()` is the observation seam; adapters may add rendered facts through `rendered_facts()`, which the Window merges into the corresponding public Control state.

`ScrollView.interact()` accepts normalized Wheel, Activate, and Drag payloads and owns row offsets and exact clamps; a manifest may instead declare a zero-range unavailable visual authority, which rejects every gesture without mutation. `TextField.edit()` accepts or rejects complete candidate text atomically. `ControlWindow.action_emitted` publishes accepted Window Actions to the Desktop Action Router without granting it access to private adapter nodes.

## Errors

`control_errors.gd` owns the stable error codes named by spec #124. Callers branch on `code`; `path` and `detail` are evidence, not alternate error types.

## Acceptance tests

`res://tests/run_control_spec_contracts.gd` tests this seam from issue literals. Runtime controls and Windows are tested through their manifest actions and QA-state results, never through private node structure.

## Implementation freedom

The validator, constructors, render nodes, Gesture Capabilities, and adapters may change behind the seam. Schema version, named errors, stable manifest IDs, two-axis State Sets, and acceptance behavior require a new Issue to change.
