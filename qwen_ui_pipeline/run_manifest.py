"""Fail-closed validator for the versioned generation run manifest.

The manifest is the minimum trustworthy record of one run: identity, commit,
provider evidence, source and output hashes, approvals, and — for Assembly —
deterministic fidelity evidence. Structural checks and semantic invariants
both live here; a manifest that merely *looks* complete must fail visibly.

Usage:
    python -m qwen_ui_pipeline.run_manifest path/to/run-manifest.json
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

MANIFEST_VERSION = "run-manifest-v1"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$")
_CREDENTIAL_VALUE = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|Bearer\s+\S+|AKIA[0-9A-Z]{16}|BWS_[A-Za-z0-9]+)"
)
_CREDENTIAL_KEY = re.compile(r"(api[_-]?key|secret|token|password|credential)", re.IGNORECASE)

ALLOWED_TOP_LEVEL = {
    "manifest_version", "run_id", "kind", "repository_commit", "created_at",
    "status", "provider", "generation", "sources", "outputs", "approvals",
    "region", "fidelity", "extensions",
}
ALLOWED_KINDS = {"render", "assembly"}
ALLOWED_STATUS = {"complete", "incomplete", "rejected"}
ALLOWED_PROVIDERS = {"openrouter", "alibaba"}
ALLOWED_DECISIONS = {"approved", "rejected", "pending"}
MAX_REQUESTED_OUTPUTS = 10  # ADR 0003 per-Issue verification ceiling


def _is_unsafe_path(value: str) -> bool:
    if value.startswith(("/", "~", "\\")) or re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    return ".." in value.split("/")


def _scan_secrets(node: Any, path: str, errors: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if _CREDENTIAL_KEY.search(str(key)):
                errors.append(f"{child}: credential-like key is not allowed in a manifest")
            _scan_secrets(value, child, errors)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _scan_secrets(value, f"{path}[{index}]", errors)
    elif isinstance(node, str) and _CREDENTIAL_VALUE.search(node):
        errors.append(f"{path}: credential-like value is not allowed in a manifest")


def _require(container: dict, key: str, kind, path: str, errors: list[str]):
    value = container.get(key)
    if value is None:
        errors.append(f"{path}.{key}: required field is missing")
        return None
    if kind is not None and not isinstance(value, kind):
        errors.append(f"{path}.{key}: expected {getattr(kind, '__name__', kind)}")
        return None
    return value


def _check_file_record(record: Any, path: str, errors: list[str], *, dimensions: bool) -> None:
    if not isinstance(record, dict):
        errors.append(f"{path}: expected an object")
        return
    file_path = _require(record, "path", str, path, errors)
    if file_path is not None and _is_unsafe_path(file_path):
        errors.append(f"{path}.path: absolute or escaping paths are not allowed; use repo-relative paths")
    digest = _require(record, "sha256", str, path, errors)
    if digest is not None and not _SHA256.fullmatch(digest):
        errors.append(f"{path}.sha256: not a lowercase hex SHA-256")
    if dimensions:
        for key in ("width", "height", "bytes"):
            value = _require(record, key, int, path, errors)
            if value is not None and value <= 0:
                errors.append(f"{path}.{key}: must be a positive integer")


def validate_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["$: manifest must be a JSON object"]

    for key in manifest:
        if key not in ALLOWED_TOP_LEVEL:
            errors.append(f"$.{key}: undeclared field (use extensions for forward compatibility)")

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append(f"$.manifest_version: must be {MANIFEST_VERSION!r}")

    run_id = _require(manifest, "run_id", str, "$", errors)
    if run_id is not None and not _RUN_ID.fullmatch(run_id):
        errors.append("$.run_id: must be kebab-case, 3-81 chars")

    commit = _require(manifest, "repository_commit", str, "$", errors)
    if commit is not None and not _COMMIT.fullmatch(commit):
        errors.append("$.repository_commit: must be a full 40-hex commit SHA")

    created = _require(manifest, "created_at", str, "$", errors)
    if created is not None and not _TIMESTAMP.fullmatch(created):
        errors.append("$.created_at: must be an ISO 8601 timestamp with offset")

    kind = _require(manifest, "kind", str, "$", errors)
    if kind is not None and kind not in ALLOWED_KINDS:
        errors.append(f"$.kind: must be one of {sorted(ALLOWED_KINDS)}")

    status = _require(manifest, "status", str, "$", errors)
    if status is not None and status not in ALLOWED_STATUS:
        errors.append(f"$.status: must be one of {sorted(ALLOWED_STATUS)}")

    sources = _require(manifest, "sources", list, "$", errors)
    if sources is not None:
        if not sources:
            errors.append("$.sources: at least one source identity is required")
        for index, source in enumerate(sources):
            _check_file_record(source, f"$.sources[{index}]", errors, dimensions=False)
            if isinstance(source, dict) and not source.get("role"):
                errors.append(f"$.sources[{index}].role: required field is missing")

    outputs = _require(manifest, "outputs", list, "$", errors)
    output_hashes: set[str] = set()
    if outputs is not None:
        for index, output in enumerate(outputs):
            _check_file_record(output, f"$.outputs[{index}]", errors, dimensions=True)
            if isinstance(output, dict) and isinstance(output.get("sha256"), str):
                output_hashes.add(output["sha256"])

    approvals = _require(manifest, "approvals", list, "$", errors)
    if approvals is not None:
        for index, approval in enumerate(approvals):
            path = f"$.approvals[{index}]"
            if not isinstance(approval, dict):
                errors.append(f"{path}: expected an object")
                continue
            decision = _require(approval, "decision", str, path, errors)
            if decision is not None and decision not in ALLOWED_DECISIONS:
                errors.append(f"{path}.decision: must be one of {sorted(ALLOWED_DECISIONS)}")
            _require(approval, "actor", str, path, errors)
            timestamp = _require(approval, "timestamp", str, path, errors)
            if timestamp is not None and not _TIMESTAMP.fullmatch(timestamp):
                errors.append(f"{path}.timestamp: must be an ISO 8601 timestamp with offset")
            if decision == "approved":
                approved = _require(approval, "approved_sha256", str, path, errors)
                if approved is not None:
                    if not _SHA256.fullmatch(approved):
                        errors.append(f"{path}.approved_sha256: not a lowercase hex SHA-256")
                    elif output_hashes and approved not in output_hashes:
                        errors.append(f"{path}.approved_sha256: does not match any output sha256")

    if kind == "render":
        provider = _require(manifest, "provider", dict, "$", errors)
        if provider is not None:
            name = _require(provider, "name", str, "$.provider", errors)
            if name is not None and name not in ALLOWED_PROVIDERS:
                errors.append(f"$.provider.name: must be one of {sorted(ALLOWED_PROVIDERS)}")
            _require(provider, "model", str, "$.provider", errors)
            _require(provider, "prompt_id", str, "$.provider", errors)
            requested = _require(provider, "requested_outputs", int, "$.provider", errors)
            completed = _require(provider, "completed_outputs", int, "$.provider", errors)
            if requested is not None:
                if not 1 <= requested <= MAX_REQUESTED_OUTPUTS:
                    errors.append(
                        f"$.provider.requested_outputs: must be 1-{MAX_REQUESTED_OUTPUTS} (ADR 0003)"
                    )
                if completed is not None and completed > requested:
                    errors.append("$.provider.completed_outputs: cannot exceed requested_outputs")
            if completed is not None and outputs is not None and status == "complete":
                if completed != len(outputs):
                    errors.append(
                        "$.provider.completed_outputs: must equal len(outputs) for a complete run"
                    )
        generation = _require(manifest, "generation", dict, "$", errors)
        if generation is not None:
            _require(generation, "seed", int, "$.generation", errors)
        if "fidelity" in manifest:
            errors.append(
                "$.fidelity: deterministic fidelity evidence belongs to assembly manifests, "
                "not model-generation records"
            )
    elif kind == "assembly":
        for forbidden in ("provider", "generation"):
            if forbidden in manifest:
                errors.append(
                    f"$.{forbidden}: assembly manifests record deterministic composition, "
                    "not model-generation metadata"
                )
        region = _require(manifest, "region", dict, "$", errors)
        if region is not None:
            for key in ("x", "y", "width", "height"):
                value = _require(region, key, int, "$.region", errors)
                if value is not None and key in ("width", "height") and value <= 0:
                    errors.append(f"$.region.{key}: must be a positive integer")
        fidelity = _require(manifest, "fidelity", dict, "$", errors)
        if fidelity is not None:
            changed = _require(
                fidelity, "outside_region_changed_pixels", int, "$.fidelity", errors
            )
            if changed is not None and changed < 0:
                errors.append("$.fidelity.outside_region_changed_pixels: cannot be negative")

    if status == "complete" and isinstance(outputs, list) and not outputs:
        errors.append("$.outputs: a complete run must record at least one output")

    _scan_secrets(manifest, "$", errors)
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m qwen_ui_pipeline.run_manifest <manifest.json>", file=sys.stderr)
        return 2
    try:
        manifest = json.loads(open(argv[0], encoding="utf-8").read())
    except (OSError, json.JSONDecodeError) as error:
        print(f"$: unreadable manifest: {error}", file=sys.stderr)
        return 1
    errors = validate_manifest(manifest)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"valid {MANIFEST_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
