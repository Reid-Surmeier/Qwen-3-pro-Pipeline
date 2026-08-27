# Add Partner-compatible controls beside Edit Brief JSON

Status: accepted on 2026-08-26.

## Context

The original `QwenImage3Render` node makes an Edit Brief auditable and
reproducible, but its single JSON widget hides image roles and provider
controls from a person reading the ComfyUI graph. Replacing that node's schema
would break saved workflows. OpenRouter and Alibaba also expose different
Qwen Image 3 capabilities, so a common widget cannot imply that every selected
value is portable.

## Decision

Keep `QwenImage3Render` unchanged and add local `QwenImage3TextToImage` and
`QwenImage3Edit` nodes with Partner-compatible visible controls. The edit node
has three ordered named sockets, resolves `@Image1` through `@Image3` before
provider request construction, and rejects a batch on any named socket so the
visible role remains exact.

Translate the visible controls into an Edit Brief, then use the existing
explicit-provider router and clients. Validate the complete provider/control
combination before client creation. Provider capabilities are not silently
emulated: OpenRouter rejects unsupported negative prompt, prompt expansion,
watermark, and size combinations; Alibaba receives its supported parameters
natively. Both new nodes return the Edit Brief and run metadata beside the
IMAGE batch.

Use a session-bound SSH loopback forward over the authenticated tailnet for
Mac review. Do not expose ComfyUI publicly, add a Funnel, or forward worker
ports 8191 through 8195. A persistent Tailscale Serve route requires a separate
production-network approval.

## Consequences

- Existing JSON workflows keep their class ID and behavior.
- A reviewer can read reference roles and controls directly from the graph.
- A three-reference graph can switch providers when its chosen controls are
  in both capability sets; unsupported combinations fail before billing.
- OpenRouter's live capability record and Alibaba's direct API limits remain
  explicit, including their different size behavior.
- Remote review is authenticated and reversible, but the maintainer must run
  the final Mac-side connection check.
