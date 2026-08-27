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


def build_partner_text_workflow(
    *,
    filename_prefix: str,
    provider: str,
    prompt: str,
) -> dict[str, Any]:
    """Build a portable text-to-image graph with visible preview and save nodes."""

    if provider not in {"openrouter", "alibaba"}:
        raise ValueError("Partner text workflow provider must be openrouter or alibaba")
    return {
        "1": {
            "class_type": "QwenImage3TextToImage",
            "inputs": {
                "provider": provider,
                "model": "qwen-image-3.0-pro",
                "prompt": prompt,
                "negative_prompt": "",
                "width": 1024,
                "height": 1024,
                "count": 1,
                "seed": 42,
                "prompt_extend": False,
                "watermark": False,
            },
        },
        "2": {
            "class_type": "PreviewImage",
            "inputs": {"images": ["1", 0]},
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["1", 0],
            },
        },
    }


def build_partner_edit_workflow(
    *,
    reference_filenames: list[str],
    filename_prefix: str,
    provider: str,
    prompt: str,
) -> dict[str, Any]:
    """Build a portable three-reference graph with visible source previews."""

    if len(reference_filenames) != 3:
        raise ValueError("Partner edit workflow evidence requires exactly three references")
    if provider not in {"openrouter", "alibaba"}:
        raise ValueError("Partner edit workflow provider must be openrouter or alibaba")

    workflow: dict[str, Any] = {
        str(index): {
            "class_type": "LoadImage",
            "inputs": {"image": filename},
        }
        for index, filename in enumerate(reference_filenames, start=1)
    }
    workflow["4"] = {
        "class_type": "QwenImage3Edit",
        "inputs": {
            "provider": provider,
            "model": "qwen-image-3.0-pro",
            "prompt": prompt,
            "negative_prompt": "",
            "size_mode": "custom",
            "width": 1024,
            "height": 1024,
            "count": 1,
            "seed": 42,
            "prompt_extend": False,
            "watermark": False,
            "image_1": ["1", 0],
            "image_2": ["2", 0],
            "image_3": ["3", 0],
        },
    }
    for node_id, load_id in zip(("5", "6", "7"), ("1", "2", "3")):
        workflow[node_id] = {
            "class_type": "PreviewImage",
            "inputs": {"images": [load_id, 0]},
        }
    workflow["8"] = {
        "class_type": "PreviewImage",
        "inputs": {"images": ["4", 0]},
    }
    workflow["9"] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": filename_prefix,
            "images": ["4", 0],
        },
    }
    return workflow
