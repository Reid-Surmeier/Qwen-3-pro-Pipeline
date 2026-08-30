# オプション window — throwaway prototype (#111)

A Godot 4.7.2 rebuild of one window from Reference Screen image 79
(`artifacts/references/ro-desktop-b/reference-native.png`, the sole visual
authority) on the approach charted by map #103. Not a release; not a library.

## Rebuild

```bash
# 1. cut the parts and derive the missing states (deterministic, no model calls)
python3.12 replica/tools/extract_options.py

# 2. import, then export the Web build
GODOT=~/.cache/qwen-ui-pipeline/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64
"$GODOT" --headless --path replica --import
"$GODOT" --headless --path replica --export-release Web "$PWD/replica/web/index.html"

# 3. serve it
sudo -n tailscale serve --bg --set-path /godot-v2-options "$PWD/replica/web"
```

`replica/web/` is not committed.

## Layout

| Path | What |
| --- | --- |
| `tools/extract_options.py` | cuts every part out of the reference and derives the missing states; writes `assets/options/manifest.json` |
| `tools/drive_web.mjs` | builder-side Playwright drive; writes `evidence/builder/` |
| `tools/compare_idle.py` | idle frame vs the reference at 4x, plus the numeric residual |
| `assets/options/manifest.json` | every asset with its source rect and its derivation, every control with its ink rect, place rect, states and behaviour provenance |
| `scripts/options_window.gd` | the window: manifest-driven nodes, per-control hit rects, slider/dropdown/drag logic |
| `scripts/desktop.gd` | the magenta desktop and the `window.godotQaState` bridge |

## QA bridge

The running build publishes the full state to `window.godotQaState` on every
change and prints the same JSON to stdout: all values, window position and
size, minimized, visible, skin, `skin_open`, hovered and pressed control ids,
both thumb x positions, and an `interaction_log` array.

## What is source and what is not

`assets/options/manifest.json` carries the answer per asset and per control.
In short: every idle pixel is cut from the reference; hover is
invented-in-style under the owner's hover-everywhere rule and marked as such;
the arrow step, the wheel step, the window drag, the dropdown dismiss and the
minimized form are intent-specified; there are no tweens anywhere, because the
Behaviour Cards measured every transition in the Source Game at one frame.

The `reopen` text button in the desktop's top-left is a prototype affordance,
not a Source Game control. It appears only while the window is hidden.
