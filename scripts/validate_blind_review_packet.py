#!/usr/bin/env python3
"""Fail-closed validation for an exact-SHA blind artifact-review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
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
    for relative in (
        "godot/data/image-79-control-spec.json",
        "godot/image79_options.tscn",
        "godot/control_library/control_window.gd",
    ):
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{candidate}:{relative}"],
            cwd=repository, capture_output=True, check=False,
        )
        if result.returncode != 0:
            problems.append(f"candidate snapshot is missing {relative}")
    _require_file(repository, packet.get("acceptance_contract"), "acceptance_contract", problems)
    for index, reference in enumerate(packet.get("references", [])):
        _verify_hashed_file(repository, reference, f"references[{index}]", problems)
    candidate_packet = packet.get("candidate", {})
    evidence = candidate_packet.get("evidence", []) if isinstance(candidate_packet, dict) else []
    if not isinstance(evidence, list) or not evidence:
        problems.append("candidate.evidence must be a non-empty array")
    else:
        for index, relative in enumerate(evidence):
            _require_file(repository, relative, f"candidate.evidence[{index}]", problems)
    manifest_relatives = candidate_packet.get("evidence_manifests") \
        if isinstance(candidate_packet, dict) else None
    if manifest_relatives is None:
        manifest_relatives = [
            f"artifacts/reviews/issue-{packet.get('issue')}/builder/evidence-manifest.json"
        ]
    if not isinstance(manifest_relatives, list) or not manifest_relatives or not all(
        isinstance(relative, str) and relative for relative in manifest_relatives
    ):
        problems.append("candidate.evidence_manifests must contain non-empty paths")
        manifest_relatives = []
    locked_paths: set[Path] = set()
    for index, relative in enumerate(manifest_relatives):
        manifest_path = _require_file(
            repository, relative, f"candidate.evidence_manifests[{index}]", problems
        )
        if manifest_path is not None:
            locked_paths.update(
                _validate_evidence_manifest(manifest_path, repository, candidate, problems)
            )
    for index, relative in enumerate(evidence if isinstance(evidence, list) else []):
        evidence_path = _require_file(
            repository, relative, f"candidate.evidence[{index}]", problems
        )
        if evidence_path is not None and evidence_path not in locked_paths:
            problems.append(f"candidate.evidence[{index}] is not hash-locked by an evidence manifest")
    return problems


def _validate_evidence_manifest(
    manifest_path: Path, repository: Path, candidate: str, problems: list[str]
) -> set[Path]:
    locked_paths: set[Path] = set()
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"evidence manifest is unreadable: {error}")
    else:
        if manifest.get("candidate_commit") != candidate:
            problems.append("evidence manifest candidate does not match")
        root = manifest_path.parent
        files = manifest.get("files")
        if not isinstance(files, list) or not files:
            problems.append("evidence manifest files must be a non-empty array")
            files = []
        for index, entry in enumerate(files):
            _verify_hashed_file(root, entry, f"evidence files[{index}]", problems)
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                locked = (root / entry["path"]).resolve()
                if locked.is_relative_to(root.resolve()):
                    locked_paths.add(locked)
        play_log_path = root / "play-log.json"
        try:
            play_log = json.loads(play_log_path.read_text())
            manifest_bytes = subprocess.run(
                ["git", "show", f"{candidate}:godot/data/image-79-control-spec.json"],
                cwd=repository, capture_output=True, check=True,
            ).stdout
            control_manifest = json.loads(manifest_bytes)
            if str(repository) not in sys.path:
                sys.path.insert(0, str(repository))
            from qwen_ui_pipeline.play_log import evaluate_play_log
            verdict = evaluate_play_log(play_log, root, control_manifest)
            if verdict.get("verdict") != "PASS":
                problems.append(f"committed Play Log is not reproducible: {verdict}")
        except (OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
            problems.append(f"committed Play Log cannot be verified: {error}")
    return locked_paths


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
    parser.add_argument("packet_positional", nargs="?", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--candidate", "--expect-sha", dest="candidate", required=True)
    parser.add_argument("--repository", "--repo", dest="repository", type=Path,
                        default=Path.cwd())
    args = parser.parse_args()
    packet = args.packet or args.packet_positional
    if packet is None:
        parser.error("--packet is required")
    problems = validate_packet(packet.resolve(), args.repository.resolve(), args.candidate)
    print(json.dumps({"valid": not problems, "candidate": args.candidate, "problems": problems}))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
