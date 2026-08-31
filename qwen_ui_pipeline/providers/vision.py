"""An OpenRouter-backed reviewer for the independent verification gate.

The reviewing model must not be the model that produced the image. This client
refuses to run against the builder's own family, because an agent that grades
its own output shares the blind spots that produced it, and a weak visual
judgement is precisely the blind spot that matters here.

Only bounded region crops are sent. Whole screenshots are not supported: a
large correct area is exactly what lets a small wrong one pass unnoticed.
"""

from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ..verifier import RegionReview, VisionClient

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

#: Families that build images in this pipeline; a reviewer must be none of them.
BUILDER_FAMILIES = ("qwen/",)

#: Pillow's nearest-neighbour resampling filter, named by value so this module
#: needs no import of Pillow and stays testable on a host without it.
NEAREST_NEIGHBOUR = 0

SYSTEM_PROMPT = """You review one region of a reconstructed user interface against \
the approved source for that same region.

You are given two crops of the SAME rectangle: the approved baseline first, then \
the candidate. Judge only this rectangle.

The candidate is allowed to differ from the baseline where the edit brief \
licensed a change. It is not allowed to lose the source's rendering character: \
crisp aliased bitmap text, one-pixel rules, flat fills, exact glyph shapes, and \
control positions must survive.

Reply with a single JSON object and nothing else:

{"verdict": "match" | "defect",
 "defect_class": "visual-state" | "geometry" | "z-order" | "missing-component" \
| "asset-ownership" | "interaction" | "motion" | "runtime-only",
 "coordinates": [x, y],
 "confidence": 0.0-1.0,
 "note": "one sentence"}

Use "match" only when the candidate would be accepted by someone comparing it \
closely with the source. Use "defect" otherwise, and give coordinates relative \
to the crop's top-left corner pointing at the clearest instance of the problem. \
A defect you cannot point at is not a usable finding. Never reply with prose."""


def _encode(image: Any, scale: int = 1) -> str:
    """Encode a crop as a PNG data URL, optionally magnified.

    Bitmap interface defects -- a caption misregistered by a few pixels, glyphs
    softened by a resample -- are invisible at native size in an 18 pixel tall
    band. Nearest-neighbour magnification adds no information but puts the
    defect above the reviewer's threshold, so it is applied to both crops
    equally.
    """

    image = image.convert("RGB")
    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), NEAREST_NEIGHBOUR)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@dataclass
class OpenRouterVisionClient(VisionClient):
    """Review region crop pairs through a model the builder did not use."""

    api_key: str = ""
    model: str = "anthropic/claude-opus-4.5"
    timeout: int = 120
    scale: int = 4
    calls: list[RegionReview] = field(default_factory=list)
    usage: list[Mapping[str, Any]] = field(default_factory=list)
    _opener: Callable[..., Any] = urllib.request.urlopen

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("an OpenRouter key is required to review")
        if self.model.startswith(BUILDER_FAMILIES):
            raise ValueError(
                f"{self.model} builds images in this pipeline; a reviewer must be "
                "an independent model family"
            )

    def review(self, review: RegionReview) -> Mapping[str, Any]:
        self.calls.append(review)

        instructions = [f"Region under review: {review.region}."]
        if review.intent:
            instructions.append(
                "The edit brief licensed exactly this change in this region: "
                f"{review.intent}\n"
                "That change is intended. Judge whether the candidate carries it "
                "out faithfully and preserves the source's rendering character. "
                "Do not report the licensed change itself as a defect."
            )
        if review.questions:
            instructions.append("Also check each of the following:")
            instructions.extend(f"- {question}" for question in review.questions)

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "\n".join(instructions)},
                        {
                            "type": "text",
                            "text": f"Approved baseline crop (shown at {self.scale}x nearest-neighbour magnification):",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": _encode(review.baseline_crop, self.scale)},
                        },
                        {
                            "type": "text",
                            "text": f"Candidate crop (same {self.scale}x magnification):",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": _encode(review.candidate_crop, self.scale)},
                        },
                    ],
                },
            ],
        }

        request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:400]
            raise RuntimeError(f"reviewer returned HTTP {error.code}: {detail}") from error

        if payload.get("usage"):
            self.usage.append(payload["usage"])

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("reviewer returned no choice")
        content = choices[0].get("message", {}).get("content", "")
        return _strip_fence(content)


def _strip_fence(content: Any) -> str:
    """Unwrap a fenced code block so an otherwise valid verdict still parses."""

    if not isinstance(content, str):
        return content
    text = content.strip()
    if not text.startswith("```"):
        return text
    body = text.split("\n", 1)[1] if "\n" in text else ""
    return body.rsplit("```", 1)[0].strip()
