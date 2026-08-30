# Official jRO window corpus — the clean control-artwork source (#116)

**Question:** does a clean copy of Reference Screen image 79 exist online?

**Answer: no — and something better for the Control Library does.**

## The screenshot itself is not online

Every distinctive string in image 79 and in the earlier `ro-hud-fullscreen` screen
was searched (`SakumaRiri`, `AyanaIshizuka`, `LunaBrigade`, `Sebas*`, `Show_A`,
`ET登頂作戦部屋`, skin names). None returns a hit anywhere. Both screens share the same
cast of character names, which means they came from one private source — not from a
public page a clean copy could be fetched from. A clean original, if it exists, is on
the owner's machine, not on the web.

## What is online: GungHo's official per-window screenshots

The official play manual (`ragnarokonline.gungho.jp/playmanual/operation/window.html`
and `novice/config.html`) hosts one screenshot per window of the current jRO client in
`<Basic Skin>` — the same chrome family as image 79. Measured on the PNGs:
0.3–0.5 % unique colours, 80–96 % flat horizontal neighbour pairs, hard 1-px edges.
These are true 1:1 client pixels.

Layouts are the *modern* client's (the skill window is a tree, the option window is a
button menu, the party window has tabs), so they are **not** a substitute for image 79
as the composition reference. They are the clean source for **control artwork and
Behaviour-Card evidence**: the slider (left arrow, track, round thumb, right arrow),
checkbox, radio, dropdown field + arrow, tab strip, title bar with ⊖ and ⊗, list rows,
scrollbar. `compare-image79-vs-official-3x.png` shows image 79's オプション window over
the official ゲーム設定 window: same slider, same checkbox, same dropdown arrow — one soft,
one crisp.

## A scale finding

The official option/config windows and image 79's オプション window carry the same
controls at visibly different sizes: image 79's are ≈1.5× larger. Image 79 is therefore
a ~1.5× resample of client-native pixels, which is consistent with its soft edges (#106
tested only for integer upscales). This does not change the owner's decision on #114 —
visual comparison at magnification is the gate — but #107 should decide whether the
Control Library's artwork is authored at **client-native scale** (from these official
crops) and rendered at the Reference Screen's scale, or authored at the Reference
Screen's scale directly.

## Files

`artifacts/references/ro-source-game/official-windows/` — 31 images + `sources.json`
(URL, size, mode, sha256 per file; licence note: private study).
