from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS = (
    "source_authority",
    "style_lock",
    "motion",
    "camera",
    "background",
    "negative_constraints",
)


def load_brief(path: Path) -> dict[str, Any]:
    brief = json.loads(path.read_text())
    missing = [section for section in REQUIRED_SECTIONS if not brief.get(section)]
    if missing:
        raise ValueError(f"Brief is missing required sections: {', '.join(missing)}")
    return brief


def compile_prompt(brief: dict[str, Any]) -> str:
    """Compile a stable, inspectable prompt without hiding requirements in prose."""
    blocks = [
        ("SOURCE AUTHORITY", brief["source_authority"]),
        ("LOCKED STYLE", brief["style_lock"]),
        ("MOTION", brief["motion"]),
        ("CAMERA", brief["camera"]),
        ("BACKGROUND / MATTE", brief["background"]),
        ("MUST NOT", brief["negative_constraints"]),
    ]
    if brief.get("timing"):
        blocks.insert(3, ("TIMING", brief["timing"]))
    return "\n\n".join(f"{title}:\n{_render(value)}" for title, value in blocks)


def _render(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"- {key}: {item}" for key, item in value.items())
    return str(value)
