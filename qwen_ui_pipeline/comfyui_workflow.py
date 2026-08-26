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


def build_comfyui_mask_assembly_workflow(
    *,
    reference_filename: str,
    generated_filename: str,
    mask_filename: str,
    filename_prefix: str,
    mask_threshold: float = 0.5,
    cutline_width: int = 0,
    contact_width: int = 0,
) -> dict[str, Any]:
    """Build an opt-in mask-owned Assembly graph with fail-closed checks."""

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
            "class_type": "LoadImage",
            "inputs": {"image": mask_filename},
        },
        "4": {
            "class_type": "ImageToMask",
            "inputs": {"image": ["3", 0], "channel": "red"},
        },
        "5": {
            "class_type": "StickerMaskBands",
            "inputs": {
                "sticker_masks": ["4", 0],
                "threshold": mask_threshold,
                "artwork_inset": 0,
                "cutline_width": cutline_width,
                "contact_width": contact_width,
            },
        },
        "6": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["1", 0],
                "source": ["2", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["5", 0],
            },
        },
        "7": {
            "class_type": "MaskedReferenceFidelityGate",
            "inputs": {
                "reference_images": ["1", 0],
                "candidate_images": ["6", 0],
                "allowed_masks": ["5", 3],
                "mask_threshold": 0.5,
                "exact_outside_mask": True,
                "max_global_normalized_rmse": 1.0,
                "min_inside_changed_pixels": 1,
            },
        },
        "8": {
            "class_type": "ArtworkFidelityGate",
            "inputs": {
                "approved_images": ["2", 0],
                "candidate_images": ["7", 0],
                "approved_masks": ["5", 0],
                "candidate_masks": ["5", 0],
                "mask_threshold": 0.5,
                "exact_artwork": True,
                "max_masked_normalized_rmse": 0.0,
                "min_masked_ssim": 0.999,
                "min_edge_iou": 0.99,
                # Assembly reuses the approved mask, so candidate geometry is
                # fixed rather than independently inferred. Geometry gates are
                # intentionally disabled here instead of reporting a tautology.
                "min_silhouette_iou": 0.0,
                "max_centroid_drift_px": 16384.0,
                "max_scale_drift": 1.0,
            },
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["8", 0],
            },
        },
    }


def build_comfyui_mask_reference_workflow(
    brief: Mapping[str, Any],
    *,
    reference_filename: str,
    mask_guide_filename: str,
    filename_prefix: str,
) -> dict[str, Any]:
    """Build a Qwen graph where a mask is an RGB guide, not an inpaint input."""

    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": mask_guide_filename},
        },
        "3": {
            "class_type": "BatchImagesNode",
            "inputs": {
                "images.image0": ["1", 0],
                "images.image1": ["2", 0],
            },
        },
        "4": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(brief, sort_keys=True),
                "reference_images": ["3", 0],
            },
        },
        "5": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["4", 0],
            },
        },
        "6": {
            "class_type": "SaveText",
            "inputs": {
                "text": ["4", 1],
                "filename_prefix": f"{filename_prefix}-metadata",
                "format": "json",
            },
        },
    }
