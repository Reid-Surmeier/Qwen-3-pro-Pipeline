# Qwen UI asset-to-product workflow

## Layers

1. **FigJam research board** — source references, notes, arrows, and iteration contact sheets. Preserve original references.
2. **Generated assets** — versioned raster or SVG outputs with prompts, model settings, seeds, and source-node provenance stored in the project.
3. **Figma Design file** — editable components, variables, typography, icons, and composed screens. Use native nodes and component instances where possible.
4. **Working application** — accessible HTML/CSS/TypeScript components with real buttons, sliders, state, and animation.

Do not mistake a raster screenshot on FigJam for an editable UI. Text inside node `1:41` is part of the PlantStudio image; changing it requires an image edit/replacement or a separately reconstructed native Figma screen.

## Iteration contract

For every generated variant, retain:

- source Figma file key and node ID;
- source image checksum;
- prompt and negative constraints;
- model/provider/workflow version;
- seed and generation parameters when available;
- output checksum and dimensions;
- placement node ID after upload;
- focused before/after screenshots.

Keep the source reference unchanged during exploration. Place variants in a named FigJam section beside the source. Promote an accepted variant into a Figma Design component or screen only after visual review.

## Drift control

- Edit one semantic region at a time: hero object, labels, icons, or graph—not the whole screen.
- Lock invariant geometry, palette, typography scale, chrome placement, and canvas dimensions in the prompt/evaluation record.
- Generate text-bearing controls as native Figma/web text whenever possible. Use the image model for the visual object, texture, illustration, and difficult raster effects.
- Validate at full size and at the intended 10 px detail scale; a reduced whole-board screenshot is not evidence of legibility.

## First golf test

1. Preserve PlantStudio node `1:41` as the immutable reference.
2. Generate only the flower-to-golf-club preview edit first.
3. Upload the result as a new FigJam asset and label it `golf-ui/club-preview/v001`.
4. Compare source and variant for layout, palette, crop, line weight, and small-detail drift.
5. Reconstruct golf text and controls as editable Figma nodes rather than repeatedly regenerating raster text.
6. Implement the accepted screen in code, then exercise buttons, slider state, and golf-club animation in the browser.
