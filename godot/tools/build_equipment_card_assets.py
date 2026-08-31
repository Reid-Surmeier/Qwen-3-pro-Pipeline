#!/usr/bin/env python3.12
"""Build source-owned Issue #129 Equipment Card assets and manifest entries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
OUTPUT = ROOT / "godot/assets/image-79/equipment-card"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (1108, 0, 424, 290)
BLUE = (47, 101, 174, 255)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict[str, object]]) -> str:
    path = OUTPUT / name
    image.save(path)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                    "size": list(image.size)})
    return "res://assets/image-79/equipment-card/" + name


def variants(image: Image.Image, stem: str, records: list[dict[str, object]]) -> dict[str, str]:
    hover = ImageEnhance.Brightness(image).enhance(1.08)
    pressed = ImageEnhance.Brightness(image).enhance(0.88)
    return {
        "idle": save(image, f"{stem}-idle.png", records),
        "hover": save(hover, f"{stem}-hover.png", records),
        "pressed": save(pressed, f"{stem}-pressed.png", records),
    }


def control(control_id: str, control_type: str, geometry: dict[str, int],
            state_set: dict[str, dict[str, str]], gestures: list[str],
            actions: list[dict[str, str]], semantic_states: list[str] | None = None,
            initial: str = "ready", **extra: object) -> dict[str, object]:
    result: dict[str, object] = {
        "id": control_id, "type": control_type, "geometry": geometry,
        "interaction_phases": ["idle", "hover", "pressed"],
        "semantic_states": semantic_states or [initial],
        "initial_semantic_state": initial, "state_set": state_set,
        "gestures": gestures, "actions": actions,
    }
    result.update(extra)
    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    source = Image.open(SOURCE).convert("RGBA")
    x, y, width, height = WINDOW
    window = source.crop((x, y, x + width, y + height))
    expanded = save(window, "source-plate.png", records)
    minimized = save(window.crop((0, 0, width, 28)), "minimized-plate.png", records)
    transparent = save(Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
                       "transparent.png", records)
    transparent_states = {"idle": transparent, "hover": transparent,
                          "pressed": transparent}

    minimize_crop = window.crop((6, 5, 28, 27))
    close_crop = window.crop((400, 7, 418, 25))
    minimize = control(
        "equipment_card.minimize", "Button", {"x": 6, "y": 5, "width": 22, "height": 22},
        {"ready": variants(minimize_crop, "minimize", records)}, ["Activate"],
        [{"gesture": "Activate", "action": "ToggleMinimized"}],
    )
    close = control(
        "equipment_card.close", "Button", {"x": 400, "y": 7, "width": 18, "height": 18},
        {"ready": variants(close_crop, "close", records)}, ["Activate"],
        [{"gesture": "Activate", "action": "CloseWindow"}],
    )

    decrement = window.crop((390, 80, 418, 106))
    track = window.crop((390, 106, 418, 244))
    increment = window.crop((390, 244, 418, 270))
    scroll_visuals = {**transparent_states, "dragging": transparent}
    scroll_states = {state: scroll_visuals for state in ["at_start", "between", "at_end"]}
    decrement_states = variants(decrement, "scroll-decrement", records)
    increment_states = variants(increment, "scroll-increment", records)
    track_states = variants(track, "scroll-track", records)
    track_states["dragging"] = track_states["pressed"]
    thumb = window.crop((390, 106, 418, 184))
    thumb_hover = save(ImageEnhance.Brightness(thumb).enhance(1.08),
                       "scroll-thumb-hover.png", records)
    thumb_pressed = save(ImageEnhance.Brightness(thumb).enhance(0.88),
                         "scroll-thumb-pressed.png", records)
    thumb_states = {"idle": transparent, "hover": thumb_hover,
                    "pressed": thumb_pressed, "dragging": thumb_pressed}
    scroll = control(
        "equipment_card.scroll", "ScrollView",
        {"x": 390, "y": 80, "width": 28, "height": 190}, scroll_states,
        ["Wheel", "Activate", "Drag"],
        [{"gesture": "Wheel", "action": "ScrollEquipmentCard"},
         {"gesture": "Activate", "action": "StepEquipmentCardScroll"},
         {"gesture": "Drag", "action": "SetEquipmentCardScrollOffset"}],
        ["at_start", "between", "at_end"], "at_start",
        interaction_phases=["idle", "hover", "pressed", "dragging"],
        value={"minimum": 0, "maximum": 0, "initial": 0,
               "wheel_rows": 3, "arrow_rows": 1, "available": False,
               "unavailable_reason": "image 79 does not attest continuation pixels"},
        surfaces={
            "decrement": {"geometry": {"x": 0, "y": 0, "width": 28, "height": 26},
                          "state_set": {state: decrement_states for state in scroll_states}},
            "track": {"geometry": {"x": 0, "y": 26, "width": 28, "height": 138},
                      "state_set": {state: track_states for state in scroll_states}},
            "increment": {"geometry": {"x": 0, "y": 164, "width": 28, "height": 26},
                          "state_set": {state: increment_states for state in scroll_states}},
            "thumb": {"geometry": {"x": 0, "y": 26, "width": 28, "height": 78},
                      "state_set": {state: thumb_states for state in scroll_states}},
        },
    )

    equipment_card = {
        "id": "equipment_card", "evidence_policy": {"issue": 129},
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "drag_geometry": {"x": 30, "y": 0, "width": 365, "height": 28},
        "plates": {"expanded": expanded, "minimized": minimized},
        "minimized_controls": ["equipment_card.minimize", "equipment_card.close"],
        "gestures": ["Drag", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"}],
        "detail": {"id": "mistress-card", "source_attested": True,
                   "continuation_available": False},
        "controls": [minimize, close, scroll],
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [item for item in manifest["windows"]
                           if item.get("id") != "equipment_card"]
    manifest["windows"].append(equipment_card)
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1, "issue": 129, "provider_requests": 0,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE),
                   "window_rect": list(WINDOW)},
        "assembly": "deterministic source-pixel crops; unattested continuation unavailable",
        "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"window": "equipment_card", "controls": 3,
                      "assets": len(records), "provider_requests": 0}))


if __name__ == "__main__":
    main()
