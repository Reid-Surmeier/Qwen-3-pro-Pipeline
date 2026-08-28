# Seedance addon guidance

This addon generates paid video assets. Planning, research, and verification may proceed
autonomously; a paid OpenRouter submission requires explicit user approval of the exact estimate.

Scope: these rules govern work inside `seedance/`. The repository root's `AGENTS.md`
(issue gate, branch rules, PR template, canonical baseline) still applies to any change
in this directory; where both speak, the stricter rule wins. The core ADR 0003 image
allowance neither covers nor is extended by this addon — see "Addon boundary" in
`README.md`. Paths below are relative to `seedance/`.

## Non-negotiable gates

1. Fetch or load a dated live capability snapshot before selecting a model.
2. Never silently fall back between Seedance 2.0 Mini and Seedance 2.5.
3. Lock the source asset hash and style guide before prompt iteration.
4. Keep every attempt in a new run directory. Never overwrite an accepted output.
5. Do not claim native alpha, loop closure, source fidelity, or style compliance without evidence.
6. Keep generated, verified, reviewed, and accepted as distinct states.
7. Do not restart or modify a shared ComfyUI runtime without checking ownership and approval.
8. For pixel-art sources, raw model output is not reviewable: briefs must pass the
   sprite-grammar rules and outputs the certification in `docs/retro-conformance-gate.md`
   (`seedance-icons retro-conform`) before human style review.

## Agent skills

Skills live in `skills/` (not registered at repo root — the root `.agents/skills/to-spec`
name belongs to the locked skill set). Read the SKILL.md directly and follow it:

- `skills/research-seedance-capabilities/` — refresh provider/model facts or design experiments.
- `skills/animate-icon/` — plan or run an icon/favicon animation.
- `skills/verify-icon-animation/` — independent output review.
- `skills/to-spec/` — iterate an animation against a written design spec until every clause
  has evidence.

## Commands

```bash
python -m pytest
ruff check .
python scripts/validate_repo.py
```

Runs and secrets are ignored. Commit briefs only after removing private references and large data
URLs.

