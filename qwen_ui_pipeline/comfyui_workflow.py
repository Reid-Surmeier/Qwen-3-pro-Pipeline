"""Deterministic ComfyUI API workflow construction."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Mapping


_UPSCALE_METHODS = {"nearest-exact", "bilinear", "area", "bicubic", "lanczos"}


def _coordinates(value: Any, *, length: int, label: str) -> tuple[int, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != length
        or any(not isinstance(item, int) or isinstance(item, bool) for item in value)
    ):
        raise ValueError(f"{label} must contain exactly {length} integer coordinates")
    coordinates = tuple(value)
    if any(item < 0 for item in coordinates):
        raise ValueError(f"{label} coordinates must be non-negative")
    if length == 4 and (coordinates[2] == 0 or coordinates[3] == 0):
        raise ValueError(f"{label} width and height must be positive")
    return coordinates


def _bounding_box(region: tuple[int, ...]) -> dict[str, int]:
    x, y, width, height = region
    return {"x": x, "y": y, "width": width, "height": height}


def _contains(outer: tuple[int, ...], inner: tuple[int, ...]) -> bool:
    outer_x, outer_y, outer_width, outer_height = outer
    inner_x, inner_y, inner_width, inner_height = inner
    return (
        inner_x >= outer_x
        and inner_y >= outer_y
        and inner_x + inner_width <= outer_x + outer_width
        and inner_y + inner_height <= outer_y + outer_height
    )


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
    preserve_reference_alpha: bool = False,
) -> dict[str, Any]:
    """Build a deterministic graph that preserves the reference outside a region."""

    composite_inputs: dict[str, Any] = {
        "reference_images": ["1", 0],
        "generated_images": ["2", 0],
        "region": region,
    }
    if preserve_reference_alpha:
        composite_inputs["reference_masks"] = ["1", 1]

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
            "inputs": composite_inputs,
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["3", 0],
            },
        },
    }


def build_comfyui_component_assembly_workflow(
    *,
    reference_filename: str,
    generated_filename: str,
    layout: Mapping[str, Any],
    filename_prefix: str,
    preserve_reference_alpha: bool = False,
) -> dict[str, Any]:
    """Build an opt-in graph that repairs a Qwen donor with source-owned components."""

    if not isinstance(layout, Mapping):
        raise ValueError("layout must be a JSON object")
    cleanplate = layout.get("cleanplate")
    if not isinstance(cleanplate, Mapping):
        raise ValueError("layout.cleanplate must be a JSON object")
    donor_normalization = layout.get("donor_normalization")
    if not isinstance(donor_normalization, Mapping):
        raise ValueError("layout.donor_normalization must be a JSON object")
    donor_width = _coordinates(
        [donor_normalization.get("width"), donor_normalization.get("height")],
        length=2,
        label="donor_normalization width and height",
    )
    if donor_width[0] == 0 or donor_width[1] == 0:
        raise ValueError("donor_normalization width and height must be positive")
    donor_method = donor_normalization.get("upscale_method", "nearest-exact")
    if donor_method not in _UPSCALE_METHODS:
        raise ValueError(
            "donor_normalization.upscale_method must be one of "
            + ", ".join(sorted(_UPSCALE_METHODS))
        )
    donor_crop = donor_normalization.get("crop", "disabled")
    if donor_crop not in {"disabled", "center"}:
        raise ValueError("donor_normalization.crop must be disabled or center")
    cleanplate_source = _coordinates(
        cleanplate.get("source_region"),
        length=4,
        label="cleanplate.source_region",
    )
    cleanplate_target = _coordinates(
        cleanplate.get("target_region"),
        length=4,
        label="cleanplate.target_region",
    )
    method = cleanplate.get("upscale_method", "nearest-exact")
    if method not in _UPSCALE_METHODS:
        raise ValueError(
            "cleanplate.upscale_method must be one of "
            + ", ".join(sorted(_UPSCALE_METHODS))
        )
    components = layout.get("components")
    if (
        not isinstance(components, Sequence)
        or isinstance(components, (str, bytes))
        or not components
    ):
        raise ValueError("layout.components must contain at least one component")
    final_edit_region = _coordinates(
        layout.get("final_edit_region"),
        length=4,
        label="final_edit_region",
    )
    if not _contains(final_edit_region, cleanplate_target):
        raise ValueError("cleanplate.target_region must fit inside final_edit_region")
    if not _contains((0, 0, *donor_width), final_edit_region):
        raise ValueError("final_edit_region must fit inside donor_normalization")
    if not _contains((0, 0, *donor_width), cleanplate_source):
        raise ValueError(
            "cleanplate.source_region must fit inside donor_normalization"
        )

    workflow: dict[str, Any] = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": generated_filename},
        },
        "3": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["2", 0],
                "upscale_method": donor_method,
                "width": donor_width[0],
                "height": donor_width[1],
                "crop": donor_crop,
            },
        },
        "4": {
            "class_type": "ImageCropV2",
            "inputs": {
                "image": ["3", 0],
                "crop_region": _bounding_box(cleanplate_source),
            },
        },
        "5": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["4", 0],
                "upscale_method": method,
                "width": cleanplate_target[2],
                "height": cleanplate_target[3],
                "crop": "disabled",
            },
        },
        "6": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["1", 0],
                "source": ["5", 0],
                "x": cleanplate_target[0],
                "y": cleanplate_target[1],
                "resize_source": False,
            },
        },
    }

    destination_node = "6"
    next_node = 7
    for index, component in enumerate(components):
        if not isinstance(component, Mapping):
            raise ValueError(f"components[{index}] must be a JSON object")
        source_region = _coordinates(
            component.get("source_region"),
            length=4,
            label=f"components[{index}].source_region",
        )
        target = _coordinates(
            component.get("target"),
            length=2,
            label=f"components[{index}].target",
        )
        target_region = (*target, source_region[2], source_region[3])
        if not _contains(final_edit_region, target_region):
            raise ValueError(
                f"components[{index}] target extent must fit inside final_edit_region"
            )
        crop_node = str(next_node)
        composite_node = str(next_node + 1)
        workflow[crop_node] = {
            "class_type": "ImageCropV2",
            "inputs": {
                "image": ["1", 0],
                "crop_region": _bounding_box(source_region),
            },
        }
        workflow[composite_node] = {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": [destination_node, 0],
                "source": [crop_node, 0],
                "x": target[0],
                "y": target[1],
                "resize_source": False,
            },
        }
        destination_node = composite_node
        next_node += 2

    final_node = str(next_node)
    save_node = str(next_node + 1)
    final_inputs: dict[str, Any] = {
        "reference_images": ["1", 0],
        "generated_images": [destination_node, 0],
        "region": ",".join(str(value) for value in final_edit_region),
    }
    if preserve_reference_alpha:
        final_inputs["reference_masks"] = ["1", 1]
    workflow[final_node] = {
        "class_type": "ReferenceRegionComposite",
        "inputs": final_inputs,
    }
    workflow[save_node] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": filename_prefix,
            "images": [final_node, 0],
        },
    }
    return workflow
