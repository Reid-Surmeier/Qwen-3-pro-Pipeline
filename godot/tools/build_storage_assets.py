#!/usr/bin/env python3
"""Deterministically derive Issue #128 Storage assets and ControlSpec."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
OUTPUT = ROOT / "godot/assets/image-79/storage"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (492, 609, 539, 393)
BLUE = (62, 117, 184, 255)
HOVER = (115, 157, 209, 255)
MODIFIER = (138, 93, 176, 255)
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
    return f"res://assets/image-79/storage/{name}"


def variants(image: Image.Image, stem: str, records: list[dict[str, object]],
             outline: tuple[int, int, int, int] | None = None,
             width: int = 1) -> dict[str, str]:
    idle = image.convert("RGBA")
    if outline:
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
    catalog = json.loads(INVENTORY.read_text())
    entries = [entry for entry in catalog["controls"]
               if entry.get("window") == "storage"]
    records: list[dict[str, object]] = []
    transparent = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    transparent_path = save(transparent, "transparent.png", records)
    transparent_variants = {phase: transparent_path
                            for phase in ["idle", "hover", "pressed"]}

    grids = [entry for entry in entries if entry["type"] == "grid cell"]
    slots: list[str] = []
    surfaces: dict[str, object] = {}
    details: dict[str, str] = {}
    for entry in grids:
        geometry = rel(entry["rect"])
        row = (geometry["y"] - 30) // 63
        column = (geometry["x"] - 88) // 60
        slot = f"r{row}c{column}"
        slots.append(slot)
        quantity = str(entry["state"]).removeprefix("occupied x")
        details[slot] = f"倉庫 {row + 1}-{column + 1}\n個数 {quantity}"
        crop = window.crop(box(geometry))
        local = dict(geometry)
        local["x"] -= 88
        local["y"] -= 30
        surfaces[slot] = {"geometry": local, "state_set": {
            "unselected": variants(crop, f"cell-{slot}-unselected", records),
            "selected": variants(crop, f"cell-{slot}-selected", records, BLUE, 2),
            "modifier_selected": variants(crop, f"cell-{slot}-transfer", records,
                                          MODIFIER, 3),
        }}

    collection = [f"stock-{index:03d}" for index in range(70)]
    labels = {item: f"Potion {index + 1:02d}"
              for index, item in enumerate(collection)}
    item_values = {slot: collection[index] for index, slot in enumerate(slots)}
    selection = control(
        "storage.items", "SelectionView", {"x": 88, "y": 30, "width": 420, "height": 315},
        {"unselected": transparent_variants, "selected": transparent_variants},
        ["Activate", "ModifierActivate", "ModifierDoubleActivate"],
        [{"gesture": "Activate", "action": "SelectStorageItem"},
         {"gesture": "ModifierActivate", "action": "ToggleStorageSelection"},
         {"gesture": "ModifierDoubleActivate", "action": "TransferStorageItem"}],
        ["unselected", "selected"], "unselected",
        value={"items": slots, "initial": "r0c0", "details": details,
               "value_control_ids": {}, "item_values": item_values,
               "allowed_modifiers": ["ctrl"], "initial_version": 0,
               "collection_items": collection, "collection_labels": labels,
               "columns": 7, "visible_rows": 5, "capacity": 300,
               "list_layout": {"columns": 2, "rows": 12, "row_height": 24,
                               "column_width": 198, "origin": [8, 7]}},
        surfaces=surfaces,
    )

    category_entries = [entry for entry in entries if entry["type"] == "tab"]
    category_ids = ["consumable", "equipment", "card", "material", "collectible", "other"]
    category_surfaces: dict[str, object] = {}
    for category, entry in zip(category_ids, category_entries, strict=True):
        geometry = rel(entry["rect"])
        crop = window.crop(box(geometry))
        local = dict(geometry)
        local["x"] -= 12
        local["y"] -= 40
        category_surfaces[category] = {"geometry": local, "state_set": {
            "unselected": variants(crop, f"category-{category}-unselected", records),
            "selected": variants(crop, f"category-{category}-selected", records,
                                 BLUE, 2),
        }}
    categories = control(
        "storage.categories", "Tabs", {"x": 12, "y": 40, "width": 66, "height": 228},
        {"ready": transparent_variants}, ["Activate"],
        [{"gesture": "Activate", "action": "SelectStorageCategory"}],
        value={"choices": category_ids, "initial": "consumable"},
        surfaces=category_surfaces,
    )

    def button(entry: dict[str, object], control_id: str, action: str) -> dict[str, object]:
        geometry = rel(entry["rect"])
        crop = window.crop(box(geometry))
        return control(control_id, "Button", geometry,
                       {"ready": variants(crop, control_id.replace(".", "-"), records)},
                       ["Activate"], [{"gesture": "Activate", "action": action}])

    close_entries = [entry for entry in entries if entry["type"] == "close"
                     or entry.get("label") == "close"]
    title_close = button(close_entries[0], "storage.close", "CloseWindow")
    bottom_close = button(close_entries[1], "storage.bottom_close", "CloseWindow")
    list_entry = next(entry for entry in entries if entry.get("label") == "list mode (icon)")
    search_icon_entry = next(entry for entry in entries if entry.get("label") == "search (icon)")
    sort_entry = next(entry for entry in entries if entry.get("label") == "sort")
    list_button = button(list_entry, "storage.list", "ToggleStorageView")
    search_icon = button(search_icon_entry, "storage.search_focus", "FocusStorageSearch")
    sort_button = button(sort_entry, "storage.sort", "SortStorage")

    field_geometry = rel(next(entry for entry in entries if entry.get("label") == "search")["rect"])
    field_image = window.crop(box(field_geometry))
    ImageDraw.Draw(field_image).rectangle((5, 4, field_image.width - 6,
                                           field_image.height - 5), fill=WHITE)
    empty_field = variants(field_image, "search-empty", records)
    filtered_field = variants(field_image, "search-filtered", records, BLUE, 1)
    search = control(
        "storage.search", "TextField", field_geometry,
        {"empty": empty_field, "filtered": filtered_field}, ["KeyCommand"],
        [{"gesture": "KeyCommand", "action": "FilterStorage"}],
        ["empty", "filtered"], "empty",
        value={"initial": "", "maximum_length": 24,
               "accepted_pattern": "^[A-Za-z0-9 ]*$",
               "selection_control_id": "storage.items"},
        tokens={"font": "res://fonts/PixelMplus10-Regular.ttf",
                "font_size": 13, "font_color": "#2a252a"},
    )

    track = Image.new("RGBA", (14, 283), (225, 232, 240, 255))
    ImageDraw.Draw(track).rectangle((0, 0, 13, 282), outline=(91, 112, 149, 255))
    arrow_up = Image.new("RGBA", (14, 16), (224, 233, 244, 255))
    draw = ImageDraw.Draw(arrow_up)
    draw.rectangle((0, 0, 13, 15), outline=(71, 94, 137, 255))
    draw.polygon([(3, 10), (7, 5), (11, 10)], fill=BLUE)
    arrow_down = arrow_up.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    thumb = Image.new("RGBA", (14, 56), (128, 158, 202, 255))
    ImageDraw.Draw(thumb).rectangle((0, 0, 13, 55), outline=(55, 82, 129, 255), width=1)
    track_path = save(track, "scroll-track.png", records)
    up_states = variants(arrow_up, "scroll-up", records)
    down_states = variants(arrow_down, "scroll-down", records)
    thumb_states = variants(thumb, "scroll-thumb", records)
    semantic_scroll = {state: transparent_variants for state in ["at_start", "between", "at_end"]}
    scroll = control(
        "storage.scroll", "ScrollView", {"x": 508, "y": 30, "width": 14, "height": 315},
        semantic_scroll, ["Wheel", "Activate", "Drag"],
        [{"gesture": "Wheel", "action": "ScrollStorage"},
         {"gesture": "Activate", "action": "StepStorageScroll"},
         {"gesture": "Drag", "action": "SetStorageScrollOffset"}],
        ["at_start", "between", "at_end"], "at_start",
        value={"minimum": 0, "maximum": 5, "initial": 0,
               "wheel_rows": 3, "arrow_rows": 1,
               "selection_control_id": "storage.items"},
        surfaces={
            "decrement": {"geometry": {"x": 0, "y": 0, "width": 14, "height": 16},
                          "state_set": {state: up_states for state in semantic_scroll}},
            "track": {"geometry": {"x": 0, "y": 16, "width": 14, "height": 283},
                      "asset": track_path},
            "increment": {"geometry": {"x": 0, "y": 299, "width": 14, "height": 16},
                          "state_set": {state: down_states for state in semantic_scroll}},
            "thumb": {"geometry": {"x": 0, "y": 16, "width": 14, "height": 56},
                      "state_set": {state: thumb_states for state in semantic_scroll}},
        },
    )

    expanded_path = save(window, "source-plate.png", records)
    minimized_path = expanded_path
    list_plate = window.copy()
    ImageDraw.Draw(list_plate).rectangle((88, 30, 507, 344), fill=(248, 248, 248, 255),
                                         outline=(170, 178, 192, 255))
    list_path = save(list_plate, "list-plate.png", records)
    storage_window = {
        "id": "storage",
        "geometry": {"x": WINDOW[0], "y": WINDOW[1],
                     "width": WINDOW[2], "height": WINDOW[3]},
        "drag_geometry": {"x": 24, "y": 0, "width": 470, "height": 24},
        "plates": {"expanded": expanded_path, "minimized": minimized_path,
                   "list": list_path},
        "gestures": ["Drag", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"}],
        "controls": [title_close, categories, selection, scroll, list_button,
                     search_icon, search, sort_button, bottom_close],
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [item for item in manifest["windows"]
                           if item.get("id") != "storage"]
    manifest["windows"].append(storage_window)
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1, "issue": 128,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE),
                   "window_rect": list(WINDOW)},
        "assembly": "deterministic source-pixel crops and source-palette state transforms",
        "provider_requests": 0, "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"window": "storage", "controls": len(storage_window["controls"]),
                      "slots": len(slots), "assets": len(records),
                      "provider_requests": 0}))


if __name__ == "__main__":
    main()
