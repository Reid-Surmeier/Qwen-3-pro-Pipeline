# Acceptance contract — Issue #86: Godot Interactive Replica of ro-hud-fullscreen

Derived from the approved body of GitHub Issue #86 (owner, 2026-08-27). The
authoritative reference is `artifacts/references/ro-hud-fullscreen/reference-native.png`
(1973x1319, sha256 `1b7af8b2c3b1be3e5dd7514b689c75a8576651bcb99d6e62536800df8068c8de`).
A blind reviewer dispositions every clause below as pass, fail, or unverified.

## Visual clauses (vs the reference at idle)

- **V1 — Window inventory.** Every item from the Reference Screen is present:
  基本情報 status window (HP/SP/levels/weight/zeny + 8 buttons) · ギルド情報 guild
  window (roster table, 5 buttons, scroll) · パーティー party window (5 ON members,
  HP bars, tabs, checkboxes) · チャットルーム作成 create-room form (fields, radio,
  OK/cancel) · チャットルーム chat room (13/20 roster, log, input, send) ·
  アイテム交換 trade window (two item columns, zeny, OK/trade/cancel) ·
  個人メッセージ PM window (log, input, send) · ミニマップ (+/- zoom) · bottom
  status bar + icon tray · pink desktop + game scene backdrop.
- **V2 — Fidelity.** Each window's geometry, chrome, palette, typography, and
  density read as the reference's, judged on magnified crops.
- **V3 — Layering.** Window stacking and the backdrop composition match the
  reference's arrangement.

## Behavioral clauses (aliveness bar, owner 2026-08-27)

- **B1 — Draggable.** All windows are draggable/movable.
- **B2 — Sizes fluctuate.** Windows resize, and minimize/restore where the
  window chrome offers it.
- **B3 — Live text.** Text is live and changeable: editable fields accept
  typed input and submit.
- **B4 — Checkboxes.** Checkboxes check (visible state change on click).
- **B5 — All buttons.** ALL buttons respond visibly; no dead control.
- **B6 — Animations.** Animations mimic the source screenshot or are exactly
  referenced from it.

## Notes for the reviewer

- Live text means rendered from a font, not baked pixels: glyphs must change
  when the text changes.
- Expected terminal states for trade completion and room creation are not
  defined in the Issue; report gaps as unverified, not as failures.
- Findings outside these clauses are follow-up observations, never blocking.
