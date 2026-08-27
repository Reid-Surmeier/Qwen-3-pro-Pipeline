import json
from pathlib import Path

import httpx

from seedance_icons.openrouter import OpenRouterVideoClient, asset_reference, sanitized_request


def test_asset_reference_encodes_local_image(tmp_path: Path):
    image = tmp_path / "icon.png"
    image.write_bytes(b"png bytes")
    ref = asset_reference(str(image), "image", "first_frame")
    assert ref["type"] == "image_url"
    assert ref["frame_type"] == "first_frame"
    assert ref["image_url"]["url"].startswith("data:image/png;base64,")


def test_sanitization_removes_data_urls_and_internal_fields():
    result = sanitized_request({"_note": True, "image": "data:image/png;base64,abc"})
    assert "_note" not in result
    assert result["image"].startswith("<data-url sha256=")


def test_client_uses_async_video_endpoints(tmp_path: Path):
    calls = []

    def handler(request: httpx.Request):
        calls.append((request.method, request.url.path))
        if request.method == "POST":
            assert json.loads(request.content)["model"] == "bytedance/seedance-2.0-mini"
            return httpx.Response(200, json={"id": "job-1", "status": "pending"})
        if request.url.path.endswith("/content"):
            return httpx.Response(200, content=b"video")
        return httpx.Response(200, json={"id": "job-1", "status": "completed"})

    http = httpx.Client(
        base_url="https://openrouter.ai/api/v1", transport=httpx.MockTransport(handler)
    )
    client = OpenRouterVideoClient("test-key", http)
    assert client.submit({"model": "bytedance/seedance-2.0-mini"})["id"] == "job-1"
    assert client.wait("job-1", interval=0)["status"] == "completed"
    assert client.download("job-1", tmp_path / "output.mp4")
    assert calls == [
        ("POST", "/api/v1/videos"),
        ("GET", "/api/v1/videos/job-1"),
        ("GET", "/api/v1/videos/job-1/content"),
    ]
