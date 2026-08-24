"""Fail-closed contract for source-locked Qwen image generation."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping


WORKFLOW_PROFILE = "qwen-source-locked-single-decision-v1"
REQUIRED_PROVIDER = "alibaba"
REQUIRED_MODEL = "qwen/qwen-image-3-pro"
REQUIRED_RUNTIME = "comfyui"
REQUIRED_CANDIDATE_COUNT = 4


class WorkflowContractError(ValueError):
    """Raised before generation when the full Qwen procedure is incomplete."""


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_workflow_contract(brief: Mapping[str, Any]) -> None:
    """Require the complete single-decision Qwen + ComfyUI workflow profile."""

    errors: list[str] = []

    exact_values = (
        ("workflow_profile", WORKFLOW_PROFILE),
        ("provider", REQUIRED_PROVIDER),
        ("model", REQUIRED_MODEL),
        ("runtime", REQUIRED_RUNTIME),
    )
    for field, expected in exact_values:
        if brief.get(field) != expected:
            errors.append(f"{field} must be {expected!r}")

    for field in (
        "objective",
        "reference_role",
    ):
        if not isinstance(brief.get(field), str) or not str(brief[field]).strip():
            errors.append(f"{field} must be a non-empty string")

    for field in (
        "preservation_invariants",
        "canvas",
        "style",
        "negative_constraints",
        "quality_checks",
    ):
        if not _nonempty_list(brief.get(field)):
            errors.append(f"{field} must be a non-empty list of strings")

    reference = brief.get("reference")
    if not isinstance(reference, Mapping):
        errors.append("reference must contain the immutable source path and sha256")
    else:
        if not isinstance(reference.get("path"), str) or not reference["path"].strip():
            errors.append("reference.path must be a non-empty string")
        if not _sha256(reference.get("sha256")):
            errors.append("reference.sha256 must be a lowercase 64-character SHA-256")

    stage = brief.get("stage")
    if not isinstance(stage, Mapping):
        errors.append("stage must identify the one visual decision and approval state")
    else:
        for field in ("id", "decision"):
            if not isinstance(stage.get(field), str) or not stage[field].strip():
                errors.append(f"stage.{field} must be a non-empty string")
        if stage.get("status") not in {
            "planned",
            "rendered",
            "awaiting_approval",
            "approved",
            "rejected",
        }:
            errors.append("stage.status is not a supported approval state")

    regions = brief.get("regions")
    if not isinstance(regions, list) or len(regions) != 1:
        errors.append("regions must contain exactly one visual decision")
    elif not isinstance(regions[0], Mapping):
        errors.append("regions[0] must be an object")
    else:
        region = regions[0]
        for field in ("name", "change"):
            if not isinstance(region.get(field), str) or not region[field].strip():
                errors.append(f"regions[0].{field} must be a non-empty string")
        bounds = region.get("bounds")
        if (
            not isinstance(bounds, list)
            or len(bounds) != 4
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in bounds)
            or bounds[0] < 0
            or bounds[1] < 0
            or bounds[2] <= 0
            or bounds[3] <= 0
        ):
            errors.append(
                "regions[0].bounds must be [x, y, width, height] with non-negative "
                "coordinates and positive dimensions"
            )

    output = brief.get("output")
    if not isinstance(output, Mapping):
        errors.append("output must define resolution, source geometry, count, and seed")
    else:
        if output.get("count") != REQUIRED_CANDIDATE_COUNT:
            errors.append(f"output.count must be {REQUIRED_CANDIDATE_COUNT}")
        seed = output.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2147483647:
            errors.append("output.seed must be a fixed 31-bit integer")
        if output.get("aspect_ratio") != "source":
            errors.append("output.aspect_ratio must be 'source'")
        if not isinstance(output.get("size"), str) or re.fullmatch(
            r"[1-9][0-9]*\*[1-9][0-9]*", output["size"]
        ) is None:
            errors.append("output.size must be the measured source ratio as width*height")

    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise WorkflowContractError(
            f"{WORKFLOW_PROFILE} preflight failed:\n{formatted}"
        )


def verify_reference_hash(brief: Mapping[str, Any], reference_path: Path) -> str:
    """Validate the contract and prove that the supplied immutable source matches it."""

    validate_workflow_contract(brief)
    if not reference_path.is_file():
        raise WorkflowContractError(f"reference file does not exist: {reference_path}")
    actual = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    expected = str(brief["reference"]["sha256"])
    if actual != expected:
        raise WorkflowContractError(
            f"reference SHA-256 mismatch: expected {expected}, got {actual}"
        )
    return actual


def validate_assembly_gate(brief: Mapping[str, Any]) -> None:
    """Allow deterministic assembly only after one donor is explicitly approved."""

    validate_workflow_contract(brief)
    stage = brief["stage"]
    if stage.get("status") != "approved":
        raise WorkflowContractError(
            "deterministic assembly requires stage.status='approved'"
        )
    if not _sha256(stage.get("approved_output_sha256")):
        raise WorkflowContractError(
            "deterministic assembly requires stage.approved_output_sha256"
        )


def verify_approved_output_hash(brief: Mapping[str, Any], output_path: Path) -> str:
    """Prove that assembly uses the donor frozen by the approval gate."""

    validate_assembly_gate(brief)
    if not output_path.is_file():
        raise WorkflowContractError(f"approved donor file does not exist: {output_path}")
    actual = hashlib.sha256(output_path.read_bytes()).hexdigest()
    expected = str(brief["stage"]["approved_output_sha256"])
    if actual != expected:
        raise WorkflowContractError(
            f"approved donor SHA-256 mismatch: expected {expected}, got {actual}"
        )
    return actual
