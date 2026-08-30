# Issue 125 blind artifact contract

Review candidate `7dcc651993319b5cfbb1aee1049bc7b9c82d0caf` without relying on the builder narrative.

## Visual authority

- Image 79 is `artifacts/references/ro-desktop-b/reference-native.png`, SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`.
- The Options Window occupies `(1108, 297, 424, 202)` on the 1536×1024 canvas.
- The open Skin list is an approved best-guess Asset Pass in the same visual language; it must not look like a native/default web select.

## Required observations

1. Idle, hover, pressed, and settled/active artwork is source-coherent at 4× inspection.
2. Both Range controls support arrow, wheel, track/thumb Drag, continuous motion, reversal, and endpoint clamping.
3. All six Toggles reverse on a second activation.
4. Skin opens a themed four-row list, selects a row, and dismisses with Escape.
5. Minimize swaps to a purpose-built 424×28 Window, and restore preserves position and control state.
6. Title Drag follows the pointer without tweening; Close hides the Window.
7. No Godot/browser console error occurs, and the factual QA state matches the visible result.

The review must name candidate SHA, expected behavior, actual behavior, evidence path, and violated clause for every finding. It does not approve the final eleven-Window desktop.
