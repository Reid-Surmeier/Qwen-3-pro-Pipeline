# Issue 71: resolution evidence and timeout boundary

Issue: [#71 — Resolution effect and 2K reliability](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/71)

## Corrected evidence state

The Issue originally said the Issue #52 2K arm had not completed. That statement
described the superseded experiment in PR #67. The authoritative canvas ablation
in [PR #69](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/pull/69)
completed a matched `5:4` pair through explicit OpenRouter with the source,
Edit Brief, seed `1786`, model, and one-output setting held constant.

| Arm | Native dimensions | Actual cost | Outside-region luma-delta fraction | Edge-strip luma-delta fraction | Bounded review |
| --- | ---: | ---: | ---: | ---: | --- |
| 1K, `5:4` | 1024x820 | $0.043 | 34.58% | 66.41% | T20 present/moderate; T22 present/moderate |
| 2K, `5:4` | 2048x1640 | $0.078 | 28.42% | 55.73% | T20 present/mild-to-moderate; T22 present/moderate |

The 2K arm produced more pixels and lower normalized raw-difference indicators
in this seed, but did not change the categorical result: both arms had T20
global redraw, T21 aspect drift, and T22 bottom-edge truncation. One matched
pair supplies no variance estimate, so this is not evidence of a general 2K
fidelity improvement. PR #69 retains native images, hashes, request identities,
costs, deterministic scores, bounded crop evidence, and final FigJam readback.

No request-duration field was exposed in those provider records. This change
therefore makes no latency-distribution claim and does not select a new default.

## Timeout contract

`OpenRouterImageClient` continues to use 180 seconds by default. A caller with
issue-specific evidence may pass a finite positive timeout in seconds when it
constructs the client. Zero, negative, boolean, non-numeric, NaN, and infinite
values are rejected before a request.

This is an explicit waiting boundary, not a retry mechanism. A timeout remains
an ambiguous possibly billed request: callers must preserve the request record,
count it against the Issue allowance, reconcile it, and never resubmit blindly.
The change does not affect provider selection, output settings, Alibaba, or any
pipeline default.

## Verification scope

No provider call or paid generation is part of Issue #71. Unit tests verify the
180-second default, exact forwarding of an explicit override, and fail-closed
validation before network access.
