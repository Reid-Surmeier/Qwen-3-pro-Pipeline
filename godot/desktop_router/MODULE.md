# Desktop Action Router module

## Interface

`desktop_action_router.gd` owns cross-Window transactions and source-attested
detail routing. `transfer()` accepts
immutable source and target collection snapshots, the selected logical item,
both expected versions, and normalized modifiers. It returns either two new
collection snapshots or one typed rejection; it never mutates either input.
`open_detail()` refuses unattested pixels and `close_detail()` returns a factual
visibility route without reaching into a Window adapter.

## Errors

The router returns `InvalidModifierError`, `GestureConflictError`,
`TransactionRejectedError`, `ActionRoutingError`, or `VisualAuthorityError`
from `control_errors.gd`. Every rejection preserves supplied data byte-for-byte.

## Acceptance tests

`res://tests/run_desktop_router_contracts.gd` proves two-sided commit and
rejection atomicity at the public `transfer()` seam. The Equipment Card contract
proves attested open, factual close, and unattested-detail refusal.

## Implementation freedom

Validation and copying may change behind the seam. Snapshot shape, typed error
codes, exact modifier rule, version rule, and all-or-neither result are frozen.
