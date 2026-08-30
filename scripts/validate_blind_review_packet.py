#!/usr/bin/env python3
"""Fail-closed validation for an exact-SHA blind artifact-review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def validate_packet(packet_path: Path, repository: Path, candidate: str) -> list[str]:
    problems: list[str] = []
    try:
        packet: Any = json.loads(packet_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return [f"packet is unreadable: {error}"]
    if not isinstance(packet, dict):
        return ["packet root must be an object"]
    if packet.get("candidate_commit") != candidate:
        problems.append("packet candidate_commit does not match requested candidate")
    commit = subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0:
        problems.append("candidate is not a commit in this repository")
    _require_file(repository, packet.get("acceptance_contract"), "acceptance_contract", problems)
    for index, reference in enumerate(packet.get("references", [])):
        _verify_hashed_file(repository, reference, f"references[{index}]", problems)
    evidence = packet.get("candidate", {}).get("evidence", [])
    if not isinstance(evidence, list) or not evidence:
        problems.append("candidate.evidence must be a non-empty array")
    else:
        for index, relative in enumerate(evidence):
            _require_file(repository, relative, f"candidate.evidence[{index}]", problems)
    manifest_path = repository / "artifacts" / "reviews" / f"issue-{packet.get('issue')}" / "builder" / "evidence-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"evidence manifest is unreadable: {error}")
    else:
        if manifest.get("candidate_commit") != candidate:
            problems.append("evidence manifest candidate does not match")
        root = manifest_path.parent
        for index, entry in enumerate(manifest.get("files", [])):
            _verify_hashed_file(root, entry, f"evidence files[{index}]", problems)
    return problems


def _require_file(root: Path, relative: Any, label: str, problems: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        problems.append(f"{label} must be a non-empty path")
        return None
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        problems.append(f"{label} does not resolve to a file: {relative}")
        return None
    return path


def _verify_hashed_file(root: Path, entry: Any, label: str, problems: list[str]) -> None:
    if not isinstance(entry, dict):
        problems.append(f"{label} must be an object")
        return
    path = _require_file(root, entry.get("path"), f"{label}.path", problems)
    digest = entry.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        problems.append(f"{label}.sha256 must be a SHA-256")
    elif path is not None and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        problems.append(f"{label}.sha256 does not match {entry.get('path')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    args = parser.parse_args()
    problems = validate_packet(args.packet.resolve(), args.repository.resolve(), args.candidate)
    print(json.dumps({"valid": not problems, "candidate": args.candidate, "problems": problems}))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
