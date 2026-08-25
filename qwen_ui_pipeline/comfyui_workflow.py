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


def build_sticker_mask_assembly_workflow(
    *,
    reference_filename: str,
    artwork_filename: str,
    mask_filename: str,
    integration_filename: str,
    canvas_width: int,
    canvas_height: int,
    target_quad: str,
    cutline_width: int,
    contact_width: int,
    filename_prefix: str,
    artwork_inset: int = 0,
    mask_threshold: float = 0.5,
    color_transfer_method: str = "reinhard_lab",
    color_transfer_strength: float = 0.35,
) -> dict[str, Any]:
    """Build an opt-in, mask-owned sticker Assembly graph.

    The original rectangle Assembly builder remains unchanged.  This graph
    assigns the approved artwork, white cutline, and generated contact band to
    separate masks, then verifies both source and artwork ownership before the
    SaveImage node can run.
    """

    if canvas_width <= 0 or canvas_height <= 0:
        raise ValueError("Canvas dimensions must be positive")
    if min(artwork_inset, cutline_width, contact_width) < 0:
        raise ValueError("Mask widths must be non-negative")
    if color_transfer_method not in {"reinhard_lab", "mkl_lab", "histogram"}:
        raise ValueError("Unsupported ColorTransfer method")

    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": reference_filename}},
        "2": {"class_type": "LoadImage", "inputs": {"image": artwork_filename}},
        "3": {"class_type": "LoadImage", "inputs": {"image": mask_filename}},
        "4": {
            "class_type": "StickerPerspectiveWarp",
            "inputs": {
                "artwork_images": ["2", 0],
                "sticker_masks": ["3", 1],
                "canvas_width": canvas_width,
                "canvas_height": canvas_height,
                "target_quad": target_quad,
            },
        },
        "5": {
            "class_type": "StickerMaskBands",
            "inputs": {
                "sticker_masks": ["4", 1],
                "threshold": mask_threshold,
                "artwork_inset": artwork_inset,
                "cutline_width": cutline_width,
                "contact_width": contact_width,
            },
        },
        "6": {
            "class_type": "EmptyImage",
            "inputs": {
                "width": canvas_width,
                "height": canvas_height,
                "batch_size": 1,
                "color": 16777215,
            },
        },
        "7": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["1", 0],
                "source": ["6", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["5", 1],
            },
        },
        "8": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["7", 0],
                "source": ["4", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["5", 0],
            },
        },
        "9": {
            "class_type": "ColorTransfer",
            "inputs": {
                "image_target": ["14", 0],
                "image_ref": ["1", 0],
                "method": color_transfer_method,
                "source_stats": "per_frame",
                "strength": color_transfer_strength,
            },
        },
        "10": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["8", 0],
                "source": ["9", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["5", 2],
            },
        },
        "11": {
            "class_type": "MaskedReferenceFidelityGate",
            "inputs": {
                "reference_images": ["1", 0],
                "candidate_images": ["10", 0],
                "allowed_masks": ["5", 3],
                "mask_threshold": mask_threshold,
                "exact_outside_mask": True,
                "max_global_normalized_rmse": 1.0,
                "min_inside_changed_pixels": 1,
            },
        },
        "12": {
            "class_type": "ArtworkFidelityGate",
            "inputs": {
                "approved_images": ["4", 0],
                "candidate_images": ["11", 0],
                "approved_masks": ["5", 0],
                "candidate_masks": ["5", 0],
                "mask_threshold": mask_threshold,
                "exact_artwork": True,
                "max_masked_normalized_rmse": 0.0,
                "min_masked_ssim": 0.999,
                "min_edge_iou": 0.99,
                "min_silhouette_iou": 0.999,
                "max_centroid_drift_px": 0.5,
                "max_scale_drift": 0.001,
            },
        },
        "13": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["12", 0]},
        },
        "14": {
            "class_type": "LoadImage",
            "inputs": {"image": integration_filename},
        },
    }
