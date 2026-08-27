from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def create_run(root: Path, slug: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}-{slug}"
    path.mkdir(parents=True, exist_ok=False)
    for child in ("inputs", "outputs", "verification"):
        (path / child).mkdir()
    return path


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def read_job_id(run: Path) -> str:
    payload = json.loads((run / "job.json").read_text())
    return payload.get("id") or payload.get("data", {}).get("id")
