# Control Library module

## Interface

`control_spec.gd` is the public seam. It loads and validates schema-version 3 ControlSpec manifests and returns either the complete manifest or factual typed errors. No runtime Window is constructed from an invalid manifest.

## Errors

`control_errors.gd` owns the stable error codes named by spec #124. Callers branch on `code`; `path` and `detail` are evidence, not alternate error types.

## Acceptance tests

`res://tests/run_control_spec_contracts.gd` tests this seam from issue literals. Runtime controls and Windows are tested through their manifest actions and QA-state results, never through private node structure.

## Implementation freedom

The validator, constructors, render nodes, Gesture Capabilities, and adapters may change behind the seam. Schema version, named errors, stable manifest IDs, two-axis State Sets, and acceptance behavior require a new Issue to change.
