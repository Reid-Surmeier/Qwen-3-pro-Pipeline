#!/usr/bin/env python3
"""Deterministically derive Issue #127 Inventory assets and ControlSpec."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
OUTPUT = ROOT / "godot/assets/image-79/inventory"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (0, 701, 484, 303)
BLUE = (62, 117, 184, 255)
HOVER = (115, 157, 209, 255)
MODIFIER = (138, 93, 176, 255)
DROP = (74, 175, 108, 255)
WHITE = (247, 247, 247, 255)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(rect: list[int]) -> dict[str, int]:
    return {"x": rect[0] - WINDOW[0], "y": rect[1] - WINDOW[1],
            "width": rect[2], "height": rect[3]}


def box(geometry: dict[str, int]) -> tuple[int, int, int, int]:
    return (geometry["x"], geometry["y"], geometry["x"] + geometry["width"],
            geometry["y"] + geometry["height"])


def save(image: Image.Image, name: str, records: list[dict[str, object]]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/inventory/{name}"


def variant_set(image: Image.Image, stem: str, records: list[dict[str, object]],
                outline: tuple[int, int, int, int] | None = None,
                width: int = 1, dragging: bool = False) -> dict[str, str]:
    idle = image.convert("RGBA")
    if dragging:
        white = Image.new("RGBA", idle.size, WHITE)
        idle = Image.blend(white, idle, 0.55)
        draw = ImageDraw.Draw(idle)
        for x in range(0, idle.width, 6):
            draw.line((x, 0, min(x + 3, idle.width - 1), 0), fill=BLUE)
            draw.line((x, idle.height - 1, min(x + 3, idle.width - 1), idle.height - 1),
                      fill=BLUE)
        for y in range(0, idle.height, 6):
            draw.line((0, y, 0, min(y + 3, idle.height - 1)), fill=BLUE)
            draw.line((idle.width - 1, y, idle.width - 1, min(y + 3, idle.height - 1)),
                      fill=BLUE)
    elif outline is not None:
        ImageDraw.Draw(idle).rectangle((0, 0, idle.width - 1, idle.height - 1),
                                       outline=outline, width=width)
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=HOVER, width=1)
    pressed = ImageEnhance.Brightness(idle).enhance(0.72)
    return {"idle": save(idle, f"{stem}-idle.png", records),
            "hover": save(hover, f"{stem}-hover.png", records),
            "pressed": save(pressed, f"{stem}-pressed.png", records)}


def control(control_id: str, control_type: str, geometry: dict[str, int],
            state_set: dict[str, object], gestures: list[str],
            actions: list[dict[str, str]], semantic_states: list[str] | None = None,
            initial: str | None = None, **extra: object) -> dict[str, object]:
    states = semantic_states or ["ready"]
    return {"id": control_id, "type": control_type, "geometry": geometry,
            "interaction_phases": ["idle", "hover", "pressed"],
            "semantic_states": states, "initial_semantic_state": initial or states[0],
            "state_set": state_set, "gestures": gestures, "actions": actions, **extra}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")
    window = source.crop((WINDOW[0], WINDOW[1], WINDOW[0] + WINDOW[2],
                          WINDOW[1] + WINDOW[3]))
    inventory = json.loads(INVENTORY.read_text())
    controls = [entry for entry in inventory["controls"]
                if entry.get("window") == "inventory"]
    records: list[dict[str, object]] = []

    clean = window.copy()
    clean_draw = ImageDraw.Draw(clean)
    transparent = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    transparent_path = save(transparent, "transparent.png", records)
    parent_variants = {phase: transparent_path for phase in ["idle", "hover", "pressed"]}

    grids = [entry for entry in controls if entry["type"] == "grid cell"]
    item_ids: list[str] = []
    item_surfaces: dict[str, object] = {}
    item_details: dict[str, str] = {}
    item_values: dict[str, str] = {}
    for entry in grids:
        geometry = rel(entry["rect"])
        row = (geometry["y"] - 30) // 61
        column = (geometry["x"] - 42) // 54
        item = f"r{row}c{column}"
        item_ids.append(item)
        item_values[item] = item
        quantity = str(entry["state"]).removeprefix("occupied x")
        item_details[item] = f"所持品 {row + 1}-{column + 1}\n個数 {quantity}"
        crop = window.crop(box(geometry))
        relative = dict(geometry)
        relative["x"] -= 42
        relative["y"] -= 30
        item_surfaces[item] = {
            "geometry": relative,
            "state_set": {
                "unselected": variant_set(crop, f"cell-{item}-unselected", records),
                "selected": variant_set(crop, f"cell-{item}-selected", records,
                                        BLUE, 2),
                "modifier_selected": variant_set(crop, f"cell-{item}-modifier", records,
                                                 MODIFIER, 3),
                "dragging": variant_set(crop, f"cell-{item}-dragging", records,
                                        dragging=True),
                "drop_target": variant_set(crop, f"cell-{item}-drop", records,
                                           DROP, 3),
            },
        }

    detail = Image.new("RGBA", (156, 50), (244, 246, 249, 255))
    detail_draw = ImageDraw.Draw(detail)
    detail_draw.rectangle((0, 0, 155, 49), outline=(56, 83, 128, 255), width=2)
    detail_draw.rectangle((2, 2, 153, 47), outline=(151, 177, 210, 255), width=1)
    detail_draw.line((3, 14, 152, 14), fill=(194, 210, 231, 255), width=1)
    detail_states = {"ready": variant_set(detail, "item-detail", records)}

    selection = control(
        "inventory.items", "SelectionView", {"x": 42, "y": 30, "width": 378, "height": 244},
        {"unselected": parent_variants, "selected": parent_variants},
        ["Activate", "DoubleActivate", "ModifierActivate", "DragDrop"],
        [{"gesture": "Activate", "action": "SelectInventoryItem"},
         {"gesture": "DoubleActivate", "action": "OpenInventoryItem"},
         {"gesture": "ModifierActivate", "action": "ToggleInventorySelection"},
         {"gesture": "DragDrop", "action": "MoveInventoryItem"}],
        ["unselected", "selected"], "unselected",
        value={"items": item_ids, "initial": "r0c0", "details": item_details,
               "value_control_ids": {}, "item_values": item_values,
               "allowed_modifiers": ["ctrl"], "drop_targets": item_ids,
               "initial_version": 0,
               "detail_view": {"size": [156, 50], "offset": [8, 0],
                               "padding": [8, 5],
                               "font": "res://fonts/PixelMplus10-Regular.ttf",
                               "font_size": 12, "font_color": "#2a252a",
                               "state_set": detail_states}},
        surfaces=item_surfaces,
    )

    tab_entries = [entry for entry in controls if entry["type"] == "tab"]
    tab_ids = ["item", "equip", "etc-1", "etc-2", "cash"]
    tab_surfaces: dict[str, object] = {}
    for tab, entry in zip(tab_ids, tab_entries, strict=True):
        geometry = rel(entry["rect"])
        crop = window.crop(box(geometry))
        relative = dict(geometry)
        relative["x"] -= 10
        relative["y"] -= 30
        tab_surfaces[tab] = {"geometry": relative, "state_set": {
            "unselected": variant_set(crop, f"tab-{tab}-unselected", records),
            "selected": variant_set(crop, f"tab-{tab}-selected", records, BLUE, 2),
        }}
    tabs = control(
        "inventory.tabs", "Tabs", {"x": 10, "y": 30, "width": 26, "height": 192},
        {"ready": parent_variants}, ["Activate"],
        [{"gesture": "Activate", "action": "SelectInventoryTab"}],
        value={"choices": tab_ids, "initial": "item"}, surfaces=tab_surfaces,
    )

    def bitmap_button(entry: dict[str, object], control_id: str,
                      action: str) -> dict[str, object]:
        geometry = rel(entry["rect"])
        crop = window.crop(box(geometry))
        return control(control_id, "Button", geometry,
                       {"ready": variant_set(crop, control_id.replace(".", "-"), records)},
                       ["Activate"], [{"gesture": "Activate", "action": action}])

    minimize_entry = next(entry for entry in controls if entry["type"] == "minimize")
    close_entry = next(entry for entry in controls if entry["type"] == "close")
    minimize = bitmap_button(minimize_entry, "inventory.minimize", "ToggleMinimized")
    close = bitmap_button(close_entry, "inventory.close", "CloseWindow")

    grip_geometry = {"x": 460, "y": 279, "width": 24, "height": 24}
    grip = window.crop(box(grip_geometry))
    clean_draw.rectangle(box(grip_geometry), fill=WHITE)
    grip_states = {"ready": variant_set(grip, "resize-grip", records)}

    title_fill = window.crop((260, 0, 360, 24))
    footer = window.crop((0, 279, 484, 303))
    footer_fill = window.crop((260, 279, 360, 303))
    right_edge = window.crop((480, 80, 484, 180))
    resize_frame = {
        "home_size": [484, 303], "title_height": 24, "footer_height": 24,
        "right_edge_width": 4,
        "anchored_right_controls": ["inventory.minimize", "inventory.close"],
        "stale_title_controls_geometry": {"x": 436, "y": 0, "width": 48, "height": 24},
        "stale_footer_geometry": {"x": 0, "y": 278, "width": 484, "height": 25},
        "stale_footer_grip_geometry": grip_geometry,
        "stale_right_edge_geometry": {"x": 480, "y": 24, "width": 4, "height": 255},
        "title_fill": save(title_fill, "resize-title-fill.png", records),
        "footer": save(footer, "resize-footer.png", records),
        "footer_fill": save(footer_fill, "resize-footer-fill.png", records),
        "right_edge": save(right_edge, "resize-right-edge.png", records),
    }

    expanded_path = save(clean, "clean-plate.png", records)
    minimized = Image.new("RGBA", (WINDOW[2], 28), WHITE)
    minimized.paste(window.crop((0, 0, WINDOW[2], 24)), (0, 0))
    minimized.paste(window.crop((0, 20, WINDOW[2], 24)), (0, 24))
    minimized_path = save(minimized, "minimized-plate.png", records)

    inventory_window = {
        "id": "inventory",
        "geometry": {"x": WINDOW[0], "y": WINDOW[1],
                     "width": WINDOW[2], "height": WINDOW[3]},
        "drag_geometry": {"x": 24, "y": 0, "width": 390, "height": 24},
        "resize": {"grip_geometry": grip_geometry, "minimum": [332, 220],
                   "maximum": [734, 512], "state_set": grip_states,
                   "frame": resize_frame},
        "minimized_controls": ["inventory.minimize", "inventory.close"],
        "plates": {"expanded": expanded_path, "minimized": minimized_path},
        "gestures": ["Drag", "Resize", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "Resize", "action": "ResizeWindow"},
                    {"gesture": "KeyCommand", "key": "Escape",
                     "action": "CloseWindow"}],
        "controls": [minimize, close, tabs, selection],
    }

    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [window_spec for window_spec in manifest["windows"]
                           if window_spec.get("id") != "inventory"]
    manifest["windows"].append(inventory_window)
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1,
        "issue": 127,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE),
                   "window_rect": list(WINDOW)},
        "assembly": "deterministic source-pixel crops and source-palette state transforms",
        "provider_requests": 0,
        "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"window": "inventory", "controls": len(inventory_window["controls"]),
                      "slots": len(item_ids), "assets": len(records),
                      "provider_requests": 0}))


if __name__ == "__main__":
    main()
