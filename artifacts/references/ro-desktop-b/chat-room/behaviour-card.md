# Image 79 Chat Room Behaviour Card

Source identity: `reference-native.png`, SHA-256
`f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
Source Window rectangle: `[1037, 782, 495, 226]` native pixels.

## Source-observed

- The source shows five read-only rows: four player messages and one system
  report, one vertical scrollbar, one empty input field, and one unidentified
  icon. The modern tab strip is absent.
- A wheel notch moves three complete rows in one frame and clamps at either end.
- Enter clears accepted input in the accepted frame. The exact submitted text
  appears in the log three frames (100 ms in the 30 fps source) later.

## Manual-attested

- Ordinary Enter sends to everyone on the same screen.
- Ctrl+Enter, Alt+Enter, and Shift+Enter override one message to party, guild,
  and allied-guild scope respectively.
- F10 changes the number of visible conversation rows. This replica declares
  the reversible cycle `5 -> 7 -> 3 -> 5`; only the source state of five and
  the fact of row-count change are authoritative.
- Alt+F10 toggles the complete conversation Window.

## Intent-specified

- Arrow clicks step one row and thumb drag is continuous and clamped, matching
  the shared ScrollView contract because the Source Game did not expose those
  gestures.
- Title drag follows the shared continuous, viewport-clamped Window contract.
- The unidentified icon remains baked into the source plate and has no hit
  target. Assigning it settings, scope, whisper, or tab behavior would invent
  evidence.
