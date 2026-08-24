# Repository guidance

## Image generation contract

For every raster generation or edit intended for this repository, load
`.agents/skills/qwen-source-locked-image-generation/SKILL.md` before choosing a
tool or provider.

- Production candidates must use workflow profile
  `qwen-source-locked-single-decision-v1`: Alibaba Qwen Image 3 Pro through the
  repository's ComfyUI runtime.
- Do not use Codex's built-in OpenAI `image_gen`, an OpenAI image CLI, or a
  direct provider call for a production candidate, donor, correction, or
  FigJam review sibling.
- Run `python3 -m qwen_ui_pipeline preflight ...` before generation. A failed
  preflight stops the run; do not substitute another provider.
- One Render Pass may contain exactly one visual decision and four fixed-seed
  candidates. Freeze the selected donor before moving to another decision.
- Deterministic assembly is a separate recorded operation and is blocked until
  the donor stage is approved.
- Preserve failed attempts beneath the same stage. Do not create a new top-level
  run merely to change provider or retry the same decision.

Historical artifacts may record other providers. They are provenance, not
permission to bypass the current contract.

## Agent skills

### Issue tracker

Work is tracked as local Markdown for this snapshot repository. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical five-role label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository with a root glossary and root ADR directory. See `docs/agents/domain.md`.
