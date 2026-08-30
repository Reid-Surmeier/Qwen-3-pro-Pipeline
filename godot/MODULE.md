# Existing Godot replica module

## Interface

`data/runtime-manifest.json` is the retained replica interface while image-79 Windows migrate to schema-version 3 ControlSpecs.

## Errors

Import and runtime failures are published by `qa/qa.sh`; callers never infer health from a screenshot alone.

## Acceptance tests

`tests/run_contracts.gd` and the capture, fidelity, and real-input stages registered by `qa/qa.sh` define acceptance.
