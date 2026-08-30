# Behaviour Cards v1 — Ragnarok Online, Japanese client, classic-era UI

Research ticket [#104](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/104), extended in
place by [#115](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/115) and again by
[#117](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/117), under map
[#103](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/103). Written 2026-08-29, extended
2026-08-30. **The owner confirms these cards; this document does not decide anything.**

Everything #115 added is marked `(#115)` where it sits and everything #117 added is marked `(#117)`, so
the three passes stay tellable apart. #104's own wording is kept wherever it was right, including where
it recorded not knowing something.

**Three evidence classes, and they answer different questions.** #104 and #115 are **video-observed** —
gestures read frame by frame off footage of the running client, which is where every timing and every
pixel form in this document comes from. #117 adds **manual-attested** — the publisher stating in prose
what a control is *for*, which is where the *purposes*, the modes, the keyboard map and the cross-window
gestures come from. What neither reaches is **intent-specified**. The manual never gives a duration and
its screenshots are the wrong client; the video corpus never explains what a button is for. Each class
is labelled wherever it is used.

One card per control type in the Control Catalogue. Each card says what gesture produces what visible
response, how long the response takes **in frames**, whether it reverses, and **whether the Source Game
shows a hover state**. Hover is being added in-style everywhere regardless — the card exists to record
what the source actually did, not to authorise a decision. `## Manual-attested behaviour` then works the
other way round — **per window**, keyed to the eleven windows of Reference Screen image 79.

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

### Primary for *behaviour* — official GungHo Japanese play manual (promoted by [#117](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/117))

**Owner rule, 2026-08-30: the official jRO play manual is the _behaviour_ authority for how windows and
menus work. It is _not_ an artwork reference.** Its screenshots show the updated client UI, which is not
the UI in Reference Screen image 79. Nothing in it may be copied as art, and no statement in it may be
transplanted onto image 79's layout without checking that image 79 actually has the control.

Under that rule the manual stops being a source of *screenshots* and becomes a source of *statements*:
it is the publisher describing, in its own words, what each control does. That makes it the document's
**third evidence class** — see `## Manual-attested behaviour` below, which extracts every behavioural
statement in it and maps each one to image 79's windows and controls.

Pages read in full (fetched 2026-08-30, extracted as Markdown):

| Page | URL |
| --- | --- |
| 各ウィンドウについて (27 window sections) | `https://ragnarokonline.gungho.jp/playmanual/operation/window.html` |
| 基本的な操作 | `https://ragnarokonline.gungho.jp/playmanual/operation/operation.html` |
| 設定方法 | `https://ragnarokonline.gungho.jp/playmanual/novice/config.html` |
| ショートカット一覧 (44 shortcuts) | `https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html` |

Its **screenshots** continue to be used exactly as #104 used them, and only that way: where they show a
state set the videos do not (tab active/inactive, the skill stepper on a fresh character, the resize
grip's own annotation). Those crops live under `artifacts/references/ro-source-game/behaviour/` and are
retained for private study.

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
| **Caret** | **Confirmed.** A thin vertical bar drawn immediately after the last character (`01-replay-filename-typed.png`: `replay010101\|`; `02-chatroom-title-caret.png`: `ちゃっとるーむ\|`). In an empty field the caret sits at the field's left inset (`03-chat-input-bar.png`). Blink rate is **unverified**. |
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

## Manual-attested behaviour — the official jRO play manual (#117)

Ticket [#117](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/117), 2026-08-30, under map
[#103](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/103). Everything in this section is
marked `(#117)` where it appears elsewhere in the document.

This section adds a **third evidence class** to the two the cards already carried. Every statement below
is quoted from the publisher's own manual, in Japanese, with the page it came from, and then mapped —
or explicitly *not* mapped — to a window and control in Reference Screen image 79
(`artifacts/references/ro-desktop-b/control-inventory.json` and `window-rects.json`, branch
`research/image-79-native-scale`: 11 windows, 239 controls).

### The three evidence classes

| Class | What it is | What it can settle | What it cannot |
| --- | --- | --- | --- |
| **video-observed** (#104, #115) | A gesture and its response read frame by frame off footage of the running client. | Timing, state sets, pixel form, whether a thing actually happens. | Anything nobody happened to do on camera — thumb drag, window drag, hold-to-repeat. |
| **manual-attested** (#117) | The publisher stating in prose what a control does. | *Intent and outcome* — what a button opens, what a gesture is *for*, what a mode means, which key does what. | **Timing, form, or pixels.** The manual never says how long anything takes and its pictures are the wrong client. |
| **intent-specified** | A decision the owner makes where neither of the above reaches. | Whatever is left. | — |

**The two classes are complementary in exactly the way the gaps needed.** The video corpus is strong on
timing and blind to purpose; the manual is strong on purpose and silent on timing. Three of #104's
long-standing "form confirmed, gesture unverified" entries are answered below *as gestures* — the
minimize toggle, the bottom-right resize drag, and drag-an-item-out-to-drop — while their timings stay
exactly as unverified as they were.

### The two rules this section follows

The manual documents **the current jRO client**. Image 79 is an older layout. So:

1. **A statement is only mapped where image 79 has the control.** Where it does not, the statement is
   recorded verbatim and labelled 🕘 **modern client; not directly attested for image 79's layout**.
   It is never transplanted.
2. **Where the manual's window and image 79's window disagree in structure, the disagreement is the
   finding**, and it is written down as such — the オプション window is the clearest case and is worth
   reading before anything else here.

Markers used throughout:

| | |
| --- | --- |
| ✅ | Attested, and image 79 has the control the statement is about. |
| ⚠️ | Candidate mapping — plausible, not certain, and the reason for the doubt is given. |
| 🕘 | Modern client; not directly attested for image 79's layout. |
| ❌ | The manual says nothing about this. |

---

### The finding that reframes the ticket: image 79 splits one modern window into two

The ticket expected a divergence at the オプション window — "the オプション window with BGM/Effect sliders
vs today's button menu". It is real, and it is bigger and cleaner than that: **image 79 has both halves,
as two separate windows, and the modern client has merged them into one.**

The manual's §18 オプションウィンドウ opens with a sentence that describes image 79's window and then
presents a table that describes image 79's *other* window:

> 「BGMやEffectなどのオプションを設定できる。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §18 オプションウィンドウ

That lead sentence is an exact description of image 79's `options` window, which contains a **BGM
slider, an Effect slider and a Skin dropdown** and nothing else. But §18's table underneath it lists
five *buttons* — キャラクター選択 / ゲーム設定 / ショートカット設定 / ゲームを終了する / 閉じる — and
those are image 79's `system-menu` window, near-line-for-line.

So the lead sentence is **residue**: the manual kept describing the old window while its table was
updated to the new one. Read together, the two halves of §18 attest the older two-window arrangement
that image 79 shows, and date the merge to somewhere between them.

| | Image 79 | Modern client per the manual |
| --- | --- | --- |
| Sound/skin settings surface | `options` — BGM slider, Effect slider, Skin dropdown, `on` mute boxes | moved into ゲーム設定 (オプション＞ゲーム設定＞基本設定, per [config.html](https://ragnarokonline.gungho.jp/playmanual/novice/config.html)) |
| Session command menu | `system-menu` — セーブポイントへ / キャラクター選択 / サウンド設定 / 環境設定 / ショートカット / ゲーム終了 / return to game | **is** the オプションウィンドウ (§18's table) |

**Do not take the manual's §18 table as a description of image 79's オプション window.** It describes
image 79's システムメニュー.

---

### Cross-cutting, manual-attested

These are behaviours the manual states about the client generally, or about a control type rather than
one window. They belong beside the cross-cutting findings near the top of this document.

#### M1. The ⊖ button is a maximize/minimize **toggle** ✅ — and this is the first statement of what it does

> 「ウィンドウ右上のボタンで、最大化／最小化の切り替えも可能だ。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §1 基本ウィンドウ

**This is new information for the `minimize / restore` card**, whose "Gesture → response for `⊖`" has
read **unverified** since #104 — no frame in either corpus caught a `⊖` click or a collapsed window, and
roBrowser gave three contradictory behaviours. The manual settles the *semantics*: it is a **two-state
toggle** between 最大化 and 最小化, operated by the **top-right** button, and it is **reversible by the
same button**. Image 79 carries a `minimize` control on **six** windows (`basic-info`, `status`,
`options`, `equipment-items`, `system-menu`, `inventory`), each at the top right, each ~14–17 px square.

What the manual still does **not** give, and what stays unverified: how many frames the toggle takes,
what the minimized window looks like (a bare title strip? the 基本情報 collapse the videos caught?), and
whether the glyph changes. The manual's word is 最小化, not "collapse to title bar", and it says nothing
about the intermediate. **Timing and form remain video-or-intent questions.**

⚠️ One caution against over-reading: the video corpus separately confirms a *different* collapse control
on 基本情報 — a small triangular handle in the middle of the separator below the stats block
(`minimize-restore/01`, `/02`). Whether the top-right `⊖` and that handle are the same mechanism, or two,
is **unverified**. The manual describes only the top-right button.

#### M2. Two windows in image 79 have no `✕`, and the manual explains both ✅

A structural fact fell out of cross-checking the inventory against the shortcut list. Of image 79's 11
windows, exactly **two carry a `minimize` but no `close`** — `basic-info` and `system-menu` — and the
manual accounts for each independently:

> 「**F11** ゲーム内の基本情報ウィンドウ以外を閉じる／ウィンドウをすべて隠す」
> — [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html)

基本情報 is the one window the client's own "close everything" key **exempts**. It is the persistent
window; it is not meant to be closed, which is why it has no `✕` and only a `⊖`.

> 「閉じる | オプションウィンドウを閉じる。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §18 オプションウィンドウ

システムメニュー closes by its own **footer button** — image 79's bottom row button, read as
`return to game` in the inventory — exactly as the manual's option window closes by its 閉じる row rather
than by a title-bar `✕`.

Neither window is missing a control. Both are the manual's design.

#### M3. Right-click on an icon opens a detail window ✅ — stated twice, for two different grids

> 「アイテムにカーソルを合わせて右クリックすれば、アイテムの詳細が別ウィンドウで表示される。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §5 アイテムウィンドウ

> 「各スキルアイコン | アイコンにカーソルを合わせて右クリックすることで、スキルの詳細ウィンドウが開く。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §3 スキルウィンドウ

Two independent statements of the same grammar: **hover a grid cell, right-click, a separate detail
window opens.** Note the shared phrasing 「カーソルを合わせて右クリック」 — hovering is part of the
described gesture in both. Maps to image 79's `inventory` (28 grid cells) and `skill-tree` (27 grid
cells). ⚠️ The manual states it for the *item* window, not the *storage* window; image 79's `storage`
(35 grid cells) is not covered — see M9.

This gives the `list row / grid cell selection` card its missing **right-button** gesture. The card
records hover (pink fill, tooltip) and selection, and left `dblclick` from roBrowser only; right-click
was not in it at all.

#### M4. The bottom-right corner drag-resizes ✅ — the gesture for a grip the cards had only seen

> 「アイテムウィンドウと、アイテムの詳細ウィンドウでは、ウィンドウの右下部分をマウスでドラッグすると、表示範囲を変えられる。説明文が長いアイテムを確認するときに便利だ。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §5 アイテムウィンドウ

The `window title drag` card confirms a **diagonal hatched resize grip at the bottom-right corner**
(`window-drag/04-manual-resize-grip.png`, circled by the manual's own annotation) and says only "Resize
is a separate control" — it never had a statement of what the grip *does*. Now it does: **drag it with
the mouse and the window's 表示範囲 (visible extent) changes.**

Two limits worth keeping honest:

- The manual names **only two windows** for this — the item window and the item detail window. It does
  **not** say every window resizes. Image 79's `inventory` is the attested target; `storage`,
  `skill-tree` and `chat-room` are ⚠️ **candidates by analogy only**.
- This is the **one sustained drag gesture in the whole manual**, and the #115 title-bar-drag hunt is
  still open. The manual attests resize-drag exists; it gives **no** motion profile, no threshold, no
  frame count, no clamping. The card's ≥30-frame monotonic-drag gate still has no source reference.

#### M5. Dragging an item out of the window drops it on the ground ✅

> 「ドロップロック | 鍵をかけておくと、アイテムをウィンドウの外にドラッグしてもアイテムをドロップしなくなる。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §5 アイテムウィンドウ

Stated as the *lock's* purpose, but it attests the underlying gesture plainly: **drag an item outside
the window and it is dropped.** That is a grid-cell behaviour with a consequence outside the UI, and
nothing in either video corpus caught it. The 🕘 ドロップロック control itself is modern — image 79's
`inventory` has no lock — but the gesture it guards against is what image 79's 28 grid cells do.

#### M6. Alt+right-click moves an item **between** the inventory and storage windows ✅

> 「**Alt+右クリック** 指定したアイテムを所持アイテムや倉庫などのウィンドウ間で移動させる」
> — [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html)

**This is the only sentence in the entire manual corpus that mentions 倉庫** (see M9), and it is a real
behavioural statement about image 79: it names 所持アイテム and 倉庫 — image 79's `inventory` and
`storage` — as a pair of windows items move *between*, by a modifier-click rather than a drag. Image 79
shows both windows open simultaneously, which is precisely the situation this shortcut exists for.

#### M7. Shift+left-click writes an item's info into the chat window ✅

> 「**Shift+左クリック** 指定したアイテムの情報をチャットウィンドウに作成する」
> — [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html)

A cross-window behaviour with both ends present in image 79: a grid cell in `inventory` or `storage`
produces text in `chat-room`'s input field. Worth recording because it is a rare attested *link* between
two windows rather than a behaviour inside one.

#### M8. Right-click on a character raises a context menu ✅ (mechanism, not a window)

> 「ほかのプレイヤーに話しかけるときは、対象を右クリックをして「1:1ウィンドウを開く」を選ぼう。」
> — [operation.html](https://ragnarokonline.gungho.jp/playmanual/operation/operation.html) 話しかける

> 「機能制限設定 | クリックで機能制限のON、OFFを切り替えられる。右クリックメニューなど、一部の機能を制限して誤クリックを防ぐ。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §12 パーティーウィンドウ

The client has a **right-click context menu on characters** carrying named entries, and a global
"function restriction" mode that suppresses it to prevent misclicks. No context menu appears in image
79, so there is no control to map — but this is the mechanism that starts a trade (§11, M10) and opens a
1:1 chat, and both of those are referenced from windows image 79 does have.

#### M9. Ctrl+Tab cycles a window through **three** display states ✅ (mechanism, no target in image 79)

> 「Ctrl+Tabキーを押すことで、「デフォルト」「半透明表示」「表示なし」を切り替えられる。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §7 ミニマップウインドウ

> 「**Ctrl+Tab** マップウィンドウの表示／半透明化／非表示の切り替え」
> — [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html)

Both pages agree: **a three-state cycle — default → semi-transparent → hidden → default.** ❌ **Image 79
has no minimap window**, so there is nothing to map this to. It is recorded anyway because it is a
*state model* the client uses and nothing else in this document has: a window visibility that is not
binary. A second shortcut confirms semi-transparency is a general client idiom —
「**Ctrl+End** 他のユーザーの半透明化の切り替え」 — so a replica that only has shown/hidden is missing a
state the source has.

#### M10. The trade flow is a two-stage confirm: both OK, then trade ✅ (mechanism, no target in image 79)

> 「アイテムやZenyの受け渡し時に使用。受け渡ししたいプレイヤーキャラクターを右クリックすると表示されるメニューから、選択する。アイテムの場合はウィンドウにドラッグ＆ドロップ、Zenyの場合は「send yours」欄に金額を入力。お互いに［OK］をクリックし、［trade］を選べば、交換が成立する。」
> — [window.html](https://ragnarokonline.gungho.jp/playmanual/operation/window.html) §11 交換ウィンドウ

❌ **Image 79 has no trade window**, so nothing maps. It is recorded because of the *pattern*, which
recurs in windows image 79 does have: **an arming action separate from a committing action**, with the
commit disabled until both parties have armed. That is the same shape as the skill window's
allocate-then-確定 model #115 measured (pending red digits, arrows hidden window-wide, `cancel`
discards). Two independent instances of one interaction grammar is worth knowing before designing a
replica's confirm behaviour.

The manual also attests a side effect that is pure client behaviour:
「スクリーンショットを撮るチェックボックスにチェックを入れると、[trade]をクリックした際に、自動的にスクリーンショットが撮影されます。」
— a checkbox whose effect fires on *another* control's click.

#### M11. The setup utility shows a tooltip on hover ⚠️

> 「オプションタブでは、ゲーム内のチャットコマンドや、Alt+Yキーで表示されるコマンドリストの設定内容の一部を編集できます。各項目にマウスカーソルを合わせると、コマンドについての説明がでます。」
> — [config.html](https://ragnarokonline.gungho.jp/playmanual/novice/config.html) 画面・サウンド設定

The document's tooltip finding (#115: icon buttons, grid cells and list rows raise a floating label on
hover) gets a written statement of the same idiom — **hover an item, an explanation appears** — but
⚠️ this sentence is about the external **setup.exe** utility, not the in-game client, so it is
corroboration of the house style, not evidence about a game window. The manual gives **no** tooltip
delay anywhere, so that stays **unverified**.

### Keyboard shortcuts that open a window

All from [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html) unless noted.
This is a straight extraction; the right-hand column is the mapping to image 79.

| Key | Manual text | Image 79 target |
| --- | --- | --- |
| **Alt+V** | 基本ウィンドウの開閉 | ✅ `basic-info` |
| **Alt+A** | ステータスウィンドウの開閉 | ✅ `status` |
| **Alt+S** | スキルウィンドウの開閉 | ✅ `skill-tree` |
| **Alt+Q** | 装備ウィンドウの開閉 | ✅ `equipment-items` |
| **Alt+E** | アイテムウィンドウの開閉 | ✅ `inventory` |
| **Alt+O** | オプションウィンドウの開閉 | ⚠️ `options` **or** `system-menu` — the manual's オプションウィンドウ is image 79's `system-menu` (see above), so this key most likely opens `system-menu`. Not resolvable from the manual. |
| **Alt+Z** | パーティーウィンドウの開閉 | ✅ `party` |
| **Alt+H** | 友達ウィンドウの開閉 | ✅ `party` in its 友達 state (the same window — see W7) |
| **Alt+C** | チャットウィンドウの開閉 | 🕘 the **room-creation** dialog (§17), which image 79 does not have — *not* the chat log |
| **Alt+F10** | 会話ウィンドウの表示/非表示の切り替え | ✅ `chat-room` (which is the 会話ウィンドウ — see W11) |
| **Esc** | ウィンドウを閉じる／ゲーム終了などのゲームオプションウィンドウを表示する | ✅ closes a window; raises `system-menu` (「ゲーム終了などの」 matches its ゲーム終了 button) |
| **F11** | ゲーム内の基本情報ウィンドウ以外を閉じる／ウィンドウをすべて隠す | ✅ global; exempts `basic-info` (see M2) |
| **Alt+.** | ワールドマップの表示／非表示 | ❌ no world-map window in image 79 |
| **Alt+N** | ナビゲーションウィンドウの開閉 | 🕘 modern |
| **Alt+U** | クエストウィンドウの開閉 | 🕘 modern; no quest window in image 79 |
| **Alt+P** | パーティ設定ウィンドウの開閉 | ❌ separate window, not in image 79 |
| **Alt+I** | 友達設定ウィンドウの開閉 | ❌ not in image 79 |
| **Alt+M** | ショートカットリストの開閉 | ❌ not in image 79 |
| **Alt+L** | エモーションリストの開閉 | ❌ not in image 79 |
| **Alt+G** | ギルドウィンドウの開閉（加入時のみ） | ❌ not in image 79 — note the **conditional**: the key does nothing unless you are in a guild |
| **Alt+R / Alt+T** | ホムンクルス情報ウィンドウの開閉／待機⇔独自行動の切り替え（所持している時のみ） | 🕘 modern, conditional |
| **Alt+Y** | 「ゲーム設定」の「その他」タブの開閉 | 🕘 modern |
| **Alt+B** | メモリアルダンジョン情報ウィンドウの開閉（挑戦時のみ） | 🕘 modern, conditional |
| **Ctrl+Q** | 装備能力値ウィンドウの開閉 | 🕘 modern |
| **Ctrl+Z** | パーティー掲示板の開閉 | 🕘 modern |
| **F12 / Ctrl+F12** | ショートカットウィンドウの表示がスライドする／（1～4）の表示/非表示の切り替え | ❌ no shortcut window in image 79 |
| **F10** | 会話ウィンドウの大きさを変更する | ✅ `chat-room` — but see W11, the two pages disagree |
| **Ctrl+Tab** | マップウィンドウの表示／半透明化／非表示の切り替え | ❌ see M9 |
| **Ctrl+End** | 他のユーザーの半透明化の切り替え | ❌ world, not UI |
| **Ctrl+H** | モンスター討伐状況の表示／非表示の切り替え | 🕘 modern |
| **Insert** | 座る/立つの切り替え。ノービスの基本スキルLv.3以上が必要 | ❌ world, not UI — recorded for the **conditional**: a key gated on a skill level |
| **Tab** | 入力ウィンドウのあいだをカーソル移動できる | ✅ text-field behaviour; `chat-room`'s input |
| **Shift+Insert / Shift+Delete** | コピーしたテキストの貼り付け／テキストの切り取り | ✅ text-field behaviour |
| **Alt+Enter / Ctrl+Enter / Shift+Enter** | オープンチャット時に発言がギルド／パーティー／同盟ギルドメッセージになる | ✅ `chat-room` input — see W11 |

**Nine of image 79's eleven windows have an attested open/close key** — though one of the nine rests on
`Alt+O`, which the manual cannot split between `options` and `system-menu`, so strictly it is eight
certain and one ambiguous. The two windows with **no** key at all are `equipment-card` and `storage` —
the same two the manual does not document at all (W3, W9).

---

### What the manual says each of image 79's eleven windows does

One subsection per window, keyed to the `key` field in `window-rects.json`. Control counts are from
`control-inventory.json`.

#### W1. `basic-info` — 基本情報 · manual §1 基本ウィンドウ · 14 controls

> 「プレイキャラクターの諸情報を確認できるウィンドウ。項目別に配置されたボタンを押すことで、ステータスや装備アイテム、所持アイテムなどの個別情報が表示される。ウィンドウ右上のボタンで、最大化／最小化の切り替えも可能だ。」

✅ **The purpose statement maps exactly.** Image 79's `basic-info` is 4 meters + 8 text buttons + a
title drag + a minimize, and the sentence describes precisely that: a status readout whose buttons open
individual windows, plus a top-right maximize/minimize toggle (M1).

**The eight buttons.** The manual's §1 button table gives one sentence per button, and **all eight of
image 79's buttons have an exact match**:

| Image 79 button | Manual sentence | |
| --- | --- | --- |
| `status` | 「ステータスウィンドウを開きます。」 | ✅ → `status` (W4) |
| `equip` | 「装備ウィンドウを開きます。」 | ✅ → `equipment-items` (W6) |
| `items` | 「アイテムウィンドウを開きます。」 | ✅ → `inventory` (W10) |
| `skill` | 「スキルウィンドウを開きます。」 | ✅ → `skill-tree` (W2) |
| `chat` | 「チャットウィンドウを開きます。」 | ⚠️ the manual's チャットウィンドウ is the **room-creation** dialog (§17); image 79's `chat-room` is the 会話ウィンドウ. Either the older button opened the log, or it opened a room dialog image 79 does not show. **Not resolvable from the manual.** |
| `friend` | 「パーティー・友達ウィンドウを開きます。」 | ✅ → `party` (W7), which is one window with two states |
| `map` | 「ワールドマップウィンドウを開きます。」 | ✅ opens a window image 79 does not contain |
| `option` | 「オプションウィンドウを開きます。」 | ✅ → `system-menu` (W8), per the §18 finding above |

Note the button table's *phrasing* is uniform — every row is 「…ウィンドウを開きます。」 — so a
`basic-info` button is attested as a **plain window-opener**, not a toggle. (The `Alt+` keys are
attested as 開閉 — toggles. The buttons are not.) Image 79 renders `status` in a `selected` state, which
the manual does not describe: ❌ **whether these buttons show which window is open is not attested.**

**The meters.** 「HP | キャラクターの生命力。」「SP | 「アクティブスキル」を使用するために必要なポイント。」
「Base Lv | キャラクター自身のレベル。」「Job Lv | キャラクターの職業レベル。」
「Weight | キャラクターが持てるアイテム重量と限界値。」「Zeny | 所持金を表す（Zenyはゲーム内通貨の単位）。」
✅ All four of image 79's meters (HP, SP, Base Lv. 60, Job Lv. 47) are covered.

🕘 **Modern:** 「AP | 「APを消費するスキル」を使用するために必要なポイント。4次職、上位特殊2次職、スピリットハンドラーから表示されます。」 — AP is a 4th-job-era stat and image 79 has no AP meter. The manual's own
sentence dates it, which is useful: image 79 predates 4th jobs.

🕘 **Modern:** the §1 table lists **21** buttons (adding ギルド設定, クエスト, ナビゲーション, リプレイ記録,
メール, 実績, Tips, スペシャルアイテムショップ, ショートカット設定, 期間限定デイリーボーナス,
パーティー掲示板, 冒険ガイド, and one 未実装). Image 79 has **8**. The 13 extra are the modern client's.

#### W2. `skill-tree` — スキルツリー · manual §3 スキルウィンドウ · 59 controls

> 「キャラクターの所持スキル状況を確認できる。スキルポイントを獲得したときは、この画面で習得と強化ができ、未習得の場合は灰色で表示される。」

✅ **Directly confirmed by image 79's own contents.** The window has 26 steppers, and **eight** of them
read a zero current value — `デーモン.. 0/5`, `魔法反射 0/3`, `ストリッ.. 0/5`, `ペイニッ.. 0/5`,
`セイフティ.. 0/5`, `ターンア.. 0/10` and `エクスピア.. 0/1` ×2. Those are the 未習得 skills, and the
manual says they render **grey**. This is a manual-attested *rendering rule* for a state image 79 shows,
on eight controls, and the `stepper` card had nothing on it.

> 「ちなみに、習得するだけで効果を発揮するスキルを「パッシブスキル」、SPを消費して使用できるスキルを「アクティブスキル」と呼ぶ。」

✅ Vocabulary, and it explains W1's SP meter sentence.

**The tree/list toggle.**

> 「表示ウィンドウは2種類あり、右上の[－]ボタンをクリックすると「ツリー表示」と「リスト表示」を切り替えられる。」

⚠️ **Function attested; the control differs.** The manual says a **top-right** button toggles between
**ツリー表示 and リスト表示** — a two-state view toggle, reversible by the same button. Image 79 has a
top-right inline title-bar button labelled **`View`** at `[1022, 6, 53, 19]`, which is the right position
and the right kind of control for exactly this job. But the manual's glyph is `[－]` and image 79's is a
word, so **the mapping is a candidate, not a fact.** What is worth taking is the *semantics*: image 79's
window is titled スキル**ツリー** and the manual attests that a tree is one of two mutually exclusive
renderings of the same data.

⚠️ Note the collision this creates: `[－]` is also the glyph family of the minimize `⊖` (M1). On the
skill window the manual assigns a top-right `[－]` to **view switching**, not minimizing — and image 79's
`skill-tree` indeed has **no minimize control at all**, only a `close`. The two agree. Recorded because
a replica that puts a minimize on the skill window would contradict both sources.

**Right-click for detail.** 「各スキルアイコン | アイコンにカーソルを合わせて右クリックすることで、スキルの詳細ウィンドウが開く。」 ✅ → the 27 grid cells. See M3.

🕘 **Modern:** 「スキル詳細ウィンドウ内の時計アイコンをクリックすると、詠唱関連情報ウィンドウが開き、詠唱時間とディレイの内訳や詳細が確認できる。」 — a detail-window-within-a-detail-window; not attested for image 79.

🕘 **Modern — the job-class tab strip.** 「職業分類のタブ | タブをクリックすることで、各職業のスキルの画面が表示される。」 and 「特定のアイテムを装備したり、スキル「クローンスキル」で追加されるスキルは、「その他」タブに表示される。」 **Image 79's `skill-tree` has no tabs whatsoever** (its 59 controls are 1 title drag,
1 close, 1 checkbox, 3 buttons, 27 grid cells, 26 steppers). The modern skill window is tabbed by job
tier; image 79's is a single flat tree. **Do not add a tab strip to image 79's skill window on the
strength of this sentence.**

> 「スキルポイント | 現在、スキルポイントを振り分けられるポイント。」

✅ Confirms the footer counter #115 measured going `16` → `15 / 16`.

❌ **Not covered:** image 79's title-bar checkbox `スキル説明表示`, its `View` button as such, and its
footer `use` / `close` buttons. The manual's §3 has no footer-button table at all. The video corpus is
the only source for those (`checkbox/03`, `/04` capture the 説明表示 checkbox in both states).

#### W3. `equipment-card` — 装備カード · **no manual section** · 4 controls

❌ **The manual does not document this window.** Its 各ウィンドウについて index names 27 windows and
**装備カード is not among them**. Nothing in window.html, operation.html, config.html or shortcut.html
refers to it, and it has no open/close shortcut key.

The nearest the manual comes is M3's 「アイテムの詳細が**別ウィンドウ**で表示される」 — right-clicking an
item opens a separate detail window, itself bottom-right resizable (M4). Image 79's `equipment-card` is
a small window with **1 grid cell and a scrollbar**, which is the shape a single-item detail view would
have. **That is a resemblance, not an attestation, and it is recorded as speculation only.** The manual
supports no claim about this window.

#### W4. `status` — ステータス · manual §2 ステータスウィンドウ · 15 controls

> 「キャラクターのステータス情報を表示するウィンドウ。左に並んだ各ステータスは、レベルアップ時に強化できる。右に並んだステータスは、各ステータスと装備アイテムによって数値が変化する。」

✅ **A two-column model, and it maps.** Image 79's `status` has six read-only text fields — Str, Agi,
Vit, Int, Dex, Luk — each rendered as a `base + bonus` pair, five of them carrying a raise stepper. The
manual attests the split: the **left** column is the raisable one, the **right** column is derived from
those and from equipment. Image 79's field states (`1 +2 -> 2`, `92+10 -> 11`) are exactly that
`base + equipment bonus` form.

> 「Status Point | レベルアップ時に獲得できる、キャラクターステータス強化用のポイント。」

✅ The currency the five steppers spend.

**Why Int has no stepper — a manual-attested candidate.** Image 79 shows raise steppers on Str, Agi,
Vit, Dex and Luk but **not on Int**, whose value is `92+10` while the others sit at `1 +n`.

> 「左に並んだ各ステータスの純粋なステータスには上限値があります。」

⚠️ The manual attests that base stats have a **cap**, which would remove the raise control — a genuinely
useful explanation for an asymmetry in image 79 that no video evidence covers. But it is **one of two
candidates**: the other is simply that the character has too few status points for the next Int step
(cost rises with the stat). **Not resolvable from image 79 alone.** Recorded as a candidate, and it is a
reminder that a stepper's presence in this client is *state-dependent* — the same lesson #115 learned on
the skill window's window-wide arrow hiding.

🕘 **Modern — the whole 特性ステータス system.** 「ウィンドウ左下の「特性ステータス」ボタンで、特性ステータス関連の表示ON/OFFの切り替えが可能です。」 plus the Pow / Sta / Wis / Spl / Con / Crt block and
P.Atk, S.Matk, Res, Mres, H.Plus, C.Rate, T.Status Point. Image 79 has none of it, consistent with W1's
missing AP meter. 🕘 The 「特性ステータス」 **toggle button** is likewise modern.

❌ **Not covered:** image 79's vertical tab at `[8, 241, 13, 165]` (labelled `職業/status`, selected).
The manual's status window has no tab; the modern equivalent is a button, not a tab. The manual attests
nothing about it.

#### W5. `options` — オプション · manual §18 lead sentence + config.html · 12 controls

**Read the §18 finding above first** — image 79's `options` is *not* the manual's オプションウィンドウ
table, which is image 79's `system-menu`.

> 「BGMやEffectなどのオプションを設定できる。」
> — window.html §18, lead sentence

✅ **This one sentence is the attestation for the whole window**, and it is exact: image 79's `options`
holds a **BGM** slider and an **Effect** slider, named in that order, exactly as the sentence names them.

**The `on` checkboxes beside the sliders — the best behavioural detail in this window.**

> 「サウンド設定 | 「off」にチェックを入れると、音量設定を変えずに、音が消せます。」
> — [config.html](https://ragnarokonline.gungho.jp/playmanual/novice/config.html) 基本設定

> 「サウンド設定 | 「全てミュート」にチェックを入れると、音量設定を変えずに、全ての音が消せます。」
> — [config.html](https://ragnarokonline.gungho.jp/playmanual/novice/config.html) 画面・サウンド設定

✅ Two independent statements of the same rule, and the load-bearing clause is
**「音量設定を変えずに」 — *without changing the volume setting*.** So image 79's two `on` checkboxes
(one per slider, both `unchecked`) are **mutes that do not move the slider**: the thumb keeps its
position while the sound is silenced, and unchecking restores the same level. The `slider` card lists
its gesture→response as **unverified** and this does not change that — but it does settle the
**relationship** between the checkbox and the slider beside it, which the card never addressed. 🕘 The
modern control is labelled `off` (or 全てミュート) and image 79's is labelled `on`, so the polarity is
inverted between eras; the *independence from the volume value* is the attested part.

**The Skin dropdown.**

> 「スキン | ゲーム内のウィンドウのスキンを変更できます。 新しくスキンを追加するには、ラグナロクオンラインのゲームクライアントが保存されているRagnarok Online フォルダの中のSkinの中に保存してください。」
> — [config.html](https://ragnarokonline.gungho.jp/playmanual/novice/config.html) 基本設定

✅ Image 79's `options` has a closed dropdown at `[1224, 416, 294, 26]` reading **`Classic Blue`**. The
manual attests (a) it changes the skin of the game's **windows**, and (b) **its option list is populated
from a folder on disk** — which is why the video corpus's dropdown contains a user-installed
`scribbling kid` beside `<Basic Skin>`. That is a genuinely useful structural fact: the list is not a
fixed enumeration. It also corroborates the `dropdown` card's cut-verified finding that committing a
skin **repaints every window on screen in one frame** — the manual says the setting's scope is
ゲーム内のウィンドウ, i.e. all of them.

🕘 **Modern:** in the current client this whole surface lives at オプション＞ゲーム設定＞基本設定, three
levels down a menu, not in the オプション window itself.

❌ **Not covered:** image 79's four checkboxes `attack` / `skill` / `item` / `option` at y≈467 (states
`unchecked` / `checked` / `checked` / `unchecked`). config.html has a 操作設定 section but **prints no
table for it** — only a screenshot — so the manual names none of these rows. The video corpus reads the
analogous row as グラフィック設定's スナップ attack/skill/item (`checkbox/02`), which is the better source.
The manual is silent.

#### W6. `equipment-items` — 装備アイテム · manual §4 装備ウィンドウ · 16 controls

> 「キャラクターが装備している武器、防具を表示。アイテムウィンドウからドラッグ＆ドロップするか、ダブルクリック（持ち替え装備の場合、Ctrl+ダブルクリック）で装備する。装備をしたときに、同じ箇所にすでに装備品がある場合、古いものは自動的にアイテムウィンドウに移動する。」

✅ **Three separate behaviours, all mappable to image 79's 10 grid cells:**

1. **Equip by drag-and-drop** from the item window — `inventory` (W10) → `equipment-items`. A second
   attested cross-window gesture, alongside M6 and M7.
2. **Equip by double-click** — confirming `dblclick` as this client's "use/act" gesture on a grid cell,
   which the `list row / grid cell selection` card had only from roBrowser.
3. **Displacement is automatic and reversed** — equipping into an occupied slot sends the old item back
   to the item window by itself. A state rule with no user gesture, and nothing in the video corpus
   covers it.

**The tabs — an era marker.** 「一般装備 | 現在装備中の一般装備を表示する。」 and
「補助装備 | 現在装備中の衣装装備とシャドウ装備を表示する。」

⚠️ Image 79's two tabs read **`一般装備` (selected)** and **`衣装装備`**. The first matches the manual
exactly. The second does not: the modern client's second tab is **補助装備**, a *container* for 衣装装備
**and** シャドウ装備, while image 79's is 衣装装備 alone. So image 79 predates shadow gear, and its second
tab shows costume equipment only. ✅ The *behaviour* — a tab strip switching which equipped set is
displayed — is attested; ❌ the modern tab's contents are not image 79's.

⚠️ **The `items` button.** Image 79 has a button labelled `items` at `[212, 635, 52, 24]`. The manual's
§4 table contains exactly one `item`-labelled row —
「item | カートアイテムウィンドウを表示する。(カートがあるときに表示される)」 — but that button is
**conditional on owning a cart**, and image 79's character is an Acolyte-line character (its skill tree
is ヒール / ブレッシング / キリエエリソン / サンクチュアリ), a class that has no cart. **So the manual's
`item` row is probably not what image 79's `items` button is, and the manual attests nothing about it.**
Recorded as a rejected mapping so nobody re-proposes it.

🕘 **Modern — everything else in §4's table:** 称号 (titles), ダメージ (damage skin), off (dismount),
装備公開, 持ち替え装備 with its 取り消し/実行 pair and 10-second cooldown, 装備一括解除, 装備能力値.
Image 79 has none of these controls. Two are worth recording anyway as *client idioms*: 持ち替え装備's
**実行/取り消し** pair is another instance of the arm-then-commit grammar (M10), and its
「※再度実行するのに10秒の再使用待機時間があります。」 attests that **a button can be on cooldown**, a
disabled-state cause the `button` card lists as only partially verified.

#### W7. `party` — パーティー · manual §12 パーティー・友達ウィンドウ · 14 controls

> 「パーティーメンバーのリストと、ログイン/ログアウト情報を表示できる。ログインしているメンバーは現在位置も表示される。パーティーメンバーが同一マップ上にいる場合は、ミニマップにキャラクターのいる位置が表示される。」

✅ **Directly confirmed by image 79's own contents.** Its five list rows read
`SakumaRiri（フェイヨン..`, `Sebas*（フェイヨン...`, `ANRI（フェイヨン森）`, `Show_A（フェイヨン森..`,
`AyanaIshizuka（フェイヨン...` — a name followed by a **parenthesised map location**. The manual explains
exactly that: **the location is shown because the member is logged in.** A logged-out member would show
the name without it. That is a per-row state distinction image 79 only shows one side of, now attested.
The row also carries an HP bar (`1109/1109`, `1340/1340`, …), which §12 does **not** mention — ❌ not
attested.

**The party/friends switch.**

> 「（切り替えボタン）| パーティーウィンドウと友達ウィンドウを切り替えられる。」

✅ **Function attested; form differs, and the difference matters.** The manual describes a **button**
that switches between the party window and the friends window. Image 79 implements the same switch as a
**radio pair** — `友達` (unselected) and `パーティー` (selected) at y=750. So the two "windows" the manual
names are ✅ **one window with two mutually exclusive modes**, which is why `Alt+Z` and `Alt+H` both land
here (see the shortcut table). 🕘 The modern client's *control* is a button; image 79's is a radio pair
— and a radio pair is the more honest rendering of "exactly one of two", so the older form states the
model more clearly than the newer one.

**The buttons.** Image 79 has five icon-only buttons — read as `memo`, `info`, `target`, `search`,
`leave` — at y=719. §12's table names six functions: パーティー掲示板, パーティー設定, 機能制限設定,
パーティー招待, パーティー脱退, ミニパーティーウィンドウの自動整列.

- ✅ `leave` → 「パーティー脱退 | パーティーから脱退する。」 The only confident match.
- ⚠️ `search` → 「パーティー招待 | 入力した名前のキャラクターをパーティーに招待する。」 Possible — invite
  works by **typing a name**, which fits a search-shaped control — but image 79's `party` window has no
  text field, so where the name would be typed is unclear. **Candidate only.**
- ❌ `memo`, `info`, `target` — the manual names its buttons by *function*, image 79's are icon-only,
  and the icon sets differ between eras. **No mapping is defensible.** Do not guess these from §12.

> 「※パーティーに加入していないときは、ウィンドウに「パーティー作成」ボタンが出現します。ボタンを押してパーティー名を入力すれば、パーティーが作成できます。」

✅ **A conditional control**, and a useful one: this window's button set **changes with party
membership**. Image 79 shows the in-a-party state (five members listed). A replica needs the other one.

Two more attested behaviours with no control in image 79:
🕘 「機能制限設定 | クリックで機能制限のON、OFFを切り替えられる。右クリックメニューなど、一部の機能を制限して誤クリックを防ぐ。」 (see M8) and, from the 友達ウィンドウ table,
「1：1会話 | リスト内の指定メンバーと1対1で会話ができる。」「消す | 登録リストから削除できる。」 — both
belong to the 友達 mode image 79 does not show.

🕘 **Modern:** パーティー掲示板 (§14), パーティー募集 (§15), and the whole recruitment system, plus
ミニパーティーウィンドウの自動整列.

**Party settings** are a separate window (§13, `Alt+P`) that image 79 does not have. Its three radio
groups — 経験値の分配方法 (各自で取得 / 公平に分配), アイテムの収集方式 (各自で取得 / パーティー全体で共有),
アイテムの分配方式 (各自で取得 / 一定確率で分配) — are the source of the `radio` card's "three groups"
frame, and §13 attests 「設定できるのは、パーティーを組織したリーダーのみ。」 — ✅ **the whole window is
read-only for non-leaders**, a permission-driven disabled state the cards do not otherwise have.

#### W8. `system-menu` — システムメニュー · manual §18 オプションウィンドウ (table) · 9 controls

**This window is the manual's オプションウィンドウ.** Five of image 79's seven buttons have a
sentence-level match in §18's table:

| Image 79 button | Manual row and sentence | |
| --- | --- | --- |
| `キャラクター選択` | **キャラクター選択** — 「キャラクター選択画面に行く。」 | ✅ exact, label and all |
| `ゲーム終了` | **ゲームを終了する** — 「ゲームをやめる。」 | ✅ function exact; image 79's label is shorter |
| `ショートカット` | **ショートカット設定** — 「ショートカットキーを設定できる。」 | ✅ function exact; image 79's label is shorter |
| `サウンド設定` | **ゲーム設定** — 「グラフィックやBGMなどの設定が行える。」 | ✅ **split in image 79** — see below |
| `環境設定` | **ゲーム設定** — 「グラフィックやBGMなどの設定が行える。」 | ✅ the other half of the same split |
| `return to game` | **閉じる** — 「オプションウィンドウを閉じる。」 | ✅ function match, label differs — and see M2 |
| `セーブポイントへ` | — | ❌ **no row in the manual** |

**The ゲーム設定 split is a second era marker, and it corroborates the video corpus.** The modern manual
has **one** row, ゲーム設定, covering 「グラフィックやBGMなど」. Image 79 has **two** buttons,
`サウンド設定` and `環境設定`. And the #104 video corpus independently shows exactly that older
arrangement — **サウンド設定 and グラフィック設定 as two separate windows** (`checkbox/01`,
`checkbox/02`, `close/01`). Three sources agree that the modern client merged what image 79 keeps apart.
config.html shows the merged form as a tabbed 基本設定 / 表示設定 / 操作設定 / 描画設定 / その他.

❌ **`セーブポイントへ` is not attested.** The manual's option window has no such row. The *concept* is
documented — 「戦闘不能になったり、「蝶の羽」を使用したときに戻る場所は、セーブを行なうと変更できる。」
([operation.html](https://ragnarokonline.gungho.jp/playmanual/operation/operation.html) セーブする) —
but a **menu button that returns you there** appears nowhere in the manual. This is image 79's window
having a control the current client does not, and the manual cannot say what it does.

✅ **`Esc` raises this window.** 「Esc | ウィンドウを閉じる／ゲーム終了などのゲームオプションウィンドウを表示する」 — the phrase 「ゲーム終了などの」 identifies it by its ゲーム終了 button, which image 79's
`system-menu` has. Note `Esc` is attested as doing **two different things** depending on context: close
the focused window, or, with nothing to close, raise this menu.

#### W9. `storage` — 倉庫 · **no manual section** · 48 controls

❌ **The manual does not document the storage window.** The 各ウィンドウについて index lists 27 windows
and **倉庫 is not one of them**. This is the largest gap in the manual relative to image 79 — 48 controls,
the second-largest window on screen, and it has no section, no shortcut key, and no table.

**One sentence in the entire corpus mentions it**, and it is a real behavioural statement (M6):

> 「**Alt+右クリック** 指定したアイテムを所持アイテムや倉庫などのウィンドウ間で移動させる」
> — [shortcut.html](https://ragnarokonline.gungho.jp/playmanual/novice/shortcut.html)

✅ **Alt+right-click moves an item between the inventory and the storage window.** Image 79 has both
windows open at once — `inventory` (28 grid cells) and `storage` (35) — which is exactly the arrangement
this shortcut serves.

**What is not attested, and must not be borrowed from §5 アイテムウィンドウ.** It is tempting to
transplant the item window's statements onto storage, because both are tabbed grids. **The tab sets
prove they are different windows:**

| | Tabs |
| --- | --- |
| Manual §5 アイテムウィンドウ | 消耗アイテム / 装備アイテム / 収集アイテム / 個人用 — **four** |
| Image 79 `inventory` | 5 tabs (`item`, `equip`, `etc`, `etc`, `cash`) |
| Image 79 `storage` | **six** — 消耗品 / 装備品 / **カード** / **材料** / 収集品 / その他 |

Storage has カード and 材料 categories the item window does not, and その他 where the item window has
個人用. So §5's tab sentence does not describe storage. Likewise ❌ **unattested for storage:** the
right-click-for-detail gesture (M3 is stated for the item window only), the bottom-right resize (M4
names only the item window and the item detail window), and image 79's footer buttons `list mode`,
`search` ×2, `sort` and `close`. **The video corpus is the only source for this window** — and
fortunately it is the strong one, since #115's 4 h 44 m of unedited footage is almost entirely storage
work (the wheel scroll, the row tooltip and the row selection were all measured here).

#### W10. `inventory` — 所持アイテム · manual §5 アイテムウィンドウ · 38 controls

The manual's richest window section, and most of it maps.

> 「キャラクターが所持しているアイテムを表示する。左側のタブをクリックすることで「消耗アイテム」、「装備アイテム」、「収集アイテム」、「個人用」を切り替えられる。」

✅ **Tabs are on the left and click switches category** — image 79's five tabs sit at `x = 10`, a
vertical strip down the left edge, which matches 「左側のタブ」 exactly. ⚠️ The **category set** does not:
the manual's four are 消耗 / 装備 / 収集 / 個人, image 79 has five (`item`, `equip`, `etc`, `etc`, `cash`).
🕘 The 個人 tab is modern — the manual introduces it together with NPC売却ロック and a Shift+右クリック
gesture to file items into it, all later additions. **Take the gesture, not the category list.**

Per-tab sentences, ✅ for the first three: 「消耗 | 回復アイテムなどの消費アイテムを表示する。」
「装備 | キャラクターが装備していない装備アイテムを表示する。」 — note this one is a **filter rule**, not
just a label: the equip tab shows only *un*equipped gear, so equipping an item removes it from this tab
(and W6 attests the reverse). 「収集 | 収集品や貴重品など、消費アイテムに分類されないアイテムが表示される。」

> 「アイテムにカーソルを合わせて右クリックすれば、アイテムの詳細が別ウィンドウで表示される。」

✅ Right-click a grid cell → detail window. See M3.

> 「アイテムウィンドウと、アイテムの詳細ウィンドウでは、ウィンドウの右下部分をマウスでドラッグすると、表示範囲を変えられる。」

✅ **The bottom-right drag-resize, attested for this window by name.** See M4. Image 79's `inventory` is
the one window in the frame for which resize is explicitly attested.

> 「カバンアイコン | 現在のアイテム所持種類数。アイテムは100種類までしか持てないので注意しよう。」

✅ A **counter with a hard cap of 100 kinds** — a display whose value has a documented limit.

> 「ドロップロック | 鍵をかけておくと、アイテムをウィンドウの外にドラッグしてもアイテムをドロップしなくなる。」

✅ For the gesture (M5); 🕘 for the lock control, which image 79 lacks.

⚠️ **The magnifier button.** Image 79's `inventory` has an icon button at `[109, 976, 19, 20]` read as
`search`. §5's only magnifier-icon control is
「アイテム比較 | 拡大鏡アイコンをクリックしてONにすると、装備アイテムを右クリックした時に現在装備中のアイテムの詳細ウィンドウも一緒に表示されます。」 — a **toggle** that makes right-click open *two* detail
windows for comparison. The icon matches; the feature is a modern one, and the minimap has an unrelated
虫眼鏡ボタン too. **Candidate only — probably not this.** Recorded so the resemblance is on the record
with its doubt attached.

✅ **Shift+左クリック** writes the item's info to the chat window (M7). 🕘 **Shift+右クリック** files it
into the 個人 tab — modern.

#### W11. `chat-room` — チャットルーム · manual §10 **会話ウィンドウ** · 10 controls

**A mapping correction first, because the title is misleading.** `window-rects.json` titles this window
チャットルーム, which is the manual's §17 チャットウィンドウ — 「チャットルームを作成するウィンドウ。」, a
creation dialog with Title / Limit / Sign fields. **Image 79's window is not that.** It holds five
read-only log lines, a scrollbar, a text input and an icon button. That is the manual's **§10 会話ウィンドウ**, the conversation log. All statements below are from §10.

> 「主にプレイヤー同士の会話内容が表示されるウィンドウ。ステータス変化時や、アイテム入手時の報告メッセージなども表示される。」

✅ **Confirmed by image 79's own contents.** Four of its five log rows are player speech
(`Sebas*：レイドリック終わったー`, `SakumaRiri：おつかれさま〜`, `ANRI：もう1周いきますか？`,
`Show_A：いきましょう！`) and the fifth is `経験値が 10800 上がりました。` — a system report line. The
manual's sentence names exactly that mix: player conversation **plus** status-change and item-acquisition
reports in the same log. ✅ **One log, two kinds of line**, and the `text field + send` card's finding
that lines are **coloured by scope** is the rendering that keeps them apart.

> 「下段右側の空欄にメッセージを入れ、Enterキーを押すと、同一画面内の全プレイヤーにメッセージを送信する（送信先の指定も可能）。」

✅ **Enter-to-send, attested.** Three things in one sentence, all mapping to image 79's input field at
`[1044, 978, 458, 21]` (state: `empty, caret at left`):

1. The input is at the **bottom right** of the window — image 79's is.
2. **Enter sends.** This is the manual's statement of the gesture #115 measured frame by frame
   (field clears in 1 frame, log line appended 100 ms later). Manual and video agree on the gesture;
   only the video has the timing.
3. The **default scope is everyone on the same screen**, and the target is selectable
   (「送信先の指定も可能」). The video corpus confirms the selector's contents
   (全体に送る / パーティーに送る / ギルドに送る).

**Send scope from the keyboard**, all from shortcut.html and all ✅ for image 79's input field:

| | |
| --- | --- |
| 「**Ctrl+Enter** オープンチャット時に発言がパーティーメッセージになる」 | → party |
| 「**Alt+Enter** オープンチャット時に発言がギルドメッセージになる」 | → guild |
| 「**Shift+Enter** オープンチャット時に発言が同盟ギルドメッセージになる」 | → allied guild |

A **modifier on the send key overrides the scope for one message** — a behaviour the video corpus does
not cover at all, and one that pairs with the scope dropdown rather than replacing it. Note the
precondition 「オープンチャット時」: these apply while the input bar is open.

> 「（入力欄）| コマンドを入力したり、会話の内容を入力できる。」

✅ **The same field takes chat text and slash commands.** The manual uses this throughout — 「/where」
(§8), 「/minimap」 (§7), 「/agency」 (§14) — so the input is a dual-purpose field, and a replica that
treats it as chat-only is missing half its job.

**F10 — and the two pages disagree, so both are recorded.**

> 「F10キー | 表示する行を増やせる。」 — window.html §10

> 「**F10** 会話ウィンドウの大きさを変更する」 — shortcut.html

⚠️ §10 says F10 **increases the number of displayed rows**; shortcut.html says it **changes the window's
size**. These are compatible (more rows = a taller window) but not identical, and §10's 増やせる implies a
one-way cycle while shortcut.html's 変更する does not. **The row count is the attested quantity; whether
it wraps back to the smallest is not stated.** Image 79 shows **five** log rows — one point on whatever
that cycle is. ✅ Separately, 「**Alt+F10** 会話ウィンドウの表示/非表示の切り替え」 toggles the whole window.

🕘 **Modern — the entire tab strip.** 「＋ | 会話ウィンドウのタブを増やせる。」「- | 会話ウィンドウのタブを減らせる。」「>> | 会話ウィンドウのタブを分離できる。」「◎ | タブに表示する情報を選択できる。」
「鍵 | ウィンドウの位置を固定できる。」 **Image 79's `chat-room` has no tabs and no such control strip** —
it has a single icon button at `[1505, 978, 21, 21]` beside the input. The five-control row is the modern
client's. Two of them are worth recording as *concepts* even so: **>> detaches a tab into its own
window**, and **鍵 pins a window's position** — a lock that would directly answer the `window title drag`
card's question of whether windows can be prevented from moving. Neither is attested for image 79.

⚠️ Image 79's single icon button is a **candidate** for §10's 「（送信先）| どこに送るか選択できる。」 (the
send-scope selector, which the video corpus confirms exists in this era) or for
「（耳打ちリスト）| 耳打ちリストから話す相手を選べる。」 (the whisper-target list). **The manual cannot
distinguish them**, and the inventory's guess of `chat settings` is a third possibility.

🕘 **§17 チャットウィンドウ** — the room-creation dialog with Title / Limit / Sign and a public/private
radio pair — is a **separate window** image 79 does not show, though the `radio` and `dropdown` cards
both draw evidence from it in the video corpus. Its one non-obvious rule:
「チャットルームの作成には、ノービスの「基本スキル」Lv4以上が必要となる。」 — ✅ another **skill-gated
control**, like Insert/sitting.

---

### What the manual does not cover

Stated plainly, because a coverage table's blanks are as useful as its ticks.

**Two of image 79's eleven windows have no manual section at all:**

1. **`storage` (倉庫)** — 48 controls, six tabs, four footer buttons. Not in the 27-window index, no
   shortcut key, no table. One shortcut sentence mentions the word 倉庫 (M6) and that is the whole of it.
2. **`equipment-card` (装備カード)** — 4 controls. Not in the index under any name; nothing anywhere
   refers to it.

**Whole categories the manual never addresses, for any window:**

- **Timing.** Not one duration, frame count, easing or transition anywhere in four pages. Every timing
  in this document is video-observed, and always will be. The single exception is a *cooldown*
  (持ち替え装備's 10 seconds), which is a game rule, not a UI transition.
- **Hover, pressed and disabled states.** The manual describes what controls *do*, never what they
  *look like* while you interact with them. It never mentions a hover state, a pressed state, a
  highlight, or a disabled rendering. The one adjacent statement (M11) is about setup.exe.
- **The title bar.** No statement about dragging a window by its title bar, about z-order, snapping,
  clamping, or where a window opens. The `window title drag` card gains **nothing** from the manual
  except the 鍵 pin concept (modern, chat window only) and the resize grip's purpose (M4).
- **Scrollbars.** Not one sentence. No thumb drag, no arrow step, no wheel. #115's two open gestures
  stay open.
- **Hold-to-repeat**, on any stepper or arrow, anywhere.
- **Sound.** No statement that any control makes a sound when clicked or hovered (the video corpus has
  `button/01-menu-hover-sound.png`).
- **Window open/close animation or position memory.** Nothing on whether a window reopens where it was,
  which #115 inferred from streamers' fixed layouts.

**And one asymmetry worth naming.** The manual is at its most detailed exactly where the video corpus is
thinnest — cross-window gestures (M5, M6, M7, W6's drag-to-equip), conditional and permission-gated
controls (W7's パーティー作成, §13's leader-only settings, §17's skill gate), and what a mode *means*
(W2's tree/list, W5's mute-without-changing-volume). Those are things a player does rarely and a
streamer never does on camera. It is silent exactly where the video corpus is strong. Neither source
would have produced this document alone.

## Coverage summary

The first six columns are **video-observed** (#104, #115) and are unchanged. The last column is the new
**manual-attested** class (#117) — the publisher's own statement of what the control is *for*. It never
carries timing or form; see `## Manual-attested behaviour` for every sentence and its mapping.

| Control | Idle | Hover in source | Pressed | Selected / active | Transition timing | Gesture → action | **Manual-attested (#117)** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| button | ✅ | ✅ **yes, 1 frame @60 fps** | ✅ **yes — third sprite, held ~150–200 ms** | ✅ | ✅ **1 frame, cut-verified ×5** | ✅ **click → action measured** | ✅ **purpose of all 8 `basic-info` + 6 of 7 `system-menu` buttons, one sentence each**; a button can be on **cooldown** (10 s). ❌ nothing on hover/pressed/timing; ❌ nothing on the `selected` marking image 79 shows |
| checkbox | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred | ✅ **the `on` box mutes 「音量設定を変えずに」 — independent of its slider**; drop-lock; 機能制限 ON/OFF; a checkbox whose effect fires on *another* control's click (trade screenshot) |
| radio | ✅ | ❌ unverified | ❌ unverified | ✅ both states | ❌ unverified | ⚠️ inferred | ✅ **party/friends is one window in two exclusive modes**; §13's three groups are **leader-only** (permission-gated disabled state) |
| tab | ✅ | ❌ unverified | ❌ unverified | ✅ full set | ❌ unverified | ⚠️ inferred | ✅ **click switches category; the item window's strip is on the left**; the equip tab is a **filter rule** (unequipped only). ⚠️ category sets differ between eras and between `inventory` and `storage` |
| stepper | ✅ | ✅ **yes — pink cell frame** | ✅ **yes — icon darkens while held** | n/a | ✅ **1 frame, cut-verified** | ✅ **one click = one point, pending; cancel discards** | ✅ **skill points are the currency; 未習得 skills render grey**; base stats have a **cap**, a candidate reason a raise arrow is absent. ❌ still nothing on hold-to-repeat |
| slider | ✅ + end clamp | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified | ✅ **BGM and Effect named as this window's two sliders**; muting does not move the thumb. ❌ no gesture, no range, no step |
| scrollbar | ✅ + thumb sizing | ❌ unverified | ❌ unverified | n/a | ✅ **wheel = 1 frame @60 fps, ×40** | ⚠️ **wheel ✅ (3 rows/notch, clamped); drag ❌; arrow ❌** | ❌ **nothing whatsoever.** Not one sentence about a scrollbar in four pages — thumb drag and arrow step stay exactly as open as #115 left them |
| dropdown | ✅ | ✅ **yes, 1 frame** | ✅ arrow inset while open | ✅ | ✅ **1 frame, cut-verified ×4** | ✅ | ✅ **Skin's scope is 「ゲーム内のウィンドウ」 — all of them**, corroborating the 1-frame whole-UI reskin; **the option list is populated from a folder on disk**, not fixed |
| list / grid selection | ✅ | ✅ **yes** (both kinds) | ❌ unverified | ✅ | ❌ unverified (cut) | ✅ states only | ✅ **right-click → detail window** (stated twice); **double-click equips**; **drag out of the window = drop on the ground**; **Alt+right-click moves an item between windows**; **Shift+left-click writes it to chat**; a party row shows a location **because the member is logged in** |
| window title drag | ✅ | ❌ unverified | ❌ unverified | n/a | ❌ unverified | ❌ unverified | ✅ **the bottom-right corner drag-resizes** — the gesture for the grip #104 had only *seen* (item window + item detail window, by name). ❌ still nothing on title-bar drag, z-order, snapping or position memory. 🕘 a **鍵 pin** exists in the modern chat window |
| minimize / restore | ✅ | ❌ unverified | ❌ unverified | ✅ both panel states | ❌ unverified | ❌ unverified | ✅ **the biggest single gain: `⊖` is a two-state 最大化／最小化 toggle on the top-right button, reversible by itself** — the card's central "unverified" is now answered *semantically*. ❌ timing, minimized form and glyph change all still unverified |
| close | ✅ | ❌ unverified | n/a | n/a | ⚠️ open = 1 frame (verified); close not measured | ❌ gesture unverified | ✅ **a gesture at last: `Esc` closes the focused window; `F11` closes every window except 基本情報.** That also explains why image 79's `basic-info` and `system-menu` carry no `✕` (M2). ❌ timing still not measured |
| text field + send | ✅ + caret + masked + disabled | ❌ unverified | n/a | ✅ | ✅ **clear 1 frame; log +100 ms** | ✅ **send measured** | ✅ **Enter sends; the default scope is everyone on the same screen**; **Ctrl / Alt / Shift + Enter override the scope for one message**; the field takes **slash commands** as well as speech; `Tab` moves between input fields; `F10` changes the log's row count |

**Manual coverage of image 79's eleven windows**

| Window | Manual section | Verdict |
| --- | --- | --- |
| `basic-info` | §1 基本ウィンドウ | ✅ **Best-covered window.** Purpose, the ⊖ toggle, all 4 meters and all 8 buttons attested one sentence each. 13 modern buttons and the AP meter excluded. |
| `skill-tree` | §3 スキルウィンドウ | ✅ Purpose, the grey 未習得 rendering, right-click detail, the skill-point counter. ⚠️ tree/list toggle attested but image 79's control is `View`, not `[－]`. 🕘 job-tab strip is modern — image 79 has none. ❌ 説明表示 checkbox and the `use`/`close` footer. |
| `equipment-card` | **none** | ❌ **Not in the manual's 27-window index under any name.** Nothing attested. |
| `status` | §2 ステータスウィンドウ | ✅ The two-column raisable/derived model and Status Point. ⚠️ the stat cap as a candidate reason Int has no stepper. 🕘 the whole 特性ステータス block. ❌ image 79's vertical tab. |
| `options` | §18 **lead sentence** + config.html | ✅ 「BGMやEffectなどのオプションを設定できる。」 is exact; mute-without-changing-volume; the Skin dropdown's scope and folder-backed list. ⚠️ **§18's button table is NOT this window — it is `system-menu`.** ❌ the four attack/skill/item/option checkboxes. |
| `equipment-items` | §4 装備ウィンドウ | ✅ Drag-to-equip, double-click-to-equip, automatic displacement back to the item window; the 一般装備 tab. ⚠️ image 79's second tab is 衣装装備, the manual's is 補助装備 (predates shadow gear). ❌ the `items` button (the manual's `item` row is the cart button, and this character has no cart). |
| `party` | §12 パーティー・友達ウィンドウ | ✅ The member list, **location shown because logged in**, the party/friends switch as one window in two modes, `leave`. ⚠️ `search` → パーティー招待 only. ❌ `memo`, `info`, `target`; ❌ the per-row HP bar. |
| `system-menu` | §18 **table** オプションウィンドウ | ✅ 6 of 7 buttons matched sentence-for-sentence; `Esc` raises it; its footer button is the manual's 閉じる. ✅ image 79 splits ゲーム設定 into サウンド設定 + 環境設定, which the video corpus independently confirms. ❌ `セーブポイントへ` has no row. |
| `storage` | **none** | ❌ **Not in the index.** 48 controls, no section, no key. One sentence in four pages mentions 倉庫: Alt+right-click moves items between it and the inventory. Its six tabs differ from the item window's, so §5 must **not** be transplanted. |
| `inventory` | §5 アイテムウィンドウ | ✅ **Richest section.** Left tab strip, per-tab filter rules, right-click detail, **bottom-right drag-resize by name**, the 100-kind cap, drag-out-to-drop, Shift+left-click to chat. ⚠️ the magnifier button (アイテム比較 is modern). 🕘 the 個人 tab. |
| `chat-room` | §10 **会話ウィンドウ** | ✅ **Note the correction: this is §10, not §17.** The mixed player/system log, Enter-to-send with same-screen default scope, modifier+Enter scope overrides, slash commands, F10 row count, Alt+F10 toggle. ⚠️ two pages disagree on what F10 does. 🕘 the entire +/-/>>/◎/鍵 tab strip. ⚠️ the single icon button is unidentifiable. |

**Nine of eleven windows are covered; two are not covered at all.** The two uncovered ones —
`equipment-card` and `storage` — are also the only two with no keyboard shortcut in the manual.

**#104's five gaps, and where they stand after #115 and #117**

| # | Gap | Status after #115 (video) | What #117 (manual) adds |
| --- | --- | --- | --- |
| 1 | A scrollbar being driven | ⚠️ **Partly closed.** The **wheel** is measured — 3 rows per notch, one frame, clamped at the ends. **Thumb drag and arrow step are still open.** | ❌ **Nothing.** The manual contains no sentence about a scrollbar. |
| 2 | A window being dragged | ❌ **Still open.** No title-bar drag exists in any footage searched. | ⚠️ **A neighbouring gesture closes instead.** The bottom-right **resize** drag is now attested with its effect (M4). The **title-bar** drag is not mentioned anywhere. 🕘 The modern chat window has a 鍵 that pins a window's position — evidence the client models "movable" as a togglable property. |
| 3 | A chat message typed and sent | ✅ **Closed.** Field-clear and log-append measured as two cut-verified one-frame events 100 ms apart. | ✅ **Widened.** Enter-to-send confirmed in prose, plus the default scope (everyone on the same screen), three modifier+Enter scope overrides, and the field's dual role as a command line. |
| 4 | A skill stepper arrow clicked | ✅ **Closed.** One click = one pending point; the counter, the red digit and the window-wide arrow hide all land in one cut-verified frame; `cancel` on 確定 discards. **Hold-to-repeat is the one part still open.** | ⚠️ Adds the **grey 未習得 rendering** and the **stat cap** as a second reason an arrow can be absent. ❌ Hold-to-repeat still unmentioned. |
| 5 | A button held long enough to show a pressed sprite | ✅ **Closed twice over** — the dialog OK button (5 presses, 117–200 ms) and, independently, the skill cell's darkening icon. | n/a — the manual never describes an interaction state. |

**A sixth gap, opened and closed by #117 itself**

| # | Gap | Status |
| --- | --- | --- |
| 6 | What `⊖` actually does | ✅ **Closed semantically.** 「ウィンドウ右上のボタンで、最大化／最小化の切り替えも可能だ。」 — a reversible two-state toggle on the top-right button (M1). ⚠️ Its **timing, its minimized form and whether the glyph changes remain unverified**, and only video can settle those. |

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

**#117 changes that position in one respect and confirms it in another.** It confirms it for the
scrollbar: the manual has nothing, so thumb drag and arrow step really are intent-specified and no
further reading will change that. It changes it for **purpose**: a large class of things the replica has
to get right — what a button opens, what a mode means, which key reaches which window, what a gesture is
*for* — is now **manual-attested** rather than intent-specified, and does not need to be invented. The
division of labour that falls out is worth stating once, plainly:

| Question | Ask |
| --- | --- |
| *What does this control do?* | the **manual** — it answers for 9 of image 79's 11 windows |
| *How does it look and how long does it take?* | the **video corpus** — the manual answers neither, ever |
| *What about `storage`, `equipment-card`, scrollbar gestures, and window drag?* | **intent**, and the video corpus where it reaches — the manual is silent on all four |
