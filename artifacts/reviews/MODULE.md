# Review module

## Interface

`issue-<n>/packet.json` is the exact-candidate blind artifact-review packet.

## Errors

Missing references, mismatched hashes, missing evidence, or a verdict for another commit invalidate the packet.

## Acceptance tests

The packet validator and an independent reviewer must name the exact candidate SHA before visual approval.
