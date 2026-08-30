# Image 79 — native scale, hash-locked reference, window rects, control inventory

Research ticket [#106](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/106), map #103.
Board `wbOhmbJkG83vj2NMgfnQr2` (FigJam), nodes `1:5` ("image 79") and `1:3` ("image 86").

## Answer in one line

**Image 79 is natively 1536×1024. There is no integer upscale to undo — the raster is
already at native scale (1×).** The 3000×2000 figure in the ticket is the FigJam
*display box*, not the image; Figma is showing a 1536×1024 upload at a non-integer
1.953125× on the canvas.

## 1. What the source actually is

The premise that a 1536×1024 file must be "Figma's downscaled preview" is wrong, and it
is worth being precise about why. Read through the Figma Plugin API:

| | node `1:5` | node `1:3` |
| --- | --- | --- |
| node name | image 79 | image 86 |
| node type | `RECTANGLE` | `RECTANGLE` |
| node box on canvas | 3000 × 2000 | 1588.12 × 1548.32 |
| fill | `IMAGE`, `scaleMode: CROP`, identity transform | same |
| image fill hash | `7d00a2c0…7a45` | `a1df72ce…3a0c` |
| **original upload size** | **1536 × 1024** | **1596 × 1556** |
| original container | PNG, 8-bit, colour type 2 (RGB) | PNG, 8-bit, colour type 6 (RGBA) |
| original file bytes | 2,062,041 | 1,439,278 |
| original file sha256 | `73d0b347d723d6f93d7db37804dad123043b6cea933b70cb419ae3feff29ef4a` | `d7d331db0d89189241661eb832dad34b75b168d117fc33d9451e3ebe0d8efdb6` |
| original RGBA pixel sha256 | `df2d8752b3ab2fda9caea44def3a453c66b9588f9d1ad57dca2f8b7ebca24758` | `5d2053358309f32b670e61f54772491ce6e1db1c133e4eebb51164d9bc76fbbe` |

`getImageByHash(hash).getSizeAsync()` reports the size of the *uploaded* file, and
`getBytesAsync()` returns its bytes. Both were read in-process; the PNG header, an
in-process inflate + unfilter, and an in-process SHA-256 produced the table above.

Note node `1:3`: its canvas box (1588×1548) is *smaller* than its upload (1596×1556).
A "preview" theory cannot explain an asset that is larger than the box it sits in.

## 2. Limitation — the byte-exact original could not be exported

This is the honest boundary of the result. Three routes to the original object, all shut:

1. **`GET /v1/files/:key/images`** is the only endpoint that hands back the original S3
   object for an image fill. It needs the `files:read` OAuth scope. The local Figma
   credential is an MCP credential scoped **`mcp:connect`** only
   (`scripts/figma-oauth-bootstrap.mjs`, `const FIGMA_SCOPE = "mcp:connect"`), and it
   returns **403 on every REST v1 call, `/v1/me` included** — under both `Authorization:
   Bearer` and `X-Figma-Token`. This is also why the earlier attempt recorded
   `"fills": {}`: the `nodes` call had already failed with 403, so no `imageRef` was ever
   collected. It was never a lookup bug.
2. **`download_assets`** does return `rawImages` (the original uploads) — but it refuses
   FigJam: *"This tool is not supported for Figjam files. Supported file type: Design."*
3. **`use_figma`** *can* read the original bytes in-process, and did. But its response is
   **truncated at 20KB**, so 2.06MB of PNG cannot be ferried out through it. Chunked
   base64 would need ~140 round trips per image.

**What is stored instead**, and how far it is from the original — measured, not assumed:

The `get_figjam(includeImagesOfNodes)` inline image comes back at the upload's exact
native size (1536×1024 and 1596×1556 — note the second is the *upload* size, not the node
box, confirming this path serves the fill source rather than a node render). It is
re-encoded in transit, so it is neither byte- nor pixel-exact. Against a 64×32 crop of
the true original at (8,4), 2047 pixels compared:

| measure | value |
| --- | --- |
| pixels byte-identical to the original | **91.4 %** |
| max absolute channel error | **6** / 255 |
| mean absolute channel error | **0.081** |
| error distribution | 5760 channels exact, 316 off by 1, 35 by 2, 15 by 3, 10 by 4, 3 by 5, 2 by 6 |

That profile is a high-quality lossy re-encode, not a resample: a resample would blur
edges and leave almost no pixel untouched. Row-hash comparison agrees — row 0 is
identical, rows 1–9 differ slightly.

`sources.json` records both hash families, so the stored copy can be re-verified and
swapped for the true original the moment a `files:read` credential exists. **Getting a
Figma personal access token, or re-running the OAuth bootstrap with `files:read`, is the
one action that would close this gap.**

## 3. Native scale — method and evidence

The raster was tested for an integer upscale four ways. The script is
`scale.py` in the session scratchpad; all four tests agree.

### Test 1 — edge-phase concentration

For a candidate scale *k*, take the per-column horizontal edge energy and ask what
fraction falls on the best single phase `x ≡ r (mod k)`. A true *k*× nearest/box upscale
puts ~100 % on one phase. Chance level is 1/k.

| k | horizontal | vertical | chance level |
| --- | --- | --- | --- |
| 2 | 50.31 % | 50.36 % | 50 % |
| 3 | 33.77 % | 33.60 % | 33.3 % |
| 4 | 25.81 % | 25.52 % | 25 % |

Every scale sits on chance. No phase structure exists.

### Test 2 — flat-run histogram (the discriminating test)

Run lengths of identical adjacent pixels. A *k*× upscale forces every run to a multiple
of *k*. Run this against the known-3× precedent screen as a positive control:

| | image 79 (this ticket) | ro-hud-fullscreen (known clean 3×) |
| --- | --- | --- |
| median run length | **1** | **3** |
| mean run length | 1.54 | 3.68 |
| run length 1 | 78.96 % | 32.36 % |
| run length 2 | 9.69 % | 1.82 % |
| run length 3 | 5.04 % | **37.83 %** |
| runs divisible by 2 | 13.57 % | 22.43 % |
| runs divisible by 3 | **6.66 %** | **40.38 %** |

The control lights up at 3 exactly as it should; image 79 shows the monotone decay of a
natural, unscaled image. This is the strongest single piece of evidence.

### Test 3 — autocorrelation of the edge-energy signal

Lags 1–12 decay monotonically (+0.715, +0.566, +0.403, +0.418, +0.352 …) with no peak at
any lag. An upscale of period *k* produces a clear spike at *k*.

### Test 4 — point-sample round trip

Downsample by *k* with point sampling, re-expand, compare to the original. A true *k*×
upscale round-trips exactly.

| k | mean abs error | exact pixels |
| --- | --- | --- |
| 2 (best phase) | 11.31 | 45.4 % |
| 3 | impossible — 1024 / 3 is not an integer | — |
| 4 (best phase) | 19.22 | 26.1 % |

### Test 5 — look at it

`native-crispness-4x.png` is the 基本情報 title bar magnified 4× nearest-neighbour. Every
source pixel is a hard 4×4 block, glyph strokes step by exactly one pixel, and the item
icons carry 1-pixel detail. One-pixel features cannot survive an integer downscale, so
there is nothing to undo.

### Confidence

**High.** Four independent numerical tests plus a visual check all agree, and the method
was validated against a positive control whose scale was already known. `1024` is not
divisible by 3, which alone rules out the precedent's 3×.

Consequently `reference-native.png` is a **byte copy** of `reference-source.png` — the
correct derivation when the measured scale is 1, since any resampling would destroy
information rather than recover it.

For the record, node `1:3` is not a clean integer upscale either: best-phase 2× round
trip leaves mean error 4.32 with only 69.7 % of pixels exact, and only 43.8 % of runs are
divisible by 2. Its native size is its upload size, 1596×1556.

## 4. The eleven windows

`window-rects.json`, native pixels, `[x, y, w, h]`, origin top-left of the 1536×1024
frame. Found by masking the magenta desktop backdrop and labelling connected components —
exactly 11 components survive, each with rectangular fill ≥ 0.993. Verified by eye against
`window-rects-contact-sheet.png`.

| # | title | key | rect |
| --- | --- | --- | --- |
| 1 | 基本情報 | `basic-info` | 0, 0, 484, 205 |
| 2 | スキルツリー | `skill-tree` | 492, 0, 611, 595 |
| 3 | 装備カード | `equipment-card` | 1108, 0, 424, 290 |
| 4 | ステータス | `status` | 0, 211, 484, 208 |
| 5 | オプション | `options` | 1108, 297, 424, 202 |
| 6 | 装備アイテム | `equipment-items` | 0, 423, 484, 271 |
| 7 | パーティー | `party` | 1107, 505, 215, 269 |
| 8 | システムメニュー | `system-menu` | 1328, 505, 204, 273 |
| 9 | 倉庫 | `storage` | 492, 609, 539, 399 |
| 10 | 所持アイテム | `inventory` | 0, 701, 484, 303 |
| 11 | チャット・ルーム[#map] | `chat-room` | 1037, 782, 495, 226 |

The window's own title text confirms each mapping; #7 reads パーティー(狩りPT) and #11
reads チャット・ルーム[#map] in the reference.

## 5. First-pass control inventory

`control-inventory.json` — 239 controls, typed per map #103, each with a native rect, the
state visible in the reference, and its label.

| type | count | | type | count |
| --- | --- | --- | --- | --- |
| grid cell | 101 | | close | 9 |
| button | 31 | | checkbox | 7 |
| stepper | 31 | | text field | 7 |
| tab | 14 | | minimize | 6 |
| title drag | 11 | | meter | 4 |
| list row | 10 | | scrollbar | 3 |
| radio | 2 | | slider | 2 |
| dropdown | 1 | | | |

Per window: basic-info 14, skill-tree 59, equipment-card 4, status 15, options 12,
equipment-items 16, party 14, system-menu 9, storage 48, inventory 38, chat-room 10.

`meter` is not in the map #103 type list; HP/SP/Base-Lv/Job-Lv bars are read-only progress
indicators rather than any of the listed interactive types, so they are typed separately
rather than forced into `slider`. **Map #103 should decide whether `meter` joins the
vocabulary.**

States worth carrying into the replica work, all visible in the reference:

- **basic-info** — `status` is the selected button of the eight; the other seven are normal.
- **status** — five of six stat rows carry an enabled `▶` stepper; the **Int row has none**
  (it reads `92+10 → 11`), so the stepper is state-dependent, not decoration.
- **options** — `skill` and `item` checked; `attack` and `option` unchecked; both `on`
  checkboxes unchecked; BGM slider thumb at ~80 %, Effect at ~48 %; Skin dropdown closed
  showing "Classic Blue".
- **party** — `パーティー` radio selected, `友達` unselected; all five HP bars full.
- **skill-tree** — 27 skill cells, 26 steppers: `リザレク..` has an icon but **no stepper**
  (a prerequisite arrow runs from it down to `キリエエ..`). Nine skills sit at 0/n
  (unlearned), the rest are maxed. `スキル説明表示` unchecked. Skill points: 0.
- **equipment-items** — `一般装備` tab selected, `衣装装備` normal; all ten equip slots filled.
- **inventory / storage** — first tab selected in both (`item`, `消耗品`); 28 occupied
  inventory cells, 23 occupied storage cells of 35 (269/300 and 73/100 counters).
- **chat-room** — input field empty with the caret at the left; scrollbar thumb in the
  upper third.

### Accuracy

Explicit control rects were measured by eye from 2× nearest-neighbour crops overlaid with
a 20-pixel native grid: **±3 px**. Repeated grids are generated from measured pitch and
origin: **±4 px**. Skill-tree icon cells are measured programmatically per cell rather
than modelled. Every rect was drawn back over the reference and checked by eye —
`control-inventory-overlay.png`. Two defects were found that way and fixed: the party
icon-button row had drifted (pitch corrected to 35 px from a 5× measurement) and the
skill icons were 34 px boxes on 40 px icons.

## 6. Files

| path | what |
| --- | --- |
| `artifacts/references/ro-desktop-b/reference-source.png` | 1536×1024, best obtainable copy of node `1:5` |
| `artifacts/references/ro-desktop-b/reference-native.png` | byte copy of the source; measured scale is 1 |
| `artifacts/references/ro-desktop-b/skilltree-close-up.png` | 1596×1556, node `1:3` |
| `artifacts/references/ro-desktop-b/sources.json` | hash lock: original + stored hashes, node ids, sizes, retrieval method and limitation |
| `artifacts/references/ro-desktop-b/window-rects.json` | the 11 windows with titles |
| `artifacts/references/ro-desktop-b/control-inventory.json` | 239 controls |
| `artifacts/references/ro-desktop-b/window-rects-contact-sheet.png` | rects drawn on the reference |
| `artifacts/references/ro-desktop-b/control-inventory-overlay.png` | controls drawn on the reference |
| `artifacts/references/ro-desktop-b/native-crispness-4x.png` | 4× nearest-neighbour crispness evidence |

## 7. What this changes for the map

1. The replica target is **1536×1024**, not 3000×2000 and not a downscale of it. Anything
   built against a 3000×2000 canvas is building against a Figma display box.
2. Unlike the previous screen, there is **no upscale to undo** before pixel comparison, so
   the QA loop can diff against `reference-native.png` directly.
3. The stored reference is 91.4 % byte-identical to the original with a max channel error
   of 6. That is fine for layout, rect and state work. **If a pixel-exact diff ever
   becomes the acceptance gate, obtain a `files:read` Figma credential first** and
   re-pull; `sources.json` already carries the original's hashes to verify against.
