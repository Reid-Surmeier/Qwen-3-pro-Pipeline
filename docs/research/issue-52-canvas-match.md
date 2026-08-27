# Issue 52: canvas-match ablation

Issue: [#52 — Quantify canvas-match as a drift lever](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/52)

## Result

Matching the Reference Screen's canvas was a strong lever for aspect and crop
behavior in this four-arm, one-seed run. It reduced the degree of outside-region
disturbance, but **did not prevent global redraw**: bounded independent review
found T20 in every arm.

- Exact `size: 948x806` preserved the source ratio exactly and produced no T21.
- The closest enumerated geometry, `5:4`, had 6.17% relative aspect error at
  both 1K and 2K. Both outputs clipped the bottom window edge (T22).
- Deliberately mismatched `16:9` had 51.15% relative aspect error and severely
  reframed the application with teal pillarbox padding (T22).
- Raising the same 5:4 arm from 1K to 2K improved the raw outside-region and
  edge-strip indicators, but did not repair T20, T21, or T22.

This supports guidance to use exact pixel size when the Images API and endpoint
accept it, otherwise the closest supported aspect, to reduce canvas and crop
drift. Geometry alone is not a strict-preservation mechanism; deterministic
Assembly and a Fidelity Check remain necessary when unchanged pixels are the
contract. Resolution is a detail control, not a substitute for canvas matching.
The result is exploratory: one seed and one localized edit cannot establish an
across-task causal effect.

## Frozen experiment

The run changed only output geometry.

| Variable | Frozen value |
| --- | --- |
| Reference Screen | `artifacts/references/plantstudio-main-window.png`, 474x403 |
| Reference SHA-256 | `c9ddeaa3cd27d0d5b502710ad12bc8f810529339c87b97a289b6d6932df8f45d` |
| Edit Brief | `artifacts/runs/golf-club-object-v002/brief.json` |
| Brief SHA-256 | `e5e12aa3056739123b04d764c8ee6fafa5458d7b4965a2c9ab40b2375590c3d5` |
| Licensed edit | Replace the selected flower inside x=182..218, y=78..242 with one upright seven-iron |
| Builder | `qwen/qwen-image-3-pro` via OpenRouter Images API |
| Seed | `1786` |
| Count | one output per arm |

OpenRouter's live model record exposed Qwen's 1K/2K tiers and enumerated
aspects, while the Images API documented an explicit pixel `size` as
authoritative. The exact-size request was therefore treated as a real arm,
not an unsupported placeholder. It succeeded at exactly 948x806. See the
[Image Generation API documentation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
and [Qwen Image 3 Pro model record](https://openrouter.ai/api/v1/images/models).

The preregistration and corrected endpoint-price estimate were posted before
submission in [Issue #52](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/52#issuecomment-5433901790).
A concurrent, inaccurate five-arm comment was explicitly reconciled in the
[same Issue](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/52#issuecomment-5434039838);
it did not describe the run and incurred no worktree spend.

## Per-arm evidence

T20 and T22 pixel indicators compare a nearest-neighbour normalized candidate
to the source. They are continuous evidence, not automatic taxonomy verdicts.
T21 is a hard dimension check. T20 and T22 visual outcomes came from an
independent `OpenAI Codex (GPT-5)` reviewer comparing four named, bounded
source/candidate crop pairs per arm. All 20 declared crop hashes were verified;
whole screenshots and prior labels were excluded. The review is advisory and
cannot waive deterministic evidence.

| Arm | Request | Native output | Relative aspect error | Outside-region pixels with luma delta >8 | Edge-strip pixels with luma delta >8 | Bounded T20 | Bounded T22 | Cost |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| exact-size | `size=948x806` | 948x806 | 0.00% | 31.21% | 52.03% | present, moderate | present, mild bottom clip | $0.043 |
| nearest-1k | `1K`, `5:4` | 1024x820 | 6.17% | 34.58% | 66.41% | present, moderate | present, moderate bottom truncation | $0.043 |
| mismatch-1k | `1K`, `16:9` | 1024x576 | 51.15% | 61.47% | 87.91% | present, moderate | present, severe teal pillarboxing | $0.043 |
| nearest-2k | `2K`, `5:4` | 2048x1640 | 6.17% | 28.42% | 55.73% | present, mild-to-moderate | present, moderate bottom truncation | $0.078 |

The 16:9 arm is the clear geometric failure: its outside-region indicator is
1.97x the exact arm and its edge-strip indicator is 1.69x the exact arm. The
5:4 arms retain the application's full width but still lose the source's exact
ratio and bottom framing. The 2K arm's lower raw diff does not justify choosing
2K for strict preservation because its categorical T20/T21/T22 outcomes still
fail.

### Native comparison evidence

The images remain separate files at their provider-native dimensions. No
contact sheet or batched composite substitutes for these outputs.

- [`exact-size`](../../artifacts/benchmarks/issue-52-canvas-match/runs/exact-size/image-01.png) — SHA-256 `978c097bbf76f6f0932d6eebf9f769566ae6b6e30917ad54591fb32023bb0bbe`
- [`nearest-1k`](../../artifacts/benchmarks/issue-52-canvas-match/runs/nearest-1k/image-01.png) — SHA-256 `633196949387f131194739277dc96a9a5f609ac227a681df3e9f1e091ca85ecb`
- [`mismatch-1k`](../../artifacts/benchmarks/issue-52-canvas-match/runs/mismatch-1k/image-01.png) — SHA-256 `5c436802ba237c7a333946ad34df948ff7f1fdc493fb247213989d870712ed7c`
- [`nearest-2k`](../../artifacts/benchmarks/issue-52-canvas-match/runs/nearest-2k/image-01.png) — SHA-256 `520b3f3ac6088035283df1e57b168daebc943d83d8543ebad348ed5d7cb2c4d2`

These are probabilistic Render Passes classified as comparison evidence, not
approved outputs. Human visual approval remains at the pull-request gate.

## Spend and provenance

Four images were requested and four completed, with no retry or ambiguous
attempt. Actual image cost was $0.207: three 1K-class calls at $0.043 and one
2K call at $0.078. Each arm has a pre-network attempt sentinel, sanitized
request, provider usage, native file, SHA-256, and provenance under
`artifacts/benchmarks/issue-52-canvas-match/`.

The image responses exposed no provider request ID (`request_id: null`). The
pre-network canonical request hashes therefore supply the durable identities:
`issue-52-exact-size-2389de5ac76cc189`,
`issue-52-nearest-1k-545f93c3b87906a1`,
`issue-52-mismatch-1k-1082bf8219ba1375`, and
`issue-52-nearest-2k-05110be7d7f2b75a`. Full request SHA-256 values live in
the corresponding attempt and run records.

One separately preregistered advisory review was requested and completed
through OpenRouter for $0.004879125. It compared whole screenshots, contrary to
ADR 0004's bounded-crop method, and its T20 annotations visibly contradicted the
crop and pixel evidence. The call is retained only as rejected-method
provenance: model, exact prompts, canonical request hash, response ID, blind
mapping, parsed annotations, and usage are recorded. The raw response was not
retained, and no paid retry was made. Total measured external cost for the
experiment and invalid review was $0.211879125.

## Interpretation limits

- One output per arm avoids batch confounds but provides no variance estimate.
- A fixed seed does not guarantee identical latent trajectories across output
  shapes; it only removes an avoidable input difference.
- The pixel indicators include generative and resampling differences and must
  not be relabeled as a deterministic T20/T22 verdict.
- Bounded independent review found visible redraw across multiple named
  preservation regions in every arm. Exact size and the nearest aspect reduce
  disturbance relative to 16:9, but do not pass strict T20 preservation.
- Exact size still produced a mild bottom crop. Canvas matching suppresses
  crop severity; it does not guarantee source-locked composition.

## Reproduction

The script creates an exclusive, durable sentinel before every image request.
Any ambiguous HTTP, transport, output-count, or persistence result retains a
global lock and blocks every later arm. The paid advisory-review command was
removed after its method was rejected.

```bash
python3.12 scripts/issue52_canvas_match.py prepare
OPENROUTER_API_KEY=... python3.12 scripts/issue52_canvas_match.py submit exact-size
OPENROUTER_API_KEY=... python3.12 scripts/issue52_canvas_match.py submit nearest-1k
OPENROUTER_API_KEY=... python3.12 scripts/issue52_canvas_match.py submit mismatch-1k
OPENROUTER_API_KEY=... python3.12 scripts/issue52_canvas_match.py submit nearest-2k
python3.12 scripts/issue52_canvas_match.py score
python3.12 scripts/issue52_canvas_match.py review-crops
```

The crop manifest is then reviewed by an independent, different-family agent.
Paid image commands are issue-scoped manual verification and are not part of
CI.
