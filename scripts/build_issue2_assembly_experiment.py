"""Build the no-cost ComfyUI Assembly comparison for Issue #2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REFERENCE_FILENAME = "issue2-useful-edit-intel-source-v001.png"
BASELINE_DONOR_FILENAME = "baseline-selected-donor-v001.png"
GUIDED_DONOR_FILENAME = "guided-selected-donor-v001.png"
GREEN_KEY_FILENAME = "issue2-useful-edit-green-key-v001.png"
SOURCE_REGION_FILENAME = "issue2-useful-edit-source-region-v001.png"
TARGET_REGION_FILENAME = "issue2-useful-edit-target-region-v001.png"
SOURCE_E_FILENAME = "issue2-useful-edit-source-e-v001.png"


def _fidelity_inputs(candidate_node: str, mask_node: str) -> dict[str, Any]:
    return {
        "reference_images": ["1", 0],
        "candidate_images": [candidate_node, 0],
        "allowed_masks": [mask_node, 0],
        "mask_threshold": 0.5,
        "exact_outside_mask": True,
        "max_global_normalized_rmse": 1.0,
        "min_inside_changed_pixels": 1,
    }


def build_workflow() -> dict[str, Any]:
    """Compare exact-green ownership with a four-pixel tapered union."""

    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": REFERENCE_FILENAME}},
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": BASELINE_DONOR_FILENAME},
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": GUIDED_DONOR_FILENAME},
        },
        "4": {
            "class_type": "BatchImagesNode",
            "inputs": {"images.image0": ["2", 0], "images.image1": ["3", 0]},
        },
        "5": {
            "class_type": "SolidMask",
            "inputs": {"value": 1.0, "width": 1024, "height": 684},
        },
        "6": {
            "class_type": "StickerPerspectiveWarp",
            "inputs": {
                "artwork_images": ["4", 0],
                "sticker_masks": ["5", 0],
                "canvas_width": 1136,
                "canvas_height": 800,
                "target_quad": "0,0,1135,0,1135,799,0,799",
            },
        },
        "7": {"class_type": "LoadImage", "inputs": {"image": GREEN_KEY_FILENAME}},
        "8": {
            "class_type": "ImageColorToMask",
            "inputs": {"image": ["7", 0], "color": 65280},
        },
        "9": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["23", 0],
                "source": ["6", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["8", 0],
            },
        },
        "10": {
            "class_type": "MaskedReferenceFidelityGate",
            "inputs": _fidelity_inputs("9", "8"),
        },
        "11": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["10", 0],
                "filename_prefix": "issue-2/useful-edit/assembly/exact-green-v002",
            },
        },
        "12": {
            "class_type": "SaveText",
            "inputs": {
                "text": ["10", 1],
                "filename_prefix": "issue-2/useful-edit/assembly/exact-green-v002-fidelity",
                "format": "json",
            },
        },
        "13": {
            "class_type": "LoadImage",
            "inputs": {"image": SOURCE_REGION_FILENAME},
        },
        "14": {
            "class_type": "ImageToMask",
            "inputs": {"image": ["13", 0], "channel": "red"},
        },
        "15": {
            "class_type": "LoadImage",
            "inputs": {"image": TARGET_REGION_FILENAME},
        },
        "16": {
            "class_type": "ImageToMask",
            "inputs": {"image": ["15", 0], "channel": "red"},
        },
        "17": {
            "class_type": "MaskComposite",
            "inputs": {
                "destination": ["14", 0],
                "source": ["16", 0],
                "x": 0,
                "y": 0,
                "operation": "or",
            },
        },
        "18": {
            "class_type": "GrowMask",
            "inputs": {"mask": ["17", 0], "expand": 4, "tapered_corners": True},
        },
        "19": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["23", 0],
                "source": ["6", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["18", 0],
            },
        },
        "20": {
            "class_type": "MaskedReferenceFidelityGate",
            "inputs": _fidelity_inputs("19", "18"),
        },
        "21": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["20", 0],
                "filename_prefix": "issue-2/useful-edit/assembly/grown-union-v002",
            },
        },
        "22": {
            "class_type": "SaveText",
            "inputs": {
                "text": ["20", 1],
                "filename_prefix": "issue-2/useful-edit/assembly/grown-union-v002-fidelity",
                "format": "json",
            },
        },
        "23": {
            "class_type": "RepeatImageBatch",
            "inputs": {"image": ["1", 0], "amount": 2},
        },
    }


def build_feather_workflow() -> dict[str, Any]:
    """Blend donor texture inside an eight-pixel bounded ownership region."""

    previous = build_workflow()
    workflow = {
        node_id: previous[node_id]
        for node_id in ("1", "2", "3", "4", "5", "6", "13", "14", "15", "16", "17", "23")
    }
    workflow.update(
        {
            "24": {
                "class_type": "GrowMask",
                "inputs": {
                    "mask": ["17", 0],
                    "expand": 8,
                    "tapered_corners": True,
                },
            },
            "25": {
                "class_type": "FeatherMask",
                "inputs": {
                    "mask": ["24", 0],
                    "left": 8,
                    "top": 8,
                    "right": 8,
                    "bottom": 8,
                },
            },
            "26": {
                "class_type": "ImageCompositeMasked",
                "inputs": {
                    "destination": ["23", 0],
                    "source": ["6", 0],
                    "x": 0,
                    "y": 0,
                    "resize_source": False,
                    "mask": ["25", 0],
                },
            },
            "27": {
                "class_type": "MaskedReferenceFidelityGate",
                "inputs": _fidelity_inputs("26", "24"),
            },
            "28": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["27", 0],
                    "filename_prefix": "issue-2/useful-edit/assembly/feathered-union-v003",
                },
            },
            "29": {
                "class_type": "SaveText",
                "inputs": {
                    "text": ["27", 1],
                    "filename_prefix": "issue-2/useful-edit/assembly/feathered-union-v003-fidelity",
                    "format": "json",
                },
            },
        }
    )
    return workflow


def build_source_blur_workflow() -> dict[str, Any]:
    """Use source-derived blur for removal and the guided donor for placement."""

    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": REFERENCE_FILENAME}},
        "2": {"class_type": "LoadImage", "inputs": {"image": GUIDED_DONOR_FILENAME}},
        "3": {
            "class_type": "SolidMask",
            "inputs": {"value": 1.0, "width": 1024, "height": 684},
        },
        "4": {
            "class_type": "StickerPerspectiveWarp",
            "inputs": {
                "artwork_images": ["2", 0],
                "sticker_masks": ["3", 0],
                "canvas_width": 1136,
                "canvas_height": 800,
                "target_quad": "0,0,1135,0,1135,799,0,799",
            },
        },
        "5": {"class_type": "LoadImage", "inputs": {"image": SOURCE_REGION_FILENAME}},
        "6": {"class_type": "ImageToMask", "inputs": {"image": ["5", 0], "channel": "red"}},
        "7": {
            "class_type": "GrowMask",
            "inputs": {"mask": ["6", 0], "expand": 8, "tapered_corners": True},
        },
        "8": {
            "class_type": "FeatherMask",
            "inputs": {"mask": ["7", 0], "left": 8, "top": 8, "right": 8, "bottom": 8},
        },
        "9": {
            "class_type": "ImageBlur",
            "inputs": {"image": ["1", 0], "blur_radius": 31, "sigma": 10.0},
        },
        "10": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["1", 0],
                "source": ["9", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["8", 0],
            },
        },
        "11": {"class_type": "LoadImage", "inputs": {"image": TARGET_REGION_FILENAME}},
        "12": {"class_type": "ImageToMask", "inputs": {"image": ["11", 0], "channel": "red"}},
        "13": {
            "class_type": "GrowMask",
            "inputs": {"mask": ["12", 0], "expand": 4, "tapered_corners": True},
        },
        "14": {
            "class_type": "FeatherMask",
            "inputs": {"mask": ["13", 0], "left": 4, "top": 4, "right": 4, "bottom": 4},
        },
        "15": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["10", 0],
                "source": ["4", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
                "mask": ["14", 0],
            },
        },
        "16": {
            "class_type": "MaskComposite",
            "inputs": {
                "destination": ["7", 0],
                "source": ["13", 0],
                "x": 0,
                "y": 0,
                "operation": "or",
            },
        },
        "17": {
            "class_type": "MaskedReferenceFidelityGate",
            "inputs": _fidelity_inputs("15", "16"),
        },
        "18": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["17", 0],
                "filename_prefix": "issue-2/useful-edit/assembly/source-blur-guided-v004",
            },
        },
        "19": {
            "class_type": "SaveText",
            "inputs": {
                "text": ["17", 1],
                "filename_prefix": "issue-2/useful-edit/assembly/source-blur-guided-v004-fidelity",
                "format": "json",
            },
        },
    }


def build_precise_workflow() -> dict[str, Any]:
    """Restrict donor replacement to the source glyph and target region."""

    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": REFERENCE_FILENAME}},
        "2": {"class_type": "LoadImage", "inputs": {"image": GUIDED_DONOR_FILENAME}},
        "3": {"class_type": "SolidMask", "inputs": {"value": 1.0, "width": 1024, "height": 684}},
        "4": {
            "class_type": "StickerPerspectiveWarp",
            "inputs": {
                "artwork_images": ["2", 0], "sticker_masks": ["3", 0],
                "canvas_width": 1136, "canvas_height": 800,
                "target_quad": "0,0,1135,0,1135,799,0,799",
            },
        },
        "5": {"class_type": "LoadImage", "inputs": {"image": SOURCE_E_FILENAME}},
        "6": {"class_type": "ImageToMask", "inputs": {"image": ["5", 0], "channel": "red"}},
        "7": {"class_type": "GrowMask", "inputs": {"mask": ["6", 0], "expand": 4, "tapered_corners": True}},
        "8": {"class_type": "FeatherMask", "inputs": {"mask": ["7", 0], "left": 4, "top": 4, "right": 4, "bottom": 4}},
        "9": {"class_type": "LoadImage", "inputs": {"image": TARGET_REGION_FILENAME}},
        "10": {"class_type": "ImageToMask", "inputs": {"image": ["9", 0], "channel": "red"}},
        "11": {"class_type": "GrowMask", "inputs": {"mask": ["10", 0], "expand": 4, "tapered_corners": True}},
        "12": {"class_type": "FeatherMask", "inputs": {"mask": ["11", 0], "left": 4, "top": 4, "right": 4, "bottom": 4}},
        "13": {
            "class_type": "ImageCompositeMasked",
            "inputs": {"destination": ["1", 0], "source": ["4", 0], "x": 0, "y": 0, "resize_source": False, "mask": ["8", 0]},
        },
        "14": {
            "class_type": "ImageCompositeMasked",
            "inputs": {"destination": ["13", 0], "source": ["4", 0], "x": 0, "y": 0, "resize_source": False, "mask": ["12", 0]},
        },
        "15": {"class_type": "MaskComposite", "inputs": {"destination": ["7", 0], "source": ["11", 0], "x": 0, "y": 0, "operation": "or"}},
        "16": {"class_type": "MaskedReferenceFidelityGate", "inputs": _fidelity_inputs("14", "15")},
        "17": {"class_type": "SaveImage", "inputs": {"images": ["16", 0], "filename_prefix": "issue-2/useful-edit/assembly/precise-guided-v005"}},
        "18": {"class_type": "SaveText", "inputs": {"text": ["16", 1], "filename_prefix": "issue-2/useful-edit/assembly/precise-guided-v005-fidelity", "format": "json"}},
    }


def build_plan() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "issue": 2,
        "revision": 2,
        "classification": "comparison evidence plan",
        "paid_generation_outputs": 0,
        "donor_order": [
            {
                "condition": "baseline",
                "candidate": 2,
                "path": "artifacts/issue-2/useful-edit/qwen/results/baseline-v001_00002_.png",
                "reason": "completed the requested edit and retained lowercase source lettering more closely",
            },
            {
                "condition": "guided",
                "candidate": 1,
                "path": "artifacts/issue-2/useful-edit/qwen/results/guided-v001_00001_.png",
                "reason": "completed the requested edit; guided candidate 2 left the source e in place",
            },
        ],
        "alignment": {
            "node": "StickerPerspectiveWarp",
            "source_size": [1024, 684],
            "canvas_size": [1136, 800],
            "target_quad": [0, 0, 1135, 0, 1135, 799, 0, 799],
            "limitation": "planar whole-canvas registration; not curved-surface displacement",
        },
        "mask_options": [
            {
                "name": "exact-green",
                "nodes": ["RepeatImageBatch", "ImageColorToMask", "ImageCompositeMasked"],
                "settings": {"green_integer": 65280},
            },
            {
                "name": "grown-union",
                "nodes": ["ImageToMask", "MaskComposite", "GrowMask", "ImageCompositeMasked"],
                "settings": {"operation": "or", "expand": 4, "tapered_corners": True},
            },
        ],
        "acceptance": {
            "outside_allowed_mask_changed_pixels": 0,
            "visual_review": "compare source removal, white target e, and boundary seams",
            "human_visual_approval": "pending",
        },
        "rejected_predecessor": {
            "revision": 1,
            "reason": "ImageCompositeMasked reduced the donor batch because the Reference Screen destination was not repeated to the same batch size",
            "prompt_id": "49c1f29a-c6ae-425c-a455-f064316d0199",
        },
    }


def build_feather_plan() -> dict[str, Any]:
    plan = build_plan()
    plan["revision"] = 3
    plan["selected_experiment"] = {
        "name": "feathered-union",
        "nodes": [
            "RepeatImageBatch",
            "MaskComposite",
            "GrowMask",
            "FeatherMask",
            "ImageCompositeMasked",
            "MaskedReferenceFidelityGate",
        ],
        "settings": {
            "operation": "or",
            "allowed_mask_expand": 8,
            "tapered_corners": True,
            "feather": {"left": 8, "top": 8, "right": 8, "bottom": 8},
        },
        "success_criterion": (
            "reduce the visible circular patch edge while retaining zero changed "
            "pixels outside the expanded allowed mask"
        ),
    }
    plan["rejected_predecessor"] = {
        "revision": 2,
        "reason": (
            "exact-green and four-pixel grown masks passed exact outside-mask "
            "fidelity but left visually obvious hard circular patch edges"
        ),
        "prompt_id": "c52b258f-f458-4e89-894a-4c012084b2a9",
    }
    return plan


def build_source_blur_plan() -> dict[str, Any]:
    plan = build_feather_plan()
    plan["revision"] = 4
    plan["selected_experiment"] = {
        "name": "source-blur-guided",
        "donor": "guided candidate 1",
        "nodes": [
            "ImageBlur",
            "GrowMask",
            "FeatherMask",
            "StickerPerspectiveWarp",
            "ImageCompositeMasked",
            "MaskComposite",
            "MaskedReferenceFidelityGate",
        ],
        "reason": (
            "derive the removal fill from the authoritative source while using "
            "the Qwen guided donor only for the relocated white e"
        ),
    }
    plan["rejected_predecessor"] = {
        "revision": 3,
        "reason": "feathering reduced the edge but retained the donor's mismatched pale source patch",
        "prompt_id": "0d493a16-4b8e-471a-bf72-f8b55440837d",
    }
    return plan


def build_precise_plan() -> dict[str, Any]:
    plan = build_source_blur_plan()
    plan["revision"] = 5
    plan["selected_experiment"] = {
        "name": "precise-guided",
        "donor": "guided candidate 1",
        "nodes": [
            "GrowMask",
            "FeatherMask",
            "StickerPerspectiveWarp",
            "ImageCompositeMasked",
            "MaskComposite",
            "MaskedReferenceFidelityGate",
        ],
        "reason": (
            "limit source replacement to the selected source glyph while "
            "retaining the guided donor for the relocated white e"
        ),
        "result": {
            "outside_allowed_mask_changed_pixels": 0,
            "allowed_mask_pixels": 6913,
            "human_visual_approval": "pending",
            "limitation": "a donor/source texture patch remains visible",
        },
    }
    plan["rejected_predecessor"] = {
        "revision": 4,
        "reason": "source-derived blur produced a visible blue-gray smudge",
        "prompt_id": "0c20bc4d-05a7-4ef6-96f3-755a8e2e7fce",
    }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    files = {
        "workflow-v002.api.json": build_workflow(),
        "experiment-plan-v002.json": build_plan(),
        "workflow-v003-feather.api.json": build_feather_workflow(),
        "experiment-plan-v003.json": build_feather_plan(),
        "workflow-v004-final.api.json": build_source_blur_workflow(),
        "experiment-plan-v004.json": build_source_blur_plan(),
        "workflow-v005-precise.api.json": build_precise_workflow(),
        "experiment-plan-v005.json": build_precise_plan(),
    }
    for filename, value in files.items():
        (args.output_directory / filename).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
