# Behaviour Cards v1 — Ragnarok Online, Japanese client, classic-era UI

Research ticket [#104](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/104), extended in
place by [#115](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/115), under map
[#103](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/103). Written 2026-08-29.
**The owner confirms these cards; this document does not decide anything.**

Everything #115 added is marked `(#115)` where it sits, so the two passes stay tellable apart. #104's
own wording is kept wherever it was right, including where it recorded not knowing something.

One card per control type in the Control Catalogue. Each card says what gesture produces what visible
response, how long the response takes **in frames**, whether it reverses, and **whether the Source Game
shows a hover state**. Hover is being added in-style everywhere regardless — the card exists to record
what the source actually did, not to authorise a decision.

Where the evidence does not reach, the card says **unverified**. Nothing here is inferred silently.

---

## Evidence base

**Two frame rates, and every timing below says which.** #104's four tutorial videos are **30 fps**
(one frame = 33.3 ms), decoded at 1280×720 — the resolution the game was running at — so their UI is at
1:1 pixel scale and every crop from them is pixel-exact. #115's two stream VODs are **60 fps** (one
frame = 16.7 ms) but **not** pixel-exact; see their own section below. Timestamps throughout are
`hh:mm:ss.mmm` into the source video.

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

### Primary — unedited stream VODs (added by [#115](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/115))

**These carry no editing cuts at all**, which is the whole point of them: a gesture that lasts several
seconds survives intact, and a frame pair can be trusted without argument.

| Video | Title | Channel | Uploaded | Length |
| --- | --- | --- | --- | --- |
| [`hb2UFuaMtNM`](https://www.youtube.com/watch?v=hb2UFuaMtNM) | 数Gzのレアが！倉庫整理をして視聴者を怖がらせましょう！｜ほぼ週刊『倉庫整理』 | 遊びに来たぜ伊達男 | 2025-08-09 | 2 h 05 m |
| [`FhzRyLRFwaE`](https://www.youtube.com/watch?v=FhzRyLRFwaE) | どうして未鑑定のまま倉庫に入れているのはなぜ？不要な装備を叩き壊せ！｜ほぼ週刊『倉庫整理』 | 遊びに来たぜ伊達男 | 2025-08-16 | 2 h 39 m |

Both are 1920×1080 at **60 fps** — one frame = 16.7 ms, twice the timing resolution of the tutorial
corpus. Both are live-stream VODs of a player spending hours inside storage and inventory windows,
which is why they contain the sustained list gestures the tutorials never caught. `hb2UFuaMtNM` runs a
custom pink skin; `FhzRyLRFwaE` runs the **default blue/white skin**, so its window forms are the
classic ones.

**Their one limitation, stated plainly: they are not pixel-exact.** The game occupies the left 1520 px
of the 1080p canvas and is up-scaled into it (an 8× magnification of a scrollbar shows no crisp pixel
grid). So these two videos are evidence for **behaviour, frame counts and state sets**, and are **not**
used anywhere below for a pixel measurement or a sprite description. Where a size is quoted from them
it is quoted in **list rows**, which is scale-free. They are also a *current* (2025) jRO client rather
than the classic-era build; every finding taken from them is a behaviour the tutorial corpus and the
GungHo manual already show the form of.

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

### What #115 added to the method

The stream VODs are hours long, so three instruments were built to aim at them rather than watch them.

1. **Scrollbar kymograph.** Take the narrow vertical strip containing one scrollbar, average it across
   its width to a single column per frame, and stack those columns left to right. The result is one
   image in which **time runs across and screen-Y runs down**, so the thumb draws its own trace: every
   scroll in a two-hour stream is visible at a glance, and a *staircase* (discrete steps) is instantly
   distinguishable from a *ramp* (a continuous drag). This is what located the scroll runs. A numeric
   version reads the thumb's top and bottom per frame and classifies each move as a one-frame jump or a
   multi-frame run.
2. **Vertical-shift detector.** For a list's interior, find the vertical shift *k* that best matches
   frame *N* to frame *N−1*. That measures a scroll step directly, in pixels, and returns 0 for a
   redraw. It is what turned "the list moved" into "the list moved 145 px, three rows, in one frame".
3. **Region change log.** Per-frame difference of one small control rectangle beside a UI-free
   game-world rectangle, printing only the frames that changed. On a button this makes a click legible
   as a three-beat sequence — hover, press, action — with the exact frame of each.

**A second trap, found the hard way and worth recording.** Downloading only a slice of a long video
with `yt-dlp --download-sections --force-keyframes-at-cuts` **re-encodes** that slice, and the re-encode
puts a quality step at every GOP boundary — at 60 fps, every 250th frame. The cut detector reads that
step as a cut (the UI-free region jumps 3–4). It is not one. The tell is that it is exactly periodic:
if the "cuts" land on frames 250, 500, 750, 1000 … they are the encoder, not an editor. Every timing
below was checked against a UI-free region **and** against that periodicity.

---

## Cross-cutting findings

0. **Everything measured is instantaneous — now also at 60 fps.** #115 re-tested this on unedited
   footage at twice the timing resolution and it holds: **about forty** separate wheel notches each
   move the list and the scrollbar thumb **within one frame at 60 fps (≤16.7 ms)**, with no intermediate
   position; the button's idle → hover and hover → pressed transitions are each one frame as well.
   Nothing anywhere in either corpus takes two frames. Treat "no animation" as settled.

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

5. **A pressed/held state exists and is a third rendering. ✅ Confirmed by #115** — this was the one
   cross-cutting claim #104 could not make. In the 60 fps stream VOD the OK button of the 精錬可能アイテム
   dialog passes through **idle → hover → pressed** and each is visibly different
   (`button/10-ok-three-states.png`). The pressed face is **not** the hover face nudged: a 2-D shift
   search over the button returns its best match at (0, 0), so it is a separate image, not an offset.
   It is **held for as long as the button is held** — five timed presses last 12, 9, 7, 7 and 8 frames
   (200, 150, 117, 117 and 133 ms). **A second, independent sighting on a different control confirms
   it:** the skill grid's cells darken their icon while held (see **stepper**), press-on and press-off
   each a single cut-verified frame. Two controls, two corpora, two skins. This is exactly why the
   tutorials never
   caught it: at 30 fps with cuts every few seconds, a 150 ms state is one frame that a cut can eat.
   *Secondary agreement:* roBrowser's `UIComponent.js` binds a third image per button (`data-down`,
   conventionally `btn_<name>_b.bmp` beside `btn_<name>.bmp` and `btn_<name>_a.bmp`), swapped on
   `mousedown` and restored on `mouseup`. The real client agrees. Some controls may still get only two:
   roBrowser's title-bar `close` and `mini` declare hover (`sys_close_on.bmp`) but **no** down state,
   and no footage has yet caught either of those held.

7. **The mouse cursor itself is a hover affordance. ✅ New in #115.** Over a button the pointer changes
   from the ordinary arrow to a **pointing hand** (`button/11-hover-hand-cursor.png`), in the same frame
   the button's fill lights. Any replica that draws the hover fill but keeps the arrow cursor will read
   as subtly wrong.

6. **Tooltips are a hover affordance in their own right.** Icon buttons, grid cells **and list rows**
   (the last confirmed by #115) raise a small floating label after the pointer settles. The label sits
   just above and left of the pointer and re-reads whatever row is under the pointer — including when
   the wheel moves the list beneath a stationary pointer. The delay before a tooltip appears is still
   **unverified**.

---

## button

**Where:** ゲームオプション menu rows; 基本情報 text buttons (status/rec/items/equip/skill/map/chat/friend);
確定 / リセット / OK / cancel / close footers; the icon-button grid; login dialogues.

| | |
| --- | --- |
| **Gesture** | Pointer enters the button's rectangle. |
| **Response** | The button face fills with a blue left-to-right gradient; the label stays put; the border does not move. |
| **Hover in the source** | **Yes — confirmed.** `01-menu-hover-sound.png` (00:20:13.933) has the pointer on サウンド設定 and that button lit; `02-menu-hover-shortcut.png` (00:20:13.967) has the pointer one row down on ショートカット設定 and *that* button lit instead. The lit button is not a click-selection: ショートカット設定 is lit from 00:20:13.97, and the window it opens does not appear until 00:20:16.0 — it is lit merely because the pointer is on it. The same is visible on the login dialogue's OK (`04-login-ok-hover.png`). |
| **Timing** | ✅ **Resolved by #115: 1 frame.** *(#104's own footage could not do it — an editing cut lies between frames 01 and 02, the UI-free region jumping 8.5, so that pair does not time the transition, and a 9-second frame-by-frame search of the menu found no hover change inside a single shot. The expectation recorded then was "≤1 frame, not measured".)* It is now measured on unedited 60 fps footage — see **Hover timing** below. |
| **Reversibility** | Yes — the idle face returns with no residue; both states appear on both buttons across the two shots. |
| **Click → action** | ✅ **Measured by #115.** The whole click is legible on unedited 60 fps footage as a four-beat sequence, and each beat is one frame: **idle → hover (1 frame) → pressed (1 frame) → [held 117–200 ms] → the action fires and the dialog is gone (1 frame)**. There is no delay between the release and the result and no transition on either side of it. *(#104 could not measure this: the click on ショートカット設定 at 00:20:16 straddles three consecutive cut frames. What it did establish, on a different window, is that **window construction takes one frame** — `close/04`, `close/05` — which #115 re-confirms on unedited footage: the 精錬可能アイテム dialog appears complete in a single frame at 01:22:44.283.)* |
| **Pressed state** | ✅ **Confirmed (#115).** A third rendering, distinct from both idle and hover. On the 精錬可能アイテム dialog's OK button in `FhzRyLRFwaE` at 60 fps the sequence is legible frame by frame: idle at 01:24:01.350 (`07-ok-idle.png`); **hover** arrives in a single frame across 01:24:01.4167 → .4333 and is still showing at .500 (`08-ok-hover.png`, blue gradient fill); **pressed** arrives in a single frame across 01:24:01.550 → .5667 and is still showing at .650 (`09-ok-pressed.png`); the dialog then tears down at 01:24:01.7667. **What actually changes between hover and pressed is only the label.** Measured on a label-free strip of the button face, the hover and pressed fills are the *same* — row-brightness profiles agree within 1–2 grey levels top to bottom, so the blue gradient does not deepen, invert or move. The label does: a 2-D shift search over the label box puts the best match at **(dx +2, dy +1)**, i.e. the text is **nudged down and to the right**, which at this capture's up-scale reads as the client's familiar 1 px press offset. So pressed is *hover plus a displaced label*, not a wholly repainted face — cheaper than roBrowser's `btn_<name>_b.bmp` third-bitmap convention would suggest, though the two are indistinguishable in effect. **Duration: the press is held for as long as the button is held.** Five presses were timed from the frame the pressed face appears to the frame the dialog tears down: **12, 9, 7, 7 and 8 frames — 200, 150, 117, 117 and 133 ms** (01:24:01.567, 02.267, 02.850, 03.400, 03.933). Every one produces the pixel-identical intermediate state (`13-ok-pressed-second-instance.png`). All five are cut-verified (UI-free region 0.00–0.20 across every pair). ⚠️ Measured on the **default blue skin** in an up-scaled capture: the *existence and behaviour* of the third state is the finding; its exact pixel construction is not readable here. |
| **Disabled state** | Present in the client — `text-field/04-login-password-masked.png` shows two greyed, non-editable fields with grey labels beside an active one. No disabled *button* was captured. Partially verified. |
| **Hover timing** | ✅ **Measured (#115): 1 frame at 60 fps.** Idle → hover on OK completes between 01:24:01.4167 and 01:24:01.4333, UI-free region 0.00 across the pair. An earlier hover on the same button at 01:24:01.0833 behaves the same. #104 could only infer button hover timing from a dropdown row; it is now measured on a button, at twice the resolution. |
| **Cursor** | ✅ **New (#115).** Over a button the pointer becomes a **pointing hand**; off it, the ordinary arrow (`11-hover-hand-cursor.png`). The change happens in the same frame as the fill. |
| **Hover is per-button, in one frame** | `11-hover-hand-cursor.png` has OK blue and `cancel` grey side by side in a single frame — the fill follows the pointer, it is not a "default button" marking. |
| **Evidence** | `behaviour/button/` (13 crops + `sources.json`) — 6 from #104, 7 from #115 |

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
| **Form** | On some cells the level line reads `◁ 7 / 7 ▷` — a small blue left triangle, the current/max pair, a small blue right triangle, both triangles inside the cell's own width. On other cells in the same window the same line reads a bare number (`5`, `1`, `4`) with no arrows at all. **#115 reads the pair correctly: it is `current / target`, not `current / max`** — after one `▷` click the same cell reads `7 / 8`, so the right-hand number is what the level *will be* once committed. |
| **Gesture → response** | ✅ **Confirmed and measured (#115).** One click on `▷` spends **exactly one** skill point on that skill, as a **pending** change. Three things happen in the **same single frame** (`05-click-before.png` 00:09:00.733 → `06-click-after.png` 00:09:00.767): the footer goes from `スキルポイント : 16` to `スキルポイント : 15 / 16` (remaining / total); the skill's level digit turns **red**; and **every stepper's arrows disappear across the whole window**. Once the pointer moves off, the cell reads `◁ 7 / 8 ▷` with the 7 still red (`07-cell-states.png`, panel 5). |
| **Timing** | ✅ **1 frame at 30 fps, cut-verified twice over.** Two independent UI-free game-world regions differ by **0.20** and **0.29** across the pair — well inside a shot. (There *is* a real cut 5 frames earlier at 00:09:00.583, which both regions agree on; the measured pair is clear of it.) |
| **Pressed state on the stepper** | ✅ **Confirmed (#115)** — a second, independent sighting of a pressed state, on a completely different control from the button card's. While the mouse is held down the cell's **icon tile darkens** (`07-cell-states.png`, panel 3). It darkens in one cut-verified frame at 00:09:00.567 (UI-free region 0.01) and brightens again in one cut-verified frame at 00:09:00.767 (0.29), the same frame the point is spent. Held for **6 frames (200 ms) of footage — read as a floor, not a measurement**, because an editing cut sits inside that window and an edit can only remove time. |
| **Hover in the source** | ✅ **Confirmed (#115).** The cell's icon frame changes from **blue to pink/red** while the pointer is on it (`07-cell-states.png`, panel 2 vs 1), and returns to blue when the pointer leaves (panel 5). So a skill cell has a full **idle / hover / pressed** set, like a button. |
| **Reversibility** | ✅ **Confirmed (#115).** `確定` raises a modal `message` dialog — 「確定したポイントは戻せません。※前提スキルが必要な…」 — with an OK / cancel footer (`09-confirm-dialog.png`). **Pressing `cancel` discards the pending allocation outright**: the footer returns to `スキルポイント : 16`, the cell to a black `7 / 7`, and the arrows come back (`10-after-cancel.png`), all in one cut-verified frame at 00:09:06.033 (UI-free region **0.00**). Note this is *not* "go back to editing" — cancel behaves like リセット. The allocate-then-commit model #104 inferred from the footer buttons is now demonstrated. |
| **When the arrows appear** | ✅ **Largely resolved (#115).** Two rules, both now evidenced. **(a) Per skill:** a cell that can be raised renders `current / target` *with* arrows; a cell that cannot renders a bare number *without* them. **(b) Window-wide mode:** the instant any point is spent, **every** stepper's arrows disappear until the pending state is resolved — `08-arrows-hide-elsewhere.png` shows キリエエリソン, a different skill far from the pointer, keeping its `7 / 7` while its arrows vanish and return with the allocation. **This is very probably the explanation for #104's puzzle** (`01-skill-stepper-present.png` vs `02-skill-no-stepper.png`: same character, same window, same skill, arrows in one and not the other, 16.5 s apart) — the frame without arrows was almost certainly taken while an allocation was pending. Flagged as the leading explanation, not proven for that particular pair. |
| **Hold-to-repeat** | **Still unverified.** What *is* established is that **one click yields exactly one point** — the counter moves 16 → 15, not further. No frame in either corpus catches an arrow held long enough to test repeat. Secondary: roBrowser has no stepper at all; its nearest equivalents (SkillList's `+`, WinStats' six stat `+` buttons) are single-shot with no repeat. Weak, and offered only as a default. |
| **Evidence** | `behaviour/stepper/` (10 crops + `sources.json`) — 2 video + 2 manual crops from #104, 6 from #115 |

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
| **Form** | **Confirmed.** A vertical bar with exactly **one arrow button at each end** (`▲` top, `▼` bottom) and a thumb between them on a recessed track. Two visual families appear in the client: the chat log uses a **black** track with a pale thumb and dark arrow blocks; window lists use a **light** track with blue arrows and a blue thumb. #115 re-confirms the light family on unedited default-skin footage (`12-basic-skin-grid-scrollbar.png`, 4×) — and shows the same anatomy survives a **custom skin** unchanged (`07`/`08`), so arrow-at-each-end plus proportional thumb is structural, not decorative. |
| **Thumb size** | **Confirmed** to be proportional: in `01-chatlog-scrollbar.png` the thumb fills most of a short track (little overflow); in `02-popup-list-scrollbar.png` it is a short thumb part-way down a long track (large overflow). |
| **Thumb drag** | **Still unverified after #115, and now for a different reason.** Four and a half hours of unedited storage-window footage were searched thumb-trace by thumb-trace, and the player scrolls **only with the wheel** — the pointer is never on the scrollbar. Two candidate "drags" (a thumb crossing the whole track in ~1.5 s) were found and both **dissolved at 60 fps into a burst of single-frame wheel notches**; the low-frame-rate trace had smeared them into a ramp. That is a real methodological warning for anyone hunting a drag: *a fast wheel spin is indistinguishable from a drag below about 60 fps.* |
| **Arrow-button step** | **Still unverified after #115.** No `▲`/`▼` click occurs anywhere in the footage searched — same reason: this player uses the wheel exclusively. Neither the step size nor hold-to-repeat is established. |
| **Mouse wheel** | ✅ **Confirmed and measured (#115).** Over the ワールド倉庫 item list in `hb2UFuaMtNM`, **24 notches had their list-content shift measured** (7 in 01:06:20–01:08:20, 17 in 01:14:26–01:14:50) and **37 thumb steps were traced frame by frame** in one 24-second span. Every one behaves identically: the list content jumps **±145 px — exactly 3 list rows — in exactly one frame at 60 fps**, in both directions, with **no intermediate position and no easing**. 23 of the 24 measured ±145 exactly; the 24th is the clamped one, below. Every one of the 37 thumb steps is a single-frame jump. The thumb repositions in the **same** frame as the content. `05-wheel-list-before.png` → `06-wheel-list-after.png` is one such pair (top row マルスカード → ソードフィッシュカード, three rows), with `07`/`08` showing the thumb move at 4×. All cut-verified: the UI-free game-world region differs by **0.00** across the pair, and this is unedited stream footage in the first place. |
| **Wheel — the gesture is genuinely the wheel** | `09-wheel-pointer-in-list.png`: the pointer sits **inside the list body**, over an item row (raising that row's floating name tooltip), and does **not move** while the thumb walks down the track. It is nowhere near the scrollbar. A fast spin produces notches 1–3 frames apart, each still landing in its own single frame — at a 30 fps sampling this masquerades as a smooth drag, which is exactly the mistake the 60 fps re-check caught. |
| **Wheel — clamping at the list end** | ✅ **Confirmed.** Scrolling up towards the top of the list, the **last** notch moves the content only **97 px (2 rows)** — the distance that was actually left — instead of the 145 px every other notch moved, and the thumb lands flush against the top of its track (`10-wheel-clamp-before.png` → `11-wheel-clamp-after.png`). The wheel does not overshoot and does not bounce. This matches the slider's confirmed end-clamping. |
| **Wheel — is 3 the client's number?** | ⚠️ **Do not hard-code 3 without deciding.** What is established is that a notch is quantised to a **whole number of rows** and lands in **one frame**. Whether the number is 3 because the client says so, or because Windows' default "scroll 3 lines per notch" is being honoured, **cannot be told from video** — it is one player's machine. Note this **contradicts** roBrowser, which hard-codes **one** row per notch (`Inventory.js` / `Storage.js` snap `scrollTop` to a **32 px** grid and move one step per notch; `ChatBox.js` the same at **14 px**; `SkillList` has no wheel handler at all). So roBrowser is wrong about the wheel, or the OS setting is in play — either way roBrowser is not a safe source for this number. |
| **Geometry (secondary only)** | roBrowser skins the native scrollbar at **13 px** wide with a 12 px decrement and 13 px increment button and a **6 px minimum thumb**; its chat-log scrollbar is **10 px** wide with 10 px arrows. Note roBrowser implements *no* scrollbar interaction of its own — thumb drag, arrow step and repeat are delegated to the browser — so it is **not** evidence for the real client's gesture behaviour, only for its metrics. |
| **Reversibility** | **Unverified.** |
| **Hover in the source** | **Not observed** on any scrollbar part. **Unverified.** The pointer never went there. |
| **Row hover raises a tooltip** | ✅ **New (#115).** While the pointer rests on a storage-list row, that row's item name appears in a small floating label just above and left of the pointer (`09-wheel-pointer-in-list.png`). It follows the pointer from row to row as the wheel scrolls the list underneath it. |
| **Evidence** | `behaviour/scrollbar/` (12 crops + `sources.json`) — 3 video + 1 manual crop from #104, 8 from #115 |

**One of the three gestures is now answered.** The wheel is measured and cut-verified: 3 rows per
notch, one frame, clamped at the ends. **Thumb drag and arrow step are still unanswered**, and #115
established *why*: in every hour of unedited storage-window play that was searched, the player scrolled
with the wheel and never touched the bar. Those two gestures will have to be specified from intent,
with roBrowser's **metrics** (13 px bar, 6 px minimum thumb) as the only secondary — and roBrowser is
explicitly **not** evidence for their gesture behaviour, since it delegates both to the browser.

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
| **Hover raises a tooltip on list rows too (#115)** | ✅ Not just on icon buttons. While the pointer rests on a storage-list row, that row's **item name appears in a small floating label** just above and left of the pointer, and it follows the pointer from row to row — including while the wheel scrolls the list underneath a stationary pointer, where the label re-reads the row that has arrived under it. Shown in `scrollbar/09-wheel-pointer-in-list.png`. The delay before it appears is still **unverified**. |
| **Row selection re-confirmed on the default skin (#115)** | `button/12-refine-dialog-context.png` shows the 精錬可能アイテム list with its first row selected as a **pale blue band across the full row width** — an unedited, default-skin instance of the "selection is a filled band" form. Note it is a *lighter* treatment than the tutorial corpus's dark-grey-with-white-text shortcut row, so the selection fill is a per-window/per-skin token, not one colour. |
| **Evidence** | `behaviour/list-selection/` (7 crops + `sources.json`); see also `scrollbar/09` and `button/12` |

---

## window title drag

| | |
| --- | --- |
| **Drag surface** | The title bar: window icon, title text, sometimes an inline control (スキルリスト carries its 説明表示 checkbox there), then `⊖` and `✕` at the right end. One window differs — the guide's narration for 会話ウィンドウ says to move the pointer to the window's edge until the cursor changes, i.e. that window is moved by its input bar / border rather than a title bar. #115 confirms the narration a second time at 00:03:00–00:03:05 of `oCsKRSKr2nA` (「白いところをドラッグするとウィンドウを動かせる」 / 「カーソルを右に持って行くとカーソルが変わって移動できるようになります」) — **the cursor changes shape over a drag surface**, which fits the pointing-hand cursor found on buttons. The move itself is narrated, not performed on camera. |
| **Gesture → response** | **Unverified.** Windows appear at different screen positions across the corpus, so they do move — but every position change in these videos happens across an editing cut (a single-frame jump of 40 %+ of the UI pixels with the game world jumping too), not a drag. A sustained-motion sweep at 6 fps over all five videos found **no drag run anywhere**. |
| **Timing / motion profile** | **Still unverified after #115.** The map's ≥30-frame monotonic-drag gate still has no source reference. |
| **Two false positives, both instructive** | #115 found two candidate sustained drags and **both dissolved when re-read at native frame rate**, in the same way. (1) In `hb2UFuaMtNM` a scrollbar thumb crosses its entire track in ~1.5 s and looks like a ramp at 30 fps; at 60 fps it is a burst of one-frame wheel notches. (2) In `oCsKRSKr2nA` at 00:02:51–00:02:56 the chat window appears to be dragged over ~30 frames when sampled at 6 fps — narrated 「ウィンドウを意図せず引っ張ってしまって文字を入力できなくなることがあります」 — but a frame-by-frame trace of the window's borders at 30 fps shows the outer box **never moves** and the input bar collapses in **2 frames**. **The rule that falls out: below about 30 fps you cannot tell a drag from a burst of discrete steps, and everything in this UI is a discrete step.** Any future drag hunt must sample at native rate before believing a ramp. |
| **Why #115 did not close it** | Not because the footage was cut — it wasn't — but because **experienced players do not move windows during play**. Across 4 h 44 m of unedited two-window storage work, a per-frame trace of both windows' vertical position and a 30-second position map of both whole streams show the layout **fixed for the entire session**. Windows open and close at remembered positions; none is ever dragged. The client remembers window positions between sessions, so the arranging happens off-camera. This changes what to hunt for: not "unedited footage" (that was the #104 diagnosis and it was not sufficient) but **footage of a first session or a UI being rearranged** — a fresh account, a client reinstall, or a stream where a window opens somewhere inconvenient. |
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
| **Construction re-confirmed on unedited footage (#115)** | The 精錬可能アイテム dialog appears **complete in one frame** at 01:22:44.283 in `FhzRyLRFwaE` — nothing in the rectangle at 01:22:44.267, the whole dialog with its list, footer and OK/cancel at .283. No grow-in, no fade, no partial paint. This removes the last doubt about #104's one-frame construction finding, which rested on tutorial footage. |
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
| **Send (Enter)** | ✅ **Confirmed and measured (#115).** A whole send is captured in `oCsKRSKr2nA` around 00:04:00, and **it is not one event but two, 100 ms apart, in this order.** |
| **1. Field cleared** | ✅ **1 frame, cut-verified.** `05-send-before.png` (00:04:00.167) has 「パーティー」 in the input bar with the caret after it; `06-send-field-cleared.png` (00:04:00.200) has an empty bar with the caret back at the left inset. UI-free region **0.00** across the pair. **The log is unchanged in that frame** — the field empties on its own, before anything is echoed. |
| **2. Log appended** | ✅ **1 frame, cut-verified, 3 frames (100 ms) later.** `07-send-log-appended.png` (00:04:00.300): 「P_Lioh02 : パーティー」 appears as a new bottom line in the log, in one frame, UI-free region **0.00**. |
| **Why the 100 ms gap matters** | The clear is local and instant; the log line is the **server's echo coming back**. A replica that appends to the log in the same frame it clears the field is not wrong-looking, but the source's own order is clear-then-append, and a single-player replica should keep that order even if it collapses the gap. *Secondary agreement:* roBrowser's `ChatBox.js` also clears (`$text.val('')`) **before** dispatch. |
| **A send has a second consequence** | The message also appears as a **floating speech bubble above the character's head in the game world** (`08-send-speech-bubble.png`), not only in the log. |
| **Send target is a separate control** | The chat window carries a scope dropdown (全体に送る / パーティーに送る / ギルドに送る); the captured send was made with パーティーに送る selected, and the log line is coloured by scope — the previous 全体 line is pink-red, the パーティー line green. Scope colouring is a themed token like the highlight colour. |
| **History (up/down)** | **Still unverified.** |
| **Hover in the source** | **Not observed** on any text field. **Unverified.** |
| **Secondary (roBrowser), offered as a default only** | `ChatBox.js`: Enter forces focus back to the message box and submits; the field is cleared (`$text.val('')`) *before* dispatch; Enter on an **empty** field is not a no-op — it toggles the whole input bar off and battle mode on; text starting with `/` is routed to a command handler and never sent as speech; Up/Down walk two independent histories and the recalled text is fully selected; Tab swaps between the nick and message fields; clicking a field selects all of it; the log keeps 50 lines and always auto-scrolls to the bottom. None of this is confirmed for the JP client. |
| **Evidence** | `behaviour/text-field/` (8 crops + `sources.json`) — 4 from #104, 4 from #115 |

---

## #115 — what was searched, and what it cost

Recorded so nobody repeats it. Ticket [#115](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/115),
2026-08-29. Free tools only (`yt-dlp`, `ffmpeg`, numpy/PIL); nothing paid.

**Searches run** — YouTube, 12–15 results each, Japanese and English:
`ラグナロクオンライン 実況` · `ラグナロクオンライン 生放送` · `ラグナロクオンライン 配信 アーカイブ` ·
`RO ラグナロク 倉庫整理` · `ラグナロクオンライン スキルツリー 振り方` · `ラグナロクオンライン 露店 出し方` ·
`RO ラグナロクオンライン 初心者 ウィンドウ 操作` · `ラグナロクオンライン RTA` ·
`ラグナロクオンライン 転生 実況 ノーカット` · `ragnarok online full playthrough no commentary` ·
`ragnarok online 2004 gameplay raw` · `ragnarok online private server classic client gameplay`.

**Screened on metadata** (resolution, frame rate, length, `was_live`): `hb2UFuaMtNM`, `FhzRyLRFwaE`,
`_qYk93A-t4k`, `Q1EqpwPFivk`, `ZKyymuvFax8`, `RQbJOlL-IhU`, `qjj8AkcI72U`, `aQxmhaxTgD4`,
`Ei3jEAJDBik`, `OBK6K2RZ3cY`, `yvT-kUN3_rY`, `tFUAGe9OCEE`. All are genuinely unedited; the two
`遊びに来たぜ伊達男` storage streams were chosen first because "warehouse tidying" is four hours of
uninterrupted list work.

**Analysed frame by frame:** `hb2UFuaMtNM` (2 h 05 m) and `FhzRyLRFwaE` (2 h 39 m) — **4 h 44 m of
unedited footage**. Each was pulled once in full at 360p to map it (a frame every 30–40 s, plus a
whole-stream scrollbar kymograph and a per-frame numeric thumb trace), then seven spans totalling about
**15 minutes were re-pulled at 1080p 60 fps** and read frame by frame. Raw video stayed in the
scratchpad; only crops are committed.

**A second search, in parallel, went back over the tutorial corpus** with the specific gestures in
hand rather than sweeping for anything interesting. Queries: `ラグナロクオンライン スキル振り` ·
`RO スキルポイント 振り方` · `ラグナロクオンライン 転職 スキル 解説 実況` · `ラグナロクオンライン スキルリセット` ·
`RO スキル振り直し` · `ラグナロクオンライン 初心者 育成 生放送 ノーカット` · `ラグナロクオンライン スキル 覚え方 初心者` ·
`RO ラグナロクオンライン ノービス 最初から 実況 part1` · `ラグナロクオンライン リセットNPC スキル振り直し 実演` ·
`ラグナロクオンライン RTA 転生` · `RO RTA チャート 実況` · `ラグナロクオンライン 検証 スキル レベル 上げ 生放送` ·
`ラグナロクオンライン ジョブレベル上げ 3次職マラソン` · `RO 転職クエスト 実況 スキル 取得` ·
`ラグナロクオンライン ゼロ 新規 育成 配信` · `ラグナロクオンライン 初心者講座 操作方法 ウィンドウ` ·
`RO ラグナロクオンライン UI 解説 スキルウィンドウ` · `ラグナロクオンライン 始め方 解説 キャラ作成 スキル` ·
`Ragnarok Online skill window tutorial japanese` · `ラグナロクオンライン スキル習得 やり方` ·
`RO 冒険者育成学校 チュートリアル` · `ラグナロクオンライン スタートアップガイド` ·
`ラグナロクオンライン公式チャンネル テクニック集`. Niconico search is unusable through `yt-dlp` here and
returned nothing. Screened frame-by-frame and rejected: `Obt0q6axICs` (static build showcase, numbers
never change), `7l-LG9tKVCk` (annotated explainer over a still), `7szqxLza7xU` (all NPC dialogue, the
skill window never opens), `cj8E3FKpN_8` (**worth recording: the official 公式テクニック集 series is a
produced TV-style show built from static screenshots and presenter cutaways, not live UI — treat the
whole series as a dead end**), `917aJBSiW6g` (muddy encode, tiny game window), `248-OOUgr_Q`
(852×480, skill numbers unreadable). Coarse-mapped only: `JaA_UUL4a5w`. Metadata only: `dK1FAOr29qU`,
`OBK6K2RZ3cY`, `AuzJMA_NG48`, `XXmsvycpC4M`, `cOaf34SqDm0`, `dYqjZmoB3_o`, `gipck2Av298`,
`5EKJcykdc-w`, `cJyE4mreVCg`, `EHSycKLOGJ8`, `rhGXF84xEeg`, `phg8UeJYO8s`, `qzY5qloY7ws`,
`jm7R9Wae_28`, `VeYqG6e_fA8`, `rM6jeVKb8qw`, `92A2MpKGBXI`, `le_Z9rXPPb0`.

**And it found the last two gestures where nobody had looked properly: in #104's own footage.** The
skill stepper is clicked at 00:09:00 of `P7t7cIvtEQo` and a chat message is sent at 00:04:00 of
`oCsKRSKr2nA` — both files were already on disk. #104 swept those videos for *sustained* motion, which
is the right net for a drag and the wrong net for a click: both of these are over in one frame. Every
timing taken from them here was re-checked with #104's own cut detector before being written down, and
one of the two sits five frames clear of a real editing cut.

**What #115 found:** the mouse-wheel scroll (24 measured content shifts, 37 traced thumb steps), the
button pressed sprite (5 presses) and a second pressed state on the skill cell, the hover timing on a
button, the hand cursor, the list-row hover tooltip, **the skill stepper's whole gesture** (including
what the arrows do, what the two numbers mean, and when the arrows vanish), and **the chat send** as
two separate events 100 ms apart.

**What it did not find, and why — this is the useful part.** The #104 diagnosis was "the tutorials are
cut, so find unedited footage". That diagnosis was only half right. Unedited footage fixed the
*scrollbar wheel* and the *pressed sprite* immediately. It did **not** fix thumb drag, arrow step or
window drag, for a reason that has nothing to do with editing:

- **Skilled players do not use scrollbar furniture.** The wheel is faster, so the pointer never lands
  on the thumb or the arrows. More hours of the same kind of footage will not help.
- **Skilled players do not move windows.** The client remembers window positions between sessions, so
  the arranging happened before the stream began. A layout that never changes in 4 h 44 m is not a
  small sample; it is the wrong kind of session.

So the remaining gestures need a **differently shaped** source, not simply more of the same: a first
session or a fresh account (windows get placed, skill points get spent), or a player recording a
deliberate walkthrough of a window *without* cutting it. Failing that, they are specified from intent —
see the closing section.

---

## Coverage summary

| Control | Idle | Hover in source | Pressed | Selected / active | Transition timing | Gesture → action |
| --- | --- | --- | --- | --- | --- | --- |
| button | ✅ | ✅ **yes, 1 frame @60 fps** | ✅ **yes — third sprite, held ~150–200 ms** | ✅ | ✅ **1 frame, cut-verified ×5** | ✅ **click → action measured** |
| checkbox | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred |
| radio | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred |
| tab | ✅ | ❌ unverified | ❌ unverified | ✅ full set | ❌ unverified | ⚠️ inferred |
| stepper | ✅ | ✅ **yes — pink cell frame** | ✅ **yes — icon darkens while held** | n/a | ✅ **1 frame, cut-verified** | ✅ **one click = one point, pending; cancel discards** |
| slider | ✅ + end clamp | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| scrollbar | ✅ + thumb sizing | ❌ unverified | ❌ unverified | n/a | ✅ **wheel = 1 frame @60 fps, ×40** | ⚠️ **wheel ✅ (3 rows/notch, clamped); drag ❌; arrow ❌** |
| dropdown | ✅ | ✅ **yes, 1 frame** | ✅ arrow inset while open | ✅ | ✅ **1 frame, cut-verified ×4** | ✅ |
| list / grid selection | ✅ | ✅ **yes** (both kinds) | ❌ unverified | ✅ | ❌ unverified (cut) | ✅ states only |
| window title drag | ✅ | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified |
| minimize / restore | ✅ | ❌ unverified | ❌ unverified | ✅ both panel states | ❌ unverified | ❌ unverified |
| close | ✅ | ❌ unverified | n/a | n/a | ⚠️ open = 1 frame (verified); close not measured | ❌ gesture unverified |
| text field + send | ✅ + caret + masked + disabled | ❌ unverified | n/a | ✅ | ✅ **clear 1 frame; log +100 ms** | ✅ **send measured** |

**#104's five gaps, and where they stand after #115**

| # | Gap | Status |
| --- | --- | --- |
| 1 | A scrollbar being driven | ⚠️ **Partly closed.** The **wheel** is measured — 3 rows per notch, one frame, clamped at the ends. **Thumb drag and arrow step are still open.** |
| 2 | A window being dragged | ❌ **Still open.** No title-bar drag exists in any footage searched. |
| 3 | A chat message typed and sent | ✅ **Closed.** Field-clear and log-append measured as two cut-verified one-frame events 100 ms apart. |
| 4 | A skill stepper arrow clicked | ✅ **Closed.** One click = one pending point; the counter, the red digit and the window-wide arrow hide all land in one cut-verified frame; `cancel` on 確定 discards. **Hold-to-repeat is the one part still open.** |
| 5 | A button held long enough to show a pressed sprite | ✅ **Closed twice over** — the dialog OK button (5 presses, 117–200 ms) and, independently, the skill cell's darkening icon. |

**What is left, and how to get it**

1. **Scrollbar thumb drag and arrow step.** More play footage will not help: skilled players use the
   wheel and never touch the bar. What would work is a **deliberate uncut walkthrough of a list window**,
   or a player on a machine with no wheel. Untried lead from the #115 screening:
   `JaA_UUL4a5w` (already on disk) has クエストウィンドウ at 00:40–03:50, 実績ウィンドウ at 13:15 and
   ショートカット設定 at 14:40 — all scrolling list windows, none yet read frame by frame. Also
   `oCsKRSKr2nA` 09:43–09:49, where the chat scrollbar's thumb visibly steps; it needs re-cropping wide
   enough (x 555–620) to catch the cursor and settle press-versus-wheel.
2. **A window title-bar drag.** Needs a **first session**, not more play: a fresh account or a fresh
   install, where windows are placed rather than restored. Untried lead: `dK1FAOr29qU`
   (2560×1440 @60, 3 h 10 m, live, 「キャラ作成からアサシン転職まで！…最初からプレイ」), which begins at
   character creation.
3. **Hold-to-repeat**, on either a stepper arrow or a scrollbar arrow. One frame of anyone holding one.

**If none of that turns up, the honest position is:** the wheel, the pressed state, the stepper and the
send are specified **from the source**; thumb drag, arrow step, hold-to-repeat and the title-bar drag
are specified **from intent**, with roBrowser's *metrics* (13 px bar, 6 px minimum thumb, 10 px edge
magnet, no clamping, 500 ms release fade) as the only secondary — and with roBrowser explicitly **not**
treated as evidence for gesture behaviour, since #115 has now caught it being wrong once already: it
hard-codes one row per wheel notch, and the real client moves three.
