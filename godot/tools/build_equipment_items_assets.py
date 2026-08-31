#!/usr/bin/env python3
"""Deterministically derive Issue #130 Equipment Items source-owned assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
OUTPUT = ROOT / "godot/assets/image-79/equipment-items"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (0, 423, 484, 271)
BLUE = (62, 117, 184, 255)
HOVER = (115, 157, 209, 255)
DROP = (74, 175, 108, 255)
WHITE = (247, 247, 247, 255)

SLOTS = {
    "head": (11, 58, 175, 36),
    "face": (11, 94, 175, 39),
    "armor": (11, 133, 175, 38),
    "weapon": (11, 171, 175, 40),
    "accessory_left": (11, 211, 175, 51),
    "robe": (293, 58, 180, 36),
    "body": (293, 94, 180, 40),
    "accessory_right_1": (293, 134, 180, 39),
    "accessory_right_2": (293, 173, 180, 61),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict[str, object]]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append(
        {"path": str(path.relative_to(ROOT)), "sha256": digest(path), "size": list(image.size)}
    )
    return f"res://assets/image-79/equipment-items/{name}"


def variants(
    image: Image.Image,
    stem: str,
    records: list[dict[str, object]],
    outline: tuple[int, int, int, int] | None = None,
    dragging: bool = False,
) -> dict[str, str]:
    idle = image.convert("RGBA")
    if dragging:
        idle = Image.blend(Image.new("RGBA", idle.size, WHITE), idle, 0.55)
        draw = ImageDraw.Draw(idle)
        for x in range(0, idle.width, 6):
            draw.line((x, 0, min(x + 3, idle.width - 1), 0), fill=BLUE)
            draw.line((x, idle.height - 1, min(x + 3, idle.width - 1), idle.height - 1), fill=BLUE)
    elif outline:
        ImageDraw.Draw(idle).rectangle(
            (0, 0, idle.width - 1, idle.height - 1), outline=outline, width=2
        )
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle(
        (0, 0, hover.width - 1, hover.height - 1), outline=HOVER, width=1
    )
    pressed = ImageEnhance.Brightness(idle).enhance(0.72)
    return {
        phase: save(value, f"{stem}-{phase}.png", records)
        for phase, value in [("idle", idle), ("hover", hover), ("pressed", pressed)]
    }


def control(
    control_id: str,
    control_type: str,
    geometry: dict[str, int],
    state_set: dict[str, object],
    gestures: list[str],
    actions: list[dict[str, str]],
    semantic_states: list[str] | None = None,
    initial: str | None = None,
    **extra: object,
) -> dict[str, object]:
    states = semantic_states or ["ready"]
    return {
        "id": control_id,
        "type": control_type,
        "geometry": geometry,
        "interaction_phases": ["idle", "hover", "pressed"],
        "semantic_states": states,
        "initial_semantic_state": initial or states[0],
        "state_set": state_set,
        "gestures": gestures,
        "actions": actions,
        **extra,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")
    window = source.crop((WINDOW[0], WINDOW[1], WINDOW[0] + WINDOW[2], WINDOW[1] + WINDOW[3]))
    records: list[dict[str, object]] = []
    transparent = save(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), "transparent.png", records)
    parent = {phase: transparent for phase in ["idle", "hover", "pressed"]}
    surfaces: dict[str, object] = {}
    for slot, (x, y, width, height) in SLOTS.items():
        crop = window.crop((x, y, x + width, y + height))
        available = Image.new("RGBA", crop.size, WHITE)
        draw = ImageDraw.Draw(available)
        draw.line(
            (0, available.height - 1, available.width - 1, available.height - 1),
            fill=(207, 210, 214, 255),
        )
        surfaces[slot] = {
            "geometry": {"x": x, "y": y - 28, "width": width, "height": height},
            "state_set": {
                "unselected": variants(crop, f"slot-{slot}-unselected", records),
                "selected": variants(crop, f"slot-{slot}-selected", records, BLUE),
                "dragging": variants(crop, f"slot-{slot}-dragging", records, dragging=True),
                "drop_target": variants(crop, f"slot-{slot}-drop", records, DROP),
                "available": variants(available, f"slot-{slot}-available", records, BLUE),
            },
        }
    slots = list(SLOTS)
    detail = Image.new("RGBA", (156, 50), (244, 246, 249, 255))
    detail_draw = ImageDraw.Draw(detail)
    detail_draw.rectangle((0, 0, 155, 49), outline=(56, 83, 128, 255), width=2)
    detail_draw.rectangle((2, 2, 153, 47), outline=(151, 177, 210, 255), width=1)
    detail_states = {"ready": variants(detail, "slot-detail", records)}
    selection = control(
        "equipment_items.slots",
        "SelectionView",
        {"x": 0, "y": 28, "width": 484, "height": 243},
        {"unselected": parent, "selected": parent},
        ["Activate", "DoubleActivate", "DragDrop"],
        [
            {"gesture": "Activate", "action": "SelectEquipmentSlot"},
            {"gesture": "DoubleActivate", "action": "UnequipEquipmentItem"},
            {"gesture": "DragDrop", "action": "MoveEquipmentItem"},
        ],
        ["unselected", "selected"],
        "unselected",
        value={
            "items": slots,
            "initial": "head",
            "item_values": {slot: slot for slot in slots},
            "details": {slot: slot.replace("_", " ") for slot in slots},
            "identity_surfaces": {slot: slot for slot in slots},
            "drop_targets": slots,
            "initial_version": 0,
            "capacity": 9,
            "show_empty_slots": True,
            "value_control_ids": {},
            "detail_view": {
                "size": [156, 50],
                "offset": [8, 0],
                "padding": [8, 5],
                "font": "res://fonts/PixelMplus10-Regular.ttf",
                "font_size": 12,
                "font_color": "#2a252a",
                "state_set": detail_states,
            },
        },
        surfaces=surfaces,
    )

    def button(control_id: str, rect: tuple[int, int, int, int], action: str) -> dict[str, object]:
        x, y, width, height = rect
        crop = window.crop((x, y, x + width, y + height))
        return control(
            control_id,
            "Button",
            {"x": x, "y": y, "width": width, "height": height},
            {"ready": variants(crop, control_id.replace(".", "-"), records)},
            ["Activate"],
            [{"gesture": "Activate", "action": action}],
        )

    minimize = button("equipment_items.minimize", (436, 5, 20, 20), "ToggleMinimized")
    close = button("equipment_items.close", (461, 4, 18, 18), "CloseWindow")
    expanded = save(window, "source-plate.png", records)
    minimized_image = Image.new("RGBA", (484, 28), WHITE)
    minimized_image.paste(window.crop((0, 0, 484, 24)), (0, 0))
    minimized_image.paste(window.crop((0, 20, 484, 24)), (0, 24))
    minimized = save(minimized_image, "minimized-plate.png", records)
    window_spec = {
        "id": "equipment_items",
        "evidence_policy": {"issue": 130},
        "geometry": {"x": 0, "y": 423, "width": 484, "height": 271},
        "drag_geometry": {"x": 30, "y": 0, "width": 400, "height": 28},
        "plates": {"expanded": expanded, "minimized": minimized},
        "minimized_controls": ["equipment_items.minimize", "equipment_items.close"],
        "gestures": ["Drag", "KeyCommand"],
        "actions": [
            {"gesture": "Drag", "action": "MoveWindow"},
            {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
        ],
        "controls": [minimize, close, selection],
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    inventory_window = next(
        entry for entry in manifest["windows"] if entry.get("id") == "inventory"
    )
    inventory_selection = next(
        entry for entry in inventory_window["controls"] if entry.get("id") == "inventory.items"
    )
    inventory_selection["value"]["foreign_identity_assets"] = {
        slot: surface["state_set"]["unselected"]["idle"] for slot, surface in surfaces.items()
    }
    selection["value"]["foreign_identity_assets"] = {
        item: surface["state_set"]["unselected"]["idle"]
        for item, surface in inventory_selection["surfaces"].items()
    }
    manifest["windows"] = [
        entry for entry in manifest["windows"] if entry.get("id") != "equipment_items"
    ] + [window_spec]
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1,
        "issue": 130,
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
                "window": "equipment_items",
                "slots": len(slots),
                "assets": len(records),
                "provider_requests": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
