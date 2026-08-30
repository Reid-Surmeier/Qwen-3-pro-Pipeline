# オプション window — prototype B: native controls under a source-pixel Theme (#137)

The same window as `replica/` (Version A), rebuilt as an answer to one question:
**should the Control Library be manifest-driven cut textures (A) or the engine's own
controls skinned with the same source pixels (B)?**

What is different here, mechanically:
- `HSlider`, `CheckBox`, `OptionButton`, `TextureButton`, `Panel` do the interaction;
  their grabber icons, check icons, arrows and styleboxes are crops of image 79
  (`tools/build_theme.py` → `assets/theme/`, every asset with its derivation in
  `theme-manifest.json`). Hover comes from the controls' own hover slots.
- **Live text everywhere** — title, labels, values render from DotGothic16, nothing
  textual is baked. This is the aliveness bar's "text is live and changeable".
- The minimized form is **authored** (title strip completed with the window's own
  bottom border) — the #111 owner correction, done deterministically.
- The open Skin list is themed from the field's own pixels with the title-bar
  gradient as the hover bar — a deterministic attempt at the second #111 correction.
- No tweens; Esc closes (manual-attested); the desktop `reopen` text is a test
  affordance.

Rebuild: `python3.12 replica-b/tools/build_theme.py`, then Godot `--import` and
`--export-release Web "$PWD/replica-b/web/index.html"`, serve `replica-b/web`.
