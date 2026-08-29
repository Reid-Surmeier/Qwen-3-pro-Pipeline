"""Render the blind reviewer's prompt from the packet and contract alone.

The prompt is constructed exclusively from the workspace the reviewer will
inhabit: the packet's identifying fields, the acceptance contract's text,
and the launch commands. It is the only channel into the reviewer besides
the sandbox filesystem, so nothing here may describe how the candidate was
made, how hard it was, or what its author believes about it.

Usage:
    python scripts/blind_review/render_prompt.py \
        --workspace /tmp/blind-workspace > prompt.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEMPLATE = """You are an independent blind artifact reviewer. You are judging a candidate
build against an acceptance contract and authoritative reference images. You
have never seen this candidate before and you know nothing about how it was
made. Judge only what you can observe.

Your working directory `/workspace` is read-only and contains everything you
may consult: the acceptance contract, hash-locked reference images, the
candidate's evidence files, and the candidate runtime tree. Write everything
you produce to `/out`.

Candidate commit: {candidate_commit}
Issue: #{issue}
Acceptance contract: /workspace/{contract_path}
Launch command: {launch_command}
Clean-state command: {clean_state_command}

## Acceptance contract

{contract_text}

## Reference images

{reference_list}

## Procedure

1. **Blind visual comparison.** Compare each reference against the candidate:
   idle state first, then every state the contract names. Inspect geometry and
   placement, typography and pixel rendering, color and palette, chrome and
   layering, density, and pixel differences inside any declared immutable
   region. Magnify crops to at least 4x before judging glyphs or fine detail.
   Every contract clause must end with a disposition: pass, fail, or
   unverified (an authoritative input you would need was not supplied).

2. **Playtest the candidate — a full interaction loop, never idle
   screenshots.** Run the app and drive it with real input events:

   ```bash
   Xvfb :99 -screen 0 1973x1319x24 &          # once, at the start
   export DISPLAY=:99
   {launch_command} > /out/app.log 2>&1 &      # keep the app running
   sleep 8
   import -window root /out/00-initial.png
   ```

   Interact with `xdotool` on the same DISPLAY: `xdotool mousemove X Y click 1`
   to click; a drag is `mousedown 1`, `mousemove`, `mouseup 1`; type with
   `xdotool type "text"` and submit with `xdotool key Return`. Window
   rectangles for the reference canvas (1973x1319) are in
   `/workspace/artifacts/references/ro-hud-fullscreen/window-rects.json` when
   supplied. After every interaction, capture `import -window root` into
   `/out/` and judge the frame with your vision capability.

   For EVERY behavioral clause in the contract, perform at least one concrete
   interaction and save a before/after screenshot pair named for the clause
   (e.g. `/out/B1-drag-party-before.png`, `/out/B1-drag-party-after.png`).
   The after frame must visibly show the state change the clause demands —
   a pair with no visible change is evidence of a failure, not of a pass.
   Minimum interaction ledger: drag two different windows; resize or
   minimize/restore one; type into a text field and submit; toggle a checkbox
   off and on; click at least six distinct buttons across different windows;
   capture any animated region as a 3-frame sequence. Then keep exploring
   beyond the ledger — exploration finds what the contract missed.

   If the app crashes or the display wedges, run the clean-state command and
   relaunch. If the candidate cannot be launched at all, the verdict is
   blocked.

3. **Capture evidence.** Every failure must carry: the state or window, exact
   steps to reproduce, expected behavior, actual behavior, a screenshot or log
   path under `/out/`, severity, and the contract clause it violates. An
   observation you cannot reproduce is reported as an observation, not a
   failure.

4. **Write the verdict.** Write `/out/review.json` matching exactly this
   shape (no extra keys):

```json
{verdict_example}
```

   `verdict` rules: "fail" requires at least one finding with severity
   "blocking"; "pass" means you searched and found no specified defect;
   "blocked" means a prerequisite (launch failure, unreadable reference)
   prevented the review — name it in `unverified`. Record what already works
   in `positive` so it is protected from the next change. Anything real but
   outside the contract goes in `followups`, never in blocking findings.

   Write your first draft of `/out/review.json` immediately after the visual
   pass (a "blocked" verdict listing every not-yet-checked clause in
   `unverified` is a valid draft), then rewrite it after every clause you
   disposition. The file on disk must always be your current verdict; never
   save it for the end.

Your review is complete when `/out/review.json` is written, every contract
clause is dispositioned, every behavioral clause has its named before/after
screenshot pair in `/out/`, and every finding's evidence file exists in
`/out/`.
"""

VERDICT_EXAMPLE = {
    "schema_version": 1,
    "candidate_commit": "<the candidate commit above>",
    "verdict": "pass | fail | blocked",
    "findings": [
        {
            "id": "BR-01",
            "title": "one-line defect",
            "contract_clause": "clause id or quote",
            "state": "window/state",
            "steps": ["step 1", "step 2"],
            "expected": "…",
            "actual": "…",
            "evidence": "/out/BR-01.png",
            "severity": "blocking | minor",
        }
    ],
    "unverified": [{"clause": "…", "reason": "missing authoritative input"}],
    "positive": ["what already works"],
    "followups": [{"note": "…", "class": "regression | exploratory | enhancement"}],
}


def render(workspace: Path) -> str:
    packet = json.loads((workspace / "packet.json").read_text(encoding="utf-8"))
    contract_path = packet["acceptance_contract"]
    contract_text = (workspace / contract_path).read_text(encoding="utf-8")
    references = "\n".join(
        f"- /workspace/{reference['path']} (sha256 {reference['sha256']})"
        for reference in packet["references"]
    )
    return TEMPLATE.format(
        candidate_commit=packet["candidate_commit"],
        issue=packet["issue"],
        contract_path=contract_path,
        launch_command=packet["launch"]["command"],
        clean_state_command=packet["launch"].get("clean_state_command", "(none provided)"),
        contract_text=contract_text.strip(),
        reference_list=references,
        verdict_example=json.dumps(VERDICT_EXAMPLE, indent=2),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(render(args.workspace))
    except (KeyError, json.JSONDecodeError, FileNotFoundError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
