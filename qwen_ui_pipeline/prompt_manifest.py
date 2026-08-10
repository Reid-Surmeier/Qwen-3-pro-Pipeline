"""Compile structured Edit Briefs into deterministic model instructions."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Mapping


PUBLISHED_MAX_INSTRUCTION_TOKENS = 4_500


class PromptBudgetExceeded(ValueError):
    """Raised before a provider call when an Edit Brief is too large."""


@dataclass(frozen=True)
class PromptMetrics:
    """Conservative prompt-size estimate, not a provider tokenizer result."""

    characters: int
    approximate_tokens: int
    budget_tokens: int
    over_budget: bool


@dataclass(frozen=True)
class CompiledEditBrief:
    prompt: str
    metrics: PromptMetrics


def _quoted_copy(item: Mapping[str, Any]) -> str:
    region = str(item.get("region", "unspecified region")).strip()
    text = str(item.get("text", ""))
    return f'- {region}: "{text}"'


def _bullets(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [f"- {item}" for item in items]


def _region_edit(item: Mapping[str, Any]) -> str:
    name = str(item.get("name", "unnamed region")).strip()
    change = str(item.get("change", "")).strip()
    preserve = item.get("preserve", [])
    lines = [f"- REGION: {name}"]
    if change:
        lines.append(f"  CHANGE: {change}")
    if preserve:
        lines.append(f"  PRESERVE: {'; '.join(str(value) for value in preserve)}")
    return "\n".join(lines)


def compile_edit_brief(
    brief: Mapping[str, Any],
    *,
    budget_tokens: int = PUBLISHED_MAX_INSTRUCTION_TOKENS,
) -> CompiledEditBrief:
    """Compile an Edit Brief without semantically rewriting Exact Copy."""

    invariants = brief.get("preservation_invariants", [])
    exact_copy = brief.get("exact_copy", [])
    regions = brief.get("regions", [])
    sections = [
        ("TASK", [str(brief.get("objective", "")).strip()]),
        ("REFERENCE ROLE", [str(brief.get("reference_role", "")).strip()]),
        ("PRESERVATION INVARIANTS", [f"- {item}" for item in invariants]),
        ("CANVAS AND LAYOUT", _bullets(brief.get("canvas", []))),
        ("REGION EDITS", [_region_edit(item) for item in regions]),
        ("EXACT COPY", [_quoted_copy(item) for item in exact_copy]),
        ("STYLE SYSTEM", _bullets(brief.get("style", []))),
        ("ASSET RULES", _bullets(brief.get("asset_rules", []))),
        ("NEGATIVE CONSTRAINTS", _bullets(brief.get("negative_constraints", []))),
        ("QUALITY GATE", _bullets(brief.get("quality_checks", []))),
    ]

    rendered_sections = []
    for title, lines in sections:
        content = "\n".join(line for line in lines if line)
        if content:
            rendered_sections.append(f"[{title}]\n{content}")
    prompt = "\n\n".join(rendered_sections)

    # Qwen does not publish a client-side tokenizer for this image API. Using
    # three characters per token deliberately overestimates most English UI
    # briefs and leaves visible headroom near the published 4.5k limit.
    approximate_tokens = ceil(len(prompt) / 3)
    metrics = PromptMetrics(
        characters=len(prompt),
        approximate_tokens=approximate_tokens,
        budget_tokens=budget_tokens,
        over_budget=approximate_tokens > budget_tokens,
    )
    if metrics.over_budget:
        raise PromptBudgetExceeded(
            f"Edit Brief is approximately {approximate_tokens} tokens, exceeding "
            f"the published {budget_tokens}-token budget"
        )
    return CompiledEditBrief(prompt=prompt, metrics=metrics)
