"""Deterministic ComfyUI API workflow construction."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .workflow_contract import (
    WorkflowContractError,
    validate_assembly_gate,
    validate_workflow_contract,
)


def build_comfyui_api_workflow(
    brief: Mapping[str, Any],
    *,
    reference_filename: str,
    filename_prefix: str,
) -> dict[str, Any]:
    """Build the smallest reference-edit graph accepted by ComfyUI's API."""

    validate_workflow_contract(brief)

    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(brief, sort_keys=True),
                "reference_images": ["1", 0],
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["2", 0],
            },
        },
    }


def build_comfyui_assembly_workflow(
    brief: Mapping[str, Any],
    *,
    reference_filename: str,
    generated_filename: str,
    region: str,
    filename_prefix: str,
) -> dict[str, Any]:
    """Build a deterministic graph that preserves the reference outside a region."""

    validate_assembly_gate(brief)
    expected_region = ",".join(str(value) for value in brief["regions"][0]["bounds"])
    if region != expected_region:
        raise WorkflowContractError(
            f"assembly region must match approved brief bounds: {expected_region}"
        )

    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": generated_filename},
        },
        "3": {
            "class_type": "ReferenceRegionComposite",
            "inputs": {
                "reference_images": ["1", 0],
                "generated_images": ["2", 0],
                "region": region,
                "approval_manifest_json": json.dumps(brief, sort_keys=True),
            },
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["3", 0],
            },
        },
    }
