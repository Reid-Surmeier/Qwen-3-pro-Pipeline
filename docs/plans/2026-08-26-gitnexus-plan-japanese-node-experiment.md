# GitNexus Engineering Plan

> Task: Run controlled Japanese-preserving ComfyUI node experiments for Issue #34 and promote only a verified winner.
> Evidence verified at commit 5ac269112123dc8a8f7df77d6ee9ffb92ca7fe49; GitNexus CLI index refreshed with 1.6.10-rc.223 and `--pdg` (MCP remains unreadable because its LadybugDB build is storage version 42 while the index is version 43).
> Evidence provenance schema 2; global dirty digest 43b7ac48492a3468191d8fdca468128a9533535a476ce5722583df72b8be0d0e; cited-path manifest 11 sorted entries; exact generated plan path excluded.

## Objective (§1)

Find a repeatable node-assisted improvement over a direct Qwen Image 3 Pro baseline for removing the Effect row while keeping the original Japanese and unchanged pixels outside the edit rectangle; implement an opt-in reusable workflow only if the evidence qualifies.

## Current Behaviour (§2–3)

- [verified] `QwenImage3Render` accepts an optional IMAGE batch but no MASK and forwards up to four reference images (`qwen_ui_pipeline/comfyui_node.py:16-29,51-110`).
- [verified] `ReferenceRegionComposite` nearest-resizes a complete donor and hard-copies one rectangle (`qwen_ui_pipeline/comfyui_node.py:113-162`).
- [verified] Existing public builders separate the Qwen Render Pass from deterministic region Assembly (`qwen_ui_pipeline/comfyui_workflow.py:9-72`), matching ADR 0001 and ADR 0002.
- [verified] The previous Issue #34 node arm only resized the full candidate and reapplied exterior alpha, so it cannot be credited for structural edits (`scripts/build_issue34_english_window_evidence.py:162-215`).

## Findings (§4–5)

- [graph] `gitnexus query` on Qwen/ComfyUI/region Assembly found the two public workflow builders, both Issue #34 evidence builders, and their tests as the relevant seams.
- [graph] `gitnexus context ReferenceRegionComposite --file qwen_ui_pipeline/comfyui_node.py` confirmed the class has no execution-flow membership and only its loader, documentation, and unit test import it.
- [graph] `gitnexus impact ReferenceRegionComposite --direction upstream --depth 3 --include-tests` reported LOW risk with three direct import dependants and no affected process.
- [verified] Installed-node research ranks focused crop → Qwen donor → hard/feathered composite first; exact text lock, second genuine source reference, and conditional outpaint remain bounded fallbacks (`docs/research/issue-34-comfyui-node-experiments.md`).
- [inferred] No production symbol should change before a candidate qualifies; experiment-only graphs isolate model behavior from Assembly behavior.

## Proposed Changes (§6)

1. Add `scripts/build_issue34_japanese_node_evidence.py` with a Japanese-preserving Edit Brief, direct and focused workflow builders, exact geometry, plan/run manifests, hash/dimension checks, changed-pixel checks, perimeter seam metrics, contact-sheet rendering, and a fail-closed qualification decision.
2. Add `tests/test_issue34_japanese_node_experiment.py` covering graph structure, paid boundary, exact guardrails, hard/feathered Assembly bounds, evidence classification, and rejected-output behavior.
3. Retain all submitted API JSON, raw outputs, Assembly variants, visible masks, provider metadata, reports, hashes, and comparison images under `artifacts/issue-34/japanese-node-experiment-v003/`.
4. Conditional on a repeatable winner only, add an opt-in public workflow builder in `qwen_ui_pipeline/comfyui_workflow.py`, export it through the established package seam, extend `tests/test_comfyui_workflow.py`, and document its exact contribution and limitations. If no arm qualifies, do not modify the production interface.

## Implementation Sequence (§7)

1. Red: add tests for the experiment brief and exact direct/focused graphs; run the focused test file and capture the expected import/assertion failure.
2. Green: implement the smallest evidence builder that emits pre-submission JSON and no-cost local metrics; validate both API graphs against live ComfyUI schemas.
3. Confirm the queue is empty and the Issue body contains the 2+2 matrix, ~$0.166 estimate, exact crop/rectangle, conditional 2-output fallback, and stop rule.
4. Submit two direct and two focused Render outputs once; preserve ambiguous attempts without retry. Build hard, 16-pixel feathered, and mask-preview variants from the same focused donors.
5. Inspect every output and compute the predeclared checks. Stop on a 2/2 qualifying improvement; otherwise run only the two-output genuine-detail-reference arm, then stop.
6. Promote only a qualified method to the opt-in public builder with a second red-green cycle; otherwise record “no winner” and leave production unchanged.
7. Generate the plain-language report/contact sheet, run GitNexus detect-changes, full repository verification, two required reviews, then commit/push and update draft PR #37 without merging.

## Test Strategy (§8)

- `python3.12 -m unittest tests.test_issue34_japanese_node_experiment -v`
- `python3.12 -m unittest discover -s tests -v`
- `node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs`
- `python3.12 -m compileall -q qwen_ui_pipeline tests scripts`
- `git diff --check`
- Live: queue empty, required node schemas present, API validation has zero issues, actual execution counts match, outputs retrieved, and zero changed pixels outside the declared rectangle.

## Implementation Context (§11)

```yaml
implementation_context:
  task_summary: "Compare direct Qwen against focused-crop plus deterministic mask Assembly; promote only a repeatable Japanese-preserving winner."
  evidence_provenance:
    schema_version: 2
    head_commit: "5ac269112123dc8a8f7df77d6ee9ffb92ca7fe49"
    generated_plan_path: "docs/plans/2026-08-26-gitnexus-plan-japanese-node-experiment.md"
    global_dirty_digest:
      algorithm: "sha256"
      canonicalization: "gitnexus-evidence-provenance-v2 NUL-framed UTF-8 records"
      value: "43b7ac48492a3468191d8fdca468128a9533535a476ce5722583df72b8be0d0e"
    cited_path_manifest:
      - {path: "AGENTS.md", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:b7d9c2f58d41ca36ea886088fc713546e40d47c85c7e6cdaa97672c33543a5e0", index_digest: "sha256:b7d9c2f58d41ca36ea886088fc713546e40d47c85c7e6cdaa97672c33543a5e0", worktree_digest: "sha256:b7d9c2f58d41ca36ea886088fc713546e40d47c85c7e6cdaa97672c33543a5e0", untracked_digest: absent}
      - {path: "CONTEXT.md", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:34c51c23594aaa5083db8579bea24617b35dc89f6d36bc4d6aaba61f50037e3c", index_digest: "sha256:34c51c23594aaa5083db8579bea24617b35dc89f6d36bc4d6aaba61f50037e3c", worktree_digest: "sha256:34c51c23594aaa5083db8579bea24617b35dc89f6d36bc4d6aaba61f50037e3c", untracked_digest: absent}
      - {path: "docs/adr/0001-separate-rendering-from-assembly.md", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:4eb6bc53df2e5fdd776331ee1069b657385f00e140e8ccbacd3d3c56fb89c6ea", index_digest: "sha256:4eb6bc53df2e5fdd776331ee1069b657385f00e140e8ccbacd3d3c56fb89c6ea", worktree_digest: "sha256:4eb6bc53df2e5fdd776331ee1069b657385f00e140e8ccbacd3d3c56fb89c6ea", untracked_digest: absent}
      - {path: "docs/adr/0002-preserve-immutable-pixels-with-region-assembly.md", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:baef5fb0dd6d2be4cbf332d68a6b714f2c74002082583c797781f5207335c347", index_digest: "sha256:baef5fb0dd6d2be4cbf332d68a6b714f2c74002082583c797781f5207335c347", worktree_digest: "sha256:baef5fb0dd6d2be4cbf332d68a6b714f2c74002082583c797781f5207335c347", untracked_digest: absent}
      - {path: "docs/adr/0004-bound-paid-visual-experiments-by-authoritative-issue.md", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:57adfd1f9cc26a360c5deb77a9246b112e5fb817aea5309302a2d8bc52337791", index_digest: "sha256:57adfd1f9cc26a360c5deb77a9246b112e5fb817aea5309302a2d8bc52337791", worktree_digest: "sha256:57adfd1f9cc26a360c5deb77a9246b112e5fb817aea5309302a2d8bc52337791", untracked_digest: absent}
      - {path: "docs/research/issue-34-comfyui-node-experiments.md", object_kind: {head: absent, index: absent, worktree: absent, untracked: regular}, state: untracked, rename_from: null, rename_to: null, head_digest: absent, index_digest: absent, worktree_digest: absent, untracked_digest: "sha256:d27b5a42ea3d950cc75a1e5ffefc7f796950149e82bc1128c401d4c899813bb9"}
      - {path: "qwen_ui_pipeline/comfyui_node.py", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:4253063c7eb4291e51e3f31d1df9dd4660e6a6e15691ab561fdf1025e0673b5c", index_digest: "sha256:4253063c7eb4291e51e3f31d1df9dd4660e6a6e15691ab561fdf1025e0673b5c", worktree_digest: "sha256:4253063c7eb4291e51e3f31d1df9dd4660e6a6e15691ab561fdf1025e0673b5c", untracked_digest: absent}
      - {path: "qwen_ui_pipeline/comfyui_workflow.py", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:d372c53444c0dd12010f8b367dc1ee9270e6c1b871adfc609581ff99b2c7c3a8", index_digest: "sha256:d372c53444c0dd12010f8b367dc1ee9270e6c1b871adfc609581ff99b2c7c3a8", worktree_digest: "sha256:d372c53444c0dd12010f8b367dc1ee9270e6c1b871adfc609581ff99b2c7c3a8", untracked_digest: absent}
      - {path: "scripts/build_issue34_english_window_evidence.py", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:2bcbecd3bcdcca36bc039a0979bab8c95353489a6991d0dbf0235b767012b667", index_digest: "sha256:2bcbecd3bcdcca36bc039a0979bab8c95353489a6991d0dbf0235b767012b667", worktree_digest: "sha256:2bcbecd3bcdcca36bc039a0979bab8c95353489a6991d0dbf0235b767012b667", untracked_digest: absent}
      - {path: "tests/test_comfyui_workflow.py", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:708038b8fd56b77fa314390cc321cf729e9a72cac8ea033c68a9e73aeb1a758e", index_digest: "sha256:708038b8fd56b77fa314390cc321cf729e9a72cac8ea033c68a9e73aeb1a758e", worktree_digest: "sha256:708038b8fd56b77fa314390cc321cf729e9a72cac8ea033c68a9e73aeb1a758e", untracked_digest: absent}
      - {path: "tests/test_issue34_english_window.py", object_kind: {head: regular, index: regular, worktree: regular, untracked: absent}, state: clean, rename_from: null, rename_to: null, head_digest: "sha256:10358cf2a93aa33644810bb3f2f612f9adc5bc2026b7c9c7ef915ee2dddaaf85", index_digest: "sha256:10358cf2a93aa33644810bb3f2f612f9adc5bc2026b7c9c7ef915ee2dddaaf85", worktree_digest: "sha256:10358cf2a93aa33644810bb3f2f612f9adc5bc2026b7c9c7ef915ee2dddaaf85", untracked_digest: absent}
  files_to_modify:
    - {file: "scripts/build_issue34_japanese_node_evidence.py", symbols: ["new experiment builders and evidence finalizer"], intended_change: "Create auditable direct, focused-crop, Assembly, measurement, and report paths."}
    - {file: "tests/test_issue34_japanese_node_experiment.py", symbols: ["new Issue34JapaneseNodeExperimentTests"], intended_change: "Drive the experiment red-green and lock guardrails."}
    - {file: "qwen_ui_pipeline/comfyui_workflow.py", symbols: ["conditional new opt-in builder"], intended_change: "Only after a winner, expose the proven graph without changing default behavior."}
    - {file: "tests/test_comfyui_workflow.py", symbols: ["ComfyUiWorkflowTests"], intended_change: "Only after a winner, test the public graph."}
  tests:
    - {file: "tests/test_issue34_japanese_node_experiment.py", scenarios: ["brief preserves Japanese", "baseline contains no helper nodes", "focused graph crops before Qwen", "hard and feathered outputs stay inside rectangle", "failed candidates do not qualify"]}
    - {file: "tests/test_comfyui_workflow.py", scenarios: ["conditional winning builder is opt-in and preserves the existing default"]}
  verification_commands:
    - "python3.12 -m unittest tests.test_issue34_japanese_node_experiment -v"
    - "python3.12 -m unittest discover -s tests -v"
    - "node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs"
    - "python3.12 -m compileall -q qwen_ui_pipeline tests scripts"
    - "git diff --check"
  assumptions:
    - "Re-verify live node schemas and empty queue immediately before submission."
    - "Treat provider cost as estimated until provider metadata exposes actual usage."
  open_questions:
    - "Whether either focused donor qualifies; production promotion is intentionally conditional on measured output."
  avoid:
    - "Do not translate or regenerate the source-owned Japanese regions."
    - "Do not describe an Assembly mask as Qwen guidance."
    - "Do not retry an ambiguous paid request or run unrecorded arms."
    - "Do not change the public workflow if no method qualifies."
```

## Assumptions and Open Questions (§12)

- [assumed] The live schemas remain unchanged between validation and submission; re-check immediately before execution.
- [assumed] Provider usage metadata may omit exact cost; preserve the estimate and request identity if it does.
- [open] The Render results determine whether any production change is warranted; no success is assumed by this plan.
- [deferred] Height outpaint is outside the initial matrix and remains blocked unless fixed-canvas work qualifies first.

## Definition of Done (§13)

- The initial 2+2 matrix and at most one conditional 2-output arm are fully auditable.
- Every Japanese guardrail and every pixel outside the Assembly rectangle has zero error for a claimed exact-preservation output.
- A winner is implemented only when 2/2 outputs show the predeclared improvement; otherwise the PR plainly reports no winner.
- Full verification and both repository-required reviews pass; PR #37 remains draft pending human visual approval.
