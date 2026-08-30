# Behaviour Cards v1 — Ragnarok Online, Japanese client, classic-era UI

Research ticket [#104](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/104) under map [#103](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/103).
Written 2026-08-29. **The owner confirms these cards; this document does not decide anything.**

One card per control type in the Control Catalogue. Each card says what gesture produces what visible
response, how long the response takes **in frames**, whether it reverses, and **whether the Source Game
shows a hover state**. Hover is being added in-style everywhere regardless — the card exists to record
what the source actually did, not to authorise a decision.

Where the evidence does not reach, the card says **unverified**. Nothing here is inferred silently.

---

## Evidence base

**Frame rate for every timing in this document: 30 fps.** One frame = 33.3 ms. All four videos were
decoded at 1280×720, which is the resolution the game was running at, so the UI is at 1:1 pixel scale
and every crop is pixel-exact. Timestamps are given as `hh:mm:ss.mmm` into the source video.

### Primary — gameplay video (private study)

| Video | Title | Channel | Uploaded |
| --- | --- | --- | --- |
| [`P7t7cIvtEQo`](https://www.youtube.com/watch?v=P7t7cIvtEQo) | ラグナロクオンライン　スタートアップガイド(ウィンドウ編 その１) | FRIES17 | 2020-05-09 |
| [`oCsKRSKr2nA`](https://www.youtube.com/watch?v=oCsKRSKr2nA) | ラグナロクオンライン　スタートアップガイド(ウィンドウ編 その２) | FRIES17 | 2020-07-05 |
| [`JaA_UUL4a5w`](https://www.youtube.com/watch?v=JaA_UUL4a5w) | ラグナロクオンライン　スタートアップガイド(ウィンドウ編 その３) | FRIES17 | 2020-07-19 |
| [`92A2MpKGBXI`](https://www.youtube.com/watch?v=92A2MpKGBXI) | ラグナロクオンライン　スタートアップガイド(ゲームスタート編) | FRIES17 | 2020-04-26 |

These are a Japanese-client tutorial series that walks each window in turn, which is why they carry so
many deliberate, isolated control interactions. Two further videos were downloaded and reviewed but
produced no usable control evidence: `917aJBSiW6g` (chat-window feature tour — a 1920×1080 source
downscaled, so the UI is no longer pixel-exact) and `le_Z9rXPPb0` (2004 Chaos-server GvG, 60 fps, no UI
interaction). Nico Nico videos `sm5475856` and `sm6506563` are 512×384 at 5–10 fps — too coarse to read
a control state.

### Secondary — official GungHo Japanese play manual

Screenshots under `https://ragnarokonline.gungho.jp/playmanual/images/…`. These are the publisher's own
captures of the same client. Used where they show a state set the videos do not (tab active/inactive,
the skill stepper on a fresh character).

### Secondary — roBrowser

[roBrowser](https://github.com/vthibault/roBrowser), an open-source reimplementation of the RO client.
Cited for mechanism and constants only, always labelled. **It is a reimplementation, not the client**,
and in several places it does not implement what the real client visibly does — where that is so, the
card says so rather than borrowing roBrowser's behaviour. No roBrowser file is copied into this repo.

### Licence note

Every image under `artifacts/references/ro-source-game/behaviour/` is a crop retained for **private
study** — non-commercial research into UI behaviour, not redistribution as media. Ragnarok Online
© Gravity Co., Ltd. & Lee Myoungjin (studio DTDS) / GungHo Online Entertainment.

---

## Method, and the trap in it

The videos were swept with a UI-change detector (per-frame count of light, low-saturation pixels in the
top 540 rows, differenced between samples) to locate every moment a window opened, closed, changed or
moved. Candidates were then burst-extracted at native 30 fps and read frame by frame.

**The trap: these tutorials are cut every few seconds.** In the options chapter of `JaA_UUL4a5w` there
are 38 editing cuts in 17 seconds. A cut looks exactly like an instant UI change — the pointer teleports,
a window vanishes, a highlight moves — and it is trivially easy to read one as a one-frame response.

So every timing claim below was re-checked against a **cut detector**: the mean absolute per-frame
difference of a region of the frame containing **no UI at all**, only the game world. Across a cut that
region jumps 3–10; within a shot it sits at 0.00–0.5. A frame pair is quoted as a measured transition
**only** where that UI-free region stayed below 0.5 across it.

Several claims did not survive that check and have been demoted to "two states, no timing" — they are
marked in place, and the frames are kept because the *states* are still good evidence. The pairs that
did survive are labelled **cut-verified**.

The same UI-change detector was also run at 6 fps across the whole of `P7t7cIvtEQo`, `oCsKRSKr2nA`,
`JaA_UUL4a5w`, `92A2MpKGBXI` and `917aJBSiW6g` looking for **runs** of sustained motion — a drag or a
scroll would show as one. It found none in any UI region. That is the reason the scrollbar-gesture and
window-drag cards are thin: the tutorials are cut before any sustained gesture completes.

---

## Cross-cutting findings

1. **Everything measured is instantaneous.** Five separate cut-verified transitions each complete
   **within one frame at 30 fps**, with no easing, fade, slide or growth:
   - dropdown list opens (00:19:39.567 → .600)
   - dropdown hover bar moves between rows (00:19:43.900 → .933)
   - dropdown commit + whole-UI reskin (00:19:46.767 → .800)
   - dropdown commit + whole-UI reskin, the reverse direction (00:20:08.097 → .130)
   - a window is constructed (00:20:11.367 → .400)

   Nothing in the corpus takes 2 frames. **There is no evidence of any animation anywhere in this UI.**
   *Secondary agreement:* roBrowser contains exactly one animation in its whole UI layer — a 500 ms
   opacity fade when a dragged window is released (`UIComponent.js`) — and no CSS transitions at all.

2. **The source does have hover states, and they are common.** Captured on menu buttons, dropdown list
   rows, list rows, grid cells, and icon buttons (which also raise a tooltip). One of them — the
   dropdown row — is cut-verified as moving in a single frame.

3. **Hover and selection share one highlight in list-like controls.** In the open Skin dropdown, the
   bar marks the current value until the pointer enters the list, then it marks the pointed row
   instead. There is no second, dimmer hover treatment layered on top of a selection. The **field does
   not preview** the hovered value — it keeps showing the committed one.

4. **The highlight colour belongs to the skin, not the control.** In the blue `<Basic Skin>` the
   dropdown hover bar is saturated blue with white text; in the `scribbling kid` skin the same bar is
   pale green with black text (`dropdown/08-revert-before.png`). Any replica needs the highlight as a
   themed token, not a hard-coded colour.

5. **A pressed/held state was never isolated.** Every click in this corpus goes down and up inside one
   or two frames, so no frame captured a button mid-press. Whether the client draws a distinct pressed
   sprite is **unverified from video**. *Secondary:* roBrowser's `UIComponent.js` binds a third image
   per button (`data-down`, conventionally `btn_<name>_b.bmp` beside `btn_<name>.bmp` and
   `btn_<name>_a.bmp`), swapped on `mousedown` and restored on `mouseup` — so a three-state button
   sprite family does exist in the client's art. Some controls only ever get two: roBrowser's title-bar
   `close` and `mini` buttons declare hover (`sys_close_on.bmp`) but **no** down state.

6. **Tooltips are a hover affordance in their own right.** Icon buttons and grid cells raise a small
   floating label after the pointer settles. The delay before a tooltip appears is **unverified**.

---

## button

**Where:** ゲームオプション menu rows; 基本情報 text buttons (status/rec/items/equip/skill/map/chat/friend);
確定 / リセット / OK / cancel / close footers; the icon-button grid; login dialogues.

| | |
| --- | --- |
| **Gesture** | Pointer enters the button's rectangle. |
| **Response** | The button face fills with a blue left-to-right gradient; the label stays put; the border does not move. |
| **Hover in the source** | **Yes — confirmed.** `01-menu-hover-sound.png` (00:20:13.933) has the pointer on サウンド設定 and that button lit; `02-menu-hover-shortcut.png` (00:20:13.967) has the pointer one row down on ショートカット設定 and *that* button lit instead. The lit button is not a click-selection: ショートカット設定 is lit from 00:20:13.97, and the window it opens does not appear until 00:20:16.0 — it is lit merely because the pointer is on it. The same is visible on the login dialogue's OK (`04-login-ok-hover.png`). |
| **Timing** | **Unverified for buttons specifically.** ⚠️ An editing cut lies between frames 01 and 02 (UI-free region jumps 8.5), so that pair does **not** time the transition, and a 9-second frame-by-frame search of the menu found no hover change inside a single shot. The one measured hover transition in the corpus is on a *dropdown row* and takes 1 frame (see **dropdown**); ≤1 frame is the reasonable expectation for buttons but is not measured. |
| **Reversibility** | Yes — the idle face returns with no residue; both states appear on both buttons across the two shots. |
| **Click → action** | **Unverified.** ⚠️ The click on ショートカット設定 at 00:20:16 straddles three consecutive cut frames. What *is* cut-verified, on a different window, is that **window construction takes one frame** (`close/04`,`close/05`). |
| **Pressed state** | **Unverified.** Across the ~30 frames the pointer rested on ショートカット設定 before the window appeared, the button stayed in its hover fill; no darker press face appeared. |
| **Disabled state** | Present in the client — `text-field/04-login-password-masked.png` shows two greyed, non-editable fields with grey labels beside an active one. No disabled *button* was captured. Partially verified. |
| **Evidence** | `behaviour/button/` (6 crops + `sources.json`) |

---

## checkbox

**Where:** サウンド設定 `on`; グラフィック設定 スナップ attack/skill/item, Trilinear, NoCtrl;
スキルリスト title-bar 説明表示; ショートカット設定 チャット入力タイプ変更; 装備 装備公開.

| | |
| --- | --- |
| **Gesture** | Click the box (or, in the sources, the box+label pair — the exact hit region is **unverified**). |
| **Response** | A black tick is drawn inside the same square. **The square itself does not change**: same size, same border weight, same fill. Only the tick appears or disappears. |
| **Timing** | **Unverified** — no frame pair caught one toggling. The two states are captured on the same control 16.5 s apart (`03-skill-description-off.png` at 00:09:40.000, `04-skill-description-on.png` at 00:09:56.500). |
| **Reversibility** | Yes — both states of the same control are captured. |
| **Hover in the source** | **Not observed.** No frame caught the pointer resting on a checkbox. Secondary: roBrowser's option-window checkboxes are bare native `<input type="checkbox">` with no hover art at all; the one bitmap checkbox it has (`checkbox_0.bmp` / `checkbox_1.bmp`, Equipment's 装備公開) also has no hover image. **Unverified for the real client.** |
| **Mixed states in one frame** | Yes — `01` shows BGM `☐on` beside SOUND `☑on`; `02` shows `☑attack ☐skill ☑item` and `☐Trilinear ☑NoCtrl`. This is the state set to copy. |
| **Evidence** | `behaviour/checkbox/` (5 crops + `sources.json`) |

---

## radio

**Where:** パーティー設定 (three groups); the パーティー window's ○友達 / ◉パーティ view switch.

| | |
| --- | --- |
| **Gesture** | Click one option in a group. |
| **Response** | That option's ring gains a filled blue disc; the other option in the group loses its disc and becomes an empty ring. Exactly one filled per group. |
| **Timing** | **Unverified** — no toggle captured. Only a settled frame showing three groups at once. |
| **Reversibility** | Selection moves between the group's members; there is no "none selected" state in any captured group. Whether a group can be emptied is **unverified**. |
| **Hover in the source** | **Not observed.** Secondary: roBrowser's only radio group (ChatRoomCreate Public/Private) is a bare native `<input type="radio">` with no hover art. **Unverified for the real client.** |
| **Note** | The radio glyph is visually distinct from the checkbox glyph — circle vs square — so the two are not one control with two skins. |
| **Evidence** | `behaviour/radio/` (2 crops + `sources.json`) |

---

## tab

**Where:** horizontal — 会話ウィンドウ message tabs, ショートカット設定, ゲーム設定, 装備アイテム.
Vertical — 所持アイテム (消耗/装備/収集/個人), スキルリスト (job tiers).

| | |
| --- | --- |
| **Gesture** | Click a tab. |
| **Response** | The clicked tab becomes the active tab: it is drawn **lighter, slightly taller, and flush with the panel below — its bottom border disappears so tab and panel read as one surface.** Inactive tabs sit lower, keep a full box border, and are separated from the panel by a line. The panel content is replaced with that tab's content. |
| **Timing** | **Unverified** — no tab switch was captured mid-flight. The state set is captured three ways instead: `02-chat-three-tabs.png` (active vs two inactive in one frame) and the manual triple `05/06/07`, which is the same ゲーム設定 strip with 表示設定, 操作設定 and その他 active in turn. |
| **Reversibility** | Yes — the manual triple proves the strip returns to a consistent inactive rendering for whichever tab is not selected. |
| **Hover in the source** | **Not observed.** No frame caught the pointer over a tab. **Unverified.** Secondary: roBrowser's Inventory/Storage tabs are invisible hit targets over one composite strip bitmap (`tab_itm_01.bmp` … `tab_itm_03.bmp`, `tab_itm_ex_01.bmp` … `_07.bmp`) with one image per *selected* tab and **no hover image**, switched on `mousedown` rather than `click`. |
| **Vertical tabs** | The same active/inactive grammar rotated 90°: text runs top-to-bottom, the active tab is flush with the panel on its right. |
| **Evidence** | `behaviour/tab/` (4 video crops + 4 manual crops + `sources.json`) |

---

## stepper (`◁ n / n ▷`)

**Where:** the skill grid in スキルリスト. Each cell shows an icon, a truncated name, and a level line.

| | |
| --- | --- |
| **Form** | On some cells the level line reads `◁ 7 / 7 ▷` — a small blue left triangle, the current/max pair, a small blue right triangle, both triangles inside the cell's own width. On other cells in the same window the same line reads a bare number (`5`, `1`, `4`) with no arrows at all. |
| **Gesture → response** | **Unverified.** No frame in the corpus caught an arrow being clicked or a level changing. What each arrow does is not established by primary evidence. |
| **Timing** | **Unverified.** |
| **Reversibility** | **Unverified.** The presence of 確定 (confirm) and リセット (reset) buttons in the same window's footer is consistent with an allocate-then-commit model in which リセット reverses pending steps, but no frame demonstrates it. |
| **Hover in the source** | **Not observed** on the arrows themselves. The **cell** the arrows live in does have a hover state — see list-selection. |
| **When the arrows appear** | **Unverified.** `01-skill-stepper-present.png` (00:09:56.500) and `02-skill-no-stepper.png` (00:09:40.000) are the same character, same window, same skill (キリエエリソン `7 / 7`), 16.5 s apart — arrows present in one, absent in the other. Two candidate triggers were ruled out: the 説明表示 checkbox differs between the two frames but the manual screenshot `03` shows arrows in a window that has no such checkbox, and the footer skill-point total is non-zero in both. The manual pair `03`/`04` shows arrows on a learned, raisable skill and no arrows on quest/other-tab skills that also have a level — i.e. the arrows are **per-skill, not per-window**. That is as far as the evidence goes. |
| **Hold-to-repeat** | **Unverified.** Secondary: roBrowser has no stepper at all; its nearest equivalents (SkillList's `+`, WinStats' six stat `+` buttons) are single-shot, one point per click, with no repeat. That is weak evidence about the real client's arrows and is offered only as a default to fall back on. |
| **Evidence** | `behaviour/stepper/` (2 video crops + 2 manual crops + `sources.json`) |

---

## slider

**Where:** サウンド設定 BGM and SOUND (the "BGM/Effect" pair named in the ticket);
グラフィック設定 スプライト解像度 and テクスチャ解像度.

| | |
| --- | --- |
| **Form** | Left `◁` arrow button, a sunken horizontal track, a small round blue thumb, right `▷` arrow button, then (in サウンド設定) an `on` checkbox. The arrows are part of the control, flush against the track's ends. |
| **Gesture → response** | **Unverified.** No drag, no arrow click, and no value change was captured. The thumb does not move anywhere in the ~4 s the サウンド設定 window is on screen. |
| **Timing** | **Unverified.** |
| **Value → position** | Confirmed that thumb position encodes value: in `01-sound-bgm-effect.png` the BGM and SOUND thumbs sit at visibly different points on identical tracks. |
| **End clamping** | **Confirmed.** In `02-graphics-resolution.png` both graphics thumbs are hard against the right end of their tracks — the thumb stops flush at the track end and does not overlap or pass behind the `▷` arrow button. That is the maximum-value rendering to reproduce. |
| **Reversibility** | **Unverified.** |
| **Hover in the source** | **Not observed** on the thumb or the arrows. **Unverified.** Secondary: roBrowser's sliders are bare native `<input type="range">` with no custom art or hover handling — no help here. |
| **Range and step (secondary only)** | roBrowser: BGM and Effect are `min=0 max=100 step=1 value=50`; the graphics quality slider is `min=25 max=100 step=5 value=100`. Treat as a starting default, **not** as a measured fact about the JP client. |
| **Evidence** | `behaviour/slider/` (2 crops + `sources.json`) |

---

## scrollbar

**Where:** 会話ウィンドウ message log; the NewTab display-info popup list; the chat-room Limit dropdown
list; ゲーム設定 setting list.

| | |
| --- | --- |
| **Form** | **Confirmed.** A vertical bar with exactly **one arrow button at each end** (`▲` top, `▼` bottom) and a thumb between them on a recessed track. Two visual families appear in the client: the chat log uses a **black** track with a pale thumb and dark arrow blocks; window lists use a **light** track with blue arrows and a blue thumb. |
| **Thumb size** | **Confirmed** to be proportional: in `01-chatlog-scrollbar.png` the thumb fills most of a short track (little overflow); in `02-popup-list-scrollbar.png` it is a short thumb part-way down a long track (large overflow). |
| **Thumb drag** | **Unverified.** No drag of a scrollbar thumb exists anywhere in the corpus — the sustained-motion sweep across all five videos found no scroll run. |
| **Arrow-button step** | **Unverified.** Neither the step size nor whether holding an arrow auto-repeats was captured. |
| **Mouse wheel** | **Unverified from video.** Secondary, roBrowser only: the wheel is quantised to one row per notch — `Inventory.js` and `Storage.js` snap `scrollTop` to a **32 px** grid and move one grid step per notch (32 px = one item row); `ChatBox.js` does the same at **14 px** (one chat line). roBrowser's `SkillList` has no wheel handler and scrolls natively. |
| **Geometry (secondary only)** | roBrowser skins the native scrollbar at **13 px** wide with a 12 px decrement and 13 px increment button and a **6 px minimum thumb**; its chat-log scrollbar is **10 px** wide with 10 px arrows. Note roBrowser implements *no* scrollbar interaction of its own — thumb drag, arrow step and repeat are delegated to the browser — so it is **not** evidence for the real client's gesture behaviour, only for its metrics. |
| **Reversibility** | **Unverified.** |
| **Hover in the source** | **Not observed** on any scrollbar part. **Unverified.** |
| **Evidence** | `behaviour/scrollbar/` (3 video crops + 1 manual crop + `sources.json`) |

**This is the thinnest card in the set, and the map's quality floor demands scrollbars answer thumb
drag, arrow step and wheel.** Those gestures will have to be specified from intent rather than copied
from the source, unless further footage is found.

---

## dropdown

**Where:** スキン in グラフィック設定 (the one named in the ticket); Limit and Type in チャットルーム作成.
**This is the best-evidenced control in the corpus** — every state and every transition is cut-verified.

| | |
| --- | --- |
| **Closed form** | A sunken field showing the current value, with a **raised** `▽` arrow button butted against its right edge. |
| **Gesture: click the field or arrow** | The list opens **downward**, drawn over whatever is beneath it (it is not clipped by its own window). Its width matches the field. The current value is the highlighted row. The arrow button is repainted **darker/inset** while the list is open. |
| **Timing: open** | **1 frame — cut-verified.** `01-closed.png` at 00:19:39.567 → `02-open-current-marked.png` at 00:19:39.600. Burst-confirmed: frames 0–17 of a 30 fps burst closed, frame 18 fully open, and the UI-free region reads 0.00 across the pair. No slide, no fade, no partial draw. |
| **Gesture: move the pointer over a row** | The highlight bar **moves to the pointed row** and leaves the current-value row unhighlighted. One bar serves both roles. The field keeps showing the committed value — hover does not preview. |
| **Timing: hover** | **1 frame — cut-verified.** `06-row-hover-frame-a.png` at 00:19:43.900 (bar on `Rec_Replay`) → `07-row-hover-frame-b.png` at 00:19:43.933 (pointer one row down, bar on `scribbling kid`). UI-free region 0.00 across the pair. **This is the corpus's one measured hover transition.** |
| **Gesture: click a row** | In **one frame**: the list disappears, the field text becomes the chosen value, and — because this particular dropdown is the UI skin — **every window on screen is repainted** in the new skin. |
| **Timing: commit** | **1 frame — cut-verified, twice, in both directions.** Forward: 00:19:46.767 → 00:19:46.800 (`03` → `04`), `<Basic Skin>` → `scribbling kid`. Reverse: 00:20:08.097 → 00:20:08.130 (`08-revert-before.png` → `09-revert-after.png`), `scribbling kid` → `<Basic Skin>`, with the ステータス window behind it repainting in the same frame. UI-free region 0.00 across both pairs. |
| **Reversibility** | **Yes — measured as a full round trip.** The two commits above are each other's inverse, ~21 s apart, and the UI returns to its original appearance. |
| **Skin-dependent highlight** | `08-revert-before.png` shows the same open list in the `scribbling kid` skin: the hover bar is **pale green with black text** rather than blue with white. The highlight is a skin token. |
| **Dismiss without choosing** | **Unverified** — no capture of clicking away from an open list. |
| **Scrolling list** | When the list is longer than its box it carries its own scrollbar (`05` / `scrollbar/03`). |
| **Evidence** | `behaviour/dropdown/` (9 crops + `sources.json`) |

---

## list row / grid cell selection

**Where:** ショートカット設定 key list; the NewTab display-info list; the スキルリスト skill grid;
所持アイテム item grid; the パーティー member list.

| | |
| --- | --- |
| **Gesture: pointer over a list row** | The row gains a **thin blue outline box** drawn around it — an outline, not a fill. (`03-popup-row-hover.png`.) |
| **Gesture: pointer over a grid cell** | The cell gains a **pink/red fill behind the icon**; neighbouring cells are unchanged. (`04-skill-grid-cell-hover.png`.) A floating name tooltip also appears for item cells. |
| **Hover in the source** | **Yes — confirmed for both list rows and grid cells**, with two visibly different treatments (outline for rows, fill for cells). Timing not measured here; the dropdown row's 1-frame move is the nearest measurement. |
| **Selected row** | A **dark grey block with white text**, filling the selected cell within the row rather than the whole row. (`01-shortcut-row-selected.png`, 00:20:16.200.) This is a much stronger treatment than the hover outline, so hover and selection are distinguishable at a glance. |
| **Timing** | **Unverified.** ⚠️ `01` (selected) and `02-shortcut-row-committed.png` (00:20:16.567, cleared and the value changed from `ショートカット 4-8` to `4-7`) straddle an editing cut at 00:20:16.500, so the pair shows both states but does not time the change. |
| **Reversibility** | Selection clears — `02` shows the list back to a uniform unselected rendering. |
| **Grid mode change** | The item grid has a whole-grid state: after NPC売却ロック適用 every cell is repainted blue and a banner is laid across the window (`05` vs `06`). Reversible — the grid returns to normal later in the same chapter. |
| **Single vs double click** | **Unverified from video.** Secondary: roBrowser selects a skill row on `mousedown` and uses the row on `dblclick`; its Inventory/Storage grids have **no** selection state at all, only a hover tooltip, and act on `dblclick`. The real JP client clearly *does* have a grid mode state, so roBrowser is incomplete here. |
| **Evidence** | `behaviour/list-selection/` (7 crops + `sources.json`) |

---

## window title drag

| | |
| --- | --- |
| **Drag surface** | The title bar: window icon, title text, sometimes an inline control (スキルリスト carries its 説明表示 checkbox there), then `⊖` and `✕` at the right end. One window differs — the guide's narration for 会話ウィンドウ says to move the pointer to the window's edge until the cursor changes, i.e. that window is moved by its input bar / border rather than a title bar. |
| **Gesture → response** | **Unverified.** Windows appear at different screen positions across the corpus, so they do move — but every position change in these videos happens across an editing cut (a single-frame jump of 40 %+ of the UI pixels with the game world jumping too), not a drag. A sustained-motion sweep at 6 fps over all five videos found **no drag run anywhere**. |
| **Timing / motion profile** | **Unverified.** The map's ≥30-frame monotonic-drag gate has no source reference at all. |
| **Ghosting, snapping, clamping, z-order on drag** | **Unverified.** |
| **Hover in the source** | **Not observed** on a title bar. **Unverified.** |
| **Resize is a separate control** | Confirmed: windows carry a diagonal hatched **resize grip** at the bottom-right corner, distinct from the title bar (`04-manual-resize-grip.png`, circled by the manual's own annotation; also visible in the 所持アイテム and スキルリスト frames). |
| **Secondary (roBrowser), offered as a default only** | `UIComponent.prototype.draggable`: drag starts on left `mousedown` with **no threshold**, position is repolled on a **15 ms** timer (≈66 Hz) rather than from mouse events, a **10 px magnet** snaps the window to each screen edge, the window is **not** clamped and can be dragged off-screen, opacity drops 0.02 per tick to a floor of **0.7** while dragging and animates back to 1.0 over **500 ms** on release, and any `mousedown` reaching the window body raises it (base z-index 50). None of this is confirmed for the JP client. |
| **Evidence** | `behaviour/window-drag/` (3 video crops + 1 manual crop + `sources.json`) |

---

## minimize / restore

| | |
| --- | --- |
| **The `⊖` button** | Confirmed present as a round blue disc bearing a minus, immediately left of the `✕` on the title bar of every window that has one (`03-titlebar-minimize-close.png`, 10× magnification). |
| **Gesture → response for `⊖`** | **Unverified.** No frame in the corpus shows a window collapsed to a bare title strip, and no `⊖` click was captured. Secondary: roBrowser's Inventory hides the body panel and squeezes the window to **17 px** — a title strip — remembering the previous height to restore; its Equipment window toggles the body without changing height; its SkillList declares the button but never wires it. Three different behaviours in one reimplementation, so this is weak. |
| **A collapse that *is* confirmed** | 基本情報 carries a small triangular handle in the middle of the separator below its stats block. `01-basicinfo-expanded.png` (00:02:56.000) shows the window with its icon panel; `02-basicinfo-collapsed.png` (00:10:10.000) shows the same window with the panel gone and the window ending just below the handle. Nothing else changes — same width, same stats block, same eight text buttons. |
| **Timing** | **Unverified** — the two states are seven minutes apart, not a transition pair. |
| **Reversibility** | Yes at the state level — both states of the same window exist in the same video. |
| **Handle glyph change** | **Unverified.** The handle reads as a small triangle in both frames; at this capture quality the up/down difference cannot be resolved. Secondary: roBrowser swaps `viewon.bmp` ⇄ `viewoff.bmp` on this control, so the glyph does change in the client's art. |
| **Hover in the source** | **Not observed.** Secondary: roBrowser gives `.mini` a hover image (`sys_mini_on.bmp`) but no pressed image. |
| **Evidence** | `behaviour/minimize-restore/` (3 crops + `sources.json`) |

---

## close

| | |
| --- | --- |
| **The `✕` button** | Confirmed: a round blue disc bearing a cross, at the right end of the title bar, immediately right of `⊖` (`03-inventory-close-button.png`, 10× magnification). Some windows also carry a labelled `close` / `cancel` button in a footer (`button/06`). |
| **Gesture → response** | The window disappears **whole** — `01-sound-window-before.png` (00:20:13.933) has サウンド設定 on screen and `02-sound-window-after.png` (00:20:13.967) does not. |
| **Timing** | **Unverified.** ⚠️ Those two frames straddle an **editing cut** (the UI-free game-world region jumps 7.7), so they do not time a teardown. What *is* cut-verified is the inverse: **window construction takes exactly one frame** — `04-window-open-frame-a.png` (00:20:11.367, no サウンド設定) → `05-window-open-frame-b.png` (00:20:11.400, the window complete and correct), UI-free region 0.00 across the pair. No grow-in, no fade. Popup teardown is also cut-verified at one frame: the dropdown list vanishes in a single frame at both commits. Whole-window teardown in one frame is the reasonable expectation on that basis, but it is not directly measured. |
| **Which gesture** | **Unverified.** In the captured frames the pointer is not over the window's `✕`, so this teardown may have been triggered by the menu or by ESC rather than by the close button. |
| **Reversibility** | Reopening from the menu is available; whether it reopens at the same position with the same contents is **unverified**. |
| **Hover in the source** | **Not observed** on `✕`. **Unverified.** Secondary: roBrowser gives the title-bar close a hover image (`sys_close_on.bmp`) and **no** pressed image; a footer `close` button gets the full `btn_close.bmp` / `_a` / `_b` triple. |
| **Hide vs destroy** | **Unverified** from video. Secondary: roBrowser splits these — most windows `hide()` (state preserved), the two option windows `remove()` (torn down and preferences saved). |
| **Evidence** | `behaviour/close/` (5 crops + `sources.json`) |

---

## text field + send

**Where:** 会話ウィンドウ input bar; チャットルーム作成 Title and Sign; the replay filename prompt;
the login パスワード入力 dialogue.

| | |
| --- | --- |
| **Form** | A sunken field with a light interior and a dark border. Text is left-aligned with a small inset. |
| **Caret** | **Confirmed.** A thin vertical bar drawn immediately after the last character (`01-replay-filename-typed.png`: `replay010101|`; `02-chatroom-title-caret.png`: `ちゃっとるーむ|`). In an empty field the caret sits at the field's left inset (`03-chat-input-bar.png`). Blink rate is **unverified**. |
| **Typing → response** | Characters appear left to right and the caret advances. Confirmed by the presence of partial typed content, not by a frame-by-frame capture; per-keystroke latency is **unverified**. |
| **Masked input** | Confirmed: the password field renders `****`, one glyph per character (`04-login-password-masked.png`). |
| **Disabled field** | Confirmed: in the same dialogue, 新規パスワード and 確認パスワード are drawn with a **grey interior and a grey label** while the active field is white with a black label. This is the client's own disabled-input rendering. |
| **Send (Enter)** | **Unverified.** No frame captured a submit — no typed-then-cleared field, no message appearing in the log as a result of a send. |
| **Field cleared after send** | **Unverified.** |
| **History (up/down)** | **Unverified.** |
| **Hover in the source** | **Not observed** on any text field. **Unverified.** |
| **Secondary (roBrowser), offered as a default only** | `ChatBox.js`: Enter forces focus back to the message box and submits; the field is cleared (`$text.val('')`) *before* dispatch; Enter on an **empty** field is not a no-op — it toggles the whole input bar off and battle mode on; text starting with `/` is routed to a command handler and never sent as speech; Up/Down walk two independent histories and the recalled text is fully selected; Tab swaps between the nick and message fields; clicking a field selects all of it; the log keeps 50 lines and always auto-scrolls to the bottom. None of this is confirmed for the JP client. |
| **Evidence** | `behaviour/text-field/` (4 crops + `sources.json`) |

---

## Coverage summary

| Control | Idle | Hover in source | Pressed | Selected / active | Transition timing | Gesture → action |
| --- | --- | --- | --- | --- | --- | --- |
| button | ✅ | ✅ **yes** | ❌ unverified | ✅ | ❌ unverified (cut) | ❌ unverified (cut) |
| checkbox | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred |
| radio | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred |
| tab | ✅ | ❌ unverified | ❌ unverified | ✅ full set | ❌ unverified | ⚠️ inferred |
| stepper | ✅ | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| slider | ✅ + end clamp | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| scrollbar | ✅ + thumb sizing | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| dropdown | ✅ | ✅ **yes, 1 frame** | ✅ arrow inset while open | ✅ | ✅ **1 frame, cut-verified ×4** | ✅ |
| list / grid selection | ✅ | ✅ **yes** (both kinds) | ❌ unverified | ✅ | ❌ unverified (cut) | ✅ states only |
| window title drag | ✅ | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| minimize / restore | ✅ | ❌ unverified | ❌ unverified | ✅ both panel states | ❌ unverified | ❌ unverified |
| close | ✅ | ❌ unverified | n/a | n/a | ⚠️ open = 1 frame (verified); close not measured | ❌ gesture unverified |
| text field + send | ✅ + caret + masked + disabled | ❌ unverified | n/a | ✅ | ❌ unverified | ❌ unverified |

**What would close the biggest gaps, in priority order**

1. **A scrollbar being driven.** Nothing in this corpus scrolls by gesture. A recording of a warehouse
   or mail window being scrolled — thumb drag, then arrow clicks, then wheel — would settle three of
   the map's twelve quality gates at once.
2. **A window being dragged.** The ≥30-frame monotonic-drag gate has no source reference at all.
3. **A chat message being typed and sent**, for the field-clear and log-append behaviour.
4. **A skill stepper arrow being clicked**, for what `◁` and `▷` actually do and whether they repeat.
5. **Any button held down long enough to expose a pressed sprite.**

Unedited play footage — a stream VOD or a long single-take session — is the likeliest source for all
five. The tutorial series is cut every few seconds, which is precisely why no sustained gesture
survives in it.
