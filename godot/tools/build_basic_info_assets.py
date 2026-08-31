#!/usr/bin/env python3
"""Deterministic image-79 Basic Info Assembly; no provider request."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
OUTPUT = ROOT / "godot/assets/image-79/basic-info"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (0, 0, 484, 205)
BLUE = (54, 145, 190, 255)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append(
        {"path": str(path.relative_to(ROOT)), "sha256": digest(path), "size": list(image.size)}
    )
    return f"res://assets/image-79/basic-info/{name}"


def variants(image: Image.Image, stem: str, records: list[dict], disabled=False) -> dict:
    idle = image.convert("RGBA")
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1), outline=BLUE)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    values = [("idle", idle), ("hover", hover), ("pressed", pressed)]
    return {phase: save(value, f"{stem}-{phase}.png", records) for phase, value in values}


def control(
    control_id: str,
    control_type: str,
    rect: tuple[int, int, int, int],
    state_set: dict,
    gestures: list[str],
    actions: list[dict],
    states: list[str] | None = None,
    initial: str = "ready",
    **extra,
) -> dict:
    x, y, width, height = rect
    return {
        "id": control_id,
        "type": control_type,
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "interaction_phases": ["idle", "hover", "pressed"],
        "semantic_states": states or ["ready"],
        "initial_semantic_state": initial,
        "state_set": state_set,
        "gestures": gestures,
        "actions": actions,
        **extra,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reference = Image.open(SOURCE).convert("RGBA")
    window = reference.crop((0, 0, 484, 205))
    records: list[dict] = []

    expanded = save(window, "source-plate.png", records)
    # Purpose-built source-pixel Assembly: title chrome plus a separately
    # sourced bottom rule. Runtime never crops the expanded Window.
    minimized_image = Image.new("RGBA", (484, 28), (247, 247, 247, 255))
    minimized_image.paste(window.crop((0, 0, 484, 24)), (0, 0))
    minimized_image.paste(window.crop((0, 20, 484, 24)), (0, 24))
    minimized = save(minimized_image, "minimized-plate.png", records)

    controls: list[dict] = []
    for control_id, rect, action in [
        ("basic_info.close", (5, 5, 18, 18), "CloseWindow"),
        ("basic_info.minimize", (460, 6, 16, 16), "ToggleMinimized"),
    ]:
        x, y, w, h = rect
        states = variants(window.crop((x, y, x + w, y + h)), control_id.replace(".", "-"), records)
        controls.append(
            control(
                control_id,
                "Button",
                rect,
                {"ready": states},
                ["Activate"],
                [{"gesture": "Activate", "action": action}],
            )
        )

    destination_rows = [
        ("status", (356, 42, 48, 26), "status", True),
        ("option", (418, 42, 48, 26), "options", True),
        ("items", (356, 83, 48, 26), "inventory", True),
        ("equip", (418, 83, 48, 26), "equipment_items", True),
        ("skill", (356, 124, 48, 26), "skill_tree", True),
        ("map", (418, 124, 48, 26), "map", False),
        ("chat", (356, 165, 48, 26), "chat_room", False),
        ("friend", (418, 165, 48, 26), "friends", False),
    ]
    for name, rect, target, available in destination_rows:
        x, y, w, h = rect
        crop = window.crop((x, y, x + w, y + h))
        variants_map = variants(crop, f"destination-{name}", records)
        semantic = "ready" if available else "disabled"
        controls.append(
            control(
                f"basic_info.destination.{name}",
                "Button",
                rect,
                {semantic: variants_map},
                ["Activate"],
                [{"gesture": "Activate", "action": "OpenWindow"}],
                [semantic],
                semantic,
                value={"target_window": target},
            )
        )

    meter_rows = [
        ("hp", (189, 37, 151, 15), 0, 1109, 1109, 151),
        ("sp", (189, 74, 151, 14), 0, 613, 601, 151),
        ("base", (146, 131, 184, 11), 0, 99, 60, 184),
        ("job", (146, 148, 184, 11), 0, 50, 47, 184),
    ]
    for name, rect, minimum, maximum, current, pixels in meter_rows:
        x, y, w, h = rect
        crop = window.crop((x, y, x + w, y + h))
        meter_states = variants(crop, f"meter-{name}", records)
        controls.append(
            control(
                f"basic_info.meter.{name}",
                "Meter",
                rect,
                {"ready": meter_states},
                [],
                [],
                value={
                    "minimum": minimum,
                    "maximum": maximum,
                    "current": current,
                    "fill_axis": "horizontal",
                    "fill_pixels": pixels,
                },
            )
        )

    display_facts = [
        {"id": "name", "text": "SakumaRiri", "geometry": [16, 37, 132, 23]},
        {"id": "class", "text": "Acolyte", "geometry": [16, 61, 92, 22]},
        {"id": "hp-label", "text": "HP", "geometry": [163, 55, 24, 20]},
        {"id": "hp-value", "text": "1109 / 1109", "geometry": [216, 55, 124, 22]},
        {"id": "sp-label", "text": "SP", "geometry": [163, 89, 24, 20]},
        {"id": "sp-value", "text": "601 / 613", "geometry": [216, 89, 112, 22]},
        {"id": "base-level", "text": "Base Lv. 60", "geometry": [28, 126, 112, 20]},
        {"id": "job-level", "text": "Job Lv. 47", "geometry": [28, 145, 112, 20]},
        {"id": "weight", "text": "Weight : 874 / 2430", "geometry": [8, 177, 171, 22]},
        {"id": "zeny", "text": "Zeny : 321,584,092", "geometry": [178, 177, 169, 22]},
    ]
    window_spec = {
        "id": "basic_info",
        "evidence_policy": {"issue": 132},
        "geometry": {"x": 0, "y": 0, "width": 484, "height": 205},
        "drag_geometry": {"x": 24, "y": 0, "width": 434, "height": 24},
        "plates": {"expanded": expanded, "minimized": minimized},
        "backing_color": "#00000000",
        "minimized_height": 28,
        "minimized_controls": ["basic_info.minimize", "basic_info.close"],
        "display_facts": display_facts,
        "gestures": ["Drag", "KeyCommand"],
        "actions": [
            {"gesture": "Drag", "action": "MoveWindow"},
            {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
        ],
        "controls": controls,
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [
        entry for entry in manifest["windows"] if entry.get("id") != "basic_info"
    ] + [window_spec]
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1,
        "issue": 132,
        "provider_requests": 0,
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": digest(SOURCE),
            "window_rect": list(WINDOW),
        },
        "assembly": "deterministic source-pixel crops and source-palette State Sets",
        "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        json.dumps(
            {
                "window": "basic_info",
                "controls": len(controls),
                "assets": len(records),
                "provider_requests": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
