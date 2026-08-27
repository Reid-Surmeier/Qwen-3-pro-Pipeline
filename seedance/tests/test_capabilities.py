from decimal import Decimal
from pathlib import Path

import pytest

from seedance_icons.capabilities import (
    CapabilityError,
    estimate_cost,
    load_profiles,
    select_model,
    validate_request,
)


@pytest.fixture
def profiles():
    return load_profiles(Path(__file__).parent / "fixtures" / "capabilities.json")


def test_routes_studies_to_mini_and_finals_to_25(profiles):
    assert select_model("study", 6, profiles).id == "bytedance/seedance-2.0-mini"
    assert select_model("final", 20, profiles).id == "bytedance/seedance-2.5"


def test_never_silently_upgrades_long_study(profiles):
    with pytest.raises(CapabilityError, match="Select tier 'final' explicitly"):
        select_model("study", 20, profiles)


def test_validates_size_and_duration(profiles):
    profile = profiles["bytedance/seedance-2.0-mini"]
    validate_request(
        {"model": profile.id, "duration": 6, "size": "720x720", "generate_audio": False},
        profile,
    )
    with pytest.raises(CapabilityError, match="Unsupported size"):
        validate_request({"model": profile.id, "duration": 6, "size": "960x960"}, profile)


def test_rejects_ambiguous_frames_plus_references(profiles):
    profile = profiles["bytedance/seedance-2.0-mini"]
    request = {
        "model": profile.id,
        "duration": 6,
        "size": "720x720",
        "frame_images": [
            {"type": "image_url", "image_url": {"url": "x"}, "frame_type": "first_frame"}
        ],
        "input_references": [{"type": "video_url", "video_url": {"url": "y"}}],
    }
    with pytest.raises(CapabilityError, match="take precedence"):
        validate_request(request, profile)


def test_estimates_cost_from_live_metadata_formula(profiles):
    profile = profiles["bytedance/seedance-2.0-mini"]
    request = {"model": profile.id, "duration": 6, "size": "720x720", "generate_audio": False}
    assert estimate_cost(request, profile) == Decimal("0.2552")


def test_video_reference_selects_video_input_sku(profiles):
    profile = profiles["bytedance/seedance-2.5"]
    request = {
        "model": profile.id,
        "duration": 6,
        "size": "960x960",
        "input_references": [
            {"type": "video_url", "video_url": {"url": "https://example.test/ref.mp4"}}
        ],
    }
    assert estimate_cost(request, profile) == Decimal("0.8294")
