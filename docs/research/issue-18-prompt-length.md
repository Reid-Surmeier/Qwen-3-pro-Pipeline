# Does a near-ceiling prompt beat a concise Edit Brief? (Issue #18)

Exploratory, single-seed comparison of canonical (concise, complete) Edit
Briefs against near-ceiling deterministic restatements of the same atomic
requirements, run 2026-08-26 under the owner's standing session authorization.

## Design

- Provider/model: explicit OpenRouter / `qwen/qwen-image-3-pro` through the
  live ComfyUI `QwenImage3Render` node.
- Five frozen source-locked tasks x two arms x one output = 10 outputs,
  seed `2026081801`, 1K, count 1, per-task aspect ratio. Within each pair the
  prompt is the only changed input.
- The near-ceiling arm is produced by `scripts/issue18_prompt_length.py`
  (`expand_brief`): fixed restatement templates cycle over the task's atomic
  requirements until the compiled prompt reaches 4,300-4,450 approximate
  tokens (repository three-chars-per-token estimate against the published
  4,500-token positive-prompt recommendation). No new visual requirement is
  introduced; measured arms landed at ~4,306-4,329 vs ~294-488 canonical.
- Blinding: outputs were copied to neutral A/B names by a seeded shuffle
  (`blind` command) and scored per dimension before the arm mapping was read.
  Limitation: the same agent designed the experiment and scored it; the
  mapping was withheld mechanically but this is not third-party blinding.

## Primary-source context

Alibaba documents 4,500 tokens as a ceiling, not a target; Qwen's official
edit tooling asks for direct, minimally sufficient instructions. No official
controlled length ablation exists for Qwen Image 3 Pro edits. This experiment
tests the "always fill the maximum" hypothesis directly.

## Per-task blind scores

Dimensions: requested-edit success; instruction coverage; Exact Copy;
outside-region drift; visible artifacts (Issue #26 taxonomy classes).

| Task | Blind winner | Unblinded arm | Margin and reason |
| --- | --- | --- | --- |
| localized-replacement | A | **near-ceiling** | Slight: full title bar retained, crisper grooved iron head; B (canonical) top-clipped. Both succeed at the edit; both mildly re-render plants. |
| exact-copy-edit | A | **canonical** | Slight: crop only. Both arms render the new title character-exact and correctly change nothing else. |
| object-removal | tie (both pass) | — | **Corrected 2026-08-26:** both arms removed the star and faithfully preserved the source's real identity. The source file is the genuine ENERGY STAR sticker ("energy" script, "ENERGY STAR" band); the palantir parody exists only in generated outputs of that run. The original "identity substitution" reading was an annotation error — the Edit Brief itself mislabeled the source as the parody, and the model correctly followed the pixels over the wrong name. |
| style-material | A | **near-ceiling** | Marginal: both excellent gold-foil re-renders with exact copy; near-ceiling converted flag panes to permitted gold tints, canonical kept original hues. |
| dense-multi-region | A | **canonical** | All three edits applied by both; canonical matched the source's lowercase letter style ("pentium"), near-ceiling capitalized ("Pentium"). Both sharpened the blurry photo source (shared beautification deviation). |

Tally: near-ceiling 2, canonical 2, 1 tie (both arms succeeded after the correction below). Every margin was small and
none tracked prompt length (the top-crop defect appeared once in each arm).
Same-seed pairs were near-twins in composition despite roughly 10x the prompt
tokens, so (source, seed, output geometry) dominates the visual solution and
prompt wording moves only the margins.

Cost was identical per output regardless of length: $0.043 total with
$0.003 upstream prompt cost in both arms (provider-reported prompt_tokens
~226-372 canonical vs ~3,258-3,275 near-ceiling). Total spend: 10/10
completed, $0.43 actual.

## Verdict

**The blanket max-length hypothesis is rejected** under the pre-registered
rule (near-ceiling needed at least 4 of 5 tasks; it took 2 with no hard
regression either way). Deterministic restatement padding to the token
ceiling neither helped nor hurt visibly: write briefs at the length their
content requires.

Incidental findings that outrank the hypothesis:

1. **Corrected — annotation error, not brand reversion**: the object-removal
   source was the genuine ENERGY STAR sticker, mislabeled as the palantir
   parody in the Edit Brief. Both arms preserved the source faithfully while
   removing the star — the model followed the pixels over the brief's wrong
   name (a robustness datum, and a caution for reviewer source-identity
   checks). Memorized-brand reversion (T33) remains a hypothesis with no
   confirmed instance; Issue #70 now tests it against the actual approved
   parody outputs.
2. **Seed dominance**: matched seeds produced near-identical compositions
   across a 10x prompt-length gap — strong support for Issue #53's
   seed-variance study before trusting any single-seed A/B.
3. **Beautification of degraded sources**: both arms sharpened a blurry photo
   source into a crisp studio render while executing the edits — "match it
   exactly except the named edits" did not preserve photographic character.
4. **Token-estimate calibration**: the repository's 3-chars/token estimate
   overshoots the provider tokenizer by roughly a third (~4,320 estimated →
   ~3,270 provider-reported), so real briefs have more headroom than the
   compiler suggests.

## Evidence

- Briefs, compiled prompts, and metrics: `artifacts/benchmarks/issue-18-prompt-length/briefs/`
- Attempt records with prompt IDs: `.../attempts/`
- Outputs and hashes: `.../outputs/`, `.../collection-manifest.json`
- Blind mapping (read only after scoring): `.../blind-mapping.json`

## Limitations

Single seed per condition; five tasks; one provider route; approximate token
counts. Per the pre-registered rule, no default prompting policy changes from
this result alone — a positive finding requires a separately approved
replication (see Issue #53, seed variance).
