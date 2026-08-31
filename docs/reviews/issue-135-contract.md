# Issue #135 blind-review contract — Chat Room

Candidate scope: the Image 79 Chat Room Window and the existing Basic Info
Chat destination. All ten previously integrated Windows are regression scope.

## Immutable authority

- Reference: `artifacts/references/ro-desktop-b/reference-native.png`
- SHA-256: `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`
- Native Window rectangle: `[1037, 782, 495, 226]`
- The source crop must render with zero changed pixels at reset.

## Acceptance

1. The reset Window shows the exact five source rows, title, close control,
   scrollbar, empty input, and unidentified bottom-right icon. It adds no
   modern tab strip and no hit target for the unidentified icon.
2. Real text input is visible and exact. Accepted Enter clears in its accepted
   frame, then appends exactly one identical message after three engine frames.
3. Enter sends to screen; Ctrl+Enter, Alt+Enter, and Shift+Enter apply party,
   guild, and allied-guild scope to one message without leaking to the next.
4. One wheel notch moves three rows and clamps. Arrow activation moves one row;
   thumb drag is continuous and clamps. F10 cycles `5 -> 7 -> 3 -> 5` visible
   rows.
5. Close and contextual Escape hide only Chat Room. Alt+F10 toggles the whole
   Window. Basic Info's Chat destination restores and raises Chat Room while
   preserving its semantic state.
6. Title drag is continuous and viewport-clamped. No gesture mutates an
   unrelated Window.
7. The browser publishes a complete initial QA state, then changed-Window
   patches. Interaction patches remain smaller than the complete eleven-Window
   state, input latency stays under the existing 34 ms contract, and the run
   emits no application console errors.
8. Provider/model requests for this deterministic Assembly are zero.

## Required evidence

- Exact source/candidate crop comparison and reset/full-desktop frames.
- Real-browser Play Log covering every declared Chat Room Action and the Basic
  Info route, with payload metrics and console capture.
- 304/304 Image 79 engine contracts, the repository baseline, and all ten prior
  Window Play Logs on the exact candidate SHA.
- Fresh cold import and launch/reset instructions suitable for an independent
  reviewer.
