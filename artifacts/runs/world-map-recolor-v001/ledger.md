# World-map recolor — paid attempts (OpenRouter, qwen/qwen-image-3-pro)

| # | run | key | output spec | reference | result | billed |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | pass1-clean (9ad35d33) | old …126 | 2K 2:1 n=2 | 3432x1716 | read timeout @180 s | no (old-key usage_daily unchanged 0.6507) |
| 2 | pass1-1k (a8f27843) | new …7cc | 1K 2:1 n=1 | 3432x1716 | HTTP 400 Alibaba content moderation after 150 s (place names in prompt) | no |
| 3 | pass1-1k-b (scrubbed prompt) | new …7cc | 1K 2:1 n=1 | 3432x1716 | read timeout @180 s | one of #3/#4 billed |
| 4 | pass1-1k-c (1fe58c54) | new …7cc | 1K 2:1 n=1 | 1716x858 | read timeout @900 s | usage_daily 0.06498 → 0.10798 = exactly one 1K image ($0.043) across #3+#4; no output delivered |
| 5 | pass1-16x9 | new …7cc | 1K 16:9 n=1 | 1679x944 | pending | — |

Observations: the provider finishes (a billed image exists) but delivery hangs; 2:1 has no recorded success in this repo (1:1, 4:3, 5:4 do). Timeout override QWEN_OPENROUTER_TIMEOUT_SECONDS=900 verified honoured (worker logged "Prompt executed in 00:15:00").
| 5 | pass1-16x9 (node) | new …7cc | 1K 16:9 n=1 | 1679x944 | read timeout @900 s | yes ($0.043; key total 0.151 for 08-29) |
| 6 | diag-control (curl) | new …7cc | 1K 5:4 n=1 | 474x403 plantstudio | HTTP 200 in 103 s, 1024x820 | yes $0.043 |
| 7 | diag-subject (curl, same body as #5) | new …7cc | 1K 16:9 n=1 | 1679x944 | HTTP 200, TTFB 224 s, 1024x576 — but the edit was NOT applied (verbatim degraded copy) | yes $0.043 |
| 8 | diag-stream (curl, stream:true) | new …7cc | 1K 16:9 n=1 | 1679x944 | HTTP 400 after 200 s: Alibaba content moderation (output-side, nondeterministic) | no |
| 9 | pass1-blunt-2k (node, keepalive client) | new …7cc | 2K 16:9 n=1 | 1679x944 | pending | — |

Root cause of #1/#3/#4/#5: urllib opens the socket without TCP keepalive; the idle NAT/proxy mapping dies during the ~4-min generation and the finished response is lost. curl (keepalive on by default) delivers the identical request. Fixed in the served checkout + release line (`698d98d`).
| 9 | pass1-blunt-2k (node, keepalive) | new …7cc | 2K 16:9 n=1 | 1679x944 | HTTP 200 in 214 s, 2048x1152 — delivery FIXED; edit NOT applied (crisp verbatim copy) | yes $0.078 |
| 10 | pass1-minimal (node, terse prompt) | new …7cc | 1K 16:9 n=1 | 1679x944 | HTTP 400 Alibaba content moderation after 205 s | no |

Verdict on Qwen for this map: of 5 attempts that reached the provider after the keepalive fix or via curl, 2 returned unedited copies and 3 were moderation-blocked. Total map spend $0.293.

## v008 (2026-08-30)
- compose_v3 rev5→rev18 review loop: lakes-aware NE 50m layer, white-land cells, EDT patch splitting,
  Greenwich #64669C removal, AA/marker/dash cleanups, plate-interior reconstruction.
- Gates: fidelity outside_changed=0; spot checks 75/75 ok. No paid calls this round ($0).
- Deployed to FigJam node 16:67; commit 9a131d5.

## v009 (2026-08-30, second review loop)
- compose_v3 rev19→rev26: sea-truth (raw NE grid), wiped-plate land exclusion, per-colour cid sweep,
  NE-coast-only reconstruction outlines, zone-stub dissolve, strip AA wipe.
- Gates: fidelity outside_changed=0; spot checks 75/75. $0.
- Deployed to FigJam node 16:67.

## v010 (2026-08-31, third review loop — labels)
- compose_v3 rev27→rev31: label audit found Perth/INDIA/Paris damage; per-letter keep/drop now uses
  the two-live-fetch diff as ground truth (digits change, names don't); R5-ink letters always wiped;
  Greenwich caption fully removed via corridor sweep.
- Gates: fidelity outside_changed=0; spot checks 75/75. $0.
- Deployed to FigJam node 16:67.
