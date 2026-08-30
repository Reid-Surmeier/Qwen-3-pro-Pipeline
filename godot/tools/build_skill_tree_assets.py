#!/usr/bin/env python3
"""Deterministically derive Issue #126 assets and its ControlSpec fragment."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
OUTPUT = ROOT / "godot/assets/image-79/skill-tree"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (492, 0, 611, 595)
INK = (70, 89, 159, 255)
TITLE = (199, 219, 240, 255)
BODY = (252, 252, 252, 255)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(rect: list[int]) -> dict[str, int]:
    return {
        "x": rect[0] - WINDOW[0],
        "y": rect[1] - WINDOW[1],
        "width": rect[2],
        "height": rect[3],
    }


def box(geometry: dict[str, int]) -> tuple[int, int, int, int]:
    return (
        geometry["x"], geometry["y"],
        geometry["x"] + geometry["width"],
        geometry["y"] + geometry["height"],
    )


def save(image: Image.Image, name: str, records: list[dict[str, object]]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/skill-tree/{name}"


def variants(image: Image.Image, stem: str, records: list[dict[str, object]],
             selected: bool = False) -> dict[str, str]:
    idle = image.convert("RGBA")
    if selected:
        draw = ImageDraw.Draw(idle)
        draw.rectangle((0, 0, idle.width - 1, idle.height - 1), outline=INK, width=2)
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=INK, width=1)
    pressed = ImageEnhance.Brightness(idle).enhance(0.72)
    return {
        "idle": save(idle, f"{stem}-idle.png", records),
        "hover": save(hover, f"{stem}-hover.png", records),
        "pressed": save(pressed, f"{stem}-pressed.png", records),
    }


def stable_cell_id(rect: list[int]) -> str:
    x_centers = [558, 658, 757, 856, 950, 1042]
    y_centers = [87, 190, 291, 392, 493]
    cx = rect[0] + rect[2] / 2
    cy = rect[1] + rect[3] / 2
    column = min(range(len(x_centers)), key=lambda i: abs(cx - x_centers[i])) + 1
    row = min(range(len(y_centers)), key=lambda i: abs(cy - y_centers[i])) + 1
    return f"r{row}c{column}"


def control_entry(control_id: str, control_type: str, geometry: dict[str, int],
                  state_set: dict[str, object], gestures: list[str],
                  actions: list[dict[str, str]], semantic_states: list[str] | None = None,
                  initial: str | None = None, **extra: object) -> dict[str, object]:
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
    inventory = json.loads(INVENTORY.read_text())
    controls = [entry for entry in inventory["controls"] if entry.get("window") == "skill-tree"]
    grids = [entry for entry in controls if entry["type"] == "grid cell"]
    steppers = [entry for entry in controls if entry["type"] == "stepper"]
    records: list[dict[str, object]] = []
    clean = window.copy()
    clean_draw = ImageDraw.Draw(clean)

    transparent = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    transparent_path = save(transparent, "transparent.png", records)
    parent_variants = {phase: transparent_path for phase in ["idle", "hover", "pressed"]}

    value_pattern = re.compile(r"(\d+)\s*/\s*(\d+)")
    stepper_values: dict[str, tuple[int, int]] = {}
    for entry in steppers:
        match = value_pattern.search(entry["label"])
        if not match:
            raise ValueError(f"Stepper value missing from {entry['label']}")
        stepper_values[stable_cell_id(entry["rect"])] = (
            int(match.group(1)), int(match.group(2)))

    selection_geometry = {"x": 30, "y": 60, "width": 550, "height": 470}
    item_ids: list[str] = []
    item_surfaces: dict[str, object] = {}
    item_labels: dict[str, str] = {}
    item_details: dict[str, str] = {}
    for entry in grids:
        item = stable_cell_id(entry["rect"])
        item_ids.append(item)
        item_labels[item] = entry["label"]
        values = stepper_values.get(item)
        item_details[item] = (f"{entry['label']}\n{values[0]} / {values[1]}"
                              if values else f"{entry['label']}\n—")
        geometry = rel(entry["rect"])
        crop = window.crop(box(geometry))
        clean_draw.rectangle(box(geometry), fill=BODY)
        relative = dict(geometry)
        relative["x"] -= selection_geometry["x"]
        relative["y"] -= selection_geometry["y"]
        item_surfaces[item] = {
            "geometry": relative,
            "state_set": {
                "unselected": variants(crop, f"skill-{item}-unselected", records),
                "selected": variants(crop, f"skill-{item}-selected", records, selected=True),
            },
        }

    selection = control_entry(
        "skill_tree.skills", "SelectionView", selection_geometry,
        {"unselected": parent_variants, "selected": parent_variants},
        ["Activate", "ContextActivate"],
        [
            {"gesture": "Activate", "action": "SelectSkill"},
            {"gesture": "ContextActivate", "action": "OpenSkillDetail"},
        ],
        ["unselected", "selected"], "unselected",
        value={"items": item_ids, "initial": "r1c3", "labels": item_labels,
               "details": item_details},
        surfaces=item_surfaces,
    )

    stepper_specs: list[dict[str, object]] = []
    # Every source Stepper uses the same complete arrow glyphs, but the
    # inventory rectangles start and end at different horizontal points based
    # on label width. Reuse one source-locked complete pair so no label can
    # yield clipped arrow fragments.
    canonical_left_arrow = window.crop((127, 414, 145, 431))
    canonical_right_arrow = window.crop((191, 414, 209, 431))
    for entry in steppers:
        item = stable_cell_id(entry["rect"])
        geometry = rel(entry["rect"])
        # The inventory rectangle ended before the right-arrow pixels. Own the
        # complete source group so a pending transaction can hide every arrow.
        geometry["width"] += 12
        geometry["height"] += 1
        crop = window.crop(box(geometry))
        clean_draw.rectangle(box(geometry), fill=BODY)
        match = value_pattern.search(entry["label"])
        if not match:
            raise ValueError(f"Stepper value missing from {entry['label']}")
        current, target = (int(match.group(1)), int(match.group(2)))
        maximum = max(current, target, 10)
        # Eighteen pixels owns each complete source arrow while leaving a
        # 46-pixel live value region for the widest `10 / 10` label.
        arrow_width = min(18, geometry["width"] // 3)
        left = canonical_left_arrow.copy()
        right = canonical_right_arrow.copy()
        hidden = {phase: transparent_path for phase in ["idle", "hover", "pressed"]}
        surfaces = {
            "decrement": {
                "geometry": {"x": 0, "y": 0, "width": arrow_width,
                             "height": geometry["height"]},
                "state_set": {"visible": variants(left, f"stepper-{item}-left", records),
                              "hidden": hidden},
            },
            "increment": {
                "geometry": {"x": geometry["width"] - arrow_width, "y": 0,
                             "width": arrow_width, "height": geometry["height"]},
                "state_set": {"visible": variants(right, f"stepper-{item}-right", records),
                              "hidden": hidden},
            },
        }
        stepper_specs.append(control_entry(
            f"skill_tree.stepper.{item}", "Stepper", geometry,
            {"ready": parent_variants, "pending": parent_variants,
             "disabled": {"idle": transparent_path}},
            ["Activate"], [{"gesture": "Activate", "action": "StepSkill"}],
            ["ready", "pending", "disabled"], "ready",
            value={"minimum": 0, "maximum": maximum, "current": current,
                   "target": target, "step": 1},
            surfaces=surfaces,
        ))

    def make_button(control_id: str, geometry: dict[str, int], action: str,
                    source_crop: Image.Image | None = None) -> dict[str, object]:
        crop = source_crop or window.crop(box(geometry))
        clean_draw.rectangle(box(geometry), fill=TITLE if geometry["y"] < 28 else BODY)
        return control_entry(control_id, "Button", geometry,
                             {"ready": variants(crop, control_id.replace(".", "-"), records)},
                             ["Activate"], [{"gesture": "Activate", "action": action}])

    minimize_geometry = {"x": 2, "y": 3, "width": 19, "height": 19}
    minimize = make_button("skill_tree.minimize", minimize_geometry, "ToggleMinimized")
    view = make_button("skill_tree.view", {"x": 530, "y": 6, "width": 53, "height": 19},
                       "ToggleSkillView")
    close = make_button("skill_tree.close", {"x": 590, "y": 7, "width": 17, "height": 17},
                        "CloseWindow")
    use = make_button("skill_tree.use", {"x": 430, "y": 556, "width": 70, "height": 26},
                      "CommitSkillChanges")
    cancel = make_button("skill_tree.cancel", {"x": 517, "y": 556, "width": 75, "height": 26},
                         "CancelSkillChanges")

    description_geometry = {"x": 258, "y": 12, "width": 16, "height": 14}
    description_crop = window.crop(box(description_geometry))
    clean_draw.rectangle(box(description_geometry), fill=TITLE)
    checked = description_crop.copy()
    checked_draw = ImageDraw.Draw(checked)
    checked_draw.line((3, 7, 7, 11), fill=INK, width=2)
    checked_draw.line((7, 11, 13, 3), fill=INK, width=2)
    description = control_entry(
        "skill_tree.descriptions", "Toggle", description_geometry,
        {"off": variants(description_crop, "skill-tree-descriptions-off", records),
         "on": variants(checked, "skill-tree-descriptions-on", records)},
        ["Activate"], [{"gesture": "Activate", "action": "ToggleValue"}],
        ["off", "on"], "off",
    )

    expanded_path = save(clean, "clean-plate.png", records)
    list_plate = clean.copy()
    ImageDraw.Draw(list_plate).rectangle((4, 29, 607, 548), fill=BODY)
    list_path = save(list_plate, "list-plate.png", records)
    minimized_plate = window.crop((0, 0, WINDOW[2], 28))
    minimized_draw = ImageDraw.Draw(minimized_plate)
    minimized_draw.rectangle((258, 0, 588, 27), fill=TITLE)
    minimized_draw.rectangle(box(minimize_geometry), fill=TITLE)
    minimized_draw.rectangle((590, 7, 607, 24), fill=TITLE)
    minimized_path = save(minimized_plate, "minimized-plate.png", records)

    skill_window = {
        "id": "skill_tree",
        "geometry": {"x": WINDOW[0], "y": WINDOW[1],
                     "width": WINDOW[2], "height": WINDOW[3]},
        "drag_geometry": {"x": 24, "y": 0, "width": 230, "height": 26},
        "minimized_controls": ["skill_tree.minimize", "skill_tree.close"],
        "plates": {"expanded": expanded_path, "list": list_path,
                   "minimized": minimized_path},
        "gestures": ["Drag", "KeyCommand"],
        "actions": [
            {"gesture": "Drag", "action": "MoveWindow"},
            {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
        ],
        "controls": [minimize, description, view, close, selection,
                     *stepper_specs, use, cancel],
    }

    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [window_spec for window_spec in manifest["windows"]
                           if window_spec.get("id") != "skill_tree"]
    manifest["windows"].append(skill_window)
    CONTROL_SPEC.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    asset_manifest = {
        "schema_version": 1,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "window_rect": {"x": WINDOW[0], "y": WINDOW[1],
                        "width": WINDOW[2], "height": WINDOW[3]},
        "method": "deterministic source crop plus declared outline, brightness, fill, and live-text transforms",
        "paid_generation": {"requested": 0, "completed": 0, "cost_usd": 0.0},
        "assets": sorted(records, key=lambda record: str(record["path"])),
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"assets": len(records), "selection_items": len(item_ids),
                      "steppers": len(stepper_specs), "manifest": str(CONTROL_SPEC)}))


if __name__ == "__main__":
    main()
