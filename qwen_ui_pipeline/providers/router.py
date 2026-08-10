"""Provider selection with a narrow, non-duplicating fallback rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .alibaba import build_alibaba_request
from .openrouter import build_openrouter_request


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    request: dict[str, Any]
    response: dict[str, Any]


def generate_with_provider(
    brief: Mapping[str, Any],
    *,
    reference_urls: Sequence[str],
    openrouter_client: Any = None,
    alibaba_client: Any = None,
) -> ProviderResult:
    """Generate once, falling back only when OpenRouter blocks before billing."""

    provider = str(brief.get("provider", "auto"))
    if provider not in {"auto", "openrouter", "alibaba"}:
        raise ValueError(f"Unknown provider: {provider}")

    if provider in {"auto", "openrouter"}:
        if openrouter_client is None:
            if provider == "openrouter":
                raise ValueError("OpenRouter client is unavailable")
        else:
            request = build_openrouter_request(brief, reference_urls=reference_urls)
            try:
                response = openrouter_client.generate(request)
                return ProviderResult("openrouter", request, response)
            except RuntimeError as error:
                privacy_block = "guardrail restrictions and data policy" in str(error)
                if provider == "openrouter" or not privacy_block:
                    raise

    if alibaba_client is None:
        raise ValueError("Alibaba client is unavailable")
    request = build_alibaba_request(brief, reference_urls=reference_urls)
    response = alibaba_client.generate(request)
    return ProviderResult("alibaba", request, response)
