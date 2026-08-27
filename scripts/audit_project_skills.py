#!/usr/bin/env python3
"""Validate the repository-local Matt Pocock skill installation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


EXPECTED_SKILL_COUNT = 37
EXPECTED_SOURCE = "mattpocock/skills"
EXPECTED_SOURCE_URL = "https://github.com/mattpocock/skills"
EXPECTED_INSTALLER = {"package": "skills", "version": "1.5.23"}
REQUIRED_SKILLS = {
    "code-review",
    "implement",
    "setup-matt-pocock-skills",
    "tdd",
    "to-spec",
    "to-tickets",
    "triage",
}
HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {path.name}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return value


def _project_relative_path(value: object, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must be a non-empty project-relative path")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{field} must stay inside the project: {value!r}")
        return None
    return Path(*path.parts)


def audit_repository(repo_root: Path) -> list[str]:
    """Return invariant violations for the project-local skill installation."""

    repo_root = repo_root.resolve()
    errors: list[str] = []
    provenance = _load_json(repo_root / "skills-provenance.json", errors)
    lock = _load_json(repo_root / "skills-lock.json", errors)
    if errors:
        return errors

    if provenance.get("source") != EXPECTED_SOURCE:
        errors.append(f"provenance source must be {EXPECTED_SOURCE!r}")
    if provenance.get("source_url") != EXPECTED_SOURCE_URL:
        errors.append(f"provenance source_url must be {EXPECTED_SOURCE_URL!r}")
    source_commit = provenance.get("source_commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        errors.append("provenance source_commit must be a full lowercase Git SHA")
    if provenance.get("installer") != EXPECTED_INSTALLER:
        errors.append("provenance installer must record skills version 1.5.23")
    if provenance.get("scope") != "project":
        errors.append("provenance scope must be 'project'")
    if provenance.get("skill_count") != EXPECTED_SKILL_COUNT:
        errors.append(f"provenance skill_count must be {EXPECTED_SKILL_COUNT}")

    raw_skills = provenance.get("skills")
    if not isinstance(raw_skills, list) or not all(
        isinstance(name, str) and name for name in raw_skills
    ):
        errors.append("provenance skills must be a list of non-empty names")
        return errors

    skills = list(raw_skills)
    skill_set = set(skills)
    if len(skills) != EXPECTED_SKILL_COUNT:
        errors.append(f"provenance must list exactly {EXPECTED_SKILL_COUNT} skills")
    if len(skill_set) != len(skills):
        errors.append("provenance skills must not contain duplicates")
    if skills != sorted(skills):
        errors.append("provenance skills must be sorted")
    missing_required = sorted(REQUIRED_SKILLS - skill_set)
    if missing_required:
        errors.append(f"required skills are missing: {', '.join(missing_required)}")

    lock_skills = lock.get("skills")
    if not isinstance(lock_skills, dict):
        errors.append("skills-lock.json skills must be an object")
        return errors
    if set(lock_skills) != skill_set:
        errors.append("lockfile and provenance skill inventories differ")

    canonical_relative = _project_relative_path(
        provenance.get("canonical_root"), "canonical_root", errors
    )
    compatibility_values = provenance.get("compatibility_links")
    if not isinstance(compatibility_values, list) or not compatibility_values:
        errors.append("compatibility_links must contain at least one project path")
        compatibility_values = []
    compatibility_roots = [
        path
        for index, value in enumerate(compatibility_values)
        if (
            path := _project_relative_path(
                value, f"compatibility_links[{index}]", errors
            )
        )
        is not None
    ]
    if canonical_relative is None:
        return errors

    canonical_root = repo_root / canonical_relative
    if not canonical_root.is_dir():
        errors.append(f"canonical skill root is missing: {canonical_relative}")
    else:
        try:
            canonical_root.resolve(strict=True).relative_to(repo_root)
        except (OSError, ValueError):
            errors.append(f"canonical skill root leaves the project: {canonical_relative}")

    for name in skills:
        if Path(name).name != name:
            errors.append(f"invalid skill name: {name!r}")
            continue
        skill_dir = canonical_root / name
        skill_file = skill_dir / "SKILL.md"
        if skill_dir.is_symlink():
            errors.append(f"canonical skill must not be a symlink: {skill_dir.relative_to(repo_root)}")
        try:
            contents = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {skill_file.relative_to(repo_root)}: {exc}")
        else:
            if not contents.strip():
                errors.append(f"empty skill file: {skill_file.relative_to(repo_root)}")

        entry = lock_skills.get(name)
        if not isinstance(entry, dict):
            errors.append(f"lock entry for {name} must be an object")
            continue
        if entry.get("source") != EXPECTED_SOURCE:
            errors.append(f"lock source for {name} must be {EXPECTED_SOURCE!r}")
        if entry.get("sourceType") != "github":
            errors.append(f"lock sourceType for {name} must be 'github'")
        source_path = entry.get("skillPath")
        parsed_source_path = _project_relative_path(
            source_path, f"lock skillPath for {name}", errors
        )
        if parsed_source_path is not None:
            if parsed_source_path.name != "SKILL.md":
                errors.append(f"lock skillPath for {name} must end in SKILL.md")
            if len(parsed_source_path.parts) < 2 or parsed_source_path.parts[-2] != name:
                errors.append(f"lock skillPath for {name} points to another skill")
        computed_hash = entry.get("computedHash")
        if not isinstance(computed_hash, str) or HASH_PATTERN.fullmatch(computed_hash) is None:
            errors.append(f"lock computedHash for {name} must be 64 lowercase hex digits")

    for relative_root in compatibility_roots:
        link_root = repo_root / relative_root
        if not link_root.is_dir():
            errors.append(f"compatibility root is missing: {relative_root}")
            continue
        try:
            link_root.resolve(strict=True).relative_to(repo_root)
        except (OSError, ValueError):
            errors.append(f"compatibility root leaves the project: {relative_root}")
            continue
        actual_links = {entry.name for entry in link_root.iterdir() if entry.is_symlink()}
        if actual_links != skill_set:
            errors.append(f"compatibility link inventory differs at {relative_root}")
        for name in skills:
            link = link_root / name
            if not link.is_symlink():
                errors.append(f"compatibility entry is not a symlink: {link.relative_to(repo_root)}")
                continue
            expected_target = (canonical_root / name).resolve()
            try:
                actual_target = link.resolve(strict=True)
            except OSError as exc:
                errors.append(f"broken compatibility link {link.relative_to(repo_root)}: {exc}")
                continue
            if actual_target != expected_target:
                errors.append(
                    f"compatibility link leaves its canonical skill: {link.relative_to(repo_root)}"
                )
            try:
                actual_target.relative_to(repo_root)
            except ValueError:
                errors.append(f"compatibility link leaves the project: {link.relative_to(repo_root)}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    errors = audit_repository(repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: {EXPECTED_SKILL_COUNT} project-local skills match provenance, lock, "
        "content, and compatibility-link invariants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
