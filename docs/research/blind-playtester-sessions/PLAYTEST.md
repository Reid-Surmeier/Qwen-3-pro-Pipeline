# PLAYTEST

You are a Playtester. Your only job is to play a web build in a real browser, using real
pointer gestures, and to record what you saw. Judge every action by **looking at the
screenshot** taken after it. Do not read the page DOM, the accessibility tree or the
console to decide whether a control worked, and do not inject JavaScript. Use your file
tools only to look at the screenshots you saved and to write the play log at the end.

## Target

`https://windows-wsl.taile06c45.ts.net/godot-ro-hud/`

## Coordinates

Every coordinate below is a **design coordinate** on the build's 1973 x 1319 design
surface. Your browser viewport is set to exactly 1973 x 1319 CSS pixels at device pixel
ratio 1 and the game canvas fills it, so for this run design coordinates *are* CSS
coordinates: pass them to the mouse tools unchanged.

Check that once on the first screenshot: the image should be 1973 x 1319 and the magenta
background should reach all four edges. If instead you see black bars, the canvas is
letterboxed and you must convert every coordinate before using it:

```
scale   = min(viewportWidth / 1973, viewportHeight / 1319)
offsetX = (viewportWidth  - 1973 * scale) / 2
offsetY = (viewportHeight - 1319 * scale) / 2
cssX    = offsetX + designX * scale
cssY    = offsetY + designY * scale
```

Record the scale and offsets you used in the play log's `notes`.

## Actions, in order

Take every screenshot **without giving it a filename** — the browser tool then returns the
picture to you inline and also saves it to disk, and its reply tells you the file name it
used. Look at the picture it returns. Write those file names down; the play log has to
name them. Never decide `responsive` from a tool's text output alone.

1. Navigate to the URL, then screenshot. If it shows a loading bar, a splash image or a
   black screen, wait 3 seconds and screenshot again until several windows on a magenta
   background are visible. That is the loaded screenshot.

2. **party-list scrollbar thumb** - the vertical scrollbar down the right edge of the
   "パーティー" window, thumb near x=1222, y=395..500.
   Screenshot (before), drag with the left mouse button from (1222, 420) to (1222, 600),
   screenshot (after).

3. **status button** - in the top-left "基本情報" window at (521, 82).
   Screenshot (before), click (521, 82), screenshot (after).

4. **OK button** - in the "チャットルーム作成" window at (1731, 638).
   Screenshot (before), click (1731, 638), screenshot (after).

## Play log

When the three controls are done, write `./play-log.json` in your working directory,
next to this file, with exactly this shape:

```json
{
  "export_url": "https://windows-wsl.taile06c45.ts.net/godot-ro-hud/",
  "viewport": { "width": 1973, "height": 1319 },
  "actions": [
    {
      "control": "party-list scrollbar thumb",
      "gesture": "drag (1222,420) -> (1222,600)",
      "observed": "<what differs between the before and after screenshots, one or two sentences; say 'no visible change' if nothing differs>",
      "responsive": false,
      "screenshots": ["<before file name the tool reported>", "<after file name the tool reported>"]
    }
  ],
  "notes": "<anything odd: load time, coordinates that did not line up, the scale/offsets you used>"
}
```

`responsive` is `true` only if the **after** screenshot shows a visible response on that
control — the thumb has moved, a button shows a pressed or settled state, a window opened
or closed. Be literal. If you cannot see a difference between before and after, write
`false`. A change you saw only while the mouse button was held down is not a response;
say so in `observed` and still write `false`.

Then stop. Your final message is the single word `DONE`.
