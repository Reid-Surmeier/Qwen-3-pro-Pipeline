#!/usr/bin/env python3.12
"""Evaluate one image-79 Play Log and optionally write the verdict."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qwen_ui_pipeline.play_log import evaluate_play_log  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("play_log", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "godot/data/image-79-control-spec.json"
    )
    parser.add_argument(
        "--review-issue", type=int, help="trusted review Issue that selects verifier policy"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        log = json.loads(args.play_log.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        verdict = {
            "verdict": "INVALID",
            "actions": 0,
            "frames_verified": 0,
            "unexercised": [],
            "failures": [],
            "problems": [f"unreadable play log: {error}"],
        }
    else:
        evidence_root = args.evidence_root or args.play_log.parent
        try:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            manifest = None
            log.setdefault("manifest_error", str(error))
        try:
            verdict = evaluate_play_log(
                log, evidence_root, manifest, trusted_issue=args.review_issue
            )
        except Exception as error:  # Fail closed at the untrusted artifact seam.
            verdict = {
                "verdict": "INVALID",
                "actions": 0,
                "frames_verified": 0,
                "unexercised": [],
                "failures": [],
                "problems": [f"Play Log verifier failed closed: {error}"],
            }

    rendered = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if verdict["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
