# Issue #1: concurrent ComfyUI routing benchmark

**Conclusion:** `promising` for the simulated routing layer.

## Exact comparison

- Baseline: `archive/source-main-2026-08-25` at `e8079a3d311f0402afa179080905b2e431c6c972` (one worker).
- Candidate: `archive/concurrent-image-routing` at `b8e226cb12f7cea8a201da73a852542938fdad9f` (five workers).
- Repetitions: 5 per configuration.
- Workload: six simultaneous opaque synthetic ComfyUI jobs with fixed identities and durations.
- No provider, model, image generation, credential, production endpoint, or paid operation was used.

## Results

| Measure | Baseline mean | Candidate mean | Change |
| --- | ---: | ---: | ---: |
| Six-job makespan | 1.021536s | 0.413506s | 59.52% reduction |
| Per-run mean queue wait | 0.417361s | 0.039245s | 90.60% reduction |
| Mean synthetic execution time | 0.170171s | 0.170135s | n/a |

Run-to-run variation is retained in `results.json`; ranges are:

- Baseline makespan 1.021307s–1.022142s; candidate 0.401447s–0.421563s.
- Baseline mean queue wait 0.417242s–0.417664s; candidate 0.039219s–0.039273s.

## Integrity and routing evidence

- Candidate workers observed: http://worker-1, http://worker-2, http://worker-3, http://worker-4, http://worker-5.
- Routing failures: 0.
- Enqueue retries: 0.
- Dropped jobs: 0.
- Timeouts: 0.
- Missing observations: 0.
- History-affinity failures: 0.
- Opaque payload mismatches: 0.
- Synthetic output digest parity: True.

## Interpretation and limits

The candidate is promising for removing local FIFO wait in the isolated simulation. The result does not establish production throughput, provider concurrency limits, GPU/CPU/memory safety, or image fidelity. The benchmark deliberately used no images, so any possible visual-output difference remains unmeasured and requires human review before a later adoption decision.

The benchmark does not adopt the router, merge either archive branch, or change provider, workflow, prompt, seed, output naming, Assembly, or Fidelity Check behavior.

## Reproduce

```bash
python3.12 scripts/benchmark_comfyui_routing.py \
  --output-dir artifacts/benchmarks/comfyui-routing-issue-1
```
