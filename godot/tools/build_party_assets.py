#!/usr/bin/env python3
"""Deterministic Image-79 Party Assembly; no provider request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
OUTPUT = ROOT / "godot/assets/image-79/party"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"
SOURCE_RECT = (1107, 505, 1322, 774)
BLUE = (54, 145, 190, 255)

MEMBERS = [
    ("sakumariri", "SakumaRiri（フェイヨン..", 1109, 1109),
    ("sebas", "Sebas*（フェイヨン...", 1340, 1340),
    ("anri", "ANRI（フェイヨン森）", 1762, 1762),
    ("show_a", "Show_A（フェイヨン森..", 1235, 1235),
    ("ayana_ishizuka", "AyanaIshizuka（フェイヨン...", 1028, 1028),
]
ACTION_NAMES = ["memo", "info", "target", "search", "leave"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image: Image.Image, name: str, records: list[dict]) -> str:
    path = OUTPUT / name
    image.save(path, optimize=True)
    records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "size": list(image.size)})
    return f"res://assets/image-79/party/{name}"


def phase_variants(image: Image.Image, stem: str, records: list[dict],
                   disabled: bool = False) -> dict:
    idle = image.convert("RGBA")
    if disabled:
        alpha = idle.getchannel("A")
        idle = ImageOps.grayscale(idle).convert("RGBA")
        idle.putalpha(alpha)
        idle = Image.blend(image.convert("RGBA"), idle, 0.55)
        pressed = ImageEnhance.Brightness(idle).enhance(0.72)
        return {phase: save(value, f"{stem}-{phase}.png", records)
                for phase, value in (("idle", idle), ("hover", idle),
                                     ("pressed", pressed))}
    hover = idle.copy()
    ImageDraw.Draw(hover).rectangle((0, 0, hover.width - 1, hover.height - 1),
                                    outline=BLUE)
    pressed = ImageEnhance.Brightness(idle).enhance(0.68)
    return {phase: save(value, f"{stem}-{phase}.png", records)
            for phase, value in (("idle", idle), ("hover", hover),
                                 ("pressed", pressed))}


def control(control_id: str, control_type: str, rect: tuple[int, int, int, int],
            state_set: dict, gestures: list[str], actions: list[dict],
            states: list[str], initial: str, **extra) -> dict:
    x, y, width, height = rect
    return {"id": control_id, "type": control_type,
            "geometry": {"x": x, "y": y, "width": width, "height": height},
            "interaction_phases": ["idle", "hover", "pressed"],
            "semantic_states": states, "initial_semantic_state": initial,
            "state_set": state_set, "gestures": gestures, "actions": actions,
            **extra}


def choice_surface(base: Image.Image, selected_disc: Image.Image,
                   unselected_disc: Image.Image, selected: bool,
                   disc_position: tuple[int, int]) -> Image.Image:
    result = base.copy()
    result.paste(selected_disc if selected else unselected_disc,
                 disc_position, selected_disc if selected else unselected_disc)
    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    desktop = Image.open(SOURCE).convert("RGBA")
    window = desktop.crop(SOURCE_RECT)
    records: list[dict] = []
    expanded = save(window, "source-plate.png", records)

    blank = window.crop((5, 27, 210, 207))
    fill = blank.getpixel((202, 176))
    blank = Image.new("RGBA", blank.size, fill)
    ImageDraw.Draw(blank).rectangle((0, 0, blank.width - 1, blank.height - 1),
                                    outline=(120, 120, 120, 255))
    blank_list = save(blank, "blank-list.png", records)
    transparent = save(Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
                       "transparent.png", records)

    controls: list[dict] = []
    close_crop = window.crop((194, 5, 207, 18))
    close_states = phase_variants(close_crop, "close-ready", records)
    controls.append(control(
        "party.close", "Button", (194, 5, 13, 13), {"ready": close_states},
        ["Activate"], [{"gesture": "Activate", "action": "CloseWindow"}],
        ["ready"], "ready"))

    row_states: dict[str, dict] = {}
    surfaces: dict[str, dict] = {}
    item_values: dict[str, str] = {}
    details: dict[str, str] = {}
    display_facts: list[dict] = []
    for index, (member_id, label, current, maximum) in enumerate(MEMBERS):
        row = window.crop((6, 33 + index * 34, 206, 65 + index * 34))
        unselected = phase_variants(row, f"member-{member_id}-unselected", records)
        selected_idle = ImageEnhance.Brightness(row).enhance(0.72)
        ImageDraw.Draw(selected_idle).rectangle((0, 0, 199, 31), outline=BLUE)
        selected = phase_variants(selected_idle, f"member-{member_id}-selected", records)
        unavailable = phase_variants(
            row, f"member-{member_id}-unavailable", records, disabled=True)
        row_states[member_id] = {
            "unselected": unselected,
            "selected": selected,
            "unavailable": unavailable,
        }
        surfaces[member_id] = {
            "geometry": {"x": 0, "y": index * 34, "width": 200, "height": 32},
            "state_set": row_states[member_id],
        }
        item_values[member_id] = member_id
        details[member_id] = f"{label}\n{current}/{maximum}"
        display_facts.extend([
            {"id": f"member-{index + 1}-label", "text": label,
             "geometry": [34, 33 + index * 34, 170, 16]},
            {"id": f"member-{index + 1}-hp", "text": f"{current}/{maximum}",
             "geometry": [128, 49 + index * 34, 76, 16]},
        ])

    controls.append(control(
        "party.members", "SelectionView", (6, 33, 200, 168),
        {"unselected": {p: transparent for p in ("idle", "hover", "pressed")},
         "selected": {p: transparent for p in ("idle", "hover", "pressed")},
         "unavailable": {p: transparent for p in ("idle", "hover", "pressed")}},
        ["Activate"], [{"gesture": "Activate", "action": "SelectPartyMember"}],
        ["unselected", "selected", "unavailable"], "unselected",
        value={"items": [entry[0] for entry in MEMBERS], "initial": MEMBERS[0][0],
               "details": details, "item_values": item_values,
               "value_control_ids": {}, "show_empty_slots": False},
        surfaces=surfaces))

    for index, (member_id, _label, current, maximum) in enumerate(MEMBERS):
        rect = (38, 52 + index * 34, 88, 5)
        meter = window.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
        meter_states = phase_variants(meter, f"meter-{member_id}", records)
        controls.append(control(
            f"party.meter.{member_id}", "Meter", rect, {"ready": meter_states},
            [], [], ["ready"], "ready",
            value={"minimum": 0, "maximum": maximum, "current": current,
                   "fill_axis": "horizontal", "fill_pixels": rect[2]}))

    for index, name in enumerate(ACTION_NAMES):
        rect = (15 + index * 35, 214, 21, 21)
        crop = window.crop((rect[0], rect[1], rect[0] + 21, rect[1] + 21))
        disabled = phase_variants(crop, f"action-{name}-disabled", records,
                                  disabled=True)
        if name == "leave":
            available = phase_variants(crop, "action-leave-available", records)
            state_set = {"available": available, "disabled": disabled}
            states, initial = ["available", "disabled"], "available"
        else:
            state_set = {"disabled": disabled}
            states, initial = ["disabled"], "disabled"
        controls.append(control(
            f"party.action.{name}", "Button", rect, state_set,
            ["Activate"], [{"gesture": "Activate", "action": "ActivatePartyAction"}],
            states, initial, value={"action_id": f"party.action.{name}"}))

    friends_base = window.crop((5, 244, 76, 267))
    party_base = window.crop((86, 244, 181, 267))
    unselected_disc = window.crop((7, 245, 23, 261))
    selected_disc = window.crop((88, 245, 104, 261))
    choice_records: dict[str, dict] = {}
    for choice, base, disc_at in (
        ("friends", friends_base, (2, 1)), ("party", party_base, (2, 1))
    ):
        choice_records[choice] = {}
        for semantic, selected in (("unselected", False), ("selected", True)):
            assembled = choice_surface(base, selected_disc, unselected_disc,
                                       selected, disc_at)
            choice_records[choice][semantic] = phase_variants(
                assembled, f"mode-{choice}-{semantic}", records)
    controls.append(control(
        "party.mode", "ChoiceGroup", (5, 244, 176, 23),
        {"selected": {p: transparent for p in ("idle", "hover", "pressed")},
         "unselected": {p: transparent for p in ("idle", "hover", "pressed")}},
        ["Activate"], [{"gesture": "Activate", "action": "SelectPartyMode"}],
        ["selected", "unselected"], "selected",
        value={"choices": ["friends", "party"], "initial": "party"},
        surfaces={
            "friends": {"geometry": {"x": 0, "y": 0, "width": 71, "height": 23},
                        "state_set": choice_records["friends"]},
            "party": {"geometry": {"x": 81, "y": 0, "width": 95, "height": 23},
                      "state_set": choice_records["party"]},
        }))

    member_specs = [
        {"id": member_id, "name": label.split("（", 1)[0],
         "location": label.split("（", 1)[1] if "（" in label else "",
         "current_hp": current, "maximum_hp": maximum}
        for member_id, label, current, maximum in MEMBERS
    ]
    party_window = {
        "id": "party", "evidence_policy": {"issue": 133},
        "geometry": {"x": 1107, "y": 505, "width": 215, "height": 269},
        "drag_geometry": {"x": 0, "y": 0, "width": 194, "height": 22},
        "plates": {"expanded": expanded, "minimized": expanded},
        "backing_color": "#00000000",
        "display_facts": display_facts,
        "gestures": ["Drag", "KeyCommand"],
        "actions": [{"gesture": "Drag", "action": "MoveWindow"},
                    {"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"}],
        "state_adapter": {
            "type": "party", "initial_mode": "party",
            "initial_membership": "member", "members": member_specs,
            "actions": {
                "party.action.memo": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
                "party.action.info": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
                "party.action.target": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
                "party.action.search": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
                "party.action.leave": {"permission": "party_member"},
            },
            "controls": {"mode": "party.mode", "members": "party.members",
                         "actions": [f"party.action.{name}" for name in ACTION_NAMES]},
            "presentation": {"blank_list": blank_list,
                             "geometry": {"x": 5, "y": 27, "width": 205, "height": 180}},
        },
        "controls": controls,
    }

    manifest = json.loads(CONTROL_SPEC.read_text())
    manifest["windows"] = [window for window in manifest["windows"]
                           if window.get("id") != "party"]
    manifest["windows"].append(party_window)
    CONTROL_SPEC.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    artifact = {
        "kind": "deterministic-assembly", "issue": 133,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": digest(SOURCE),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "source_rect": list(SOURCE_RECT), "provider_requests": 0,
        "outputs": records,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
