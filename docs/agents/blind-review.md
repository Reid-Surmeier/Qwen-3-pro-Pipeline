# Blind artifact review

An independent reviewer judges the candidate artifact itself — the pixels, the running build, the behavior — with the implementer's narrative withheld. The reviewer reviews the artifact, not the implementing agent's story about the artifact.

This gate applies to any pull request that creates or changes visual or interactive output. Under the release train that means the standing release PR and any fragment PR carrying such a candidate. It is a third, independent pass beside the specification and engineering reviews in [`AGENTS.md`](../../AGENTS.md); it replaces none of them, and it never replaces the owner's final visual approval.

## Roles

- **Implementation agent** — produces the candidate, assembles the packet, applies `ready-for-blind-review`. Never applies a verdict label.
- **Blind reviewer** — a fresh session or sub-agent whose entire input is the packet. Judges appearance and behavior. Applies exactly one verdict label per round. Never modifies the candidate and never proposes itself as the fixer.
- **Engineering reviewer** — reads code, diff, and tests as before. A separate context from the blind reviewer: a reviewer who has seen why a defect was hard to avoid will excuse it on screen, so the blind reviewer reads the packet first and the code never.
- **Owner** — final subjective visual approval, after all three passes.

## Label state machine

Verdict labels live on the pull request that carries the candidate commit. The acceptance contract lives in the authoritative Issue.

| Label | Applied by | Meaning |
| --- | --- | --- |
| `ready-for-blind-review` | implementation agent | A committed candidate SHA, a valid packet, and required evidence exist. |
| `blind-review-in-progress` | blind reviewer | One review round is running against one named SHA. |
| `blind-review-passed` | blind reviewer | No specified defect found in the reviewed SHA. |
| `blind-review-failed` | blind reviewer | At least one reproducible contract violation, with evidence. |
| `blind-review-blocked` | blind reviewer | A packet prerequisite failed; the review did not run. |

Rules:

- Every verdict names its exact candidate SHA. A new commit on the PR invalidates the prior verdict (`.github/workflows/blind-review.yml` strips verdict labels on push).
- One active review per SHA. Reapplying `ready-for-blind-review` to an already-reviewed SHA changes nothing.
- After three failed rounds on one Issue, apply `needs-human-decision` and stop; the owner arbitrates instead of a fourth round.
- The contract is fixed for the round. A defect outside it is recorded as a follow-up observation, classified as regression, exploratory concern, or future enhancement — never silently promoted to blocking, and never used to broaden the contract mid-round.

## The packet

The packet is the reviewer's entire input. It lives at `artifacts/reviews/issue-<n>/packet.json` on the candidate branch and conforms to [`schemas/blind-review-packet.schema.json`](../../schemas/blind-review-packet.schema.json): issue number, exact candidate SHA, the acceptance-contract path, hash-locked references, candidate evidence paths, and deterministic launch and clean-state commands.

Blindness is the mechanism, so these stay out of the packet and out of the reviewer's context: the PR description, the implementer's self-assessment, test counts, effort spent, fidelity claims, and known-fix suggestions. The orchestrator builds the reviewer's prompt from the packet alone.

The PR body declares the packet with one line the enforcement workflow reads:

```text
Blind-Review-Packet: artifacts/reviews/issue-86/packet.json
```

## Reviewer procedure

### 1. Validate the packet

```bash
python scripts/validate_blind_review_packet.py \
  --packet artifacts/reviews/issue-<n>/packet.json \
  --repo . --expect-sha <candidate-sha>
```

Any failure → apply `blind-review-blocked`, post the validator's JSON verdict, stop. A blocked round names what was missing; it never guesses around it. Done when: the validator reports `valid`, or the blocked verdict is posted.

### 2. Blind visual comparison

Compare reference against candidate: idle state first, then every state the contract names. Inspect geometry and placement, typography and pixel rendering, color and palette, chrome and layering, density, and pixel differences inside any declared immutable region. Magnify crops for glyph-level judgment. Done when: every contract clause has a disposition — pass, fail, or unverified (reference or expected terminal state not supplied).

### 3. Playtest the candidate

Launch with the packet's command; run the clean-state command between rounds. First contract-directed checks (each named interaction), then exploratory playtesting — drag, resize, click every control, edit and submit text, exercise stateful widgets. Contract checks prove named requirements; exploration finds what the contract missed. Done when: every interactive element named in the contract has been exercised at least once, and at least one exploratory pass has run.

### 4. Capture evidence

Every failure carries: candidate SHA, state or window, steps to reproduce, expected behavior, actual behavior, a screenshot/video/log path under `artifacts/reviews/issue-<n>/blind-review/`, severity, and the violated contract clause. An unreproducible observation is reported as an observation, not a failure.

### 5. Post one structured review

Post a single review comment on the PR using the template below, apply exactly one verdict label, and remove `blind-review-in-progress`. Done when: the comment is posted, the label state is consistent, and every finding in the comment has evidence on disk.

## Review comment template

```markdown
## Blind artifact review

Candidate: <full-sha>
Contract: docs/reviews/issue-<n>-contract.md
Verdict: PASS | FAIL | BLOCKED

### Blocking findings
#### BR-01 — <one-line defect>
- Contract clause: <id or quote>
- State: <window/state>
- Steps: <numbered repro>
- Expected: … / Actual: …
- Evidence: artifacts/reviews/issue-<n>/blind-review/BR-01-….png

### Unverified
- <clause> — <what authoritative input was missing>

### Positive observations
- <what already works; protects it from the next fixer>

### Follow-up observations (non-blocking)
- <finding outside the contract> — regression | exploratory concern | future enhancement

### Required disposition
- <what must change, and that a new commit + relabel starts the next round>
```

`PASS` means: no specified defect was found by an independent reviewer. It is evidence for the owner's decision, not the decision.

## Cost

Packet validation and label mechanics are free and deterministic. A blind reviewer that spends paid vision-model calls operates under ADR 0003 and the active milestone allowance, recorded in the generation ledger like any other paid verification.

## Reviewer harness

The spawnable reviewer is Gemini 3.7 Flash (`google/gemini-3.7-flash` via OpenRouter) running as a Hermes agent whose observable world is a Docker sandbox. Blindness is structural, not prompt discipline:

- **Hermes on the host, sandbox in Docker.** The Hermes process runs from the owner's install with the configured OpenRouter key, spawned with `--ignore-user-config --ignore-rules` so Hermes memory, rules, and skills never reach the reviewer's context. Its terminal backend is Docker (`TERMINAL_ENV=docker`); every command, file read, and screenshot happens inside the container, and Hermes's vision resolver reads captured frames from inside it.
- **The container has no network** (`--network none`). Model calls happen host-side; no credential exists in the sandbox.
- **`/workspace` is read-only and packet-derived.** `scripts/blind_review/build_workspace.py` extracts it with `git archive` at the candidate SHA: contract, hash-locked references, declared evidence, and the runtime tree passed with `--include` — no `.git`, no history, no implementer notes, no working-tree drift. The build refuses to proceed if a reference hash does not match at that SHA.
- **`/out` is the only writable path.** The reviewer must leave `review.json` there, conforming to [`schemas/blind-review-verdict.schema.json`](../../schemas/blind-review-verdict.schema.json). `scripts/blind_review/validate_verdict.py` checks it fail-closed: unparseable, self-contradictory (a pass carrying a blocking finding), SHA-mismatched, or missing-evidence verdicts are all `blind-review-blocked`.
- **Posting stays with the host.** The agent never holds `gh` credentials; the operator posts the rendered comment (`render_comment.py`) and applies the verdict label.

One round:

```bash
scripts/blind_review/run_blind_review.sh \
  --packet artifacts/reviews/issue-86/packet.json \
  --include godot
```

Add `--dry-run` to inspect the exact spawn without building the image or spending. A live round makes paid OpenRouter calls and is recorded in the generation ledger; it never runs in ordinary PR CI.

## Calibration

Before trusting a new blind-reviewer implementation, run it against a known-bad candidate (it must fail with specific findings) and a known-good candidate (it must not invent blocking defects). The packet validator's own calibration lives in `tests/test_blind_review_packet.py`. An uncalibrated reviewer is another green light wired to nothing.
