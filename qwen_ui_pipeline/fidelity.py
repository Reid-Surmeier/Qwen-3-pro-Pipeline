"""Deterministic fidelity verification against an approved baseline.

A reconstruction is not verified because it resembles a screenshot. It is
verified when every pixel the contract did not license to change is byte
identical to the approved baseline. This module owns that judgement; it never
consults a model and never scores a whole image.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class FidelityContractError(ValueError):
    """The contract itself is unusable, so no verdict can be reached."""


class FidelityEvidenceError(ValueError):
    """The images under comparison cannot support a verdict."""


@dataclass(frozen=True)
class MutableRegion:
    """A rectangle the contract licenses a Render Pass to change."""

    name: str
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def overlaps(self, other: "MutableRegion") -> bool:
        return (
            self.x < other.right
            and other.x < self.right
            and self.y < other.bottom
            and other.y < self.bottom
        )


@dataclass(frozen=True)
class FidelityContract:
    """The approved canvas plus every rectangle licensed to change."""

    width: int
    height: int
    approved_baseline: str
    mutable_regions: tuple[MutableRegion, ...]

    def region(self, name: str) -> MutableRegion:
        for candidate in self.mutable_regions:
            if candidate.name == name:
                return candidate
        raise KeyError(name)


@dataclass(frozen=True)
class RegionChange:
    """How many pixels changed inside one licensed rectangle."""

    name: str
    changed_pixels: int
    total_pixels: int

    @property
    def changed(self) -> bool:
        return self.changed_pixels > 0


@dataclass(frozen=True)
class PaletteComparison:
    """How far one region's palette grew against the approved baseline.

    A flat palettised control that multiplies its colour count many times over
    was redrawn by a continuous-tone process, whatever the pixels outside it
    say. The signal is blunt, free, and needs no model.
    """

    region: str
    baseline_colours: int
    candidate_colours: int
    growth: float
    within_tolerance: bool


@dataclass(frozen=True)
class FidelityResult:
    """A complete deterministic verdict, with the evidence behind it."""

    passed: bool
    region_changes: tuple[RegionChange, ...]
    invariant_violations: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.invariant_violations, tuple) or any(
            not isinstance(coordinate, tuple)
            or len(coordinate) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in coordinate)
            for coordinate in self.invariant_violations
        ):
            raise FidelityEvidenceError(
                "invariant violations must be a tuple of integer (x, y) coordinates"
            )
        if self.passed != (not self.invariant_violations):
            raise FidelityEvidenceError(
                "fidelity passed flag contradicts the invariant-violation evidence"
            )

    @property
    def invariant_violation_count(self) -> int:
        return len(self.invariant_violations)

    @property
    def first_violation(self) -> tuple[int, int] | None:
        return self.invariant_violations[0] if self.invariant_violations else None

    def change(self, name: str) -> RegionChange:
        for candidate in self.region_changes:
            if candidate.name == name:
                return candidate
        raise KeyError(name)


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FidelityContractError(f"{field} must be an integer")
    return value


def _parse_region(raw: Mapping[str, Any], canvas: tuple[int, int]) -> MutableRegion:
    try:
        name = raw["name"]
    except (KeyError, TypeError) as error:
        raise FidelityContractError("every mutable region needs a name") from error
    if not isinstance(name, str) or not name.strip():
        raise FidelityContractError("mutable region names must be non-empty strings")

    values = {}
    for field in ("x", "y", "width", "height"):
        if field not in raw:
            raise FidelityContractError(f"region {name} is missing {field}")
        values[field] = _require_int(raw[field], f"region {name} {field}")

    region = MutableRegion(name=name, **values)
    if region.width <= 0 or region.height <= 0:
        raise FidelityContractError(f"region {name} has zero or negative area")
    if region.x < 0 or region.y < 0:
        raise FidelityContractError(f"region {name} starts outside the canvas")
    canvas_width, canvas_height = canvas
    if region.right > canvas_width or region.bottom > canvas_height:
        raise FidelityContractError(f"region {name} extends past the canvas")
    return region


def parse_fidelity_contract(document: Mapping[str, Any]) -> FidelityContract:
    """Validate a contract document, failing closed on anything ambiguous."""

    if not isinstance(document, Mapping):
        raise FidelityContractError("contract must be a JSON object")

    width = _require_int(document.get("width"), "width")
    height = _require_int(document.get("height"), "height")
    if width <= 0 or height <= 0:
        raise FidelityContractError("contract canvas must have positive dimensions")

    baseline = document.get("approvedBaseline")
    if not isinstance(baseline, str) or not baseline.strip():
        raise FidelityContractError("approvedBaseline must name the approved image")

    raw_regions = document.get("mutableRegions")
    if not isinstance(raw_regions, Sequence) or isinstance(raw_regions, (str, bytes)):
        raise FidelityContractError("mutableRegions must be a list")
    if not raw_regions:
        raise FidelityContractError("a contract with no mutable region licenses nothing")

    regions: list[MutableRegion] = []
    for raw in raw_regions:
        region = _parse_region(raw, (width, height))
        for existing in regions:
            if existing.name == region.name:
                raise FidelityContractError(f"duplicate region name {region.name}")
            if existing.overlaps(region):
                raise FidelityContractError(
                    f"regions {existing.name} and {region.name} overlap, so a changed "
                    "pixel could not be attributed to one of them"
                )
        regions.append(region)

    return FidelityContract(
        width=width,
        height=height,
        approved_baseline=baseline,
        mutable_regions=tuple(regions),
    )


def load_fidelity_contract(path: Path) -> FidelityContract:
    """Read and validate a contract from disk."""

    return parse_fidelity_contract(json.loads(Path(path).read_text(encoding="utf-8")))


def _as_pixel_rows(image: Any) -> tuple[int, int, Sequence[Any]]:
    """Accept a PIL image or an explicit (width, height, pixels) triple."""

    if isinstance(image, tuple) and len(image) == 3:
        width, height, pixels = image
        if (
            isinstance(width, bool)
            or not isinstance(width, int)
            or isinstance(height, bool)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            raise FidelityEvidenceError(
                "explicit image dimensions must be positive integers"
            )
        try:
            pixel_rows = list(pixels)
        except TypeError as error:
            raise FidelityEvidenceError(
                "explicit image pixels must be an iterable"
            ) from error
        expected = width * height
        if len(pixel_rows) != expected:
            raise FidelityEvidenceError(
                f"explicit {width}x{height} image declares {expected} pixels but "
                f"provides {len(pixel_rows)}"
            )
        return width, height, pixel_rows

    try:
        converted = image.convert("RGBA")
    except (AttributeError, TypeError, ValueError) as error:
        raise FidelityEvidenceError(
            "image evidence must be a PIL-compatible image or an explicit pixel triple"
        ) from error
    width, height = converted.size
    pixel_rows = list(converted.getdata())
    expected = width * height
    if len(pixel_rows) != expected:
        raise FidelityEvidenceError(
            f"converted {width}x{height} image declares {expected} pixels but "
            f"provides {len(pixel_rows)}"
        )
    return width, height, pixel_rows


def verify_against_baseline(
    contract: FidelityContract,
    candidate: Any,
    baseline: Any,
) -> FidelityResult:
    """Compare a candidate with its approved baseline under one contract.

    The candidate passes only when every pixel outside every licensed rectangle
    is byte identical. Changes inside a rectangle are reported, never judged --
    whether the intended change is *correct* is a semantic question this layer
    deliberately does not answer.
    """

    candidate_width, candidate_height, candidate_pixels = _as_pixel_rows(candidate)
    baseline_width, baseline_height, baseline_pixels = _as_pixel_rows(baseline)

    if (candidate_width, candidate_height) != (baseline_width, baseline_height):
        raise FidelityEvidenceError(
            "candidate and baseline differ in size, so no pixel correspondence exists"
        )
    if (candidate_width, candidate_height) != (contract.width, contract.height):
        raise FidelityEvidenceError(
            "images do not match the contract canvas, so the regions do not apply"
        )

    changed_counts = {region.name: 0 for region in contract.mutable_regions}
    invariant_violations: list[tuple[int, int]] = []

    for index, (candidate_pixel, baseline_pixel) in enumerate(
        zip(candidate_pixels, baseline_pixels)
    ):
        if candidate_pixel == baseline_pixel:
            continue
        x = index % candidate_width
        y = index // candidate_width
        owner = next(
            (region for region in contract.mutable_regions if region.contains(x, y)),
            None,
        )
        if owner is None:
            invariant_violations.append((x, y))
        else:
            changed_counts[owner.name] += 1

    region_changes = tuple(
        RegionChange(
            name=region.name,
            changed_pixels=changed_counts[region.name],
            total_pixels=region.width * region.height,
        )
        for region in contract.mutable_regions
    )

    return FidelityResult(
        passed=not invariant_violations,
        region_changes=region_changes,
        invariant_violations=tuple(invariant_violations),
    )


def _region_colours(
    pixels: Sequence[Any], width: int, region: MutableRegion
) -> set[Any]:
    colours: set[Any] = set()
    for y in range(region.y, region.bottom):
        row = y * width
        colours.update(pixels[row + region.x : row + region.right])
    return colours


def compare_palettes(
    contract: FidelityContract,
    candidate: Any,
    baseline: Any,
    *,
    max_growth: float = 4.0,
) -> tuple[PaletteComparison, ...]:
    """Compare each licensed region's palette size with the baseline's.

    Reported separately from `verify_against_baseline` rather than folded into
    its verdict: `passed` means specifically that unlicensed pixels did not
    change, and conflating a second question with it would make both harder to
    act on.
    """

    if max_growth < 1.0:
        raise FidelityContractError("max_growth below 1.0 would reject an identical palette")

    candidate_width, candidate_height, candidate_pixels = _as_pixel_rows(candidate)
    baseline_width, baseline_height, baseline_pixels = _as_pixel_rows(baseline)

    if (candidate_width, candidate_height) != (baseline_width, baseline_height):
        raise FidelityEvidenceError(
            "candidate and baseline differ in size, so no palette comparison exists"
        )
    if (candidate_width, candidate_height) != (contract.width, contract.height):
        raise FidelityEvidenceError(
            "images do not match the contract canvas, so the regions do not apply"
        )

    comparisons: list[PaletteComparison] = []
    for region in contract.mutable_regions:
        baseline_colours = len(_region_colours(baseline_pixels, baseline_width, region))
        candidate_colours = len(_region_colours(candidate_pixels, candidate_width, region))
        growth = candidate_colours / baseline_colours if baseline_colours else float("inf")
        comparisons.append(
            PaletteComparison(
                region=region.name,
                baseline_colours=baseline_colours,
                candidate_colours=candidate_colours,
                growth=growth,
                within_tolerance=growth <= max_growth,
            )
        )
    return tuple(comparisons)


def describe_palettes(comparisons: Iterable[PaletteComparison]) -> str:
    """Render palette findings a reviewer can read without opening the images."""

    lines: list[str] = []
    for comparison in comparisons:
        verdict = "ok" if comparison.within_tolerance else "lost bitmap character"
        lines.append(
            f"  region {comparison.region}: {comparison.baseline_colours} -> "
            f"{comparison.candidate_colours} colour(s), "
            f"{comparison.growth:.1f}x ({verdict})"
        )
    return "\n".join(lines)


def describe_result(result: FidelityResult) -> str:
    """Render a verdict a reviewer can read without opening the images."""

    lines: list[str] = []
    verdict = "pass" if result.passed else "fail"
    lines.append(f"invariant pixels: {verdict}")
    if not result.passed:
        x, y = result.first_violation or (0, 0)
        lines.append(
            f"  {result.invariant_violation_count} pixel(s) changed outside every licensed "
            f"region, first at ({x}, {y})"
        )
    for change in result.region_changes:
        lines.append(
            f"  region {change.name}: {change.changed_pixels}/{change.total_pixels} "
            "pixel(s) changed"
        )
    return "\n".join(lines)


def load_correction_prompts(path: Path) -> tuple[dict[str, Any], ...]:
    """Load the correction-replay corpus, failing closed on a malformed entry."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise FidelityContractError("correction corpus must be a JSON object")
    prompts = document.get("prompts")
    if (
        not isinstance(prompts, Sequence)
        or isinstance(prompts, (str, bytes))
        or not prompts
    ):
        raise FidelityContractError("correction corpus must carry a non-empty prompts list")

    required = (
        "id",
        "source_correction",
        "review_prompt",
        "applies_to",
        "required_evidence",
        "promotion_rule",
    )
    seen: set[str] = set()
    for prompt in prompts:
        if not isinstance(prompt, Mapping):
            raise FidelityContractError("every correction prompt must be an object")
        for field in required:
            if not prompt.get(field):
                raise FidelityContractError(
                    f"correction prompt {prompt.get('id', '<unnamed>')} is missing {field}"
                )
        for field in ("applies_to", "required_evidence"):
            if not isinstance(prompt[field], Sequence) or isinstance(
                prompt[field], (str, bytes)
            ):
                raise FidelityContractError(
                    f"correction prompt {prompt['id']} {field} must be a list"
                )
            if any(
                not isinstance(value, str) or not value.strip()
                for value in prompt[field]
            ):
                raise FidelityContractError(
                    f"correction prompt {prompt['id']} {field} must contain only "
                    "non-empty strings"
                )
        if prompt["id"] in seen:
            raise FidelityContractError(f"duplicate correction prompt {prompt['id']}")
        seen.add(prompt["id"])
    return tuple(prompts)


def corrections_for(prompts: Iterable[Mapping[str, Any]], target: str) -> tuple[str, ...]:
    """Select the review prompts that apply to one reconstruction target."""

    selected: list[str] = []
    for prompt in prompts:
        applies_to = prompt.get("applies_to") or []
        if "*" in applies_to or target in applies_to:
            selected.append(prompt["id"])
    return tuple(selected)
