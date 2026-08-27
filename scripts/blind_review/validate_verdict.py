"""Validate a blind reviewer's verdict, failing closed on any ambiguity.

A verdict that cannot be parsed into the schema, contradicts itself, names
a missing evidence file, or binds to the wrong SHA is `blocked`. The model
never gets the benefit of the doubt: an unreadable pass is not a pass.

Usage:
    python scripts/blind_review/validate_verdict.py \
        --verdict /tmp/blind-out/review.json \
        --packet /tmp/blind-workspace/packet.json \
        --out-dir /tmp/blind-out

Prints a JSON result and exits 0 only for a structurally sound verdict.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
FINDING_ID = re.compile(r"^BR-[0-9]{2,}$")
VERDICTS = ("pass", "fail", "blocked")
SEVERITIES = ("blocking", "minor")
FOLLOWUP_CLASSES = ("regression", "exploratory", "enhancement")

FINDING_KEYS = {
    "id", "title", "contract_clause", "state", "steps",
    "expected", "actual", "evidence", "severity",
}
TOP_KEYS = {
    "schema_version", "candidate_commit", "verdict",
    "findings", "unverified", "positive", "followups",
}


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_verdict(
    verdict_path: Path, packet_path: Path, out_dir: Path
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []

    def fail(code: str, detail: str) -> None:
        failures.append({"code": code, "detail": detail})

    try:
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [{"code": "verdict-missing", "detail": str(verdict_path)}]
    except json.JSONDecodeError as error:
        return [{"code": "verdict-unparseable", "detail": str(error)}]
    if not isinstance(verdict, dict):
        return [{"code": "verdict-not-object", "detail": type(verdict).__name__}]

    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return [{"code": "packet-unreadable", "detail": str(error)}]

    unknown = set(verdict) - TOP_KEYS
    if unknown:
        fail("verdict-unknown-keys", ", ".join(sorted(unknown)))
    missing = TOP_KEYS - set(verdict)
    if missing:
        fail("verdict-missing-keys", ", ".join(sorted(missing)))

    if verdict.get("schema_version") != 1:
        fail("schema-version-unsupported", repr(verdict.get("schema_version")))

    sha = verdict.get("candidate_commit")
    if not isinstance(sha, str) or not FULL_SHA.match(sha):
        fail("candidate-commit-malformed", repr(sha))
    elif sha != packet.get("candidate_commit"):
        fail("candidate-commit-mismatch", f"verdict {sha} != packet {packet.get('candidate_commit')}")

    outcome = verdict.get("verdict")
    if outcome not in VERDICTS:
        fail("verdict-value-unknown", repr(outcome))

    findings = verdict.get("findings")
    blocking = 0
    if not isinstance(findings, list):
        fail("findings-not-list", repr(findings))
    else:
        for index, finding in enumerate(findings):
            label = f"findings[{index}]"
            if not isinstance(finding, dict) or set(finding) != FINDING_KEYS:
                fail("finding-malformed", label)
                continue
            if not isinstance(finding["id"], str) or not FINDING_ID.match(finding["id"]):
                fail("finding-id-malformed", label)
            steps = finding["steps"]
            if not isinstance(steps, list) or not steps or not all(_nonempty_str(s) for s in steps):
                fail("finding-steps-missing", label)
            for key in ("title", "contract_clause", "state", "expected", "actual"):
                if not _nonempty_str(finding[key]):
                    fail(f"finding-{key.replace('_', '-')}-missing", label)
            if finding["severity"] not in SEVERITIES:
                fail("finding-severity-unknown", label)
            elif finding["severity"] == "blocking":
                blocking += 1
            evidence = finding["evidence"]
            if not _nonempty_str(evidence):
                fail("finding-evidence-missing", label)
            else:
                evidence_path = Path(evidence)
                resolved = (
                    out_dir / evidence_path.relative_to("/out")
                    if evidence_path.is_absolute() and str(evidence_path).startswith("/out")
                    else out_dir / evidence_path
                )
                if not resolved.is_file():
                    fail("finding-evidence-not-found", f"{label}: {evidence}")

    if outcome == "fail" and blocking == 0:
        fail("fail-without-blocking-finding", "verdict is fail but no blocking finding exists")
    if outcome == "pass" and blocking > 0:
        fail("pass-with-blocking-finding", f"{blocking} blocking finding(s) under a pass verdict")

    unverified = verdict.get("unverified")
    if not isinstance(unverified, list) or not all(
        isinstance(item, dict)
        and set(item) == {"clause", "reason"}
        and _nonempty_str(item["clause"])
        and _nonempty_str(item["reason"])
        for item in unverified
    ):
        fail("unverified-malformed", repr(unverified))
    elif outcome == "blocked" and not unverified:
        fail("blocked-without-reason", "blocked verdict names nothing in unverified")

    positive = verdict.get("positive")
    if not isinstance(positive, list) or not all(_nonempty_str(item) for item in positive):
        fail("positive-malformed", repr(positive))

    followups = verdict.get("followups")
    if not isinstance(followups, list) or not all(
        isinstance(item, dict)
        and set(item) == {"note", "class"}
        and _nonempty_str(item["note"])
        and item["class"] in FOLLOWUP_CLASSES
        for item in followups
    ):
        fail("followups-malformed", repr(followups))

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verdict", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    failures = validate_verdict(args.verdict, args.packet, args.out_dir.resolve())
    status = "valid" if not failures else "blocked"
    print(json.dumps({"status": status, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
