# Replica convergence backlog (#86)

Ordered by impact. One item per Ralph iteration. Mark `[x]` with the commit
SHA when visually verified and pushed.

- [x] Tab active-state swaps (round 15): the source has no distinct
  active-tab chrome, so the active state borrows the source's own language —
  the blue-tinted status button background, multiply-tinted onto the tab
  cell, clamped to the measured tab band. Untouched frame stays exact
  (patches appear only after the user touches the tab group). Exclusive and
  reversible; contract-checked (tab-visible-active / tab-visible-moves).
- [ ] Close → reopen reversibility: closing a window (title-bar X) currently
  hides it with no in-UI path back. Implement the era-faithful Alt-key map
  (RO: Alt+V basic-info, Alt+E items, Alt+Z party, Alt+G guild, Alt+M
  minimap, etc.) to toggle windows, document the map in BACKLOG, and make
  the in-engine interact matrix exercise close+reopen.
- [ ] Roster/log scrolling: guild roster, chat-room log, and party list have
  scroll hits (`roster-scroll`, `log-scroll`, `list-scroll`) that produce no
  visible scroll. Decide the deterministic behavior (stepped scroll of the
  plate viewport is fine) and make the thumb + content visibly move,
  reversibly.
- [ ] Outgoing chat name color: live-sent lines render the sender name in
  blue (#4a6edc); the source PM log shows SakumaRiri in green. Match source.
- [ ] Minimized-bar corner nit: the donor closing border carries a small
  cyan shadow curl at the right corner (visible at 3x). Rebuild the donor
  crop to end cleanly.
- [ ] Trade window buttons: OK/cancel activate but produce no visible
  consequence; decide and implement the minimal visible, reversible
  response (e.g. press-flash only is acceptable — then mark done with
  rationale).
- [ ] Bottom-bar tray icons: hits exist (`tray`) but no visible response;
  same treatment as above.
