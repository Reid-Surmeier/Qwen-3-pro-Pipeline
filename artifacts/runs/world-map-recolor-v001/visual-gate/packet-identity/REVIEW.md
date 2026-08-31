# Visual gate review — wtz-map-12map-1001x485.gif

Mechanical verdict: PASS

| # | assertion | verdict | detail |
|---|---|---|---|
| A2 | registration: region land-centroid shift <=2px | PASS | `{"north-america": 0.0, "south-america": 0.0, "europe": 0.0, "great-britain": 0.0, "africa": 0.0, "middle-east": 0.0, "asia": 0.0, "se-asia": 0.0, "australia": 0.0}` |
| A3 | coverage: >=98% of source land fills painted (source frame) | PASS | `{"coverage": 1.0}` |
| A4 | sea stays sea: <=0.5% of deep ocean land-painted | PASS | `{"violation_frac": 0.0, "violation_px": 0}` |
| A6 | component count per region within +-1 (no fusion/fragmentation) | PASS | `{}` |
| A7 | palette census: candidate flat colours <= source's + 2 (final rule awaits pinned palette, #145) | PASS | `{"candidate": 27, "source": 27}` |
| A9 | anchoring: >=97% of coastal ink marks still touch land | PASS | `{"anchored_frac": 1.0, "orphaned_px": 0}` |
| A10 | label integrity: every word keeps >=90% of its glyph pixels | PASS | `{"damaged_words": 0, "worst": []}` |
| A13 | no interior strokes absent from the source (<=30px tolerance) | PASS | `{"ghost_stroke_px": 0}` |
| A15 | deliverable identity: candidate hash recorded; publish step must match it | PASS | `{"sha256": "90338b9cdbdd59ad60a7876f5e928d957837f1a816d6bd1e08ebed8f545c61e5"}` |
| A16 | frame declaration: all assertions above sample the SOURCE-raster frame | PASS | `{"frame": "source raster 1001x485"}` |

Reviewer: read every `pair-*.png` (source left, candidate right, magenta 10px grid),
then record ship/no-ship. A deploy without that recorded verdict is invalid.
