# Prototype: regional WorldTimeZone maps as gate fixtures — NO

**Question** (wayfinder map #140, last open item): should the four regional
WorldTimeZone reference maps (Middle East, Africa, South America, Australia)
become fixtures the visual-review gate compares against?

**Verdict: no.** Retire the question. Three independent disqualifiers, each
fatal on its own. A gate fixture must be immutable, comparable in the source
frame, and reproducibly re-fetchable. These are none of the three.

## 1. Not immutable — they are live clock renders

The two existing fetches of the *same* licensed source disagree:

| | |
|---|---|
| `wtz-map-12map-1001x485.gif` | sha256 `90338b9cdbdd59ad…` |
| `wtz-map-second.gif` | sha256 `c333fe1c5dccb0a3…` |
| differing pixels | **12,682 of 485,485 (2.612 %)** |
| bounding box of change | `24,11 → 980,480` (near-full canvas) |

The endpoint is `wtzmap.php?forma=12map` — a PHP script that renders the
*current local time* into every zone. The regional maps are the same
machinery (`wtz-<region>-map.php`), so they carry the same volatility.
A fixture whose bytes change every minute cannot anchor an assertion.

## 2. Not in the source frame

The one regional map that fetched successfully came back **500×380 PNG**.
The licensed source is **1001×485 GIF**.

Decision #143 froze the architecture as *recolour-only, source-frame-native*:
every assertion is defined in the source frame, and #146 established that cid
data is usable only where locally-registered residual is ≤2 px. A different
raster at a different scale and crop cannot be registered into that frame at
that tolerance. It would introduce a second, conflicting ground truth — the
precise failure mode #142 catalogued, where the gate audits its own frame.

## 3. Not reproducibly re-fetchable

After one successful fetch the endpoint returns a 21-byte hotlink guard, the
literal string `www.worldtimezone.com`, for every subsequent request —
including with a fresh `sessionid`. The Africa path 302-redirects to the site
root. Evidence: `fetch/australia-A.gif` (18,657 B PNG) versus
`australia-B.gif` and `australia-C.gif` (21 B each).

## What to do instead

Nothing new. `review_gate.py` already emits ten source-frame crop pairs —
`africa`, `asia`, `australia`, `europe`, `great-britain`, `middle-east`,
`north-america`, `se-asia`, `south-america`, `full`. Those already cover all
four regions named in the ticket, in the correct frame, cropped from the
hash-locked source. The regional maps would add volatility and a conflicting
frame while duplicating coverage that exists.

## Reproduce

    python3 probe.py ~/.qwen-worldmap-wt/artifacts/runs/world-map-recolor-v001/assembly

Throwaway probe; not production code. Owner may veto async.
