from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

import httpx

API_BASE = "https://openrouter.ai/api/v1"


class OpenRouterError(RuntimeError):
    pass


def asset_reference(path_or_url: str, kind: str, frame_type: str | None = None) -> dict[str, Any]:
    if path_or_url.startswith(("https://", "data:")):
        url = path_or_url
    else:
        path = Path(path_or_url)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        url = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
    key = f"{kind}_url"
    result: dict[str, Any] = {"type": key, key: {"url": url}}
    if frame_type:
        result["frame_type"] = frame_type
    return result


def request_digest(request: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def sanitized_request(request: dict[str, Any]) -> dict[str, Any]:
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if not key.startswith("_")}
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, str) and value.startswith("data:"):
            return f"<data-url sha256={hashlib.sha256(value.encode()).hexdigest()}>"
        return value

    return clean(request)


class OpenRouterVideoClient:
    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None):
        api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is required for paid submission or polling")
        self._owned = client is None
        self.client = client or httpx.Client(
            base_url=API_BASE,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )

    def close(self) -> None:
        if self._owned:
            self.client.close()

    def submit(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in request.items() if not key.startswith("_")}
        response = self.client.post("/videos", json=payload)
        response.raise_for_status()
        return response.json()

    def status(self, job_id: str) -> dict[str, Any]:
        response = self.client.get(f"/videos/{job_id}")
        response.raise_for_status()
        return response.json()

    def wait(self, job_id: str, interval: float = 5, timeout: float = 1800) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = self.status(job_id)
            status = job.get("status") or job.get("data", {}).get("status")
            if status == "completed":
                return job
            if status in {"failed", "cancelled", "expired"}:
                raise OpenRouterError(f"Video job ended with status {status}: {job}")
            time.sleep(interval)
        raise TimeoutError(f"Timed out waiting for OpenRouter video job {job_id}")

    def download(self, job_id: str, destination: Path) -> str:
        response = self.client.get(f"/videos/{job_id}/content")
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return hashlib.sha256(response.content).hexdigest()
