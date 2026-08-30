# Testing module

## Interface

`../qa/qa.sh` is the frozen test-runner interface and consumes the image-79 suite registry in `../qa/image79.sh`.

## Errors

Every suite writes a machine-readable report with a nonzero `failed` count and exits nonzero when its contract fails.

## Acceptance tests

`qa/qa.sh` must fail closed across import, contracts, rendered capture, fidelity, and real-input interaction.
