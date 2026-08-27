# Run contract

Each paid request gets a fresh `runs/<UTC>-<slug>/` directory:

```text
brief.json                 human-readable source/style/motion contract
request.json               sanitized request and data-URL hashes
request.payload.json       ignored execution payload; may contain embedded assets
capabilities.json          selected live profile and canonical model slug
plan.json                  request hash, estimate, approval/submission flag
job.json                   resumable OpenRouter job identity
completed-job.json         terminal provider response
inputs/                    optional copied source evidence
outputs/output.mp4         downloaded provider result
outputs/sha256.json        immutable output digest
verification/report.json   ffprobe, frame, anchor, and loop checks
```

The request payload is local and ignored because data URLs can be large or private. The sanitized
request remains inspectable. If the payload is lost, recreate it from the brief and locked sources;
do not reconstruct or guess a paid request from the sanitized record.

Before submission, the CLI re-fetches capabilities and refuses a changed canonical model version.
The exact decimal estimate must be provided to `--acknowledge-cost`. This gate documents approval;
it does not promise the provider invoice will equal the estimate.

