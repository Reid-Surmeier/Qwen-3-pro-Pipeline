# Replica convergence backlog (#86)

Ordered by impact. One item per Ralph iteration. Mark `[x]` with the commit
SHA when visually verified and pushed.

- [x] Tab active-state swaps (round 15): the source has no distinct
  active-tab chrome, so the active state borrows the source's own language —
  the blue-tinted status button background, multiply-tinted onto the tab
  cell, clamped to the measured tab band. Untouched frame stays exact
  (patches appear only after the user touches the tab group). Exclusive and
  reversible; contract-checked (tab-visible-active / tab-visible-moves).
- [x] Close → reopen reversibility (round 16): Alt-key toggles in main.gd
  WINDOW_KEYS. Canon RO 1.x keys where they exist — Alt+V basic-info,
  Alt+Z party, Alt+G guild, Alt+C chat-room; assigned in the same idiom —
  Alt+M minimap, Alt+R create-room, Alt+T trade, Alt+P pm. Reopen raises
  the window. Contract close-reopens-by-key; browser playtest closes via
  the title X and reopens with real Alt+V keystrokes.
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
