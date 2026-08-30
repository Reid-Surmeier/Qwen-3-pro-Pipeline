# PLAYTEST — オプション window

You are a Playtester. Your only job is to play a web build in a real browser with real
pointer gestures and to record what you saw, action by action. Judge every action by
**looking at the screenshots** — never by the page DOM, the accessibility tree, the
console, or a tool's text reply. Do not inject JavaScript. Use file tools only to look at
screenshots you saved and to write the play log at the end.

Take every screenshot **without giving it a filename**: the browser tool then returns the
picture inline and tells you the file name it saved. Look at every picture. Write the file
names down; the play log must name them. A screenshot you did not look at cannot be cited.

## Target

`https://windows-wsl.taile06c45.ts.net/godot-v2-options-b/`

## Coordinates

All coordinates below are design coordinates on a 1536 x 1024 surface. Your viewport is
1536 x 1024 CSS pixels at device pixel ratio 1, so pass them unchanged — but confirm on
the first screenshot that the image is 1536 x 1024 and the magenta background reaches all
four edges. If you see black bars, convert: scale = min(vw/1536, vh/1024),
offsetX = (vw - 1536*scale)/2, offsetY = (vh - 1024*scale)/2, css = offset + design*scale,
and record the numbers you used in `notes`.

The window sits at x=1108..1532, y=297..499 with a title bar across its top (y=297..321).

## What the original game does (your expectations)

These come from footage of the real client and its official manual. Compare what you see
against them; the log asks you for both.

- **Slider** (BGM row y≈355, Effect row y≈389; track x≈1236..1466 between a left arrow at
  x≈1230 and a right arrow at x≈1472; round thumb sits on the track): dragging the thumb
  moves it continuously with the pointer and it stops exactly at the track ends; clicking
  an arrow steps it a little; the thumb looks pressed (darker) while held and normal on
  release. No easing, no lag: the thumb is under the pointer on the same frame.
- **Checkbox** (12 px squares: `on` beside each slider at x≈1493 y≈358 and y≈392; footer
  row y≈473 at x≈1144 attack, x≈1234 skill, x≈1306 item, x≈1403 option): click toggles
  the tick instantly; clicking again restores the previous look exactly.
- **Dropdown** (field x=1224..1518, y=416..442; arrow button at its right end x≈1505
  y≈429): clicking opens a list below the field in one frame, with a highlight bar on the
  current value; moving the pointer over rows moves the bar; the field does not change
  until a row is clicked; clicking a row closes the list and puts that name in the field;
  Esc or clicking elsewhere closes it without changing the field.
- **Hover**: buttons, arrows, checkboxes and list rows show a light highlight while the
  pointer rests on them; the cursor becomes a pointing hand over buttons.
- **Title bar drag** (grab at x≈1300 y=309): the window follows the pointer 1:1 and stops
  at the screen edge; nothing animates.
- **⊖ minimize** (x=1491 y=311): reveals a compact minimized window (icon, title and both buttons on a finished bar) instantly;
  clicking again restores it. **⊗ close** (x=1517 y=312): the window disappears; a small
  "reopen" control appears near the top-left of the screen — clicking it brings the window
  back (that reopen control is a test affordance, not part of the game).

## Actions, in order

For every action: screenshot **before**, do the gesture, screenshot **after**. For drags,
also screenshot **mid-gesture** with the button still held. Then look at all of them.

1. Load the URL; screenshot until the window is fully drawn on magenta (loaded shot).
2. BGM thumb drag: press on the visible thumb (look at the loaded shot; it starts near
   x≈1428 y=355), drag left in at least 6 moves to x=1236, screenshot mid-way with the
   button held, release, screenshot. The thumb clamps at the track's left end (its centre
   lands near x≈1246). Then press on the thumb **where you now see it**, drag right in 6
   moves to x=1470 (past the end), mid shot, release, after shot. Note where it stopped.
   If a press misses the thumb, log that attempt with control id `miss` and retry from
   the thumb's visible centre.
3. BGM right arrow click at (1472, 355) — the thumb is already at the right end, so the
   expected response is **no movement** (an end-clamped slider does not overshoot); a
   thumb that stays put here matches expectation. Then left arrow at (1230, 355): the
   thumb should step a little to the left.
4. Effect thumb: click directly on the track at (1300, 389) without dragging.
5. BGM `on` checkbox (1493, 358): click, screenshot, click again, screenshot.
6. Footer checkboxes: attack (1144,473) click; skill (1234,473) click (it starts checked);
   then attack again to restore.
7. Dropdown: click the arrow (1505, 429), screenshot (list open?); move the pointer over
   the second row (about 30 px below the field) and screenshot; click that row and
   screenshot; open again and press Esc; screenshot.
8. Hover: move the pointer onto the ⊖ button (1491,311) and rest 1 s, screenshot; move
   onto the BGM thumb, rest, screenshot.
9. Title drag: press at (1300,309), drag in 8 moves to (900, 600), mid shot, release,
   after shot. Then drag it back toward (1300,309) so it returns near its start.
10. ⊖ minimize (1491,311): click, screenshot; click again, screenshot.
11. ⊗ close (1517,312): click, screenshot; find and click the reopen control, screenshot.
12. Free play: spend up to 6 more actions on anything you want to probe — rapid double
    clicks on a checkbox, dragging the thumb off the window and back, clicking the track
    ends, pressing Esc with the window open. Log each.

## Play log

Write `./play-log.json` next to this file, exactly this shape:

```json
{
  "export_url": "https://windows-wsl.taile06c45.ts.net/godot-v2-options-b/",
  "viewport": {"width": 1536, "height": 1024},
  "actions": [
    {
      "control": "bgm-slider-thumb",
      "gesture": "drag (1440,355) -> (1236,355)",
      "expected": "thumb follows the pointer continuously and stops at the left end",
      "observed": "what actually differed between before, mid and after — two sentences, literal",
      "responsive": true,
      "matches_expected": true,
      "screenshots": {"before": "file", "mid": "file", "after": "file"}
    }
  ],
  "free_play": [ { same shape } ],
  "notes": "load time, coordinates that did not line up, scale/offsets, anything odd"
}
```

Use these control ids: `title-drag`, `minimize`, `close`, `reopen`, `bgm-slider-thumb`,
`bgm-arrow-left`, `bgm-arrow-right`, `bgm-on`, `effect-slider-track`, `effect-on`,
`dropdown-arrow`, `dropdown-row`, `checkbox-attack`, `checkbox-skill`, `checkbox-item`,
`checkbox-option`, `hover-minimize`, `hover-thumb`, and `miss` for a press that did not land on
the control (retry counts as the real attempt).

`responsive` is true only if the **after** (or, for a hold, the **mid**) screenshot shows a
visible response on that control. `matches_expected` is true only if what you saw matches
the expectation above — a thumb that moves but overshoots the track end is responsive and
does not match. Be literal; if you cannot see a difference, write false and say so.

Then stop. Your final message is the single word `DONE`.
