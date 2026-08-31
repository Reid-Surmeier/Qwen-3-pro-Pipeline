#!/usr/bin/env python3
"""Bind all 239 source-inventory controls to the production Assembly."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
SPEC_PATH = ROOT / "godot/data/image-79-control-spec.json"
OUTPUT_PATH = ROOT / "godot/data/image-79-assembly-manifest.json"
REFERENCE_SHA256 = "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f"


def _rect(geometry: dict, offset_x: float = 0, offset_y: float = 0) -> list[float]:
    return [
        offset_x + float(geometry["x"]),
        offset_y + float(geometry["y"]),
        float(geometry["width"]),
        float(geometry["height"]),
    ]


def _intersection_coverage(source: list[float], candidate: list[float]) -> float:
    sx, sy, sw, sh = source
    cx, cy, cw, ch = candidate
    width = max(0.0, min(sx + sw, cx + cw) - max(sx, cx))
    height = max(0.0, min(sy + sh, cy + ch) - max(sy, cy))
    area = max(1.0, sw * sh)
    return width * height / area


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "unlabelled"


def _candidates(window: dict) -> list[dict]:
    origin = window["geometry"]
    result: list[dict] = []
    for control in window["controls"]:
        control_rect = _rect(control["geometry"], origin["x"], origin["y"])
        result.append(
            {
                "owner_kind": "control",
                "production_owner": control["id"],
                "control_id": control["id"],
                "rect": control_rect,
            }
        )
        for surface_id, surface in control.get("surfaces", {}).items():
            if "geometry" not in surface:
                continue
            surface_rect = _rect(
                surface["geometry"], control_rect[0], control_rect[1]
            )
            result.append(
                {
                    "owner_kind": "surface",
                    "production_owner": f'{control["id"]}#{surface_id}',
                    "control_id": control["id"],
                    "surface_id": surface_id,
                    "rect": surface_rect,
                }
            )
    return result


def _owner(entry: dict, window: dict, candidates: list[dict]) -> dict:
    if entry["type"] == "title drag":
        return {
            "owner_kind": "window_drag",
            "production_owner": f'{window["id"]}.title_drag',
        }
    if entry.get("label") == "chat settings (icon)":
        return {
            "owner_kind": "baked_visual",
            "production_owner": "chat_room.source_plate.unidentified_icon",
        }

    ranked = []
    for candidate in candidates:
        coverage = _intersection_coverage(entry["rect"], candidate["rect"])
        if coverage >= 0.45:
            ranked.append(
                (
                    coverage,
                    -(candidate["rect"][2] * candidate["rect"][3]),
                    candidate,
                )
            )
    if ranked:
        return max(ranked, key=lambda value: (value[0], value[1]))[2]
    return {
        "owner_kind": "state_surface",
        "production_owner": f'{window["id"]}.source_state',
    }


def build_manifest() -> dict:
    inventory = json.loads(INVENTORY_PATH.read_text())
    control_spec = json.loads(SPEC_PATH.read_text())
    windows = {window["id"]: window for window in control_spec["windows"]}
    counters: dict[str, int] = {window_id: 0 for window_id in windows}
    controls = []
    for source_index, entry in enumerate(inventory["controls"]):
        window_id = entry["window"].replace("-", "_")
        window = windows[window_id]
        sequence = counters[window_id]
        counters[window_id] += 1
        owner = _owner(entry, window, _candidates(window))
        source_control = {
            "source_index": source_index,
            "stable_id": (
                f"source.{window_id}.{sequence:03d}.{_slug(entry['type'])}"
            ),
            "window_id": window_id,
            "source_type": entry["type"],
            "source_label": entry.get("label"),
            "source_rect": entry["rect"],
            **{key: value for key, value in owner.items() if key != "rect"},
        }
        controls.append(source_control)

    return {
        "schema_version": 1,
        "issue": 136,
        "reference_sha256": REFERENCE_SHA256,
        "source_inventory_sha256": hashlib.sha256(INVENTORY_PATH.read_bytes()).hexdigest(),
        "viewport": [1536, 1024],
        "window_ids": list(windows),
        "source_control_count": len(controls),
        "source_counts_by_window": counters,
        "generation_requests": 0,
        "controls": controls,
    }


def main() -> None:
    manifest = build_manifest()
    OUTPUT_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(OUTPUT_PATH), "controls": len(manifest["controls"])}))


if __name__ == "__main__":
    main()
