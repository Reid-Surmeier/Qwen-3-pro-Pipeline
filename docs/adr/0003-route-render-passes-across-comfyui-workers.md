# Route Render Passes across independent ComfyUI workers

Status: accepted on 2026-08-24.

## Context

ComfyUI executes one queue with one `PromptExecutor`. A synchronous Qwen Image
3 provider call therefore holds that executor for the full Render Pass. Calls
from separate Codex sessions enter the same local FIFO even when the provider
account can accept concurrent requests. Raising an HTTP timeout or adding an
API key does not remove that local serialization.

## Decision

Keep workflow construction, custom nodes, provider clients, fallback rules,
fixed seeds, image files, Assembly, and provenance unchanged. Run independent
ComfyUI worker processes against the same installation and shared input/output
directories, with a small router at the existing API address. Give each worker
its own SQLite metadata database because ComfyUI holds an exclusive database
lock while running.

The router:

- sends each opaque `POST /prompt` body exactly once to the least-loaded worker;
- remembers which worker owns each prompt for `GET /history/<prompt_id>`;
- aggregates the global `/queue` and `/history` views;
- broadcasts queue-management commands to all workers; and
- forwards upload, view, and other filesystem-backed routes to the primary
  worker, which sees the same shared directories.

An ambiguous prompt-enqueue failure is not retried on another worker because
the first worker may already have started a paid Render Pass. WebSocket progress
is not multiplexed; clients use ComfyUI's HTTP history API instead.

## Consequences

- Five configured workers can execute up to five local Render Passes at once.
- Provider account limits remain authoritative and can still throttle the
  concurrent calls.
- Each worker is a full ComfyUI process, so increasing the worker count also
  increases host memory use.
- Concurrent workflows must retain the existing versioned, unique filename
  prefixes so independent Save Image nodes do not target the same output name.
