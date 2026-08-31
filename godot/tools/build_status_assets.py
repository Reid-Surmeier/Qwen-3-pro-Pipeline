#!/usr/bin/env python3
"""Deterministically derive Issue #131 Status source-owned assets and manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
OUTPUT = ROOT / "godot/assets/image-79/status"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
WINDOW = (0, 211, 484, 208)
WHITE = (247, 247, 247, 255)
BLUE = (62, 117, 184, 255)
HOVER = (112, 154, 207, 255)

ATTRIBUTES = {
    "str": {"key": "Str", "base": 1, "bonus": 2, "row": 0},
    "agi": {"key": "Agi", "base": 1, "bonus": 2, "row": 1},
    "vit": {"key": "Vit", "base": 1, "bonus": 3, "row": 2},
    "int": {"key": "Int", "base": 92, "bonus": 10, "row": 3},
    "dex": {"key": "Dex", "base": 1, "bonus": 3, "row": 4},
    "luk": {"key": "Luk", "base": 1, "bonus": 5, "row": 5},
}

DERIVED = {
    "Atk": {"base": 63, "coefficients": {"Str": 1, "Dex": 1}},
    "Def": {"base": 20, "coefficients": {"Vit": 1}},
    "MatkMin": {"base": 298, "coefficients": {"Int": 2}},
    "MatkMax": {"base": 502, "coefficients": {"Int": 3}},
    "Mdef": {"base": 107, "coefficients": {"Int": 1}},
    "Hit": {"base": 64, "coefficients": {"Dex": 1}},
    "Flee": {"base": 64, "coefficients": {"Agi": 1}},
    "Critical": {"base": 3, "coefficients": {"Luk": 1}},
    "Aspd": {"base": 140, "coefficients": {"Agi": 1}},
}

DERIVED_PRESENTATION = {
    "Atk": {"x": 265, "y": 35, "width": 68, "height": 25, "format": "plus_zero"},
    "Def": {"x": 413, "y": 35, "width": 63, "height": 25, "format": "def_split"},
    "MatkMin": {"x": 251, "y": 62, "width": 38, "height": 25, "format": "integer"},
    "MatkMax": {"x": 297, "y": 62, "width": 38, "height": 25, "format": "integer"},
    "Mdef": {"x": 405, "y": 62, "width": 71, "height": 25, "format": "mdef_split"},
    "Hit": {"x": 286, "y": 89, "width": 47, "height": 25, "format": "integer"},
    "Flee": {"x": 418, "y": 89, "width": 58, "height": 25, "format": "flee_split"},
    "Critical": {"x": 296, "y": 116, "width": 37, "height": 25, "format": "integer"},
    "Aspd": {"x": 431, "y": 116, "width": 45, "height": 25, "format": "integer"},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict[str, object]]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/status/{name}"


def variants(image: Image.Image, stem: str,
             records: list[dict[str, object]]) -> dict[str, str]:
    idle = image.convert("RGBA")
    hover = idle.copy()
    hover_draw = ImageDraw.Draw(hover)
    hover_draw.rectangle((0, 0, hover.width - 1, hover.height - 1), outline=HOVER)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    return {phase: save(value, f"{stem}-{phase}.png", records)
            for phase, value in [("idle", idle), ("hover", hover),
                                 ("pressed", pressed)]}


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
    records: list[dict[str, object]] = []
    transparent = save(Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
                       "transparent.png", records)
    transparent_states = {phase: transparent for phase in ["idle", "hover", "pressed"]}

    def button(control_id: str, rect: tuple[int, int, int, int],
               action: str) -> dict[str, object]:
        x, y, width, height = rect
        crop = window.crop((x, y, x + width, y + height))
        return control(control_id, "Button",
                       {"x": x, "y": y, "width": width, "height": height},
                       {"ready": variants(crop, control_id.replace(".", "-"), records)},
                       ["Activate"], [{"gesture": "Activate", "action": action}])

    controls = [
        button("status.minimize", (436, 5, 20, 20), "ToggleMinimized"),
        button("status.close", (461, 4, 18, 18), "CloseWindow"),
    ]
    adapter_attributes: dict[str, object] = {}
    attribute_values: dict[str, object] = {}
    attribute_costs: dict[str, object] = {}
    for name, fact in ATTRIBUTES.items():
        control_id = f"status.attribute.{name}"
        row = int(fact["row"])
        y = 35 + row * 27
        arrow_crop = window.crop((150, y, 172, y + 25))
        arrow = variants(arrow_crop, f"attribute-{name}-arrow", records)
        available = name != "int"
        disabled = {"idle": transparent,
                    "hover": arrow["hover"],
                    "pressed": arrow["pressed"]}
        surface_states = {
            "available": arrow,
            "disabled": disabled,
        }
        controls.append(control(
            control_id, "Stepper", {"x": 91, "y": y, "width": 108, "height": 25},
            {"available": transparent_states, "disabled": transparent_states},
            ["Activate", "ContextActivate"],
            [{"gesture": "Activate", "action": "StepStatusAttribute"},
             {"gesture": "ContextActivate", "action": "StepStatusAttribute"}],
            ["available", "disabled"], "available" if available else "disabled",
            value={"minimum": int(fact["base"]), "maximum": 99,
                   "current": int(fact["base"]), "target": int(fact["base"]), "step": 1},
            surfaces={
                "decrement": {"geometry": {"x": 59, "y": 0, "width": 22, "height": 25},
                              "state_set": {"available": transparent_states,
                                            "disabled": transparent_states}},
                "increment": {"geometry": {"x": 59, "y": 0, "width": 22, "height": 25},
                              "state_set": surface_states},
            }))
        adapter_attributes[control_id] = {
            "key": fact["key"], "base": fact["base"], "bonus": fact["bonus"],
            "maximum": 99,
        }
        attribute_values[control_id] = {"x": 91, "y": y, "width": 59, "height": 25}
        attribute_costs[control_id] = {"x": 172, "y": y, "width": 27, "height": 25}

    expanded = save(window, "source-plate.png", records)
    minimized_image = Image.new("RGBA", (484, 28), WHITE)
    minimized_image.paste(window.crop((0, 0, 484, 24)), (0, 0))
    minimized_image.paste(window.crop((0, 20, 484, 24)), (0, 24))
    minimized = save(minimized_image, "minimized-plate.png", records)
    state_adapter = {
        "type": "status", "initial_points": 4,
        "attributes": adapter_attributes, "derived": DERIVED,
        "presentation": {
            "font": "res://fonts/PixelMplus10-Regular.ttf",
            "font_size": 20, "font_color": "#171717", "background": "#fcfcfc",
            "points": {"x": 438, "y": 143, "width": 38, "height": 25},
            "attribute_values": attribute_values,
            "attribute_costs": attribute_costs,
            "derived_values": DERIVED_PRESENTATION,
        },
    }
    window_spec = {
        "id": "status", "evidence_policy": {"issue": 131},
        "geometry": {"x": 0, "y": 211, "width": 484, "height": 208},
        "drag_geometry": {"x": 30, "y": 0, "width": 400, "height": 28},
        "plates": {"expanded": expanded, "minimized": minimized},
        "minimized_controls": ["status.minimize", "status.close"],
        "state_adapter": state_adapter,
        "gestures": ["Drag", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"}],
        "controls": controls,
    }
    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [entry for entry in manifest["windows"]
                           if entry.get("id") != "status"] + [window_spec]
    CONTROL_SPEC.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    asset_manifest = {
        "schema_version": 1, "issue": 131, "provider_requests": 0,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": digest(SOURCE),
                   "window_rect": list(WINDOW)},
        "assembly": "deterministic source-pixel crops and source-palette State Sets",
        "files": records,
    }
    (OUTPUT / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"window": "status", "steppers": len(ATTRIBUTES),
                      "assets": len(records), "provider_requests": 0}))


if __name__ == "__main__":
    main()
