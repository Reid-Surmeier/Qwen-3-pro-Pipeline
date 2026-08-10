# Golf-club object test: v001 through v003

## Outcome

The pipeline successfully replaced the selected flower with a recognizable
seven-iron and produced an exact-preservation assembly. Variant v002-2 is the
selected generative donor. v003 keeps every pixel outside the selected 37×165
region identical to the lossless Reference Screen.

| Pass | Change under test | Output | Best normalized RMSE | Outside-region check |
| --- | --- | --- | ---: | ---: |
| v001 | End-to-end ComfyUI and provider path with 4:3 output | 1152×864, four variants | 0.313007 | Not accepted; screen stretched |
| v002 | Explicit source-ratio output, same seed and Edit Brief | 948×806, four variants | 0.159064 for image 2 | 0.146015 RMSE outside the region after downscaling |
| v003 | Deterministic region Assembly using v002-2 | 474×403, one assembly | 0.0665967 global | 0 AE pixels and 0 RMSE outside the region |

## Observations

- Qwen preserved the late-1990s Windows visual language and generated a
  legible club in every candidate.
- The 4:3 allowlist choice was a larger source of drift than prompt wording.
- Alibaba's direct API supports explicit `width*height`, which made the exact
  474:403 source ratio possible at 948×806.
- A longer prompt reduced semantic drift but did not prevent the model from
  redrawing pixels outside the named region.
- Loading the GIF through ComfyUI changed most color values by about one byte
  level. Lossless GIF-to-PNG conversion measured zero source pixel error and
  removed that loader-induced drift from Assembly.

## Figma placement

- `4:146` — `golf-ui/club-preview/v002-2`
- `4:147` — `golf-ui/club-preview/v002 contact sheet`
- `6:146` — `golf-ui/club-assembly/v003 exact-preservation`

The source image was not replaced. These are new, independently named FigJam
nodes.
