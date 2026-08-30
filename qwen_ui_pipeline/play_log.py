"""Deterministic, fail-closed verdicts for image-79 Play Logs."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "image79-play-log-v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def evaluate_play_log(log: Any, evidence_root: Path | str) -> dict[str, Any]:
    """Return PASS, FAIL, INCOMPLETE, or INVALID without trusting log claims."""
    problems: list[str] = []
    failures: list[str] = []
    root = Path(evidence_root).resolve()

    if not isinstance(log, dict):
        return _invalid("play log root must be an object")
    if log.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION}")

    candidate = log.get("candidate")
    if not isinstance(candidate, dict):
        problems.append("candidate must be an object")
    else:
        if not isinstance(candidate.get("issue"), int) or candidate["issue"] <= 0:
            problems.append("candidate.issue must be a positive integer")
        if not _COMMIT_SHA.fullmatch(str(candidate.get("commit_sha", ""))):
            problems.append("candidate.commit_sha must be a 40-character lowercase SHA")
        if not _nonempty_string(candidate.get("window_id")):
            problems.append("candidate.window_id must be a non-empty string")

    required = log.get("required_controls")
    if not isinstance(required, list) or not required or not all(
        _nonempty_string(control_id) for control_id in required
    ):
        problems.append("required_controls must contain non-empty control IDs")
        required = []
    elif len(set(required)) != len(required):
        problems.append("required_controls must not contain duplicates")

    console_errors = log.get("console_errors")
    if not isinstance(console_errors, list) or not all(
        isinstance(entry, str) for entry in console_errors
    ):
        problems.append("console_errors must be an array of strings")
        console_errors = []
    elif console_errors:
        failures.extend(f"console error: {entry}" for entry in console_errors)

    actions = log.get("actions")
    if not isinstance(actions, list) or not actions:
        problems.append("actions must be a non-empty array")
        actions = []

    seen: set[str] = set()
    verified_frames: set[Path] = set()
    for index, action in enumerate(actions):
        label = f"actions[{index}]"
        if not isinstance(action, dict):
            problems.append(f"{label} must be an object")
            continue
        control_id = action.get("control_id")
        gesture = action.get("gesture")
        if not _nonempty_string(control_id):
            problems.append(f"{label}.control_id must be non-empty")
        else:
            seen.add(control_id)
        if not _nonempty_string(gesture):
            problems.append(f"{label}.gesture must be non-empty")
        for field in ("expected", "observed"):
            if not _nonempty_string(action.get(field)):
                problems.append(f"{label}.{field} must be non-empty")
        for field in ("responsive", "matches_expected"):
            if not isinstance(action.get(field), bool):
                problems.append(f"{label}.{field} must be boolean")
            elif action[field] is False:
                failures.append(f"{label} {field} is false")

        assertions = action.get("assertions")
        if not isinstance(assertions, dict) or not assertions or not all(
            _nonempty_string(name) and isinstance(value, bool)
            for name, value in assertions.items()
        ):
            problems.append(f"{label}.assertions must contain named boolean checks")
        else:
            failures.extend(
                f"{label} assertion failed: {name}"
                for name, value in assertions.items()
                if not value
            )

        frames = action.get("frames")
        required_roles = {"before", "after"}
        if gesture == "Drag":
            required_roles.add("mid")
            samples = action.get("motion_samples")
            if not isinstance(samples, list) or len(samples) < 30 or not all(
                isinstance(sample, (int, float)) and not isinstance(sample, bool)
                for sample in samples
            ):
                problems.append(f"{label} Drag requires at least 30 motion samples")
        if not isinstance(frames, dict):
            problems.append(f"{label}.frames must be an object")
            continue
        for role in sorted(required_roles):
            if role not in frames:
                problems.append(f"{label}.frames.{role} is required")
        for role, frame in frames.items():
            frame_label = f"{label}.frames.{role}"
            verified = _verify_frame(frame, root, frame_label, problems)
            if verified is not None:
                verified_frames.add(verified)

    unexercised = [control_id for control_id in required if control_id not in seen]
    if problems:
        verdict = "INVALID"
    elif failures:
        verdict = "FAIL"
    elif unexercised:
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "actions": len(actions),
        "frames_verified": len(verified_frames),
        "unexercised": unexercised,
        "failures": failures,
        "problems": problems,
    }


def _verify_frame(
    frame: Any, root: Path, label: str, problems: list[str]
) -> Path | None:
    if not isinstance(frame, dict):
        problems.append(f"{label} must be an object")
        return None
    relative = frame.get("path")
    expected_sha = str(frame.get("sha256", ""))
    if not _nonempty_string(relative):
        problems.append(f"{label}.path must be non-empty")
        return None
    if not _SHA256.fullmatch(expected_sha):
        problems.append(f"{label}.sha256 must be a lowercase SHA-256")
        return None
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        problems.append(f"{label}.path leaves the evidence root")
        return None
    if not path.is_file():
        problems.append(f"{label}.path does not exist: {relative}")
        return None
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        problems.append(f"{label}.sha256 does not match {relative}")
        return None
    return path


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _invalid(problem: str) -> dict[str, Any]:
    return {
        "verdict": "INVALID",
        "actions": 0,
        "frames_verified": 0,
        "unexercised": [],
        "failures": [],
        "problems": [problem],
    }
