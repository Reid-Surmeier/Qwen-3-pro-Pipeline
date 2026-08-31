#!/usr/bin/env python3
"""Deterministic Image-79 Chat Room Assembly; no provider request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
BEHAVIOUR = ROOT / "artifacts/references/ro-desktop-b/chat-room/behaviour-card.md"
LEARNING = ROOT / "artifacts/references/ro-desktop-b/chat-room/prototype-learning-manifest.json"
OUTPUT = ROOT / "godot/assets/image-79/chat-room"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
SOURCE_RECT = (1037, 782, 1532, 1008)
BLUE = (54, 145, 190, 255)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/chat-room/{name}"


def phases(image: Image.Image, stem: str, records: list[dict]) -> dict:
    idle = image.convert("RGBA")
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=BLUE)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    return {name: save(value, f"{stem}-{name}.png", records)
            for name, value in (("idle", idle), ("hover", hover),
                                ("pressed", pressed), ("dragging", pressed))}


def state_surface(paths: dict) -> dict:
    return {state: dict(paths) for state in ("at_start", "between", "at_end")}


def clean_log(source: Image.Image) -> Image.Image:
    """Remove glyphs by replacing each row with its median source colour."""
    rgba = source.convert("RGBA")
    cleaned = Image.new("RGBA", rgba.size)
    pixels = rgba.load()
    draw = ImageDraw.Draw(cleaned)
    for y in range(rgba.height):
        color = tuple(int(median([pixels[x, y][channel]
                                  for x in range(rgba.width)]))
                      for channel in range(4))
        draw.line((0, y, rgba.width - 1, y), fill=color)
    return cleaned


def clean_scroll_track(source: Image.Image) -> Image.Image:
    """Inpaint the source thumb while preserving the exact exposed track."""
    cleaned = source.convert("RGBA").copy()
    pixels = cleaned.load()
    for y in range(1, 43):
        ratio = y / 43
        for x in range(2, 18):
            above = pixels[x, 0]
            below = pixels[x, 43]
            pixels[x, y] = tuple(round(above[channel] * (1 - ratio)
                                       + below[channel] * ratio)
                                 for channel in range(4))
    return cleaned


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    desktop = Image.open(SOURCE).convert("RGBA")
    window = desktop.crop(SOURCE_RECT)
    records: list[dict] = []
    expanded = save(window, "source-plate.png", records)
    minimized = save(window.crop((0, 0, 495, 24)), "title-plate.png", records)
    clean = save(clean_log(window.crop((7, 28, 467, 180))),
                 "clean-log.png", records)
    transparent = save(Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
                       "transparent.png", records)

    close = phases(window.crop((470, 7, 488, 25)), "close", records)
    field = phases(window.crop((7, 196, 465, 217)), "input", records)
    up = phases(window.crop((470, 28, 490, 48)), "scroll-up", records)
    down = phases(window.crop((470, 160, 490, 180)), "scroll-down", records)
    track = save(clean_scroll_track(window.crop((470, 48, 490, 160))),
                 "scroll-track.png", records)
    thumb = phases(window.crop((472, 49, 488, 91)), "scroll-thumb", records)

    controls = [
        {
            "id": "chat_room.close", "type": "Button",
            "geometry": {"x": 470, "y": 7, "width": 18, "height": 18},
            "interaction_phases": ["idle", "hover", "pressed"],
            "semantic_states": ["ready"], "initial_semantic_state": "ready",
            "state_set": {"ready": {key: close[key]
                for key in ("idle", "hover", "pressed")}},
            "gestures": ["Activate"],
            "actions": [{"gesture": "Activate", "action": "CloseWindow"}],
        },
        {
            "id": "chat_room.input", "type": "TextField",
            "geometry": {"x": 7, "y": 196, "width": 458, "height": 21},
            "interaction_phases": ["idle", "hover", "pressed", "focused"],
            "semantic_states": ["empty", "editing"],
            "initial_semantic_state": "empty",
            "state_set": {state: {"idle": field["idle"], "hover": field["hover"],
                "pressed": field["pressed"], "focused": field["hover"]}
                for state in ("empty", "editing")},
            "gestures": ["KeyCommand"],
            "actions": [
                {"gesture": "KeyCommand", "action": "SetChatDraft"},
                {"gesture": "KeyCommand", "action": "SubmitChat"},
            ],
            "value": {"initial": "", "maximum_length": 96,
                "accepted_pattern": "^[^\\n\\r]*$", "chat_input": True},
            "tokens": {"font": "res://fonts/PixelMplus10-Regular.ttf",
                "font_size": 13, "font_color": "#2a252a"},
        },
        {
            "id": "chat_room.scroll", "type": "ScrollView",
            "geometry": {"x": 470, "y": 28, "width": 20, "height": 152},
            "interaction_phases": ["idle", "hover", "pressed", "dragging"],
            "semantic_states": ["at_start", "between", "at_end"],
            "initial_semantic_state": "at_start",
            "state_set": {state: {phase: transparent for phase in
                ("idle", "hover", "pressed", "dragging")}
                for state in ("at_start", "between", "at_end")},
            "gestures": ["Wheel", "Activate", "Drag"],
            "actions": [
                {"gesture": "Wheel", "action": "ScrollChatLog"},
                {"gesture": "Activate", "action": "StepChatLog"},
                {"gesture": "Drag", "action": "SetChatLogOffset"},
            ],
            "value": {"minimum": 0, "maximum": 0, "initial": 0,
                "wheel_rows": 3, "arrow_rows": 1, "chat_log": True},
            "surfaces": {
                "decrement": {"geometry": {"x": 0, "y": 0, "width": 20, "height": 20},
                    "state_set": state_surface(up)},
                "track": {"geometry": {"x": 0, "y": 20, "width": 20, "height": 112},
                    "asset": track},
                "increment": {"geometry": {"x": 0, "y": 132, "width": 20, "height": 20},
                    "state_set": state_surface(down)},
                "thumb": {"geometry": {"x": 2, "y": 21, "width": 16, "height": 42},
                    "state_set": state_surface(thumb)},
            },
        },
    ]

    initial_lines = [
        {"kind": "chat", "text": "Sebas*：レイドリック終わったー"},
        {"kind": "chat", "text": "SakumaRiri：おつかれさま〜"},
        {"kind": "chat", "text": "ANRI：もう1周いきますか？"},
        {"kind": "chat", "text": "Show_A：いきましょう！"},
        {"kind": "system", "text": "経験値が 10800 上がりました。"},
    ]
    chat = {
        "id": "chat_room", "evidence_policy": {"issue": 135},
        "geometry": {"x": 1037, "y": 782, "width": 495, "height": 226},
        "drag_geometry": {"x": 0, "y": 0, "width": 470, "height": 24},
        "plates": {"expanded": expanded, "minimized": minimized},
        "backing_color": "#00000000",
        "display_facts": [{"id": f"source-line-{index + 1}",
            "text": line["text"], "geometry": [7, 33 + index * 25, 460, 25]}
            for index, line in enumerate(initial_lines)],
        "gestures": ["Drag", "KeyCommand"],
        "actions": [
            {"gesture": "Drag", "action": "MoveWindow"},
            {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
            {"gesture": "KeyCommand", "key": "F10", "action": "ChangeChatRows"},
            {"gesture": "KeyCommand", "key": "Alt+F10", "action": "ToggleWindow"},
        ],
        "state_adapter": {
            "type": "chat_room",
            "controls": {"input": "chat_room.input", "scroll": "chat_room.scroll"},
            "initial_lines": initial_lines,
            "row_count_cycle": [5, 7, 3],
            "presentation": {"background": clean,
                "geometry": {"x": 7, "y": 28, "width": 460, "height": 152},
                "font": "res://fonts/PixelMplus10-Regular.ttf",
                "font_size": 13,
                "colors": {"chat": "#202020", "system": "#ee2828",
                    "screen": "#202020", "party": "#1e47ee",
                    "guild": "#2b9a4a", "allied_guild": "#a84db6"}},
        },
        "controls": controls,
    }

    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [entry for entry in manifest["windows"]
                           if entry.get("id") != "chat_room"]
    # The source desktop stacks Chat Room last/frontmost.
    manifest["windows"].append(chat)
    for window_spec in manifest["windows"]:
        if window_spec.get("id") != "basic_info":
            continue
        for control in window_spec.get("controls", []):
            if control.get("id") != "basic_info.destination.chat":
                continue
            old = (control["state_set"].get("disabled")
                   or control["state_set"].get("ready")
                   or {phase: ("res://assets/image-79/basic-info/"
                               f"destination-chat-{phase}.png")
                       for phase in ("idle", "hover", "pressed")})
            control["semantic_states"] = ["ready"]
            control["initial_semantic_state"] = "ready"
            control["state_set"] = {"ready": old}
    CONTROL_SPEC.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    artifact = {
        "kind": "deterministic-assembly", "issue": 135,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": digest(SOURCE),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "behaviour_card": {"path": str(BEHAVIOUR.relative_to(ROOT)),
                           "sha256": digest(BEHAVIOUR)},
        "prototype_learning": {"path": str(LEARNING.relative_to(ROOT)),
                               "sha256": digest(LEARNING)},
        "source_rect": list(SOURCE_RECT), "provider_requests": 0,
        "outputs": records,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
