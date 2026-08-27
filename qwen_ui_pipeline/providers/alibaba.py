"""Alibaba Model Studio adapter for Qwen Image 3."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping, Sequence

from ..prompt_manifest import compile_edit_brief


MODEL_NAMES = {
    "qwen/qwen-image-3-pro": "qwen-image-3.0-pro",
    "qwen/qwen-image-3": "qwen-image-3.0",
    "qwen-image-3.0-pro": "qwen-image-3.0-pro",
    "qwen-image-3.0": "qwen-image-3.0",
}

SIZES = {
    "1K": {
        "1:1": "1024*1024", "1:2": "720*1440", "1:4": "512*2048",
        "2:1": "1440*720", "2:3": "832*1248", "3:2": "1248*832",
        "3:4": "864*1152", "4:1": "2048*512", "4:3": "1152*864",
        "4:5": "896*1120", "5:4": "1120*896", "9:16": "720*1280",
        "16:9": "1280*720",
    },
    "2K": {
        "1:1": "2048*2048", "1:2": "1024*2048", "1:4": "512*2048",
        "2:1": "2048*1024", "2:3": "1344*2016", "3:2": "2016*1344",
        "3:4": "1536*2048", "4:1": "2048*512", "4:3": "2048*1536",
        "4:5": "1600*2000", "5:4": "2000*1600", "9:16": "1152*2048",
        "16:9": "2048*1152",
    },
}

DEFAULT_ENDPOINT = (
    "https://dashscope-intl.aliyuncs.com"
    "/api/v1/services/aigc/multimodal-generation/generation"
)
MAX_SEED = 2_147_483_647


def _resolve_size(
    output: Mapping[str, Any], *, allow_partner_auto: bool = False
) -> str | None:
    if allow_partner_auto and output.get("size_mode") == "auto":
        return None
    explicit_size = output.get("size")
    if explicit_size is not None:
        match = re.fullmatch(r"([1-9][0-9]*)\*([1-9][0-9]*)", str(explicit_size))
        if match is None:
            raise ValueError("Alibaba output size must use width*height")
        width, height = (int(value) for value in match.groups())
        pixel_area = width * height
        if not 512 * 512 <= pixel_area <= 2048 * 2048:
            raise ValueError("Alibaba output size pixel area must be 512*512 to 2048*2048")
        aspect_ratio = width / height
        if not 1 / 8 <= aspect_ratio <= 8:
            raise ValueError("Alibaba output size aspect ratio must be between 1:8 and 8:1")
        return str(explicit_size)

    resolution = str(output.get("resolution", "2K"))
    aspect_ratio = str(output.get("aspect_ratio", "16:9"))
    try:
        return SIZES[resolution][aspect_ratio]
    except KeyError as error:
        raise ValueError(
            f"Unsupported Alibaba resolution/aspect ratio: {resolution} {aspect_ratio}"
        ) from error


class AlibabaImageClient:
    """Call Qwen Image 3 and immediately resolve its expiring output URLs."""

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ):
        if not api_key:
            raise ValueError("Alibaba Model Studio API key is required")
        self._api_key = api_key
        self._endpoint = endpoint
        self._opener = opener

    def generate(self, request_body: Mapping[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(dict(request_body)).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "qwen-ui-pipeline/0.1",
            },
        )
        try:
            with self._opener(request, timeout=180) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = ""
            try:
                error_payload = json.loads(error.read(8192))
                detail = str(error_payload.get("message", "")).strip()
            except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
                pass
            suffix = f": {detail}" if detail else ""
            raise RuntimeError(
                f"Alibaba Model Studio returned HTTP {error.code}{suffix}"
            ) from error
        if not isinstance(payload, dict):
            raise RuntimeError("Alibaba Model Studio returned a non-object response")

        result_urls = []
        output = payload.get("output", {})
        for choice in output.get("choices", []) if isinstance(output, dict) else []:
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            for item in message.get("content", []) if isinstance(message, dict) else []:
                if isinstance(item, dict) and isinstance(item.get("image"), str):
                    result_urls.append(item["image"])
        if not result_urls:
            raise RuntimeError("Alibaba Model Studio response did not contain an image URL")

        images = []
        for url in result_urls:
            with self._opener(url, timeout=60) as response:
                image_bytes = response.read()
                media_type = response.headers.get("Content-Type", "image/png").split(";", 1)[0]
            images.append(
                {
                    "b64_json": base64.b64encode(image_bytes).decode("ascii"),
                    "media_type": media_type,
                }
            )
        return {
            "data": images,
            "usage": payload.get("usage", {}),
            "request_id": payload.get("request_id"),
        }


def build_alibaba_request(
    brief: Mapping[str, Any],
    *,
    reference_urls: Sequence[str] = (),
) -> dict[str, Any]:
    """Translate an Edit Brief into Alibaba's multimodal generation shape."""

    if len(reference_urls) > 3:
        raise ValueError("Alibaba Qwen Image 3 accepts at most 3 reference images")
    compiled = compile_edit_brief(brief)
    output = brief.get("output", {})
    interface = brief.get("interface", {})
    is_partner = (
        isinstance(interface, Mapping)
        and interface.get("name") == "partner-compatible"
    )
    size = _resolve_size(output, allow_partner_auto=is_partner)
    model = MODEL_NAMES.get(str(brief.get("model", "qwen/qwen-image-3-pro")))
    if model is None:
        raise ValueError("Unsupported Qwen Image 3 model")
    content = [{"image": url} for url in reference_urls]
    content.append({"text": compiled.prompt})
    parameters: dict[str, Any] = {
        "prompt_extend": True,
        "prompt_extend_mode": "direct",
        "n": int(output.get("count", 1)),
        "watermark": False,
    }
    if size is not None:
        parameters["size"] = size
    if "seed" in output:
        parameters["seed"] = int(output["seed"])
    if is_partner:
        count = parameters["n"]
        if not 1 <= count <= 6:
            raise ValueError("Alibaba output count must be between 1 and 6")
        if "seed" in parameters and not 0 <= parameters["seed"] <= MAX_SEED:
            raise ValueError(f"Seed must be between 0 and {MAX_SEED}")
        parameters["prompt_extend"] = bool(output.get("prompt_extend", True))
        parameters["watermark"] = bool(output.get("watermark", False))
        negative_prompt = brief.get("negative_prompt")
        if isinstance(negative_prompt, str) and negative_prompt:
            parameters["negative_prompt"] = negative_prompt
    return {
        "model": model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": parameters,
    }
