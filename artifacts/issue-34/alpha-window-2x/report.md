# Issue #34 result

The native nearest-exact graph is the strongest enlargement in this test. It keeps every RGB pixel and control position exact at 2x. ComfyUI changes some very faint alpha-fringe pixels because of its intermediate mask precision.

The first proposed graph was wrong for an uploaded PNG: `LoadImage` had already separated RGB from alpha, so splitting RGB again returned no useful mask. The correct graph uses `LoadImage` output 1 as the mask.

Two paid source-only Qwen outputs cost $0.083. Both are recognizable, but both move the Effect slider handle and change the outer geometry. Reapplying the source mask fixes size and transparency only; it does not fix those interior changes. The initial pair answered the question, so no more paid outputs were run.

Human visual approval is still pending.
