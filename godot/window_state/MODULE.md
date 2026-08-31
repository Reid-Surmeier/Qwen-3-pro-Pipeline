# Window State Adapter module

## Interface

`status_window_state.gd` is the pure semantic interface for the Status Window. `initialize(adapter_spec)` returns the complete source state. `step(adapter_spec, state, control_id, direction, expected_version)` returns either one complete replacement state or one typed rejection and never mutates its input.

The replacement state publishes `version`, `points`, `attributes`, `derived`, and `availability` together. Cost and derived rules come only from the manifest adapter spec. The shared `Stepper` remains generic and does not calculate points or derived values.

## Errors

Malformed adapter input returns `InvalidControlSpec`; unknown controls or directions return `ActionRoutingError`; stale versions return `GestureConflictError`; unaffordable and below-source steps return `TransactionRejectedError`.

## Acceptance tests

`res://tests/run_status_window_state_contracts.gd` freezes exact initialization, single-frame derived updates, rapid-click exhaustion, reversal/refund, source-floor rejection, stale-version rejection, and byte-for-byte preservation on every failure.

## Implementation freedom

Internal cost, copy, and recomputation helpers may change. The interface, named errors, cost bands, immutable failure behavior, and one-version-step accepted transaction are frozen by Issue #131.
