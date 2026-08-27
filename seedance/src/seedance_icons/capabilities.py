from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

MODELS_URL = "https://openrouter.ai/api/v1/videos/models"
SUPPORTED_MODELS = (
    "bytedance/seedance-2.0-mini",
    "bytedance/seedance-2.5",
)


class CapabilityError(ValueError):
    """A requested run is unsupported by the selected live model profile."""


@dataclass(frozen=True)
class ModelProfile:
    id: str
    canonical_slug: str
    name: str
    resolutions: tuple[str, ...]
    aspect_ratios: tuple[str, ...]
    sizes: tuple[str, ...]
    durations: tuple[int, ...]
    frame_images: tuple[str, ...]
    generate_audio: bool
    seed: bool
    pricing_skus: dict[str, Decimal]
    passthrough: tuple[str, ...]

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> ModelProfile:
        return cls(
            id=raw["id"],
            canonical_slug=raw["canonical_slug"],
            name=raw["name"],
            resolutions=tuple(raw.get("supported_resolutions", [])),
            aspect_ratios=tuple(raw.get("supported_aspect_ratios", [])),
            sizes=tuple(raw.get("supported_sizes", [])),
            durations=tuple(raw.get("supported_durations", [])),
            frame_images=tuple(raw.get("supported_frame_images", [])),
            generate_audio=bool(raw.get("generate_audio")),
            seed=bool(raw.get("seed")),
            pricing_skus={
                key: Decimal(value) for key, value in raw.get("pricing_skus", {}).items()
            },
            passthrough=tuple(raw.get("allowed_passthrough_parameters", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "canonical_slug": self.canonical_slug,
            "name": self.name,
            "supported_resolutions": list(self.resolutions),
            "supported_aspect_ratios": list(self.aspect_ratios),
            "supported_sizes": list(self.sizes),
            "supported_durations": list(self.durations),
            "supported_frame_images": list(self.frame_images),
            "generate_audio": self.generate_audio,
            "seed": self.seed,
            "pricing_skus": {key: str(value) for key, value in self.pricing_skus.items()},
            "allowed_passthrough_parameters": list(self.passthrough),
        }


def fetch_profiles(client: httpx.Client | None = None) -> dict[str, ModelProfile]:
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.get(MODELS_URL)
        response.raise_for_status()
        rows = response.json()["data"]
    finally:
        if owned:
            client.close()
    profiles = {
        row["id"]: ModelProfile.from_api(row) for row in rows if row.get("id") in SUPPORTED_MODELS
    }
    missing = set(SUPPORTED_MODELS) - profiles.keys()
    if missing:
        raise CapabilityError(f"OpenRouter did not return expected models: {sorted(missing)}")
    return profiles


def load_profiles(path: Path) -> dict[str, ModelProfile]:
    data = json.loads(path.read_text())
    rows = data.get("models", data.get("data", data))
    return {row["id"]: ModelProfile.from_api(row) for row in rows}


def save_profiles(profiles: dict[str, ModelProfile], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"models": [profile.to_dict() for profile in profiles.values()]}
    path.write_text(json.dumps(payload, indent=2) + "\n")


def select_model(tier: str, duration: int, profiles: dict[str, ModelProfile]) -> ModelProfile:
    if tier in profiles:
        selected = profiles[tier]
    elif tier == "study":
        selected = profiles["bytedance/seedance-2.0-mini"]
    elif tier == "final":
        selected = profiles["bytedance/seedance-2.5"]
    else:
        raise CapabilityError(f"Unknown model tier: {tier}")
    if duration not in selected.durations:
        if tier == "study" and duration in profiles["bytedance/seedance-2.5"].durations:
            raise CapabilityError(
                "Seedance 2.0 Mini does not support this duration. Select tier 'final' explicitly; "
                "the pipeline will not silently switch models."
            )
        raise CapabilityError(f"{selected.id} does not support duration {duration}s")
    return selected


def validate_request(request: dict[str, Any], profile: ModelProfile) -> None:
    if request.get("model") != profile.id:
        raise CapabilityError("Request model does not match the selected capability profile")
    duration = request.get("duration")
    if duration not in profile.durations:
        raise CapabilityError(f"Unsupported duration {duration!r} for {profile.id}")
    resolution = request.get("resolution")
    if resolution and resolution not in profile.resolutions:
        raise CapabilityError(f"Unsupported resolution {resolution!r} for {profile.id}")
    aspect = request.get("aspect_ratio")
    if aspect and aspect not in profile.aspect_ratios:
        raise CapabilityError(f"Unsupported aspect ratio {aspect!r} for {profile.id}")
    size = request.get("size")
    if size and size not in profile.sizes:
        raise CapabilityError(f"Unsupported size {size!r} for {profile.id}")
    if size and (resolution or aspect):
        raise CapabilityError("Use exact size or resolution + aspect_ratio, not both")
    frames = request.get("frame_images", [])
    frame_types = [frame.get("frame_type") for frame in frames]
    if len(frame_types) != len(set(frame_types)):
        raise CapabilityError("Only one image per frame_type is allowed")
    unsupported = set(frame_types) - set(profile.frame_images)
    if unsupported:
        raise CapabilityError(f"Unsupported frame types: {sorted(unsupported)}")
    if frames and request.get("input_references") and not request.get("_experimental_mixed_inputs"):
        raise CapabilityError(
            "frame_images take precedence over input_references. Split this into separate runs or "
            "set _experimental_mixed_inputs=true and record the uncertainty."
        )
    if request.get("generate_audio") and not profile.generate_audio:
        raise CapabilityError(f"{profile.id} does not support generated audio")
    if request.get("seed") is not None and not profile.seed:
        raise CapabilityError(f"{profile.id} does not support seed")


def dimensions(request: dict[str, Any], profile: ModelProfile) -> tuple[int, int]:
    if request.get("size"):
        width, height = request["size"].split("x", 1)
        return int(width), int(height)
    resolution = request.get("resolution")
    aspect = request.get("aspect_ratio")
    matches = [size for size in profile.sizes if _size_matches(size, resolution, aspect)]
    if not matches:
        raise CapabilityError("Could not map resolution/aspect ratio to a supported exact size")
    width, height = matches[0].split("x", 1)
    return int(width), int(height)


def _size_matches(size: str, resolution: str | None, aspect: str | None) -> bool:
    width, height = (int(value) for value in size.split("x", 1))
    if resolution and min(width, height) != int(resolution.removesuffix("p")):
        return False
    if aspect:
        left, right = (int(value) for value in aspect.split(":"))
        return abs((width / height) - (left / right)) < 0.03
    return True


def estimate_cost(request: dict[str, Any], profile: ModelProfile) -> Decimal:
    """Estimate from OpenRouter's live video-token metadata; this is not an invoice."""
    width, height = dimensions(request, profile)
    video_tokens = Decimal(width * height * request["duration"] * 24) / Decimal(1024)
    references = request.get("input_references", [])
    has_video_reference = any(ref.get("type") == "video_url" for ref in references)
    if has_video_reference and "video_tokens_with_video_input" in profile.pricing_skus:
        sku = "video_tokens_with_video_input"
    elif not request.get("generate_audio") and "video_tokens_without_audio" in profile.pricing_skus:
        sku = "video_tokens_without_audio"
    else:
        sku = "video_tokens"
    return (video_tokens * profile.pricing_skus[sku]).quantize(Decimal("0.0001"))
