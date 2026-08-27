"""Independent semantic verification of a reconstruction.

Deterministic gates prove that unlicensed pixels did not change. They cannot
answer whether the licensed change reads as the intended UI. That judgement is
made here, and deliberately not by the agent that produced the output: an agent
grading its own work shares every blind spot that produced it.

Three rules hold this layer honest.

Region pairs, never whole screenshots. A bounded crop pair is a far more
reliable visual judgement than a full-screen comparison, and a large correct
area cannot mask a small wrong one.

Structured verdicts, never prose. A response that cannot be parsed into the
verdict schema is `unreadable`, which fails closed.

Gates first. The paid model is never called for a run the deterministic layer
already rejected, and a finding here can never mark a run verified.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .fidelity import FidelityContract, FidelityResult, corrections_for

MATCH = "match"
DEFECT = "defect"
UNREADABLE = "unreadable"
VERDICTS = (MATCH, DEFECT, UNREADABLE)

#: Owning production stage for each defect class, per the routing table in
#: docs/implementation/autonomous-convergence-loop.md.
DEFECT_ROUTES: Mapping[str, str] = {
    "visual-state": "render-pass",
    "missing-component": "component-extraction",
    "asset-ownership": "component-extraction",
    "geometry": "assembly",
    "z-order": "assembly",
    "interaction": "interactive-build",
    "motion": "interactive-build",
    "runtime-only": "runtime-export",
}
UNROUTED_STAGE = "triage"


class VerificationError(RuntimeError):
    """The verification pass cannot proceed, so no verdict is reached."""


@dataclass(frozen=True)
class RegionVerdict:
    """One reviewed region, localised."""

    region: str
    verdict: str
    defect_class: str | None = None
    coordinates: tuple[int, int] | None = None
    confidence: float | None = None
    note: str = ""

    @property
    def is_failure(self) -> bool:
        return self.verdict != MATCH

    @property
    def owning_stage(self) -> str | None:
        if not self.is_failure:
            return None
        if self.verdict == UNREADABLE or self.defect_class is None:
            return UNROUTED_STAGE
        return DEFECT_ROUTES.get(self.defect_class, UNROUTED_STAGE)


@dataclass(frozen=True)
class VerificationResult:
    """The complete verdict for one reconstruction."""

    verified: bool
    status: str
    region_verdicts: tuple[RegionVerdict, ...] = ()
    reason: str = ""
    reviewed_prompts: tuple[str, ...] = ()

    @property
    def findings(self) -> tuple[RegionVerdict, ...]:
        return tuple(v for v in self.region_verdicts if v.is_failure)

    def verdict_for(self, region: str) -> RegionVerdict:
        for candidate in self.region_verdicts:
            if candidate.region == region:
                return candidate
        raise KeyError(region)


@dataclass(frozen=True)
class RegionReview:
    """One region crop pair queued for review."""

    region: str
    baseline_crop: Any
    candidate_crop: Any
    questions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()


@dataclass
class VisionClient:
    """Injectable seam for the reviewing model.

    Implementations must call a model family different from the builder's and
    resolve credentials at call time. Nothing here reads a key, and no verdict
    ever carries one.
    """

    model: str = ""
    calls: list[RegionReview] = field(default_factory=list)

    def review(self, review: RegionReview) -> Mapping[str, Any]:  # pragma: no cover
        raise NotImplementedError


def build_region_reviews(
    contract: FidelityContract,
    candidate: Any,
    baseline: Any,
    *,
    correction_prompts: Sequence[Mapping[str, Any]] = (),
    target: str = "*",
) -> tuple[RegionReview, ...]:
    """Crop one review pair per licensed region, with its applicable questions."""

    applicable = set(corrections_for(correction_prompts, target))
    questions = tuple(
        str(prompt["review_prompt"])
        for prompt in correction_prompts
        if prompt.get("id") in applicable
    )
    evidence: list[str] = []
    for prompt in correction_prompts:
        if prompt.get("id") in applicable:
            evidence.extend(str(item) for item in prompt.get("required_evidence", ()))

    reviews: list[RegionReview] = []
    for region in contract.mutable_regions:
        box = (region.x, region.y, region.right, region.bottom)
        reviews.append(
            RegionReview(
                region=region.name,
                baseline_crop=_crop(baseline, box),
                candidate_crop=_crop(candidate, box),
                questions=questions,
                required_evidence=tuple(dict.fromkeys(evidence)),
            )
        )
    return tuple(reviews)


def _crop(image: Any, box: tuple[int, int, int, int]) -> Any:
    if hasattr(image, "crop"):
        return image.crop(box)
    return (image, box)


def parse_region_verdict(region: str, payload: Any) -> RegionVerdict:
    """Coerce a model response into a verdict, failing closed on ambiguity."""

    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            return RegionVerdict(
                region=region,
                verdict=UNREADABLE,
                note="response was not valid JSON",
            )

    if not isinstance(payload, Mapping):
        return RegionVerdict(
            region=region, verdict=UNREADABLE, note="response was not an object"
        )

    verdict = payload.get("verdict")
    if verdict not in VERDICTS:
        return RegionVerdict(
            region=region,
            verdict=UNREADABLE,
            note=f"unrecognised verdict {verdict!r}",
        )

    if verdict == MATCH:
        return RegionVerdict(
            region=region,
            verdict=MATCH,
            confidence=_confidence(payload.get("confidence")),
            note=str(payload.get("note", "")),
        )

    defect_class = payload.get("defect_class")
    coordinates = _coordinates(payload.get("coordinates"))
    if verdict == DEFECT and coordinates is None:
        return RegionVerdict(
            region=region,
            verdict=UNREADABLE,
            defect_class=str(defect_class) if defect_class else None,
            note="a defect the reviewer cannot localise is not a usable finding",
        )

    return RegionVerdict(
        region=region,
        verdict=verdict,
        defect_class=str(defect_class) if defect_class else None,
        coordinates=coordinates,
        confidence=_confidence(payload.get("confidence")),
        note=str(payload.get("note", "")),
    )


def _confidence(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not 0.0 <= float(value) <= 1.0:
        return None
    return float(value)


def _coordinates(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    if len(value) != 2:
        return None
    try:
        return (int(value[0]), int(value[1]))
    except (TypeError, ValueError):
        return None


def run_verification(
    contract: FidelityContract,
    fidelity: FidelityResult,
    candidate: Any,
    baseline: Any,
    *,
    client: VisionClient,
    correction_prompts: Sequence[Mapping[str, Any]] = (),
    target: str = "*",
) -> VerificationResult:
    """Review a run that already passed its deterministic gates.

    Refuses to spend on a run the deterministic layer rejected, and never
    returns `verified` on the strength of the model alone.
    """

    if not fidelity.passed:
        return VerificationResult(
            verified=False,
            status="revision-required",
            reason=(
                f"deterministic gate failed with {fidelity.invariant_violations} "
                "invariant violation(s); the vision layer is not consulted"
            ),
        )

    reviews = build_region_reviews(
        contract,
        candidate,
        baseline,
        correction_prompts=correction_prompts,
        target=target,
    )
    if not reviews:
        raise VerificationError("contract licensed no region, so there is nothing to review")

    verdicts: list[RegionVerdict] = []
    for review in reviews:
        try:
            payload = client.review(review)
        except Exception as error:  # noqa: BLE001 - a failed review must not pass
            verdicts.append(
                RegionVerdict(
                    region=review.region,
                    verdict=UNREADABLE,
                    note=f"reviewer call failed: {error}",
                )
            )
            continue
        verdicts.append(parse_region_verdict(review.region, payload))

    failures = [verdict for verdict in verdicts if verdict.is_failure]
    reviewed_prompts = tuple(corrections_for(correction_prompts, target))

    if failures:
        return VerificationResult(
            verified=False,
            status="revision-required",
            region_verdicts=tuple(verdicts),
            reason=f"{len(failures)} region(s) failed independent review",
            reviewed_prompts=reviewed_prompts,
        )

    return VerificationResult(
        verified=True,
        status="verified",
        region_verdicts=tuple(verdicts),
        reason="deterministic gates and independent review both passed",
        reviewed_prompts=reviewed_prompts,
    )


def route_findings(result: VerificationResult) -> dict[str, tuple[RegionVerdict, ...]]:
    """Group findings by the production stage that owns the fix."""

    routed: dict[str, list[RegionVerdict]] = {}
    for finding in result.findings:
        routed.setdefault(finding.owning_stage or UNROUTED_STAGE, []).append(finding)
    return {stage: tuple(items) for stage, items in routed.items()}


def describe_verification(result: VerificationResult) -> str:
    """Render a verdict a reviewer can read without opening the images."""

    lines = [f"status: {result.status}"]
    if result.reason:
        lines.append(f"  {result.reason}")
    for verdict in result.region_verdicts:
        if verdict.verdict == MATCH:
            lines.append(f"  region {verdict.region}: match")
            continue
        where = f" at {verdict.coordinates}" if verdict.coordinates else ""
        defect = verdict.defect_class or "unclassified"
        lines.append(
            f"  region {verdict.region}: {verdict.verdict} ({defect}){where}"
            f" -> {verdict.owning_stage}"
        )
    return "\n".join(lines)


def verification_questions(prompts: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    """List the review questions a corpus contributes, for logging a run."""

    return tuple(str(prompt["review_prompt"]) for prompt in prompts)
