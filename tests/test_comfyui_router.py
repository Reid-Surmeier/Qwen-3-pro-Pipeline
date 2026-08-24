import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from qwen_ui_pipeline.comfyui_router import (
    ComfyUIRouter,
    UpstreamResponse,
)


class _FakeTransport:
    def __init__(self):
        self._lock = threading.Lock()
        self.active = {"http://worker-1": [], "http://worker-2": []}
        self.requests = []
        self.fail_prompt_after_accept = False

    def request(self, backend, method, target, headers=None, body=None):
        headers = headers or {}
        body = body or b""
        with self._lock:
            self.requests.append((backend, method, target, headers, body))
            if method == "GET" and target == "/queue":
                return self._json(
                    {
                        "queue_running": list(self.active[backend]),
                        "queue_pending": [],
                    }
                )
            if method == "POST" and target == "/prompt":
                prompt_id = f"prompt-{len(self.requests)}"
                self.active[backend].append([0, prompt_id])
                if self.fail_prompt_after_accept:
                    raise TimeoutError("backend response timed out after accepting the prompt")
                return self._json({"prompt_id": prompt_id, "number": 1})
            if method == "GET" and target.startswith("/history/"):
                prompt_id = target.removeprefix("/history/")
                matching = [item for item in self.active[backend] if item[1] == prompt_id]
                return self._json({prompt_id: {"outputs": {}}} if matching else {})
            if method == "GET" and target == "/history":
                return self._json(
                    {item[1]: {"outputs": {}} for item in self.active[backend]}
                )
            if method == "GET" and target == "/view?filename=result.png&type=output":
                return UpstreamResponse(
                    status=200,
                    headers=(("Content-Type", "image/png"),),
                    body=b"png-output-bytes",
                )
        return self._json({"backend": backend, "target": target})

    @staticmethod
    def _json(value):
        return UpstreamResponse(
            status=200,
            headers=(("Content-Type", "application/json"),),
            body=json.dumps(value).encode("utf-8"),
        )


class ComfyUIRouterTests(unittest.TestCase):
    def setUp(self):
        self.transport = _FakeTransport()
        self.router = ComfyUIRouter(
            ["http://worker-1", "http://worker-2"],
            transport=self.transport,
        )

    def test_concurrent_prompts_use_separate_workers_without_changing_payload(self):
        bodies = [
            json.dumps({"prompt": {"1": {"class_type": "QwenImage3Render"}}, "n": n}).encode()
            for n in (1, 2)
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(
                executor.map(
                    lambda body: self.router.route(
                        "POST",
                        "/prompt",
                        headers={"Content-Type": "application/json"},
                        body=body,
                    ),
                    bodies,
                )
            )

        prompt_requests = [
            request
            for request in self.transport.requests
            if request[1:3] == ("POST", "/prompt")
        ]
        self.assertEqual(
            {request[0] for request in prompt_requests},
            {"http://worker-1", "http://worker-2"},
        )
        self.assertCountEqual([request[4] for request in prompt_requests], bodies)
        self.assertTrue(all(response.status == 200 for response in responses))

    def test_prompt_history_stays_on_the_worker_that_accepted_it(self):
        response = self.router.route("POST", "/prompt", body=b'{"prompt": {}}')
        prompt_id = json.loads(response.body)["prompt_id"]
        prompt_backend = next(
            request[0]
            for request in self.transport.requests
            if request[1:3] == ("POST", "/prompt")
        )

        history = self.router.route("GET", f"/history/{prompt_id}")

        self.assertIn(prompt_id, json.loads(history.body))
        history_requests = [
            request
            for request in self.transport.requests
            if request[1:3] == ("GET", f"/history/{prompt_id}")
        ]
        self.assertEqual([request[0] for request in history_requests], [prompt_backend])

    def test_unknown_prompt_history_is_discovered_after_router_restart(self):
        self.transport.active["http://worker-2"].append([7, "existing-prompt"])

        history = self.router.route("GET", "/history/existing-prompt")

        self.assertIn("existing-prompt", json.loads(history.body))

    def test_queue_and_history_views_are_aggregated_across_workers(self):
        self.transport.active["http://worker-1"].append([1, "one"])
        self.transport.active["http://worker-2"].append([2, "two"])

        queue = json.loads(self.router.route("GET", "/queue").body)
        history = json.loads(self.router.route("GET", "/history").body)

        self.assertEqual(len(queue["queue_running"]), 2)
        self.assertEqual(set(history), {"one", "two"})

    def test_ambiguous_prompt_failure_is_never_retried_on_another_worker(self):
        self.transport.fail_prompt_after_accept = True

        with self.assertRaisesRegex(TimeoutError, "after accepting"):
            self.router.route("POST", "/prompt", body=b'{"prompt": {}}')

        prompt_requests = [
            request
            for request in self.transport.requests
            if request[1:3] == ("POST", "/prompt")
        ]
        self.assertEqual(len(prompt_requests), 1)

    def test_existing_upload_and_output_routes_pass_through_unchanged(self):
        multipart = (
            b"--boundary\r\nContent-Disposition: form-data\r\n\r\n"
            b"image\r\n--boundary--"
        )

        upload = self.router.route(
            "POST",
            "/upload/image",
            headers={"Content-Type": "multipart/form-data; boundary=boundary"},
            body=multipart,
        )
        output = self.router.route("GET", "/view?filename=result.png&type=output")

        upload_request = next(
            request
            for request in self.transport.requests
            if request[1:3] == ("POST", "/upload/image")
        )
        self.assertEqual(upload_request[0], "http://worker-1")
        self.assertEqual(upload_request[4], multipart)
        self.assertEqual(upload.status, 200)
        self.assertEqual(output.body, b"png-output-bytes")
        self.assertEqual(dict(output.headers)["Content-Type"], "image/png")


if __name__ == "__main__":
    unittest.main()
