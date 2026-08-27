"""Pure validation and translation for Partner-compatible Qwen controls."""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence

from .providers.alibaba import MODEL_NAMES, SIZES


PROVIDERS = ("openrouter", "alibaba")
MODELS = ("qwen-image-3.0-pro", "qwen-image-3.0")
SIZE_MODES = ("auto", "match input", "custom")
MAX_REFERENCE_IMAGES = 3
MIN_AREA = 512 * 512
ALIBABA_MAX_AREA = 2048 * 2048
MAX_ASPECT = 8
MAX_SEED = 2_147_483_647

_IMAGE_REF_RE = re.compile(r"@image(?P<idx>\d*)(?!\w)", re.IGNORECASE | re.ASCII)
_OPENROUTER_DIMENSIONS = {
    tuple(int(value) for value in size.split("*")): (resolution, aspect_ratio)
    for resolution, sizes in SIZES.items()
    for aspect_ratio, size in sizes.items()
}
_OPENROUTER_MODELS = {
    "qwen-image-3.0-pro": "qwen/qwen-image-3-pro",
    "qwen-image-3.0": "qwen/qwen-image-3",
    "qwen/qwen-image-3-pro": "qwen/qwen-image-3-pro",
    "qwen/qwen-image-3": "qwen/qwen-image-3",
}


def resolve_image_references(prompt: str, total_images: int) -> str:
    """Resolve Partner-style ``@ImageN`` tags against visible ordered inputs."""

    parts: list[str] = []
    position = 0
    previous_end = -1
    for match in _IMAGE_REF_RE.finditer(prompt):
        start = match.start()
        if (
            start > 0
            and start != previous_end
            and (prompt[start - 1].isalnum() or prompt[start - 1] == "_")
        ):
            continue
        index = int(match.group("idx") or 1)
        if not 1 <= index <= total_images:
            raise ValueError(
                f"The prompt references @Image{index}, but only {total_images} "
                "reference images are visibly connected."
            )
        parts.append(prompt[position:start])
        parts.append(f"Image {index}")
        position = match.end()
        previous_end = match.end()
    parts.append(prompt[position:])
    return "".join(parts)


def _validate_provider_controls(
    *,
    provider: str,
    model: str,
    prompt: str,
    negative_prompt: str,
    count: int,
    seed: int,
    prompt_extend: bool,
    watermark: bool,
) -> None:
    if provider not in PROVIDERS:
        raise ValueError("Partner-compatible nodes require openrouter or alibaba")
    if provider == "openrouter" and model not in _OPENROUTER_MODELS:
        raise ValueError(f"OpenRouter does not support model {model}")
    if provider == "alibaba" and model not in MODEL_NAMES:
        raise ValueError(f"Alibaba does not support model {model}")
    if not prompt.strip():
        raise ValueError("Prompt must not be empty")
    if not 1 <= count <= 6:
        raise ValueError("Output count must be between 1 and 6")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"Seed must be between 0 and {MAX_SEED}")
    if provider == "openrouter":
        if negative_prompt.strip():
            raise ValueError("OpenRouter does not support negative_prompt")
        if prompt_extend:
            raise ValueError("OpenRouter does not support prompt_extend")
        if watermark:
            raise ValueError("OpenRouter does not support watermark")


def _validate_dimensions(width: int, height: int, *, max_area: int) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    area = width * height
    if not MIN_AREA <= area <= max_area:
        raise ValueError(
            f"Image area must be between {MIN_AREA} and {max_area} pixels; "
            f"got {width}x{height}."
        )
    if width > MAX_ASPECT * height or height > MAX_ASPECT * width:
        raise ValueError(f"Aspect ratio must be between 1:8 and 8:1; got {width}x{height}.")


def _fit_alibaba_dimensions(width: int, height: int) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        raise ValueError("Reference dimensions must be positive")
    if width > MAX_ASPECT * height:
        height = math.ceil(width / MAX_ASPECT)
    elif height > MAX_ASPECT * width:
        width = math.ceil(height / MAX_ASPECT)
    area = width * height
    if area < MIN_AREA:
        scale = math.sqrt(MIN_AREA / area)
        width, height = math.ceil(width * scale), math.ceil(height * scale)
    elif area > ALIBABA_MAX_AREA:
        scale = math.sqrt(ALIBABA_MAX_AREA / area)
        width, height = math.floor(width * scale), math.floor(height * scale)
    width = min(width, MAX_ASPECT * height)
    height = min(height, MAX_ASPECT * width)
    _validate_dimensions(width, height, max_area=ALIBABA_MAX_AREA)
    return width, height


def _openrouter_size(width: int, height: int) -> tuple[str, str]:
    try:
        return _OPENROUTER_DIMENSIONS[(width, height)]
    except KeyError as error:
        raise ValueError(
            f"{width}x{height} is not a supported OpenRouter size; choose one of "
            "the advertised Qwen 1K/2K resolution and aspect-ratio combinations"
        ) from error


def _base_brief(
    *,
    provider: str,
    model: str,
    prompt: str,
    negative_prompt: str,
    count: int,
    seed: int,
    prompt_extend: bool,
    watermark: bool,
) -> dict[str, Any]:
    _validate_provider_controls(
        provider=provider,
        model=model,
        prompt=prompt,
        negative_prompt=negative_prompt,
        count=count,
        seed=seed,
        prompt_extend=prompt_extend,
        watermark=watermark,
    )
    return {
        "provider": provider,
        "model": _OPENROUTER_MODELS[model] if provider == "openrouter" else model,
        "objective": prompt.strip(),
        "negative_prompt": negative_prompt,
        "output": {
            "count": count,
            "seed": seed,
            "prompt_extend": prompt_extend,
            "watermark": watermark,
        },
        "interface": {"name": "partner-compatible", "version": 1},
    }


def build_partner_text_brief(
    *,
    provider: str,
    model: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    count: int,
    seed: int,
    prompt_extend: bool,
    watermark: bool,
) -> dict[str, Any]:
    """Build a validated Text-to-Image Edit Brief before any provider call."""

    brief = _base_brief(
        provider=provider,
        model=model,
        prompt=prompt,
        negative_prompt=negative_prompt,
        count=count,
        seed=seed,
        prompt_extend=prompt_extend,
        watermark=watermark,
    )
    output = brief["output"]
    output["size_mode"] = "custom"
    if provider == "openrouter":
        resolution, aspect_ratio = _openrouter_size(width, height)
        output["resolution"] = resolution
        output["aspect_ratio"] = aspect_ratio
    else:
        _validate_dimensions(width, height, max_area=ALIBABA_MAX_AREA)
        output["size"] = f"{width}*{height}"
    output["requested_dimensions"] = {"width": width, "height": height}
    return brief


def build_partner_edit_brief(
    *,
    provider: str,
    model: str,
    prompt: str,
    negative_prompt: str,
    size_mode: str,
    width: int,
    height: int,
    count: int,
    seed: int,
    prompt_extend: bool,
    watermark: bool,
    reference_dimensions: Sequence[tuple[int, int]],
) -> dict[str, Any]:
    """Build a validated three-reference Edit Brief before any provider call."""

    if not 1 <= len(reference_dimensions) <= MAX_REFERENCE_IMAGES:
        raise ValueError(
            f"Partner-compatible edit nodes require 1 to a maximum of "
            f"{MAX_REFERENCE_IMAGES} reference images"
        )
    if size_mode not in SIZE_MODES:
        raise ValueError(f"Unknown size mode: {size_mode}")
    resolved_prompt = resolve_image_references(prompt, len(reference_dimensions))
    brief = _base_brief(
        provider=provider,
        model=model,
        prompt=resolved_prompt,
        negative_prompt=negative_prompt,
        count=count,
        seed=seed,
        prompt_extend=prompt_extend,
        watermark=watermark,
    )
    output = brief["output"]
    output["size_mode"] = size_mode
    if size_mode == "auto":
        if provider == "openrouter":
            raise ValueError("OpenRouter does not support size_mode auto")
    else:
        requested_width, requested_height = (
            reference_dimensions[0] if size_mode == "match input" else (width, height)
        )
        output["requested_dimensions"] = {
            "width": requested_width,
            "height": requested_height,
        }
        if provider == "openrouter":
            resolution, aspect_ratio = _openrouter_size(
                requested_width, requested_height
            )
            output["resolution"] = resolution
            output["aspect_ratio"] = aspect_ratio
        else:
            if size_mode == "match input":
                requested_width, requested_height = _fit_alibaba_dimensions(
                    requested_width, requested_height
                )
            else:
                _validate_dimensions(
                    requested_width,
                    requested_height,
                    max_area=ALIBABA_MAX_AREA,
                )
            output["size"] = f"{requested_width}*{requested_height}"
    brief["references"] = [
        {
            "role": f"image_{index}",
            "effective_index": index,
            "width": dimensions[0],
            "height": dimensions[1],
        }
        for index, dimensions in enumerate(reference_dimensions, start=1)
    ]
    return brief


def partner_capabilities() -> Mapping[str, Mapping[str, Any]]:
    """Return the fixed capability record used for preflight and audit."""

    return {
        "openrouter": {
            "references": 3,
            "negative_prompt": False,
            "prompt_extend": False,
            "watermark": False,
            "size_modes": ["match input", "custom"],
        },
        "alibaba": {
            "references": 3,
            "negative_prompt": True,
            "prompt_extend": True,
            "watermark": True,
            "size_modes": list(SIZE_MODES),
        },
    }
