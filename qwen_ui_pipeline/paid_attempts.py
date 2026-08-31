"""Crash-safe local attempt records for explicitly approved paid runs."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterable


class PaidAttemptLedger:
    """Write a durable sentinel before a paid provider request can start."""

    def __init__(self, run_directory: Path):
        self.run_directory = run_directory

    def evidence_paths(self, slugs: Iterable[str]) -> list[Path]:
        paths = [self.run_directory / "comparison.json"]
        for slug in slugs:
            paths.extend(
                (
                    self.run_directory / slug / "attempt.json",
                    self.run_directory / slug / "run.json",
                )
            )
        return paths

    def preparation_paths(self, slugs: Iterable[str]) -> list[Path]:
        return [
            self.run_directory / "brief.json",
            self.run_directory / "legacy.request.json",
            self.run_directory / "partner.request.json",
            self.run_directory / "plan.json",
            *self.evidence_paths(slugs),
        ]

    def _assert_absent(self, paths: Iterable[Path], action: str) -> None:
        existing = [path for path in paths if path.exists()]
        if existing:
            relative = ", ".join(str(path.relative_to(self.run_directory)) for path in existing)
            raise RuntimeError(
                f"Issue 32 evidence already exists ({relative}); refusing to {action}"
            )

    def assert_unprepared(self, slugs: Iterable[str]) -> None:
        self._assert_absent(self.preparation_paths(slugs), "overwrite preparation")

    def assert_unexecuted(self, slugs: Iterable[str]) -> None:
        self._assert_absent(self.evidence_paths(slugs), "submit another paid request")

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def begin(
        self,
        slug: str,
        *,
        request_sha256: str,
        requested_outputs: int,
    ) -> dict[str, Any]:
        path = self.run_directory / slug / "attempt.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "attempt_id": str(uuid.uuid4()),
            "status": "submitting",
            "request_sha256": request_sha256,
            "requested_outputs": requested_outputs,
            "retry_allowed": False,
        }
        data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self._fsync_directory(self.run_directory)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise RuntimeError(
                f"Attempt evidence already exists for {slug}; refusing to resubmit"
            ) from error
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(descriptor)
        self._fsync_directory(path.parent)
        return record

    def update(self, slug: str, **changes: Any) -> dict[str, Any]:
        path = self.run_directory / slug / "attempt.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update(changes)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        self._fsync_directory(path.parent)
        return record
