# Qwen Image 3 prompt method for reference-preserving UI work

## What the larger instruction budget changes

Qwen's Image 3 announcement says the model accepts instructions up to about 4.5K tokens and demonstrates a 3×3 grid generated from a 3.7K-token prompt. This is the missing architectural advantage: an Edit Brief can describe multiple regions, exact copy, relationships, and invariants in one request instead of compressing the design into a short aesthetic sentence.

The limit is an image-instruction budget, not a general chat-model context window. It permits more explicit control but does not guarantee that every clause will be honored. Contradictory detail, repeated adjectives, and unspecified precedence can still increase drift.

## Canonical prompt order

The compiler emits these blocks in priority order:

1. **Task** — one measurable change.
2. **Reference role** — which image is authoritative and how it may be used.
3. **Preservation invariants** — what cannot move or change.
4. **Canvas and layout** — crop, dimensions, coordinate-like regions, spatial relationships.
5. **Region edits** — one named region at a time, with separate change and preserve clauses.
6. **Exact copy** — verbatim quoted strings and their destinations.
7. **Style system** — palette, era, material, line weight, rendering character.
8. **Asset rules** — object count, isolation, silhouettes, reuse constraints.
9. **Negative constraints** — concrete failure modes, not generic “bad quality” language.
10. **Quality gate** — observable checks at full size and intended small-detail scale.

The local estimator conservatively uses three characters per token and refuses a brief above 4,500 estimated tokens. Because Qwen does not publish a client-side tokenizer for this API, the estimate is intentionally labeled approximate.

## Editing methodology

- Start with an object-only Render Pass. Do not combine object replacement, global relabeling, and layout reconstruction in the first call.
- Use the source screenshot as reference 1 and declare it authoritative outside the named region.
- Generate a small fixed-seed batch, compare variants, then change one variable per iteration.
- If the full-screen edit drifts, switch to an Asset Pass and assemble the approved asset in Figma.
- For strict preservation, normalize GIF references to lossless PNG, then use a deterministic region mask or composite. A detailed prompt cannot guarantee unchanged pixels outside its target.
- Treat model-rendered small text as evidence of capability, not as production copy. Rebuild approved labels as native Figma and web text.
- Record the source hash, brief, compiled prompt, model, provider, seed, output hash, cost, and Figma placement for every retained variant.

## Provider-specific quirks

- OpenRouter currently exposes `qwen/qwen-image-3-pro` and `qwen/qwen-image-3` through its dedicated Image API. Its live capability record accepts 1K/2K, a fixed aspect-ratio allowlist, one to six outputs, seed, and up to four references.
- Alibaba's direct API currently documents one to three input images for image-to-image. It offers `prompt_extend`; editing must use `direct`, because `agent` enhancement is text-to-image only.
- Alibaba accepts an explicit `width*height` output within its documented pixel-area and aspect-ratio bounds. Use it when the source ratio is not in OpenRouter's fixed ratio allowlist.
- OpenRouter's current Alibaba endpoint advertises no provider-specific passthrough parameters, so `prompt_extend` is not assumed there. The prompt compiler must supply the complete instruction directly.
- The current OpenRouter account enforces a privacy/ZDR guardrail that excludes Alibaba's endpoint. `provider: auto` tries OpenRouter first and falls back to direct Alibaba only for this pre-generation privacy error; it does not fall back after timeouts or ambiguous failures, which could cause duplicate billing.
- OpenRouter returns image bytes as base64. Alibaba direct returns expiring URLs; those outputs must be downloaded promptly because the documented retention window is 24 hours.

## Why final assembly remains deterministic

The model's stated ability to render 10 px detail makes it valuable for screenshots, previews, textures, and style exploration. It does not make probabilistic pixels a better source of truth than editable type, vectors, components, layout constraints, and code. The accepted pipeline therefore ends with Figma Assembly and an Interactive Replica, not a single flattened image.
