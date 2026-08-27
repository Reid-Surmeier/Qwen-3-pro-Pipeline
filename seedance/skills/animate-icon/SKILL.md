---
name: animate-icon
description: "Plan and execute additive, style-locked icon, logo, or favicon animations with OpenRouter and ByteDance Seedance. Use for motion studies, first/last-frame transitions, loops, or reference-guided icon animation in this repository."
---

# Animate an icon

Preserve source identity first. Generation is successful only when the animation satisfies the
motion brief and survives independent verification.

## Procedure

1. Read `CONTEXT.md`, `docs/run-contract.md`, `docs/model-routing.md`, and the applicable template.
2. Lock the source asset, style-guide revision, Figma file/node/export metadata when applicable,
   and SHA-256 hashes. Never replace the source or an accepted candidate.
3. Write the brief. Specify silhouette, geometry, stroke, palette, negative space, typography,
   safe area, camera, matte, motion path, easing, holds, overshoot, loop intent, and forbidden drift.
4. Choose conditioning deliberately:
   - first frame for a source-locked opening;
   - first and last frames for endpoints or a loop attempt;
   - image/video/audio references for style or motion guidance in a separate baseline run.
5. Run `$research-seedance-capabilities` when the capability snapshot is missing or stale.
6. Route `study` to Seedance 2.0 Mini and `final` to Seedance 2.5. Never switch silently.
7. Create a non-paid plan with `seedance-icons plan`. Show the model, canonical slug, exact request,
   and estimate to the user.
8. Pause before paid submission. Continue only after explicit approval of the displayed estimate,
   then pass that exact value to `--acknowledge-cost`.
9. Poll the existing job instead of resubmitting. Download into the same run and hash the output.
10. Invoke `$verify-icon-animation`. Put new variants next to old ones and keep rejection notes.

## Favicon-specific rules

- Use a square canvas and keep important geometry inside an 80% safe area.
- Review at 16, 32, 48, and 64 pixels.
- Prefer restrained transform-like motion; freeform morphing often damages identity.
- Native transparency is not assumed. Use an approved matte and inspect keyed antialiasing.

## Guardrails

- Do not submit multiple paid variants from a single approval.
- Do not commit API keys, payload data URLs, private references, or generated run contents.
- Do not claim a seamless loop merely because first and last anchors match.
- Do not restart a shared ComfyUI process without ownership checks and approval.
