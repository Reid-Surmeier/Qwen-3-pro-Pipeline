#!/usr/bin/env python3
"""Deterministic image-79 Basic Info Assembly; no provider request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-hud-fullscreen/reference-native.png"
OUTPUT = ROOT / "godot/assets/image-79/basic-info"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (0, 0, 656, 286)
BLUE = (54, 145, 190, 255)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/basic-info/{name}"


def variants(image: Image.Image, stem: str, records: list[dict], disabled=False) -> dict:
    idle = image.convert("RGBA")
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=BLUE)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    values = [("idle", idle), ("hover", hover), ("pressed", pressed)]
    return {phase: save(value, f"{stem}-{phase}.png", records)
            for phase, value in values}


def control(control_id: str, control_type: str, rect: tuple[int, int, int, int],
            state_set: dict, gestures: list[str], actions: list[dict],
            states: list[str] | None = None, initial: str = "ready", **extra) -> dict:
    x, y, width, height = rect
    return {"id": control_id, "type": control_type,
            "geometry": {"x": x, "y": y, "width": width, "height": height},
            "interaction_phases": ["idle", "hover", "pressed"],
            "semantic_states": states or ["ready"],
            "initial_semantic_state": initial, "state_set": state_set,
            "gestures": gestures, "actions": actions, **extra}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reference = Image.open(SOURCE).convert("RGBA")
    window = reference.crop((0, 0, 656, 286))
    records: list[dict] = []

    expanded = save(window, "source-plate.png", records)
    # Separate source-pixel Assembly: full title chrome plus a source-owned
    # bottom rule. Runtime never crops the expanded Window.
    minimized_image = window.crop((0, 0, 656, 48))
    minimized = save(minimized_image, "minimized-plate.png", records)

    controls: list[dict] = []
    for control_id, rect, action in [
        ("basic_info.minimize", (14, 12, 30, 30), "ToggleMinimized"),
        ("basic_info.close", (612, 12, 30, 30), "CloseWindow"),
    ]:
        x, y, w, h = rect
        states = variants(window.crop((x, y, x + w, y + h)),
                          control_id.replace(".", "-"), records)
        controls.append(control(control_id, "Button", rect, {"ready": states},
                                ["Activate"], [{"gesture": "Activate", "action": action}]))

    destination_rows = [
        ("status", (484, 56, 78, 46), "status", True),
        ("option", (572, 56, 84, 46), "options", True),
        ("items", (484, 111, 78, 46), "inventory", True),
        ("equip", (572, 111, 84, 46), "equipment_items", True),
        ("skill", (484, 166, 78, 46), "skill_tree", True),
        ("map", (572, 166, 84, 46), "map", False),
        ("chat", (484, 221, 78, 46), "chat_room", False),
        ("friend", (572, 221, 84, 46), "friends", False),
    ]
    for name, rect, target, available in destination_rows:
        x, y, w, h = rect
        crop = window.crop((x, y, x + w, y + h))
        variants_map = variants(crop, f"destination-{name}", records)
        semantic = "ready" if available else "disabled"
        controls.append(control(
            f"basic_info.destination.{name}", "Button", rect,
            {semantic: variants_map}, ["Activate"],
            [{"gesture": "Activate",
              "action": "OpenWindow" if available else "UnavailableDestination"}],
            [semantic], semantic, value={"target_window": target}))

    meter_rows = [
        ("hp", (266, 59, 194, 23), 0, 1109, 1092, 194),
        ("sp", (265, 106, 195, 23), 0, 613, 601, 195),
        ("base", (208, 187, 232, 21), 0, 99, 60, 232),
        ("job", (208, 214, 232, 20), 0, 50, 47, 232),
    ]
    for name, rect, minimum, maximum, current, pixels in meter_rows:
        x, y, w, h = rect
        crop = window.crop((x, y, x + w, y + h))
        meter_states = variants(crop, f"meter-{name}", records)
        controls.append(control(
            f"basic_info.meter.{name}", "Meter", rect,
            {"ready": meter_states}, [], [], value={
                "minimum": minimum, "maximum": maximum, "current": current,
                "fill_axis": "horizontal", "fill_pixels": pixels}))

    display_facts = [
        {"id": "name", "text": "SakumaRiri", "geometry": [30, 59, 176, 32]},
        {"id": "class", "text": "Acolyte", "geometry": [30, 92, 140, 30]},
        {"id": "hp-label", "text": "HP", "geometry": [228, 77, 39, 31]},
        {"id": "hp-value", "text": "1092 / 1109", "geometry": [298, 86, 166, 34]},
        {"id": "sp-label", "text": "SP", "geometry": [228, 127, 39, 31]},
        {"id": "sp-value", "text": "601 / 613", "geometry": [294, 128, 146, 32]},
        {"id": "base-level", "text": "Base Lv. 60", "geometry": [48, 176, 145, 28]},
        {"id": "job-level", "text": "Job Lv. 47", "geometry": [48, 204, 145, 28]},
        {"id": "weight", "text": "Weight : 987 / 2430", "geometry": [28, 248, 238, 32]},
        {"id": "zeny", "text": "Zeny : 318,430", "geometry": [276, 248, 188, 32]},
    ]
    window_spec = {
        "id": "basic_info", "evidence_policy": {"issue": 132},
        "geometry": {"x": 0, "y": 0, "width": 656, "height": 286},
        "drag_geometry": {"x": 48, "y": 6, "width": 558, "height": 40},
        "plates": {"expanded": expanded, "minimized": minimized},
        "minimized_height": 48,
        "minimized_controls": ["basic_info.minimize", "basic_info.close"],
        "display_facts": display_facts,
        "gestures": ["Drag", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"}],
        "controls": controls,
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [entry for entry in manifest["windows"]
                           if entry.get("id") != "basic_info"] + [window_spec]
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1, "issue": 132, "provider_requests": 0,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": digest(SOURCE),
                   "window_rect": list(WINDOW)},
        "assembly": "deterministic source-pixel crops and source-palette State Sets",
        "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"window": "basic_info", "controls": len(controls),
                      "assets": len(records), "provider_requests": 0}))


if __name__ == "__main__":
    main()
