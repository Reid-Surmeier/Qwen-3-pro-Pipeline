"""Fail-closed strategy gate: no plan (and therefore no paid submission) without the
batch-3 method that produced the first certified complex-motion runs (Issue #87).

The enforced strategy, each element traceable to a measured outcome:
- era_idiom_basis citing real era behavior (batch 2: zero structural failures after
  era-corpus grounding; batch 1: 2 of 4 failed without it);
- real_reference pairing every run with an actual animation from a shipped game, or an
  explicit era-corpus citation when no redistributable frames exist;
- a beat-by-beat compiled prompt (batch 3 certified cells ran 406-543 words; the ~200
  word batch-2 grammar left the model guessing);
- crisp anchors as both frame inputs: hard pixels, quantized palette (batch 3 first
  RMSE 4.0-4.3 vs 4.6-5.1 for soft screenshot texture).

A waiver exists for deliberate experiments, but it is loud: the reason is recorded in
plan.json and printed, never silent.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PIL import Image

MIN_PROMPT_WORDS = 350
MIN_IDIOM_WORDS = 8
MAX_ANCHOR_COLORS = 32
BLOCK_FACTORS = (4, 2)


def anchor_is_crisp(path: Path) -> tuple[bool, str]:
    """A crisp anchor is hard pixels: a small quantized palette outside the matte, and
    exact NEAREST block structure (it was integer-upscaled, not resampled)."""
    if not path.exists():
        return False, f"anchor not found: {path}"
    image = Image.open(path).convert("RGB")
    colors = image.getcolors(maxcolors=1_000_000)
    if not colors:
        return False, f"anchor has too many colors to count: {path}"
    colors.sort(reverse=True)
    matte = colors[0][1]
    non_matte = sum(1 for _, color in colors if color != matte)
    if non_matte > MAX_ANCHOR_COLORS:
        return False, (
            f"anchor {path.name} has {non_matte} non-matte colors "
            f"(max {MAX_ANCHOR_COLORS}); use the crisp anchor (grid-snapped, quantized), "
            "not the soft screenshot crop"
        )
    width, height = image.size
    for factor in BLOCK_FACTORS:
        if width % factor or height % factor:
            continue
        down = image.resize((width // factor, height // factor), Image.NEAREST)
        up = down.resize((width, height), Image.NEAREST)
        if list(image.getdata()) == list(up.getdata()):
            return True, f"crisp: {non_matte} non-matte colors, exact {factor}x blocks"
    return False, (
        f"anchor {path.name} is not integer-blocky at any of {BLOCK_FACTORS}; "
        "crisp anchors are NEAREST-upscaled from the native grid"
    )


def _reference_resolves(value: str, brief_path: Path) -> bool:
    """At least one path-like token in real_reference must exist on disk, searched
    relative to the brief, its evidence root, and the current directory."""
    tokens = re.findall(r"[\w./-]+/[\w./-]+", value)
    bases = [brief_path.parent, brief_path.parent.parent, Path.cwd()]
    for token in tokens:
        candidate = token.rstrip(".,;:)")
        for base in bases:
            if (base / candidate).is_file():
                return True
    return False


def check_strategy(
    brief: dict[str, Any],
    brief_path: Path,
    prompt: str,
    first_frame: str | None,
    last_frame: str | None,
) -> list[str]:
    """Return the list of strategy violations (empty means the plan may proceed)."""
    violations: list[str] = []

    idiom = str(brief.get("era_idiom_basis") or "").strip()
    if len(idiom.split()) < MIN_IDIOM_WORDS:
        violations.append(
            "era_idiom_basis is missing or too thin: cite the shipped-game behavior the "
            "motion imitates (see docs/research/era-ui-animation-reference-corpus.md)"
        )

    reference = str(brief.get("real_reference") or "").strip()
    if not reference:
        violations.append(
            "real_reference is missing: pair the run with a real-game animation asset "
            "(docs/evidence/board-icons-test/references/) or an explicit era-corpus citation"
        )
    elif not _reference_resolves(reference, brief_path):
        violations.append(
            f"real_reference does not resolve to any existing file: {reference!r}"
        )

    words = len(prompt.split())
    if words < MIN_PROMPT_WORDS:
        violations.append(
            f"compiled prompt is {words} words (min {MIN_PROMPT_WORDS}): write the motion "
            "beat by beat — the terse grammar is what the era-corpus redesign replaced"
        )

    for label, frame in (("first_frame", first_frame), ("last_frame", last_frame)):
        if not frame:
            violations.append(f"{label} anchor is required (first = last = crisp anchor)")
        elif frame.startswith(("https://", "data:")):
            violations.append(f"{label} must be a local crisp anchor file, not a URL")
        else:
            ok, detail = anchor_is_crisp(Path(frame))
            if not ok:
                violations.append(f"{label}: {detail}")

    return violations


def gate_record(violations: list[str], waiver: str | None) -> dict[str, Any]:
    """The strategy_gate entry stored in plan.json; submission requires it."""
    record: dict[str, Any] = {"passed": not violations, "violations": violations}
    if waiver is not None:
        record["waived"] = waiver
    return record


def submit_allowed(plan: dict[str, Any]) -> tuple[bool, str]:
    gate = plan.get("strategy_gate")
    if gate is None:
        return False, (
            "plan has no strategy_gate record; re-create the plan with the current CLI "
            "(the batch-3 strategy is enforced at plan time)"
        )
    if gate.get("passed"):
        return True, "strategy gate passed"
    waiver = gate.get("waived")
    if waiver:
        return True, f"strategy gate waived: {waiver}"
    return False, "strategy gate failed and no waiver was recorded; fix the brief/anchors"
