# Window State Adapter module

## Interface

`status_window_state.gd` is the pure semantic interface for the Status Window. `initialize(adapter_spec)` returns the complete source state. `step(adapter_spec, state, control_id, direction, expected_version)` returns either one complete replacement state or one typed rejection and never mutates its input.

`party_window_state.gd` is the pure semantic interface for the Party Window. `initialize(adapter_spec)`, `select_mode(adapter_spec, state, mode, expected_version)`, `select_member(adapter_spec, state, member_id, expected_version)`, and `activate_action(adapter_spec, state, action_id, expected_version)` return one complete versioned state or one typed rejection without mutating their input. Party/Friends mode, membership, member selection, and action availability belong here; shared Controls remain domain-neutral.

`system_menu_window_state.gd` is the pure destination-policy interface for the System Menu. `initialize(adapter_spec)` publishes immutable destination availability; `activate(adapter_spec, state, control_id, expected_version)` emits a normalized `OpenWindow` request, increments state only for a declared available destination, and leaves rejected destination state byte-for-byte unchanged for the Desktop Action Router to name and expose.

`chat_room_window_state.gd` is the pure conversation-log interface for the Chat
Room. `initialize(adapter_spec)`, `edit_draft(adapter_spec, state, text,
expected_version)`, `submit(adapter_spec, state, scope, expected_version)`,
`advance_frame(adapter_spec, state)`, and `change_rows(adapter_spec, state,
expected_version)` return a complete versioned replacement or a typed rejection
without mutating their input. Accepted submit clears the draft immediately and
appends its exact text on the third advance. Screen, party, guild, and allied
guild scopes are one-message facts; row count follows the declared reversible
cycle.

`window_state_spec.gd`, `window_state_runtime.gd`, and `window_state_overlay.gd` form the domain-neutral host seam consumed by the Control Library. The spec host validates adapter-owned mappings before construction; the runtime host owns dispatch and returns complete Control patches; the overlay host returns optional rendered facts. Shared Control files never import or branch on a specific Window policy.

The replacement state publishes `version`, `points`, `attributes`, `derived`, and `availability` together. Cost and derived rules come only from the manifest adapter spec. The shared `Stepper` remains generic and does not calculate points or derived values.

## Errors

Malformed adapter input returns `InvalidControlSpec`; unknown controls or directions return `ActionRoutingError`; stale versions return `GestureConflictError`; unaffordable and below-source steps return `TransactionRejectedError`.

## Acceptance tests

`res://tests/run_status_window_state_contracts.gd` freezes exact initialization, single-frame derived updates, rapid-click exhaustion, reversal/refund, source-floor rejection, stale-version rejection, and byte-for-byte preservation on every failure.

`res://tests/run_party_window_state_contracts.gd` freezes the five-member source state, atomic mode and selection updates, honest unavailable icons, complete leave behavior, repeat/stale rejection, inconsistent-state rejection, and byte-for-byte preservation on failure. `run_control_spec_contracts.gd` freezes unique adapter mappings and exact action identity.

`res://tests/run_chat_room_state_contracts.gd` freezes the five source rows,
atomic editing/submission, three-frame delivery, scope identity, row cycling,
stale rejection, and immutable failure behavior.

## Implementation freedom

Internal cost, copy, and recomputation helpers may change. The interface, named errors, cost bands, immutable failure behavior, and one-version-step accepted transaction are frozen by Issue #131.
