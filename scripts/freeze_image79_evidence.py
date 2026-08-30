#!/usr/bin/env python3
"""Freeze every file in one image-79 evidence directory by exact candidate SHA."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def freeze(root: Path, repository: Path, candidate: str) -> dict[str, object]:
    root = root.resolve()
    repository = repository.resolve()
    if not root.is_dir() or not root.is_relative_to(repository):
        raise ValueError("evidence root must be a directory inside the repository")
    subprocess.run(
        ["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
        cwd=repository,
        check=True,
    )
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "evidence-manifest.json":
            continue
        files.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    if not files:
        raise ValueError("evidence root contains no files")
    manifest: dict[str, object] = {
        "schema_version": 1,
        "candidate_commit": candidate,
        "files": files,
    }
    (root / "evidence-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    args = parser.parse_args()
    manifest = freeze(args.root, args.repository, args.candidate)
    print(json.dumps({
        "candidate_commit": manifest["candidate_commit"],
        "files": len(manifest["files"]),
        "manifest": str((args.root / "evidence-manifest.json").resolve()),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
