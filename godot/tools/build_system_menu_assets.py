#!/usr/bin/env python3
"""Deterministic Image-79 System Menu Assembly; no provider request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
OUTPUT = ROOT / "godot/assets/image-79/system-menu"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
SOURCE_RECT = (1328, 505, 1532, 778)
BLUE = (54, 145, 190, 255)

BUTTONS = [
    ("save_point", "セーブポイントへ", 31, "save_point", "reject",
     "Save-point travel requires a live game session outside this desktop"),
    ("character_select", "キャラクター選択", 65, "character_select", "reject",
     "Character selection requires a live game session outside this desktop"),
    ("sound_settings", "サウンド設定", 99, "options", "route", ""),
    ("environment_settings", "環境設定", 133, "environment_settings", "reject",
     "Environment Settings has no source-complete Window in this release"),
    ("shortcuts", "ショートカット", 167, "shortcut_settings", "reject",
     "Shortcut Settings has no source-complete Window in this release"),
    ("game_exit", "ゲーム終了", 201, "game_exit", "reject",
     "Game exit requires a live process outside this desktop"),
    ("return_to_game", "return to game", 235, "", "close", ""),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/system-menu/{name}"


def phase_variants(image: Image.Image, stem: str, records: list[dict]) -> dict:
    idle = image.convert("RGBA")
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=BLUE)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    return {phase: save(value, f"{stem}-{phase}.png", records)
            for phase, value in (("idle", idle), ("hover", hover),
                                 ("pressed", pressed))}


def control(control_id: str, rect: tuple[int, int, int, int], state_set: dict,
            action: str, target: str = "") -> dict:
    x, y, width, height = rect
    entry = {
        "id": control_id,
        "type": "Button",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "interaction_phases": ["idle", "hover", "pressed"],
        "semantic_states": ["ready"],
        "initial_semantic_state": "ready",
        "state_set": {"ready": state_set},
        "gestures": ["Activate"],
        "actions": [{"gesture": "Activate", "action": action}],
    }
    if target:
        entry["value"] = {"target_window": target}
    return entry


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    desktop = Image.open(SOURCE).convert("RGBA")
    window = desktop.crop(SOURCE_RECT)
    records: list[dict] = []
    expanded = save(window, "source-plate.png", records)
    minimized = save(window.crop((0, 0, 204, 27)), "minimized-plate.png", records)

    controls = [control(
        "system_menu.minimize", (181, 5, 14, 14),
        phase_variants(window.crop((181, 5, 195, 19)), "minimize", records),
        "ToggleMinimized",
    )]
    adapter_actions: dict[str, dict] = {}
    display_facts: list[dict] = []
    for button_id, label, y, target, disposition, reason in BUTTONS:
        control_id = f"system_menu.{button_id}"
        crop = window.crop((8, y, 196, y + 27))
        controls.append(control(
            control_id, (8, y, 188, 27),
            phase_variants(crop, f"button-{button_id}", records),
            "CloseWindow" if disposition == "close" else "OpenWindow",
            target,
        ))
        display_facts.append({"id": f"button-{button_id}-copy", "text": label,
                              "geometry": [8, y, 188, 27]})
        if disposition != "close":
            adapter_actions[control_id] = {"target": target,
                                           "disposition": disposition,
                                           "reason": reason}

    system_menu = {
        "id": "system_menu",
        "evidence_policy": {"issue": 134},
        "geometry": {"x": 1328, "y": 505, "width": 204, "height": 273},
        "minimized_height": 27,
        "drag_geometry": {"x": 0, "y": 0, "width": 181, "height": 22},
        "plates": {"expanded": expanded, "minimized": minimized},
        "backing_color": "#00000000",
        "display_facts": display_facts,
        "gestures": ["Drag", "KeyCommand"],
        "actions": [
            {"gesture": "Drag", "action": "MoveWindow"},
            {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
        ],
        "state_adapter": {"type": "system_menu", "actions": adapter_actions},
        "controls": controls,
    }

    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [entry for entry in manifest["windows"]
                           if entry.get("id") != "system_menu"]
    manifest["windows"].append(system_menu)
    CONTROL_SPEC.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    artifact = {
        "kind": "deterministic-assembly",
        "issue": 134,
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": digest(SOURCE),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "source_rect": list(SOURCE_RECT),
        "button_copy": [entry[1] for entry in BUTTONS],
        "provider_requests": 0,
        "outputs": records,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
