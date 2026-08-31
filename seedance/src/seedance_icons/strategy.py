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

The gate is profile-aware: the brief declares `grammar` — "retro-sprite" (default,
full pixel-art rules) or "smooth" (non-pixel-art sources: the general principles apply,
the crisp-pixel palette check does not). Undeclared briefs get retro-sprite, so the
original strictness never relaxes silently.

A waiver exists for deliberate experiments, but it is loud: the reason is recorded in
plan.json and printed, never silent.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from PIL import Image

MIN_PROMPT_WORDS = 350
MIN_IDIOM_WORDS = 8
MAX_ANCHOR_COLORS = 32
BLOCK_FACTORS = (4, 2)

# The brief declares its grammar; undeclared briefs default to retro-sprite so the
# original batch-3 strictness never relaxes silently. "retro-sprite" carries the full
# pixel-art rules (crisp quantized anchors); "smooth" keeps the general principles —
# reference pairing, motion-basis citation, prompt depth, anchors — for sources that
# legitimately are not pixel art (logos, brand marks, anti-aliased icons).
DEFAULT_GRAMMAR = "retro-sprite"
GRAMMARS = ("retro-sprite", "smooth")


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


MIN_MULTI_STATE_MOTION_WORDS = 120
POSE_MARKER = re.compile(
    r"\bpose (?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b|\bbeat \d+\b",
    re.IGNORECASE,
)


def enumerated_poses(motion: str) -> int:
    """How many held poses the motion field actually names."""
    return len(POSE_MARKER.findall(motion))


def check_motion_detail(brief: dict[str, Any]) -> list[str]:
    """A multi-state gesture must be written pose by pose, not summarised.

    Measured across every brief on disk, motion-field length against outcome:

        24-32 words, 0 poses   batch 1 and 2, a two-frame twinkle. Fine — a small
                               gesture needs few words, and batch 2 certified at
                               0.998-1.0 on briefs this short.
        64-76 words, 0 poses   the two failed four-state takes, 2026-08-30. A large
                               gesture summarised. The element moved fifteen pixels
                               when told to move one, twice.
        123-218 words, 3-6     batch 3 and the magazine-flip batch, all certified.
                               A large gesture written out pose by pose.

    So the rule is not "write more". It is that the detail has to match the size of
    what is being asked for: a brief that declares four states and then describes the
    motion in two sentences has told the model what to end up with and nothing about
    how to get there, and the model fills that in generously.
    """
    violations: list[str] = []
    states = brief.get("state_map") or {}
    if len(states) < 2:
        return violations
    motion = str(brief.get("motion") or "")
    words = len(motion.split())
    poses = enumerated_poses(motion)
    if words < MIN_MULTI_STATE_MOTION_WORDS:
        violations.append(
            f"motion is {words} words for a {len(states)}-state gesture (min "
            f"{MIN_MULTI_STATE_MOTION_WORDS}): every certified multi-pose run on disk "
            f"used 123-218 words, and both runs that summarised a large gesture in "
            f"64-76 words moved the element roughly fifteen times further than asked"
        )
    if poses < len(states):
        violations.append(
            f"motion names {poses} held poses for {len(states)} states: write the "
            f"gesture out pose by pose ('Beat 2, five held poses: pose one ...'), the "
            f"way the certified batch-3 briefs do"
        )
    return violations


MOTION_KINDS = ("translate", "rotate", "scale", "reveal", "blink")


def _reference_registry(brief_path: Path) -> dict[str, Any]:
    """The provenance record next to the reference assets, if it can be found."""
    for base in (brief_path.parent, *brief_path.parents):
        candidate = (
            base / "docs" / "evidence" / "board-icons-test" / "references" / "provenance.json"
        )
        if candidate.exists():
            # A present but unreadable registry is a broken safety input. Let the
            # parse/read error stop planning instead of silently skipping the
            # motion-reference compatibility gate.
            return json.loads(candidate.read_text())
    return {}


def _registered_reference_name(value: str, registry: dict[str, Any]) -> str | None:
    """Map a GIF/MP4 path or URL to its provenance-registry entry by stable stem."""
    path = unquote(urlparse(value).path) if value.startswith("https://") else value
    stem = Path(path).stem
    return next((name for name in registry if Path(name).stem == stem), None)


def check_reference_matches_motion(
    brief: dict[str, Any],
    brief_path: Path,
    video_references: Sequence[str],
) -> list[str]:
    """The reference must move the way the brief says the icon moves.

    A reference does not only teach cadence, it teaches the *kind* of movement, and the
    wrong kind is worse than none. Observed 2026-08-30: a magnifying glass asked to
    travel across a bust was handed ref-coin-spin, whose motion_kind is `rotate`. The
    glass tumbled and changed size instead of travelling, and no amount of brief wording
    corrected it — the reference was pulling the other way the whole time.

    So the brief declares its motion_kind, the reference registry declares each asset's,
    and a run whose kinds disagree does not proceed.
    """
    violations: list[str] = []
    reference = str(brief.get("real_reference") or "")
    registry = (_reference_registry(brief_path) or {}).get("assets") or {}
    named = [
        name for name in registry if name in reference or name.replace(".gif", "") in reference
    ]
    if not video_references:
        violations.append(
            "video_reference is required: pass the actual matching animation with "
            "--video-reference HTTPS_URL; naming it in real_reference is not model input"
        )
        return violations

    non_https = [value for value in video_references if not value.startswith("https://")]
    if non_https:
        violations.append(
            "video_reference must be an HTTPS URL so the provider receives the actual "
            "animation, not a prose citation or an environment-local path"
        )

    actual_names = {
        name
        for value in video_references
        if (name := _registered_reference_name(value, registry)) is not None
    }
    if registry and len(actual_names) != len(video_references):
        violations.append(
            "every video_reference must name an asset registered in provenance.json; "
            "an unregistered clip has no verified motion_kind"
        )
    if named and set(named) != actual_names:
        violations.append(
            "the submitted video_reference does not match real_reference: declared "
            f"{', '.join(sorted(named))}; submitted "
            f"{', '.join(sorted(actual_names)) or 'no registered asset'}"
        )

    names_to_check = actual_names or set(named)
    if not names_to_check:
        # A legacy corpus citation can still establish provenance, but the actual HTTPS
        # clip is now mandatory. With no local registry entry there is no motion-kind
        # metadata to compare deterministically.
        return violations

    kind = str(brief.get("motion_kind") or "").strip().lower()
    if not kind:
        violations.append(
            f"motion_kind is missing while using reference {min(names_to_check)}: "
            "declare how the "
            f"icon moves (one of {', '.join(MOTION_KINDS)}) so the reference can be "
            f"checked against it"
        )
        return violations
    if kind not in MOTION_KINDS:
        violations.append(f"motion_kind {kind!r} is not one of {', '.join(MOTION_KINDS)}")
        return violations

    for name in names_to_check:
        ref_kind = str(registry[name].get("motion_kind") or "").lower()
        if ref_kind and ref_kind != kind:
            violations.append(
                f"reference {name} moves by {ref_kind!r} but the brief declares "
                f"{kind!r}: a reference teaches the kind of movement as well as its "
                f"cadence, and the wrong kind pulls against every word of the brief"
            )
    return violations


def check_strategy(
    brief: dict[str, Any],
    brief_path: Path,
    prompt: str,
    first_frame: str | None,
    last_frame: str | None,
    *,
    video_references: Sequence[str],
) -> list[str]:
    """Return the list of strategy violations (empty means the plan may proceed)."""
    violations: list[str] = []

    grammar = str(brief.get("grammar") or DEFAULT_GRAMMAR).strip()
    if grammar not in GRAMMARS:
        violations.append(
            f"grammar {grammar!r} is not recognized (one of {', '.join(GRAMMARS)}); "
            "declare what kind of source this is so the right rules apply"
        )
        grammar = DEFAULT_GRAMMAR
    retro = grammar == "retro-sprite"

    basis_field = "era_idiom_basis" if retro else "motion_basis"
    basis = str(brief.get(basis_field) or brief.get("era_idiom_basis") or "").strip()
    if len(basis.split()) < MIN_IDIOM_WORDS:
        hint = (
            "cite the shipped-game behavior the motion imitates "
            "(see docs/research/era-ui-animation-reference-corpus.md)"
            if retro
            else "cite the real-world motion behavior this run imitates and where it is from"
        )
        violations.append(f"{basis_field} is missing or too thin: {hint}")

    reference = str(brief.get("real_reference") or "").strip()
    if not reference:
        hint = (
            "pair the run with a real-game animation asset "
            "(docs/evidence/board-icons-test/references/) or an explicit era-corpus citation"
            if retro
            else "pair the run with a real example of the motion (a clip, recording, or "
            "documented asset on disk) — visible evidence, not a cited guess"
        )
        violations.append(f"real_reference is missing: {hint}")
    elif not _reference_resolves(reference, brief_path):
        violations.append(f"real_reference does not resolve to any existing file: {reference!r}")

    violations.extend(check_motion_detail(brief))
    violations.extend(check_reference_matches_motion(brief, brief_path, video_references))

    words = len(prompt.split())
    if words < MIN_PROMPT_WORDS:
        violations.append(
            f"compiled prompt is {words} words (min {MIN_PROMPT_WORDS}): write the motion "
            "beat by beat — the terse grammar is what the era-corpus redesign replaced"
        )

    anchor_kind = "crisp anchor" if retro else "anchor"
    for label, frame in (("first_frame", first_frame), ("last_frame", last_frame)):
        if not frame:
            violations.append(f"{label} anchor is required (first = last = {anchor_kind})")
        elif frame.startswith(("https://", "data:")):
            violations.append(f"{label} must be a local {anchor_kind} file, not a URL")
        elif not Path(frame).is_file():
            violations.append(f"{label} anchor not found: {frame}")
        elif retro:
            ok, detail = anchor_is_crisp(Path(frame))
            if not ok:
                violations.append(f"{label}: {detail}")

    return violations


def gate_record(
    violations: list[str], waiver: str | None, grammar: str = DEFAULT_GRAMMAR
) -> dict[str, Any]:
    """The strategy_gate entry stored in plan.json; submission requires it."""
    record: dict[str, Any] = {
        "grammar": grammar,
        "passed": not violations,
        "violations": violations,
    }
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
