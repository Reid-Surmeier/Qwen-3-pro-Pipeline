#!/usr/bin/env python3
"""First-pass control inventory for the ro-desktop-b reference.

Rects are native pixels in the full 1536x1024 frame (origin top-left).
Explicit controls were measured by eye off 2x crops with a 20px grid;
repeated grids are expanded from measured cell geometry.
"""
import json
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
REF = ("/home/reidsurmeier/Qwen-3-pro-Pipeline/.claude/worktrees/"
       "agent-aa0361cb0549b2773/artifacts/references/ro-desktop-b/reference-native.png")
GRAY = np.asarray(Image.open(REF).convert("L")).astype(int)


def measure(gx, gy, halfw, halfh, thresh=200, minpx=150):
    """Tight bounding box of the dark content around a global centre point."""
    win = GRAY[gy - halfh:gy + halfh, gx - halfw:gx + halfw] < thresh
    if win.sum() < minpx:
        return None
    ys, xs = np.nonzero(win)
    return [gx - halfw + int(xs.min()), gy - halfh + int(ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
C = []          # controls, each dict gets "window" filled in by add()


def add(win, items):
    ox, oy = WIN[win]
    for it in items:
        x, y, w, h = it["rect"]
        it = dict(it)
        it["rect"] = [ox + x, oy + y, w, h]
        it["window"] = win
        C.append(it)


WIN = {
    "basic-info": (0, 0), "skill-tree": (492, 0), "equipment-card": (1108, 0),
    "status": (0, 211), "options": (1108, 297), "equipment-items": (0, 423),
    "party": (1107, 505), "system-menu": (1328, 505), "storage": (492, 609),
    "inventory": (0, 701), "chat-room": (1037, 782),
}


def titlebar(win, w, minimize=None, close=None, h=24):
    out = [{"type": "title drag", "rect": [0, 0, w, h], "state": "normal",
            "label": None}]
    if minimize:
        out.append({"type": "minimize", "rect": minimize, "state": "normal", "label": None})
    if close:
        out.append({"type": "close", "rect": close, "state": "normal", "label": None})
    return out


# ---------------------------------------------------------------- 1 basic-info
items = titlebar("basic-info", 484, minimize=[460, 6, 16, 16])
items += [
    {"type": "meter", "rect": [189, 37, 151, 15], "state": "full (1109/1109)", "label": "HP"},
    {"type": "meter", "rect": [189, 74, 151, 14], "state": "partial (601/613)", "label": "SP"},
    {"type": "meter", "rect": [146, 131, 184, 11], "state": "partial", "label": "Base Lv. 60"},
    {"type": "meter", "rect": [146, 148, 184, 11], "state": "partial", "label": "Job Lv. 47"},
]
BTN = [("status", 0, 0, "selected"), ("option", 1, 0, "normal"),
       ("items", 0, 1, "normal"), ("equip", 1, 1, "normal"),
       ("skill", 0, 2, "normal"), ("map", 1, 2, "normal"),
       ("chat", 0, 3, "normal"), ("friend", 1, 3, "normal")]
for label, col, row, state in BTN:
    items.append({"type": "button", "rect": [356 + col * 62, 42 + row * 41, 48, 26],
                  "state": state, "label": label})
add("basic-info", items)

# ---------------------------------------------------------------- 2 skill-tree
items = titlebar("skill-tree", 611, h=26, close=[590, 7, 17, 17])
items += [
    {"type": "checkbox", "rect": [258, 12, 16, 14], "state": "unchecked",
     "label": "スキル説明表示"},
    {"type": "button", "rect": [530, 6, 53, 19], "state": "normal", "label": "View"},
    {"type": "button", "rect": [430, 556, 70, 26], "state": "normal", "label": "use"},
    {"type": "button", "rect": [517, 556, 75, 26], "state": "normal", "label": "close"},
]
SKILLS = [
    [("ホーリー..", "5/5"), ("リザレク..", None), ("ヒール", "10/10"),
     ("アクア..", "10/10"), ("ディバイ..", "5/5"), ("ブレッシ..", "10/10")],
    [("プロテク..", "5/5"), ("キリエエ..", "1/1"), ("サンクチ..", "5/5"),
     ("デーモン..", "0/5"), ("魔法反射", "0/3"), None],
    [("速度増加", "5/5"), ("天使の恵み", "3/3"), ("エンジェ..", "1/1"),
     ("ニューマ", "5/5"), ("ストリッ..", "0/5"), ("シールド..", "3/3")],
    [("リカバリー", "1/1"), ("レックス..", "10/10"), ("カントキ..", "1/1"),
     ("クァグマ..", "1/1"), ("ペイニッ..", "0/5"), ("セイフティ..", "0/5")],
    [("グロリア", "5/5"), None, ("エクスピア..", "0/1"), ("エクスピア..", "0/1"),
     ("ターンア..", "0/10"), None],
]
for r, row in enumerate(SKILLS):
    for c, cell in enumerate(row):
        if cell is None:
            continue
        name, val = cell
        cx, cy = 66 + c * 97, 87 + r * 101
        m = measure(492 + cx, cy, 24, 22)
        rect = [m[0] - 492, m[1], m[2], m[3]] if m else [cx - 17, cy - 18, 40, 40]
        items.append({"type": "grid cell", "rect": rect,
                      "state": "learned" if val and val[0] != "0" else "unlearned",
                      "label": name})
        if val is not None:
            items.append({"type": "stepper", "rect": [cx - 36, cy + 24, 72, 16],
                          "state": f"value {val}", "label": f"{name} {val}"})
add("skill-tree", items)

# ------------------------------------------------------------ 3 equipment-card
items = titlebar("equipment-card", 424, close=[400, 7, 18, 18])
items += [
    {"type": "grid cell", "rect": [15, 39, 180, 231], "state": "occupied",
     "label": "ミストレスカード (card art)"},
    {"type": "scrollbar", "rect": [390, 80, 28, 190], "state": "vertical, thumb near top",
     "label": None},
]
add("equipment-card", items)

# -------------------------------------------------------------------- 4 status
items = titlebar("status", 484, minimize=[434, 8, 16, 16], close=[459, 8, 17, 17])
items += [{"type": "tab", "rect": [8, 30, 13, 165], "state": "selected (vertical)",
           "label": "職業/status"}]
STATS = [("Str", "1 +2", 2, True), ("Agi", "1 +2", 2, True), ("Vit", "1 +3", 2, True),
         ("Int", "92+10", 11, False), ("Dex", "1 +3", 2, True), ("Luk", "1 +5", 2, True)]
for i, (name, base, total, stepper) in enumerate(STATS):
    y = 39 + i * 27
    items.append({"type": "text field", "rect": [88, y, 112, 17],
                  "state": f"read-only, {base} -> {total}", "label": name})
    if stepper:
        items.append({"type": "stepper", "rect": [153, y + 2, 19, 13],
                      "state": "enabled", "label": f"raise {name}"})
add("status", items)

# ------------------------------------------------------------------- 5 options
items = titlebar("options", 424, minimize=[376, 6, 15, 16], close=[400, 6, 19, 18])
items += [
    {"type": "slider", "rect": [116, 50, 254, 17], "state": "thumb at ~80%", "label": "BGM"},
    {"type": "checkbox", "rect": [379, 56, 12, 11], "state": "unchecked", "label": "on (BGM)"},
    {"type": "slider", "rect": [116, 84, 254, 17], "state": "thumb at ~48%", "label": "Effect"},
    {"type": "checkbox", "rect": [379, 90, 12, 11], "state": "unchecked", "label": "on (Effect)"},
    {"type": "dropdown", "rect": [116, 119, 294, 26], "state": "closed, value 'Classic Blue'",
     "label": "Skin"},
    {"type": "checkbox", "rect": [30, 170, 12, 12], "state": "unchecked", "label": "attack"},
    {"type": "checkbox", "rect": [120, 170, 12, 12], "state": "checked", "label": "skill"},
    {"type": "checkbox", "rect": [192, 170, 12, 12], "state": "checked", "label": "item"},
    {"type": "checkbox", "rect": [289, 170, 12, 12], "state": "unchecked", "label": "option"},
]
add("options", items)

# ----------------------------------------------------------- 6 equipment-items
items = titlebar("equipment-items", 484, minimize=[434, 8, 17, 16], close=[459, 8, 17, 17])
items += [
    {"type": "tab", "rect": [8, 31, 99, 26], "state": "selected", "label": "一般装備"},
    {"type": "tab", "rect": [111, 31, 119, 26], "state": "normal", "label": "衣装装備"},
    {"type": "button", "rect": [212, 212, 52, 24], "state": "normal", "label": "items"},
]
SLOTS_L = ["+7 聖者の冠", "くわえた魚", "+5 イービルグロリアス", "+7 治癒の杖", "サバイバルイヤリング"]
SLOTS_R = ["聖者のローブ +4", "+4 ディアボロス", "ロザリオ", "+5 ソウルエンチャン...", "サバイバルイヤリング"]
YS = [(60, 35), (98, 30), (131, 37), (170, 30), (205, 45)]
for i, (y, h) in enumerate(YS):
    items.append({"type": "grid cell", "rect": [8, y, 182, h], "state": "occupied",
                  "label": SLOTS_L[i]})
    items.append({"type": "grid cell", "rect": [295, y, 181, h], "state": "occupied",
                  "label": SLOTS_R[i]})
add("equipment-items", items)

# --------------------------------------------------------------------- 7 party
items = titlebar("party", 215, h=22, close=[194, 5, 13, 13])
MEMBERS = [("SakumaRiri（フェイヨン..", "1109/1109"), ("Sebas*（フェイヨン...", "1340/1340"),
           ("ANRI（フェイヨン森）", "1762/1762"), ("Show_A（フェイヨン森..", "1235/1235"),
           ("AyanaIshizuka（フェイヨン...", "1028/1028")]
for i, (name, hp) in enumerate(MEMBERS):
    y = 33 + i * 34
    items.append({"type": "list row", "rect": [6, y, 200, 32],
                  "state": f"HP bar full, {hp}", "label": name})
for i, lbl in enumerate(["memo", "info", "target", "search", "leave"]):
    items.append({"type": "button", "rect": [15 + i * 35, 214, 21, 21],
                  "state": "normal (icon only)", "label": lbl})
items += [
    {"type": "radio", "rect": [7, 245, 16, 16], "state": "unselected", "label": "友達"},
    {"type": "radio", "rect": [88, 245, 16, 16], "state": "selected", "label": "パーティー"},
]
add("party", items)

# --------------------------------------------------------------- 8 system-menu
items = titlebar("system-menu", 204, h=22, minimize=[181, 5, 14, 14])
MENU = ["セーブポイントへ", "キャラクター選択", "サウンド設定", "環境設定",
        "ショートカット", "ゲーム終了", "return to game"]
for i, lbl in enumerate(MENU):
    items.append({"type": "button", "rect": [8, 31 + i * 34, 188, 27],
                  "state": "normal", "label": lbl})
add("system-menu", items)

# ------------------------------------------------------------------- 9 storage
items = titlebar("storage", 539, close=[515, 8, 18, 18])
TABS = ["消耗品", "装備品", "カード", "材料", "収集品", "その他"]
for i, lbl in enumerate(TABS):
    items.append({"type": "tab", "rect": [12, 40 + i * 39, 66, 33],
                  "state": "selected" if i == 0 else "normal", "label": lbl})
STORAGE = [[42, 18, 60, 7, 3, 2, 2], [10, 1, 5, 24, 17, 6, 2],
           [31, 9, 4, 2, 3, 12, 22], [1, 1, None, None, None, None, None],
           [None] * 7]
for r, row in enumerate(STORAGE):
    for c, qty in enumerate(row):
        items.append({"type": "grid cell", "rect": [88 + c * 60, 30 + r * 63, 60, 63],
                      "state": f"occupied x{qty}" if qty else "empty",
                      "label": f"storage slot r{r}c{c}"})
items += [
    {"type": "button", "rect": [129, 355, 23, 27], "state": "normal", "label": "list mode (icon)"},
    {"type": "button", "rect": [160, 355, 47, 27], "state": "normal", "label": "search (icon)"},
    {"type": "button", "rect": [244, 355, 86, 27], "state": "normal", "label": "search"},
    {"type": "button", "rect": [344, 355, 84, 27], "state": "normal", "label": "sort"},
    {"type": "button", "rect": [440, 355, 66, 27], "state": "normal", "label": "close"},
]
add("storage", items)

# ----------------------------------------------------------------- 10 inventory
items = titlebar("inventory", 484, minimize=[435, 8, 17, 16], close=[460, 8, 18, 17])
ITABS = ["item", "equip", "etc", "etc", "cash"]
for i, lbl in enumerate(ITABS):
    items.append({"type": "tab", "rect": [10, 30 + i * 39, 26, 36],
                  "state": "selected" if i == 0 else "normal", "label": lbl})
INV = [[2, 15, 147, 88, 10, 5, 2], [8, 23, 1, 2, 1, 1, 1],
       [13, 2, 5, 2, 1, 15, 1], [2, 1, 22, 7, 25, 23, 18]]
for r, row in enumerate(INV):
    for c, qty in enumerate(row):
        items.append({"type": "grid cell", "rect": [42 + c * 54, 30 + r * 61, 54, 61],
                      "state": f"occupied x{qty}", "label": f"inventory slot r{r}c{c}"})
items += [
    {"type": "scrollbar", "rect": [457, 30, 21, 230],
     "state": "vertical, thumb near top", "label": None},
    {"type": "button", "rect": [109, 275, 19, 20], "state": "normal", "label": "search (icon)"},
]
add("inventory", items)

# ----------------------------------------------------------------- 11 chat-room
items = titlebar("chat-room", 495, close=[470, 7, 18, 18])
LINES = ["Sebas*：レイドリック終わったー", "SakumaRiri：おつかれさま〜",
         "ANRI：もう1周いきますか？", "Show_A：いきましょう！",
         "経験値が 10800 上がりました。"]
for i, txt in enumerate(LINES):
    items.append({"type": "list row", "rect": [7, 33 + i * 25, 460, 25],
                  "state": "read-only log line", "label": txt})
items += [
    {"type": "scrollbar", "rect": [470, 28, 20, 152],
     "state": "vertical, thumb upper third", "label": None},
    {"type": "text field", "rect": [7, 196, 458, 21],
     "state": "empty, caret at left", "label": "chat input"},
    {"type": "button", "rect": [468, 196, 21, 21], "state": "normal",
     "label": "chat settings (icon)"},
]
add("chat-room", items)

doc = {
    "image": "reference-native.png",
    "size": [1536, 1024],
    "coordinate_space": "native pixels in the full frame, origin top-left, rect = [x, y, w, h]",
    "pass": "first",
    "accuracy_note": ("Rects were measured by eye from 2x nearest-neighbour crops overlaid "
                      "with a 20px native grid. Explicit controls are accurate to about "
                      "+/-3 px; grid cells are generated from measured pitch and origin and "
                      "are accurate to about +/-4 px. Types are drawn from the map #103 list."),
    "counts_by_type": {},
    "controls": C,
}
for c in C:
    doc["counts_by_type"][c["type"]] = doc["counts_by_type"].get(c["type"], 0) + 1
doc["counts_by_type"] = dict(sorted(doc["counts_by_type"].items()))
doc["total_controls"] = len(C)

json.dump(doc, open(OUT, "w"), indent=1, ensure_ascii=False)
print("controls:", len(C))
for k, v in doc["counts_by_type"].items():
    print(f"  {k:>12}: {v}")
per = {}
for c in C:
    per[c["window"]] = per.get(c["window"], 0) + 1
print("per window:", json.dumps(per, ensure_ascii=False))
