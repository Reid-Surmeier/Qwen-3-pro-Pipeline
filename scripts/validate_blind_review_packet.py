"""Validate a blind-review packet before a blind artifact review may start.

The packet is the reviewer's entire input, so every claim in it must be
mechanically true before the review begins: the candidate SHA must exist,
every reference must match its recorded hash, and every named evidence file
must be present. Any failure means the review is blocked, never guessed
around.

Usage:
    python scripts/validate_blind_review_packet.py \
        --packet artifacts/reviews/issue-86/packet.json \
        --repo . \
        [--expect-sha <full-sha>]

Prints a JSON verdict to stdout and exits 0 (valid) or 1 (blocked).
Exit code 2 means the tool itself was invoked incorrectly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def commit_exists(repo: Path, sha: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def validate_packet(packet_path: Path, repo: Path, expect_sha: str | None) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []

    def fail(code: str, detail: str) -> None:
        failures.append({"code": code, "detail": detail})

    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [{"code": "packet-missing", "detail": str(packet_path)}]
    except json.JSONDecodeError as error:
        return [{"code": "packet-unparseable", "detail": str(error)}]

    if not isinstance(packet, dict):
        return [{"code": "packet-not-object", "detail": type(packet).__name__}]

    if packet.get("schema_version") != 1:
        fail("schema-version-unsupported", repr(packet.get("schema_version")))

    issue = packet.get("issue")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue < 1:
        fail("issue-invalid", repr(issue))

    sha = packet.get("candidate_commit")
    if not isinstance(sha, str) or not FULL_SHA.match(sha):
        fail("candidate-commit-malformed", repr(sha))
    elif not commit_exists(repo, sha):
        fail("candidate-commit-unknown", sha)
    elif expect_sha is not None and sha != expect_sha:
        fail("candidate-commit-mismatch", f"packet {sha} != expected {expect_sha}")

    contract = packet.get("acceptance_contract")
    if not isinstance(contract, str) or not contract:
        fail("acceptance-contract-missing", repr(contract))
    elif not (repo / contract).is_file():
        fail("acceptance-contract-not-found", contract)

    references = packet.get("references")
    if not isinstance(references, list) or not references:
        fail("references-missing", repr(references))
    else:
        for index, reference in enumerate(references):
            label = f"references[{index}]"
            if not isinstance(reference, dict):
                fail("reference-malformed", label)
                continue
            path = reference.get("path")
            recorded = reference.get("sha256")
            if not isinstance(path, str) or not path:
                fail("reference-path-missing", label)
                continue
            if not isinstance(recorded, str) or not SHA256_HEX.match(recorded):
                fail("reference-hash-malformed", f"{label}: {path}")
                continue
            target = repo / path
            if not target.is_file():
                fail("reference-not-found", path)
            elif sha256_of(target) != recorded:
                fail("reference-hash-mismatch", path)

    candidate = packet.get("candidate")
    if not isinstance(candidate, dict):
        fail("candidate-missing", repr(candidate))
    else:
        evidence = candidate.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail("evidence-missing", repr(evidence))
        else:
            for item in evidence:
                if not isinstance(item, str) or not item:
                    fail("evidence-path-malformed", repr(item))
                elif not (repo / item).is_file():
                    fail("evidence-not-found", item)

    launch = packet.get("launch")
    if not isinstance(launch, dict):
        fail("launch-missing", repr(launch))
    else:
        command = launch.get("command")
        if not isinstance(command, str) or not command.strip():
            fail("launch-command-missing", repr(command))

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--expect-sha",
        default=None,
        help="Require candidate_commit to equal this SHA (e.g. the PR head).",
    )
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(json.dumps({"status": "error", "detail": f"not a git repository: {repo}"}))
        return 2

    failures = validate_packet(args.packet, repo, args.expect_sha)
    status = "valid" if not failures else "blocked"
    print(json.dumps({"status": status, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
