# Visual gate review — final-v011-assembly.png

Mechanical verdict: NO-SHIP

| # | assertion | verdict | detail |
|---|---|---|---|
| A2 | registration: region land-centroid shift <=2px | FAIL | `{"north-america": 9.41, "south-america": 4.22, "europe": 3.2, "great-britain": 7.99, "africa": 8.94, "middle-east": 2.47, "asia": 1.9, "se-asia": 10.76, "australia": 9.86}` |
| A3 | coverage: >=98% of source land fills painted (source frame) | FAIL | `{"coverage": 0.9038}` |
| A4 | sea stays sea: <=0.5% of deep ocean land-painted | FAIL | `{"violation_frac": 0.03523, "violation_px": 6267}` |
| A6 | component count per region within +-1 (no fusion/fragmentation) | FAIL | `{"north-america": {"source": 43, "candidate": 17}, "south-america": {"source": 18, "candidate": 4}, "europe": {"source": 33, "candidate": 21}, "great-britain": {"source": 10, "candidate": 6}, "africa": {"source": 44, "ca` |
| A7 | palette census: candidate flat colours <= source's + 2 (final rule awaits pinned palette, #145) | PASS | `{"candidate": 11, "source": 27}` |
| A9 | anchoring: >=97% of coastal ink marks still touch land | FAIL | `{"anchored_frac": 0.7834, "orphaned_px": 1905}` |
| A10 | label integrity: every word keeps >=90% of its glyph pixels | FAIL | `{"damaged_words": 49, "worst": [{"x": 880, "y": 86, "survival": 0.0, "px": 30}, {"x": 804, "y": 99, "survival": 0.0, "px": 30}, {"x": 931, "y": 99, "survival": 0.0, "px": 29}, {"x": 730, "y": 116, "survival": 0.0, "px": ` |
| A13 | no interior strokes absent from the source (<=30px tolerance) | FAIL | `{"ghost_stroke_px": 799}` |
| A15 | deliverable identity: candidate hash recorded; publish step must match it | PASS | `{"sha256": "1c0154a18f9a4582398763f60fadcfb3d1ce9fc73092f3e6832e2e13d98acba6"}` |
| A16 | frame declaration: all assertions above sample the SOURCE-raster frame | PASS | `{"frame": "source raster 1001x485"}` |

Reviewer: read every `pair-*.png` (source left, candidate right, magenta 10px grid),
then record ship/no-ship. A deploy without that recorded verdict is invalid.
