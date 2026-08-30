"""Deterministic, fail-closed verdicts for image-79 Play Logs."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "image79-play-log-v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def evaluate_play_log(
    log: Any, evidence_root: Path | str, manifest: Any | None = None
) -> dict[str, Any]:
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

    expected_controls, expected_actions, range_specs = _manifest_requirements(
        manifest, candidate, problems
    )
    source_sha = log.get("source_reference_sha256")
    manifest_sha = manifest.get("reference", {}).get("sha256") if isinstance(manifest, dict) else None
    if not _SHA256.fullmatch(str(source_sha or "")) or source_sha != manifest_sha:
        problems.append("source_reference_sha256 must match the frozen manifest reference")

    required = log.get("required_controls")
    if not isinstance(required, list) or not required or not all(
        _nonempty_string(control_id) for control_id in required
    ):
        problems.append("required_controls must contain non-empty control IDs")
        required = []
    elif len(set(required)) != len(required):
        problems.append("required_controls must not contain duplicates")
    if expected_controls and set(required) != expected_controls:
        problems.append("required_controls do not exactly match the frozen manifest")

    required_actions = log.get("required_actions")
    required_action_keys: list[tuple[str, str, str]] = []
    if not isinstance(required_actions, list) or not required_actions:
        problems.append("required_actions must be a non-empty array")
    else:
        for index, required_action in enumerate(required_actions):
            label = f"required_actions[{index}]"
            if not isinstance(required_action, dict):
                problems.append(f"{label} must be an object")
                continue
            fields = tuple(required_action.get(field) for field in (
                "control_id", "gesture", "window_action"
            ))
            if not all(_nonempty_string(value) for value in fields):
                problems.append(
                    f"{label} must name a control_id, gesture, and window_action"
                )
                continue
            required_action_keys.append(fields)  # type: ignore[arg-type]
        if len(set(required_action_keys)) != len(required_action_keys):
            problems.append("required_actions must not contain duplicates")
    if expected_actions and set(required_action_keys) != expected_actions:
        problems.append("required_actions do not exactly match the frozen manifest")

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
    seen_actions: set[tuple[str, str, str]] = set()
    range_endpoints: dict[str, set[str]] = {control_id: set() for control_id in range_specs}
    verified_frames: set[Path] = set()
    for index, action in enumerate(actions):
        label = f"actions[{index}]"
        if not isinstance(action, dict):
            problems.append(f"{label} must be an object")
            continue
        control_id = action.get("control_id")
        gesture = action.get("gesture")
        window_action = action.get("window_action")
        if not _nonempty_string(control_id):
            problems.append(f"{label}.control_id must be non-empty")
        else:
            seen.add(control_id)
        if not _nonempty_string(gesture):
            problems.append(f"{label}.gesture must be non-empty")
        if not _nonempty_string(window_action):
            problems.append(f"{label}.window_action must be non-empty")
        if all(_nonempty_string(value) for value in (control_id, gesture, window_action)):
            seen_actions.add((control_id, gesture, window_action))
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
        before = frames.get("before") if isinstance(frames, dict) else None
        after = frames.get("after") if isinstance(frames, dict) else None
        if isinstance(before, dict) and isinstance(after, dict) \
                and before.get("sha256") == after.get("sha256"):
            failures.append(f"{label} intended region did not change")
        if window_action == "ToggleValue":
            reversed_frame = frames.get("reversed") if isinstance(frames, dict) else None
            if not isinstance(reversed_frame, dict):
                problems.append(f"{label}.frames.reversed is required for reversible ToggleValue")
            elif isinstance(before, dict) and reversed_frame.get("sha256") != before.get("sha256"):
                failures.append(f"{label} did not reverse to its before frame")
        if window_action == "ToggleMinimized":
            restored = frames.get("restored") if isinstance(frames, dict) else None
            if not isinstance(restored, dict):
                problems.append(f"{label}.frames.restored is required for reversible minimize")
            elif isinstance(before, dict) and restored.get("sha256") != before.get("sha256"):
                failures.append(f"{label} restore did not reproduce its before frame")
        if window_action == "SetRange" and control_id in range_specs \
                and isinstance(action.get("motion_samples"), list):
            samples = [float(value) for value in action["motion_samples"]]
            if samples:
                minimum, maximum = range_specs[control_id]
                if min(samples) <= minimum:
                    range_endpoints[control_id].add("minimum")
                if max(samples) >= maximum:
                    range_endpoints[control_id].add("maximum")
                increasing = all(b >= a for a, b in zip(samples, samples[1:]))
                decreasing = all(b <= a for a, b in zip(samples, samples[1:]))
                if not (increasing or decreasing):
                    failures.append(f"{label} Range samples are not monotonic")

    invariant_frames = log.get("invariant_frames")
    if not isinstance(invariant_frames, dict):
        problems.append("invariant_frames must contain before and after crops")
    else:
        invariant_paths = [
            _verify_frame(invariant_frames.get(role), root,
                          f"invariant_frames.{role}", problems)
            for role in ("before", "after")
        ]
        verified_frames.update(path for path in invariant_paths if path is not None)
        if all(path is not None for path in invariant_paths) \
                and invariant_paths[0].read_bytes() != invariant_paths[1].read_bytes():
            failures.append("declared invariant region changed")
    for control_id, endpoints in range_endpoints.items():
        if endpoints != {"minimum", "maximum"}:
            failures.append(f"{control_id} did not prove both Range endpoints")

    unexercised = [control_id for control_id in required if control_id not in seen]
    unexercised_actions = [
        ":".join(action) for action in required_action_keys if action not in seen_actions
    ]
    if problems:
        verdict = "INVALID"
    elif failures:
        verdict = "FAIL"
    elif unexercised or unexercised_actions:
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "actions": len(actions),
        "frames_verified": len(verified_frames),
        "unexercised": unexercised,
        "unexercised_actions": unexercised_actions,
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


def _manifest_requirements(
    manifest: Any, candidate: Any, problems: list[str]
) -> tuple[set[str], set[tuple[str, str, str]], dict[str, tuple[float, float]]]:
    if not isinstance(manifest, dict):
        problems.append("a frozen ControlSpec manifest is required")
        return set(), set(), {}
    window_id = candidate.get("window_id") if isinstance(candidate, dict) else None
    windows = manifest.get("windows")
    if not isinstance(windows, list):
        problems.append("manifest.windows must be an array")
        return set(), set(), {}
    window = next(
        (entry for entry in windows if isinstance(entry, dict) and entry.get("id") == window_id),
        None,
    )
    if window is None or not isinstance(window.get("controls"), list):
        problems.append("candidate window is absent from the frozen manifest")
        return set(), set(), {}
    controls: set[str] = set()
    actions: set[tuple[str, str, str]] = set()
    range_specs: dict[str, tuple[float, float]] = {}
    for control in window["controls"]:
        if not isinstance(control, dict) or not _nonempty_string(control.get("id")):
            problems.append("manifest contains a malformed control")
            continue
        control_id = control["id"]
        controls.add(control_id)
        value = control.get("value")
        if control.get("type") == "Range" and isinstance(value, dict) \
                and isinstance(value.get("minimum"), (int, float)) \
                and isinstance(value.get("maximum"), (int, float)):
            range_specs[control_id] = (float(value["minimum"]), float(value["maximum"]))
        for binding in control.get("actions", []):
            if not isinstance(binding, dict):
                problems.append(f"manifest action for {control_id} is malformed")
                continue
            key = (control_id, binding.get("gesture"), binding.get("action"))
            if not all(_nonempty_string(value) for value in key):
                problems.append(f"manifest action for {control_id} is malformed")
                continue
            actions.add(key)  # type: ignore[arg-type]
    return controls, actions, range_specs


def _invalid(problem: str) -> dict[str, Any]:
    return {
        "verdict": "INVALID",
        "actions": 0,
        "frames_verified": 0,
        "unexercised": [],
        "unexercised_actions": [],
        "failures": [],
        "problems": [problem],
    }
