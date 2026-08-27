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
- [x] Minimized-bar corner nit (round 19): donor border switched to
  create-room's clean bottom border with the left corner mirrored for the
  right side — no cyan curl, no screen-edge contamination. Verified at 6x.
- [x] Trade/create-room cancel (round 19): cancel dismisses its window —
  era behavior — reversible via Alt+T / Alt+R (contracts cancel-closes-trade,
  cancel-reopen-by-key). OK keeps press-flash only: the issue defines no
  terminal state for trade completion or room creation (the acceptance
  contract instructs reviewers to report those as unverified, not failures).
- [x] Bottom-bar tray icons (round 19): press-flash is the visible response.
  The source defines no tray-icon destinations; opening invented windows
  would fabricate surfaces the reference does not attest. Rationale recorded.
- [ ] OPEN (needs-human-decision): guild-roster full scroll — the 11
  unlisted guild members have no source-attested names. Either authorize
  generated continuation rows (with provenance) or cap the scroll at the
  source rows.
