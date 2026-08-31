#!/usr/bin/env python3
"""Audit the local side of the authenticated ComfyUI review path without mutation."""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from typing import Any

from qwen_ui_pipeline.remote_review import audit_comfyui_listeners, validate_router_url


def _json_url(base_url: str, path: str) -> Any:
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        headers={"User-Agent": "qwen-ui-pipeline-review-audit/0.1"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read())


def _loopback_addresses() -> set[str]:
    completed = subprocess.run(
        ["ip", "-j", "address", "show", "dev", "lo"],
        check=True,
        capture_output=True,
        text=True,
    )
    records = json.loads(completed.stdout)
    return {
        address["local"]
        for record in records
        for address in record.get("addr_info", [])
        if isinstance(address.get("local"), str)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--router-url", default="http://127.0.0.1:8188")
    args = parser.parse_args()

    sockets = subprocess.run(
        ["ss", "-H", "-ltn"],
        check=True,
        capture_output=True,
        text=True,
    )
    loopback_addresses = _loopback_addresses()
    router_url = validate_router_url(
        args.router_url,
        loopback_addresses=loopback_addresses,
    )
    listener_audit = audit_comfyui_listeners(
        sockets.stdout,
        loopback_addresses=loopback_addresses,
    )
    system_stats = _json_url(router_url, "/system_stats")
    queue = _json_url(router_url, "/queue")
    text_schema = _json_url(router_url, "/object_info/QwenImage3TextToImage")
    edit_schema = _json_url(router_url, "/object_info/QwenImage3Edit")
    if "QwenImage3TextToImage" not in text_schema:
        raise RuntimeError("routed endpoint does not expose QwenImage3TextToImage")
    if "QwenImage3Edit" not in edit_schema:
        raise RuntimeError("routed endpoint does not expose QwenImage3Edit")

    print(
        json.dumps(
            {
                "listener_audit": listener_audit,
                "comfyui_version": system_stats.get("system", {}).get("comfyui_version"),
                "queue_running": len(queue.get("queue_running", [])),
                "queue_pending": len(queue.get("queue_pending", [])),
                "nodes": ["QwenImage3TextToImage", "QwenImage3Edit"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
