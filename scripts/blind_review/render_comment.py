"""Render a validated verdict into the review-comment format.

Consumes a review.json that has already passed validate_verdict.py and
emits the Markdown comment defined in docs/agents/blind-review.md. Rendering
is mechanical; judgment happened in the sandbox.

Usage:
    python scripts/blind_review/render_comment.py \
        --verdict /tmp/blind-out/review.json \
        --contract docs/reviews/issue-86-contract.md > comment.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render(verdict: dict, contract: str) -> str:
    lines = [
        "## Blind artifact review",
        "",
        f"Candidate: `{verdict['candidate_commit']}`",
        f"Contract: {contract}",
        f"Verdict: **{verdict['verdict'].upper()}**",
    ]

    if verdict["findings"]:
        lines += ["", "### Findings"]
        for finding in verdict["findings"]:
            steps = "\n".join(
                f"{number}. {step}" for number, step in enumerate(finding["steps"], start=1)
            )
            lines += [
                f"#### {finding['id']} — {finding['title']} ({finding['severity']})",
                f"- Contract clause: {finding['contract_clause']}",
                f"- State: {finding['state']}",
                "- Steps:",
                steps,
                f"- Expected: {finding['expected']}",
                f"- Actual: {finding['actual']}",
                f"- Evidence: `{finding['evidence']}`",
                "",
            ]

    if verdict["unverified"]:
        lines += ["### Unverified"]
        lines += [
            f"- {item['clause']} — {item['reason']}" for item in verdict["unverified"]
        ]
        lines += [""]

    if verdict["positive"]:
        lines += ["### Positive observations"]
        lines += [f"- {item}" for item in verdict["positive"]]
        lines += [""]

    if verdict["followups"]:
        lines += ["### Follow-up observations (non-blocking)"]
        lines += [
            f"- {item['note']} — {item['class']}" for item in verdict["followups"]
        ]
        lines += [""]

    if verdict["verdict"] == "fail":
        blocking = [f["id"] for f in verdict["findings"] if f["severity"] == "blocking"]
        lines += [
            "### Required disposition",
            f"- Fix {', '.join(blocking)}.",
            "- Reapply `ready-for-blind-review` on a new commit to start the next round.",
        ]

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verdict", required=True, type=Path)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args(argv)
    try:
        verdict = json.loads(args.verdict.read_text(encoding="utf-8"))
        sys.stdout.write(render(verdict, args.contract))
    except (KeyError, json.JSONDecodeError, FileNotFoundError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
