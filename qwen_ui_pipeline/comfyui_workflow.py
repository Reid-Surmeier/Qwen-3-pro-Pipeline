"""Deterministic ComfyUI API workflow construction."""

from __future__ import annotations

import json
from typing import Any, Mapping


def build_comfyui_api_workflow(
    brief: Mapping[str, Any],
    *,
    reference_filename: str,
    filename_prefix: str,
) -> dict[str, Any]:
    """Build the smallest reference-edit graph accepted by ComfyUI's API."""

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
    *,
    reference_filename: str,
    generated_filename: str,
    region: str,
    filename_prefix: str,
) -> dict[str, Any]:
    """Build a deterministic graph that preserves the reference outside a region."""

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


def build_comfyui_component_extraction_workflow(
    *,
    reference_filename: str,
    components: Mapping[str, tuple[int, int, int, int]],
    filename_prefix: str,
) -> dict[str, Any]:
    """Crop exact reference components without asking an image model to redraw them."""

    workflow: dict[str, Any] = {
        "1": {"class_type": "LoadImage", "inputs": {"image": reference_filename}}
    }
    next_node_id = 2
    for name, (x, y, width, height) in components.items():
        if min(x, y, width, height) < 0 or width == 0 or height == 0:
            raise ValueError(f"Invalid component rectangle for {name}")
        crop_id = str(next_node_id)
        save_id = str(next_node_id + 1)
        workflow[crop_id] = {
            "class_type": "ImageCrop",
            "inputs": {
                "image": ["1", 0],
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
        }
        workflow[save_id] = {
            "class_type": "SaveImage",
            "inputs": {
                "images": [crop_id, 0],
                "filename_prefix": f"{filename_prefix}/{name}",
            },
        }
        next_node_id += 2
    return workflow
