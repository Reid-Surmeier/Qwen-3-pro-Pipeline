"""Assemble the blind workspace a reviewer is allowed to see.

Blindness is structural: the workspace is extracted from the candidate SHA
with `git archive`, so it carries no `.git`, no history, no PR narrative,
and no working-tree drift. Its contents are exactly the paths the packet
names — contract, references, evidence — plus any runtime tree passed with
`--include` (the launchable candidate). Anything else the repository holds
stays invisible to the reviewer.

Usage:
    python scripts/blind_review/build_workspace.py \
        --packet artifacts/reviews/issue-86/packet.json \
        --repo . --out /tmp/blind-workspace \
        [--include godot]

Writes the workspace plus `workspace-manifest.json` (paths and sha256 of
every file delivered) and prints the manifest path. Exits 1 on any failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


class WorkspaceError(RuntimeError):
    """The blind workspace cannot be assembled faithfully."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def packet_paths(packet: dict) -> list[str]:
    """Every repository path the packet itself names."""
    paths = [packet["acceptance_contract"]]
    paths.extend(reference["path"] for reference in packet["references"])
    paths.extend(packet["candidate"]["evidence"])
    return paths


def extract_at_sha(repo: Path, sha: str, paths: list[str], destination: Path) -> None:
    """Extract `paths` as they exist at `sha` into `destination` via git archive."""
    with tempfile.NamedTemporaryFile(suffix=".tar") as archive:
        result = subprocess.run(
            ["git", "archive", "--format=tar", f"--output={archive.name}", sha, "--", *paths],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise WorkspaceError(f"git archive failed: {result.stderr.strip()}")
        with tarfile.open(archive.name) as tar:
            tar.extractall(destination, filter="data")


def build_workspace(
    packet_path: Path, repo: Path, out: Path, include: list[str]
) -> Path:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    sha = packet["candidate_commit"]

    if out.exists() and any(out.iterdir()):
        raise WorkspaceError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    extract_at_sha(repo, sha, packet_paths(packet) + list(include), out)

    delivered = sorted(
        str(path.relative_to(out)) for path in out.rglob("*") if path.is_file()
    )
    if not delivered:
        raise WorkspaceError("workspace is empty; nothing was extracted")

    for reference in packet["references"]:
        target = out / reference["path"]
        if not target.is_file():
            raise WorkspaceError(f"reference missing from candidate tree: {reference['path']}")
        if sha256_of(target) != reference["sha256"]:
            raise WorkspaceError(f"reference hash mismatch at {sha}: {reference['path']}")

    packet_copy = out / "packet.json"
    packet_copy.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    manifest = {
        "candidate_commit": sha,
        "files": [
            {"path": path, "sha256": sha256_of(out / path)} for path in delivered
        ],
    }
    manifest_path = out / "workspace-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Additional repository path to extract at the candidate SHA (repeatable); use for the launchable runtime tree.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_workspace(args.packet, args.repo.resolve(), args.out, args.include)
    except (WorkspaceError, KeyError, json.JSONDecodeError, FileNotFoundError) as error:
        print(json.dumps({"status": "error", "detail": str(error)}))
        return 1
    print(json.dumps({"status": "built", "manifest": str(manifest)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
