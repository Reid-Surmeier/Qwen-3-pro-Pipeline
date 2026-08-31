# Image 79 Window convergence workflow

## Trigger

Start when the first unblocked, unassigned child of spec #124 carries `ready-for-agent`. Continue automatically when its blocker closes. Ticket order is #125 through #136.

## Per-Window loop

1. Freeze the Window inventory, Behaviour Card, required two-axis State Sets, Gesture Capabilities, and ControlSpec entries against image 79.
2. Build and drive a throwaway prototype only to expose unknown interaction or state behavior.
3. Preserve the learned Behaviour Card, approved/derived State Set assets, Gesture Capability decisions, and manifest. Discard prototype implementation.
4. Write one failing production seam test, implement only enough shared-library and Window behavior to pass, then repeat vertically.
5. Drive the production browser export with real pointer and keyboard input. When a shared Control or Gesture Capability changed, rerun every earlier Window before advancing.

## Evidence per loop

- Exact reference and candidate SHA.
- Manifest/control/action coverage report.
- Before, during, after, reversal, endpoint, and applicable disabled frames.
- Engine import/contracts, browser console, Play Log, and deterministic verdict outputs.
- State asset derivation and generation-ledger provenance.

## Automatic corrections

- Promote a reproducible finding into a failing seam test before fixing it.
- Promote a newly required input grammar into a shared Gesture Capability; keep its Window Action and State Adapter separate.
- Use deterministic Assembly for pixels or exact transforms already evidenced by image 79. Use an OpenRouter Qwen Asset Pass only for genuinely absent pixels.
- If a shared module changes, regression failure returns to the same loop; it never advances to the next Window.

## Stop conditions

Stop only for a conflict between authoritative visual/behavior sources, a destructive/credential risk, or a paid request that could exceed the 200-output milestone ceiling. An ambiguous possibly billed request is preserved and counted; it is never retried blindly.

## Owner checkpoint

Do not request per-Window approval. The owner-facing checkpoint is issue #136: one complete 1536×1024 eleven-Window Assembly with release PR evidence and one share URL.

## Final verification

The exact candidate SHA must pass deterministic CI/native/browser gates, a valid primary Codex Playtester PASS, no completed secondary FAIL (Claude Fable 5, or OpenCode/OpenRouter `qwen/qwen3.8-max` xhigh when Claude is unavailable), and the independent blind artifact review. The builder never grades its own output.
