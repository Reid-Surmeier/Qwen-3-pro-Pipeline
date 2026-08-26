# ComfyUI worker-capacity investigation

Issue: #24
Decision: **keep-current-workers**

## Recommendation

Keep the current five-worker pool and admit bursts through a bounded queue. Do
not add workers from the present evidence. A request for 12 workers is clamped
to five because the conservative memory budget is already the limiting
constraint, active-job worker peaks have not been measured, and provider
concurrency remains unverified.

This is a planning result, not approval to change the deployed service.

## Evidence and assumptions

The sanitized 2026-08-25 host snapshot records 50,510,004,224 bytes total,
21,926,240,256 bytes available, and 3,546,509,312 bytes used by the five-worker
service and router. The queue was empty. The snapshot is idle evidence rather
than an active-job peak.

The deterministic model uses:

- a 45 GiB memory ceiling;
- an 8 GiB host reserve;
- 2 GiB reserved per worker, multiplied by a 1.25 safety factor;
- a 64-job queue limit;
- no asserted provider-concurrency limit; and
- a fail-closed block on worker increases until active-job peak evidence exists.

With those inputs, the memory-limited worker count is five. Projected total
memory use is 38,459,027,456 bytes, leaving 9,859,354,624 bytes below the
ceiling. That remaining amount includes the required 8 GiB host reserve; it is
not spare capacity that should automatically become another worker.

## Burst behavior

| Submitted jobs | Simultaneous | Queued | Rejected |
| ---: | ---: | ---: | ---: |
| 6 | 5 | 1 | 0 |
| 12 | 5 | 7 | 0 |
| 24 | 5 | 19 | 0 |
| 100 | 5 | 64 | 31 |

The 15-scenario sensitivity matrix covers requested worker counts 5, 6, 8,
10, and 12 crossed with bursts of 6, 12, and 24 jobs. Every scenario remains
at or below five workers under the recorded assumptions.

## Efficiency path

The immediate efficiency gain is admission control, not more resident worker
processes: keep five simultaneous jobs, allow up to 64 waiting jobs, and reject
overflow explicitly. This lets clients submit more than six jobs without
turning submission count into unbounded local concurrency.

A later deployment issue can investigate an increase only after collecting a
representative active-job memory peak without paid-provider ambiguity, checking
provider concurrency independently, and proposing reversible `MemoryHigh` or
`MemoryMax` service controls. Those actions are intentionally outside Issue
#24.

## Limitations

- Idle RSS is not active-job peak memory.
- The 2 GiB worker reserve and 1.25 factor are conservative policy assumptions,
  not measured model-load maxima.
- Host available memory varies with other desktop and WSL workloads.
- No provider job, image generation, service restart, deployment change, or
  paid operation was performed.

Reproduce the machine-readable result with `request.json`; the expected output
is committed as `result.json`.
