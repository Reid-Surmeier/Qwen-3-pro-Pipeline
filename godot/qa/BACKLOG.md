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
- [x] Log scrolling (round 18): chat-room log-scroll steps the live log two
  whole rows per click (upper/lower half of the scrollbar = up/down), snapped
  to the source's 33px row grid; sending returns the view to the tail.
  Line separation now matches the source pitch. Contract-checked
  (log-scroll-up-moves, log-scroll-send-refollows).
  Guild roster / party list / chat roster scroll: all source rows are already
  visible — the guild's 11 unlisted members (24/28 shown as 13 rows) have no
  source-attested names, so full roster scrolling is blocked on a content
  decision (generate continuation rows with provenance, or cap the scroll).
  Press feedback exists; needs-human-decision recorded here.
- [x] Outgoing chat name color (round 17): sent lines now use the source
  green (#3a9948); the live log reads as one continuous conversation.
  Verified visually in the PM window at 2x.
- [ ] Minimized-bar corner nit: the donor closing border carries a small
  cyan shadow curl at the right corner (visible at 3x). Rebuild the donor
  crop to end cleanly.
- [ ] Trade window buttons: OK/cancel activate but produce no visible
  consequence; decide and implement the minimal visible, reversible
  response (e.g. press-flash only is acceptable — then mark done with
  rationale).
- [ ] Bottom-bar tray icons: hits exist (`tray`) but no visible response;
  same treatment as above.
