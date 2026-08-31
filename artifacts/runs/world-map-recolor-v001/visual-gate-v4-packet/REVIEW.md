# Visual gate review — assembled-v4.png

Mechanical verdict: PASS

| # | assertion | verdict | detail |
|---|---|---|---|
| A2 | registration: region land-centroid shift <=2px | PASS | `{"north-america": 0.68, "south-america": 0.01, "europe": 0.32, "africa": 0.04, "middle-east": 0.01, "asia": 0.04, "se-asia": 0.04, "australia": 0.3}` |
| A3 | coverage: >=98% of source land fills painted (source frame) | PASS | `{"coverage": 0.9978}` |
| A4 | sea stays sea: <=0.5% of deep ocean land-painted | PASS | `{"violation_frac": 3e-05, "violation_px": 5}` |
| A6 | component count per region within +-2 (under-annotation topology is ambiguous; the blind reviewer judges fusion visually) | PASS | `{}` |
| A7 | palette census: candidate flat colours <= source's + 2 (final rule awaits pinned palette, #145) | PASS | `{"candidate": 11, "source": 9}` |
| A9 | anchoring: >=97% of coastal ink marks still touch land | PASS | `{"anchored_frac": 0.9996, "orphaned_px": 1}` |
| A10 | label integrity: every word keeps >=90% of its glyph pixels | PASS | `{"damaged_words": 0, "worst": []}` |
| A13 | no interior strokes absent from the source (<=30px tolerance) | PASS | `{"ghost_stroke_px": 0}` |
| A12 | leftover annotation ink: candidate keeps <=15% of plate-zone dark ink | PASS | `{"source_ink": 13647, "candidate_ink": 1947}` |
| A17 | border retention: >=97% of non-annotation black ink survives | PASS | `{"retention": 0.9993, "lost_px": 1}` |
| A17b | dark-blend retention: >=90% of dark anti-alias pixels stay dark | PASS | `{"retention": 1.0}` |
| A15 | deliverable identity: candidate hash recorded; publish step must match it | PASS | `{"sha256": "384a6521f6b1c5c13688fa2d54fc37f91e1b6b2cf0f4a7c6572b74161b031af2"}` |
| A16 | frame declaration: all assertions above sample the SOURCE-raster frame | PASS | `{"frame": "source raster 1001x485"}` |

Reviewer: read every `pair-*.png` (source left, candidate right, magenta 10px grid),
then record ship/no-ship. A deploy without that recorded verdict is invalid.
