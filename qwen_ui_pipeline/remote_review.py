"""Read-only validation for the authenticated ComfyUI review boundary."""

from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import urlsplit


def validate_router_url(
    router_url: str,
    *,
    loopback_addresses: Iterable[str],
    router_port: int = 8188,
) -> str:
    """Require the audited API URL to be the local routed ComfyUI listener."""

    try:
        parsed = urlsplit(router_url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("router URL is malformed") from error
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("router URL must be an HTTP URL with an explicit host")
    if parsed.username or parsed.password:
        raise ValueError("router URL must not contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("router URL must contain only the routed service origin")
    if parsed.hostname not in set(loopback_addresses):
        raise ValueError("router URL host is not assigned to the local loopback device")
    if port != router_port:
        raise ValueError(f"router URL must use routed port {router_port}")
    return router_url.rstrip("/")


def _split_host_port(value: str) -> tuple[str, int] | None:
    if value.startswith("[") and "]:" in value:
        host, port = value[1:].rsplit("]:", 1)
    elif ":" in value:
        host, port = value.rsplit(":", 1)
    else:
        return None
    if not port.isdigit():
        return None
    return host, int(port)


def _listeners(snapshot: str) -> list[dict[str, Any]]:
    listeners = []
    for line in snapshot.splitlines():
        fields = line.split()
        if len(fields) < 4 or fields[0] != "LISTEN":
            continue
        parsed = _split_host_port(fields[3])
        if parsed is None:
            continue
        host, port = parsed
        listeners.append({"address": host, "port": port})
    return listeners


def audit_comfyui_listeners(
    snapshot: str,
    *,
    loopback_addresses: Iterable[str],
    router_port: int = 8188,
    worker_ports: Iterable[int] = range(8191, 8196),
) -> dict[str, Any]:
    """Fail if the routed endpoint or any worker leaves the loopback device."""

    loopbacks = set(loopback_addresses)
    listeners = _listeners(snapshot)

    def require_port(port: int, role: str) -> dict[str, Any]:
        matches = [listener for listener in listeners if listener["port"] == port]
        if not matches:
            raise ValueError(f"{role} port {port} is not listening")
        unsafe = [item for item in matches if item["address"] not in loopbacks]
        if unsafe:
            addresses = ", ".join(item["address"] for item in unsafe)
            raise ValueError(f"{role} port {port} has a non-loopback listener: {addresses}")
        if len(matches) != 1:
            raise ValueError(f"{role} port {port} has multiple listeners")
        return matches[0]

    router = require_port(router_port, "router")
    workers = [require_port(port, "worker") for port in worker_ports]
    return {
        "router": router,
        "workers": workers,
        "workers_loopback_only": True,
    }
