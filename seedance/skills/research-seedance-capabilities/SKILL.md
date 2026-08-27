---
name: research-seedance-capabilities
description: "Research current OpenRouter and ByteDance Seedance video capabilities, pricing metadata, schemas, and conditioning behavior. Use before model routing, experiment design, or updating provider assumptions in this repository."
---

# Research Seedance capabilities

Use official OpenRouter API documentation, its live `/api/v1/videos/models` response, and official
provider material where available. Treat all model names, versions, durations, sizes, prices,
conditioning modes, and request fields as drift-prone.

## Procedure

1. Read `CONTEXT.md`, `docs/model-routing.md`, and the current research question.
2. Fetch the live model profiles for exactly `bytedance/seedance-2.0-mini` and
   `bytedance/seedance-2.5`. Save a dated snapshot when it will support a run or decision.
3. Verify request shapes against OpenRouter's current OpenAPI schema and video-generation guides.
4. Separate documented facts from inferences and from behavior that requires a paid experiment.
5. Design the smallest experiment matrix that changes one material variable at a time. Prefer Mini
   for screens and 2.5 for final confirmation.
6. Report estimated cost before proposing any paid test. Do not submit a paid request under this
   skill.

## Guardrails

- Never infer support from a model family name.
- Never silently substitute a model or canonical version.
- Frame anchors and general references are not interchangeable. OpenRouter documents precedence;
  flag mixed conditioning as experimental.
- Do not represent estimated video-token cost as a guaranteed invoice.
- Include source links and the observation date in updated research notes.

Read `references/provider-sources.md` for the primary starting points.
