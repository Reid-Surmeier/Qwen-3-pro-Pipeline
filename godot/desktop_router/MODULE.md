# Desktop Action Router module

## Interface

`desktop_action_router.gd` owns cross-Window transactions. `transfer()` accepts
immutable source and target collection snapshots, the selected logical item,
both expected versions, and normalized modifiers. It returns either two new
collection snapshots or one typed rejection; it never mutates either input.

## Errors

The router returns `InvalidModifierError`, `GestureConflictError`, or
`TransactionRejectedError` from `control_errors.gd`. Every rejection preserves
both supplied snapshots byte-for-byte.

## Acceptance tests

`res://tests/run_desktop_router_contracts.gd` proves two-sided commit and
rejection atomicity at the public `transfer()` seam.

## Implementation freedom

Validation and copying may change behind the seam. Snapshot shape, typed error
codes, exact modifier rule, version rule, and all-or-neither result are frozen.
