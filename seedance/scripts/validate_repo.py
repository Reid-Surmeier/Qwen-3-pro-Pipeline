from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    required = [
        "README.md",
        "AGENTS.md",
        "CONTEXT.md",
        "pyproject.toml",
        "schemas/motion-brief.schema.json",
        "templates/favicon-loop.json",
        "workflows/icon-animation-plan.json",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")
    for path in [root / "templates/favicon-loop.json", root / "workflows/icon-animation-plan.json"]:
        json.loads(path.read_text())
    print("Repository structure and JSON assets are valid")


if __name__ == "__main__":
    main()
