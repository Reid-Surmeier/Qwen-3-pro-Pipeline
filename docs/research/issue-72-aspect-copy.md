# Issue #72: paired aspect-ratio and Exact Copy replication

## Result

Changing only the requested output aspect ratio from `5:4` to `4:3` did not produce a clean T01 separation in this four-seed paired experiment. Every bounded title-bar and species-list observation in both arms was rated T01 present at mild severity. Both arms preserved readable wording, but neither preserved the Reference Screen's exact glyph geometry, rasterization, or kerning.

This null result does not support a visual-failure-taxonomy change. It does support keeping readable copy and Exact Copy typography as distinct claims.

## Design

The experiment pairs four immutable `5:4` outputs from Issue #53 with four newly generated `4:3` outputs. Seeds `11`, `733`, `4242`, and `20260826` are the first four completed seeds in Issue #53's preregistered order; they were not chosen based on output quality. Within each pair, the Reference Screen, Edit Brief, model, resolution, seed, and output count are frozen. Only `aspect_ratio` changes.

- Reference Screen: `artifacts/references/plantstudio-main-window.png`
- Reference SHA-256: `c9ddeaa3cd27d0d5b502710ad12bc8f810529339c87b97a289b6d6932df8f45d`
- Provider/model: OpenRouter / `qwen/qwen-image-3-pro`
- Resolution/output count: `1K`, one output per request
- Compiled prompt SHA-256: `4f65f2fc8742c0c04563735beb9077ae08f94f3100094bf6efa7d1f5cf5ec146`
- `4:3` brief SHA-256: `a6773a069e0ce88a4d6ee48c790c376b1724c5dd49f3d84a709d18dfbd5d4264`
- Frozen plan SHA-256: `e46ae2accdf9a9036bab152f80392b7395578fc00a9d975d3aaf0c8b2a1fcf2d`
- Crop manifest SHA-256: `afcc82145b0dbd2279c9552082621bb5cb4d0f00fa7408bc7496aecc8762781c`

The harness permits only the four preregistered new requests. Preparation creates the plan, brief, and prompt once and rejects a non-identical overwrite. Before taking the global lock, submission verifies those three artifact hashes and the seed's full request SHA-256/client request ID against the frozen plan. It then writes an exclusive attempt sentinel before submission, serializes paid submissions with a global lock, and treats any transport, provider, output-count, or persistence failure as possibly billed and globally blocking. All four requests completed; no request was retried and no ambiguous state occurred.

## Output and provenance record

| Seed | Arm | Native size | Output SHA-256 | Prompt/request identity | Cost | Bounded T01 result |
|---:|:---:|:---:|---|---|---:|---|
| 11 | 5:4 | 1024x820 | `5111d717fc41e8f70daf2c27a7f19a1a9298af7b53d4598b3a27e29864d7b9bc` | `f814d934-1c40-4e90-9d9d-6525ba1417cb` | $0.043 prior | mild in title and species list |
| 11 | 4:3 | 1024x768 | `738b3e663f287a80f9f7672b6a4ffac54d7825ffef8c322a632dbba984817f55` | `issue-72-seed-11-4x3-4003ce72deb7cfa6` | $0.043 new | mild in title and species list |
| 733 | 5:4 | 1024x820 | `68f6b2f9f5b345abaef4bbe8ea7f355d98598d83b50c992fde60576e31b345c7` | `5713915f-2f84-4d96-9b8e-7e548b917dcb` | $0.043 prior | mild in title and species list |
| 733 | 4:3 | 1024x768 | `86bf5bc8d467f1ae0caa6deeb0822cb60a5f35a05dafeca786227593199001e7` | `issue-72-seed-733-4x3-fc610dffbfed1f10` | $0.043 new | mild in title and species list |
| 4242 | 5:4 | 1024x820 | `26c7f97723f3c5b7505d00458fd08bb7153d7fd22ecabe89c295ce70c17b3fe4` | `84b29d7c-8892-4f55-a45d-b749c72181ef` | $0.043 prior | mild in title and species list |
| 4242 | 4:3 | 1024x768 | `32e654e7971a36773a9a2d3a95fca014fbcc9faf45951953b4f89198c8e8ddb8` | `issue-72-seed-4242-4x3-09a63b90ecda2e91` | $0.043 new | mild in title and species list |
| 20260826 | 5:4 | 1024x820 | `c53a53ba5be1415b18ece2008d725a9e3e2fdc54bd8dc773b413ae12d531daf4` | `f447b1be-a8ba-47ea-b49d-fae490ac3d9c` | $0.043 prior | mild in title and species list |
| 20260826 | 4:3 | 1024x768 | `041b1503b73058338cc9c70f64a817362624e999807b10e19617b9e8a07a1d45` | `issue-72-seed-20260826-4x3-78e9ad91447725bb` | $0.043 new | mild in title and species list |

The four inherited outputs cost $0.172 in Issue #53. This issue requested four new outputs for an estimated $0.172 and incurred exactly $0.172. The combined eight-output evidence set therefore represents $0.344 in image cost, of which $0.172 is new Issue #72 spend.

## Bounded advisory review

An independent reviewer from a different model family verified all 27 identities declared by the crop manifest, then compared only matching normalized title-bar and species-list crop pairs. Whole screenshots, prior labels, and global visual impressions were excluded. Visible re-kerning or glyph regeneration counted as T01 even when spelling remained readable.

| Arm | Title-bar T01 | Species-list T01 |
|:---:|:---:|:---:|
| 5:4 | 4/4 present, mild | 4/4 present, mild |
| 4:3 | 4/4 present, mild | 4/4 present, mild |

The machine-readable review is in `artifacts/benchmarks/issue-72-aspect-text/bounded-advisory-review.json`. It is comparison evidence, not a human visual approval.

## Final-board delivery

The eight native files were delivered as eight separate image nodes in the canonical Agent FigJam board. Session `issue-72-aspect-text` is the untitled white section `46:10`; it contains no added text nodes or contact sheet. Its two-column, four-row order is one seed pair per row:

| Order | Seed/arm | Node | Read-back size |
|---:|---|---|:---:|
| 1 | 11, 5:4 | `46:2` | 1024x820 |
| 2 | 11, 4:3 | `46:3` | 1024x768 |
| 3 | 733, 5:4 | `46:4` | 1024x820 |
| 4 | 733, 4:3 | `46:5` | 1024x768 |
| 5 | 4242, 5:4 | `46:6` | 1024x820 |
| 6 | 4242, 4:3 | `46:7` | 1024x768 |
| 7 | 20260826, 5:4 | `46:8` | 1024x820 |
| 8 | 20260826, 4:3 | `46:9` | 1024x768 |

The focused readback contains exactly those eight frames in row-major order, with native dimensions preserved. Placement provenance is recorded in `figjam-placement.json`; the focused XML and screenshot hashes are `49c316d8f550f983e41dfaa0d049593110ac4d999f36ba5f2a9fb23fd3d55dba` and `2ad14f75d58cb472b7407bcb76220b01fac7d3d5d5c15650adde13bed6da8d65` respectively.

## Artifact classification and limits

- Native generated images and bounded crops are comparison evidence.
- Plans, attempt records, request/run metadata, hashes, and manifests are reproducibility metadata.
- FigJam placement, focused readback XML, and focused screenshot are delivery evidence.
- The inherited `5:4` images remain owned by Issue #53; this branch references them without changing them.
- This is four matched pairs for one Reference Screen and one Edit Brief. It does not establish a general aspect-ratio rule.
- Review crops are nearest-neighbour normalized to the 474x403 source geometry before cropping. That enables bounded comparison but is not a pixel-equivalence test.
- The result does not authorize either arm as an approved output. Subjective visual acceptance remains a human PR-gate decision.
