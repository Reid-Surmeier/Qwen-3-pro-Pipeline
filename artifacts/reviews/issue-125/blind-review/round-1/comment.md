## Blind artifact review — Issue #125 Options Window

Candidate: `e395a3413a4d6bfc05582eaf17340662cc6420c2`
Evidence bundle: `9d6978ac0ddbfe2934b0e532b39bfdc0d9cb6274`
Contract: `docs/reviews/issue-125-contract.md`
Primary verdict: **PASS** — fresh-context Codex `gpt-5.6-sol`, `xhigh`
Secondary fallback: **BLOCKED** — OpenCode `qwen/qwen3.8-max`, `xhigh`, via OpenRouter

The primary packet-only review reproduced packet validation, matched the source and all 54 frame hashes, and found no contract violation. The earlier overlapping Skin label was corrected; `tanublue` remains the only selected label through Escape, minimize/restore, and drag. Range endpoints, reversible toggles, custom Skin list, distinct minimized Window, title drag, Close, stable invariants, and public QA facts all match the submitted evidence.

The OpenCode fallback reached OpenRouter and inspected the packet, but its local tool runner aborted before returning a verdict. The final request may have been billed and was not retried. Three attempts across invalidated and final candidates cost `$0.331876` total; full provenance is in `qwen-fallback.json`.

Specification review: **PASS**. Engineering review: **PASS**. This is advisory evidence for the Options tracer only; final owner review remains the assembled desktop.
