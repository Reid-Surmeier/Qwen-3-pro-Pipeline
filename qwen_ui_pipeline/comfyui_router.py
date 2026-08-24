"""Route one ComfyUI API surface across independent worker processes.

The router deliberately treats the workflow body as opaque.  It changes which
ComfyUI queue receives a prompt, never the Render Pass, provider request, or
output handling performed by that queue.
"""

from __future__ import annotations

import argparse
import json
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import unquote, urlsplit


_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
_BROADCAST_PATHS = {"/free", "/history", "/interrupt", "/queue"}


@dataclass(frozen=True)
class UpstreamResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


class Transport(Protocol):
    def request(
        self,
        backend: str,
        method: str,
        target: str,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> UpstreamResponse: ...


class RouterUnavailable(RuntimeError):
    """Raised when no configured ComfyUI worker can answer a request."""


class URLTransport:
    def __init__(self, *, timeout_seconds: float = 300):
        if timeout_seconds <= 0:
            raise ValueError("upstream timeout must be positive")
        self._timeout_seconds = timeout_seconds

    def request(
        self,
        backend: str,
        method: str,
        target: str,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> UpstreamResponse:
        request_headers = {
            name: value
            for name, value in (headers or {}).items()
            if name.lower() not in _HOP_BY_HOP_HEADERS
            and name.lower() not in {"host", "content-length"}
        }
        request = urllib.request.Request(
            f"{backend}{target}",
            data=body if method not in {"GET", "HEAD"} else None,
            headers=request_headers,
            method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=self._timeout_seconds)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return UpstreamResponse(
                status=response.status,
                headers=tuple(response.headers.items()),
                body=response.read(),
            )


class ComfyUIRouter:
    """Load-aware prompt router with prompt-to-worker history affinity."""

    def __init__(
        self,
        backends: Sequence[str],
        *,
        transport: Transport | None = None,
        probe_transport: Transport | None = None,
    ):
        normalized = tuple(dict.fromkeys(backend.rstrip("/") for backend in backends))
        if not normalized or any(not backend for backend in normalized):
            raise ValueError("at least one non-empty ComfyUI backend is required")
        self.backends = normalized
        self._transport = transport or URLTransport()
        self._probe_transport = probe_transport or self._transport
        self._dispatch_lock = threading.Lock()
        self._mapping_lock = threading.Lock()
        self._prompt_backends: dict[str, str] = {}
        self._tie_cursor = 0

    def route(
        self,
        method: str,
        target: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> UpstreamResponse:
        method = method.upper()
        path = urlsplit(target).path
        if method == "POST" and path == "/prompt":
            return self._route_prompt(target, headers, body)
        if method == "GET" and path == "/queue":
            return self._aggregate_queue(target, headers)
        if method == "GET" and path == "/history":
            return self._aggregate_history(target, headers)
        if method == "GET" and path.startswith("/history/"):
            prompt_id = unquote(path.removeprefix("/history/"))
            return self._route_prompt_history(prompt_id, target, headers)
        if method == "POST" and path in _BROADCAST_PATHS:
            return self._broadcast(method, target, headers, body)
        return self._transport.request(self.backends[0], method, target, headers, body)

    def _route_prompt(
        self,
        target: str,
        headers: Mapping[str, str] | None,
        body: bytes | None,
    ) -> UpstreamResponse:
        # Selection and enqueue are one short critical section.  Once the POST
        # returns, ComfyUI has made the new queue depth visible to the next caller.
        with self._dispatch_lock:
            backend = self._select_backend()
            # Never replay this POST.  A transport timeout is ambiguous because
            # the worker may already have accepted a paid provider Render Pass.
            response = self._transport.request(backend, "POST", target, headers, body)
            if 200 <= response.status < 300:
                prompt_id = _json_object(response).get("prompt_id")
                if isinstance(prompt_id, str) and prompt_id:
                    with self._mapping_lock:
                        self._prompt_backends[prompt_id] = backend
            return response

    def _select_backend(self) -> str:
        responses = self._request_many("GET", "/queue", transport=self._probe_transport)
        loads: list[tuple[int, int, str]] = []
        for index, backend in enumerate(self.backends):
            response = responses.get(backend)
            if response is None or not 200 <= response.status < 300:
                continue
            queue = _json_object(response)
            running = queue.get("queue_running", [])
            pending = queue.get("queue_pending", [])
            if not isinstance(running, list) or not isinstance(pending, list):
                continue
            loads.append((len(running) + len(pending), index, backend))
        if not loads:
            raise RouterUnavailable("no ComfyUI worker answered the queue probe")

        minimum = min(load for load, _, _ in loads)
        tied = [(index, backend) for load, index, backend in loads if load == minimum]
        index, backend = min(
            tied,
            key=lambda item: (item[0] - self._tie_cursor) % len(self.backends),
        )
        self._tie_cursor = (index + 1) % len(self.backends)
        return backend

    def _route_prompt_history(
        self,
        prompt_id: str,
        target: str,
        headers: Mapping[str, str] | None,
    ) -> UpstreamResponse:
        with self._mapping_lock:
            backend = self._prompt_backends.get(prompt_id)
        if backend is not None:
            return self._transport.request(backend, "GET", target, headers)

        responses = self._request_many("GET", target, headers)
        healthy: list[UpstreamResponse] = []
        for candidate_backend in self.backends:
            response = responses.get(candidate_backend)
            if response is None or not 200 <= response.status < 300:
                continue
            healthy.append(response)
            if prompt_id in _json_object(response):
                with self._mapping_lock:
                    self._prompt_backends[prompt_id] = candidate_backend
                return response
        if healthy:
            return _json_response({})
        raise RouterUnavailable("no ComfyUI worker answered the history lookup")

    def _aggregate_queue(
        self,
        target: str,
        headers: Mapping[str, str] | None,
    ) -> UpstreamResponse:
        responses = self._request_many("GET", target, headers)
        running: list[Any] = []
        pending: list[Any] = []
        healthy = 0
        for backend in self.backends:
            response = responses.get(backend)
            if response is None or not 200 <= response.status < 300:
                continue
            queue = _json_object(response)
            backend_running = queue.get("queue_running", [])
            backend_pending = queue.get("queue_pending", [])
            if isinstance(backend_running, list) and isinstance(backend_pending, list):
                running.extend(backend_running)
                pending.extend(backend_pending)
                healthy += 1
        if not healthy:
            raise RouterUnavailable("no ComfyUI worker answered the queue request")
        return _json_response({"queue_running": running, "queue_pending": pending})

    def _aggregate_history(
        self,
        target: str,
        headers: Mapping[str, str] | None,
    ) -> UpstreamResponse:
        responses = self._request_many("GET", target, headers)
        history: dict[str, Any] = {}
        healthy = 0
        for backend in self.backends:
            response = responses.get(backend)
            if response is None or not 200 <= response.status < 300:
                continue
            value = _json_object(response)
            history.update(value)
            healthy += 1
            with self._mapping_lock:
                self._prompt_backends.update(
                    (prompt_id, backend) for prompt_id in value if isinstance(prompt_id, str)
                )
        if not healthy:
            raise RouterUnavailable("no ComfyUI worker answered the history request")
        return _json_response(history)

    def _broadcast(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str] | None,
        body: bytes | None,
    ) -> UpstreamResponse:
        responses = self._request_many(method, target, headers, body)
        for backend in self.backends:
            if backend in responses:
                return responses[backend]
        raise RouterUnavailable(f"no ComfyUI worker answered {method} {target}")

    def _request_many(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
        *,
        transport: Transport | None = None,
    ) -> dict[str, UpstreamResponse]:
        responses: dict[str, UpstreamResponse] = {}
        request_transport = transport or self._transport
        with ThreadPoolExecutor(max_workers=len(self.backends)) as executor:
            futures = {
                executor.submit(
                    request_transport.request,
                    backend,
                    method,
                    target,
                    headers,
                    body,
                ): backend
                for backend in self.backends
            }
            for future in as_completed(futures):
                try:
                    responses[futures[future]] = future.result()
                except (OSError, TimeoutError):
                    continue
        return responses


def _json_object(response: UpstreamResponse) -> dict[str, Any]:
    try:
        value = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _json_response(value: Mapping[str, Any], *, status: int = 200) -> UpstreamResponse:
    body = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return UpstreamResponse(
        status=status,
        headers=(("Content-Type", "application/json"),),
        body=body,
    )


class _RouterHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], router: ComfyUIRouter):
        self.router = router
        super().__init__(address, _RouterRequestHandler)


class _RouterRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "QwenComfyUIRouter/0.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._route()

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._route()

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._route()

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._route()

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._route()

    def _route(self) -> None:
        if self.headers.get("Upgrade", "").lower() == "websocket":
            self._write_response(
                _json_response(
                    {
                        "error": (
                            "WebSocket progress is unavailable through the worker "
                            "router; use HTTP history polling."
                        )
                    },
                    status=426,
                )
            )
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None
        headers = {name: value for name, value in self.headers.items()}
        try:
            response = self.server.router.route(
                self.command,
                self.path,
                headers=headers,
                body=body,
            )
        except RouterUnavailable as error:
            response = _json_response({"error": str(error)}, status=503)
        except (OSError, TimeoutError) as error:
            response = _json_response({"error": str(error)}, status=502)
        self._write_response(response)

    def _write_response(self, response: UpstreamResponse) -> None:
        self.send_response(response.status)
        for name, value in response.headers:
            if name.lower() not in _HOP_BY_HOP_HEADERS and name.lower() != "content-length":
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response.body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qwen-comfyui-router")
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", default=8188, type=int)
    parser.add_argument("--backend", action="append", required=True)
    parser.add_argument("--upstream-timeout", default=300, type=float)
    parser.add_argument("--probe-timeout", default=2, type=float)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    router = ComfyUIRouter(
        args.backend,
        transport=URLTransport(timeout_seconds=args.upstream_timeout),
        probe_transport=URLTransport(timeout_seconds=args.probe_timeout),
    )
    server = _RouterHTTPServer((args.listen, args.port), router)
    print(
        f"ComfyUI router listening on http://{args.listen}:{args.port} "
        f"for {len(router.backends)} workers",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
