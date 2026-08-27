import unittest

from qwen_ui_pipeline.remote_review import audit_comfyui_listeners


SAFE_LISTENERS = """\
LISTEN 0 128 192.0.2.10:8188 0.0.0.0:*
LISTEN 0 128 192.0.2.10:8191 0.0.0.0:*
LISTEN 0 128 192.0.2.10:8192 0.0.0.0:*
LISTEN 0 128 192.0.2.10:8193 0.0.0.0:*
LISTEN 0 128 192.0.2.10:8194 0.0.0.0:*
LISTEN 0 128 192.0.2.10:8195 0.0.0.0:*
"""


class RemoteReviewAuditTests(unittest.TestCase):
    def test_accepts_router_and_workers_bound_only_to_a_loopback_alias(self):
        audit = audit_comfyui_listeners(
            SAFE_LISTENERS,
            loopback_addresses={"127.0.0.1", "192.0.2.10"},
        )

        self.assertEqual(audit["router"]["port"], 8188)
        self.assertEqual(
            [listener["port"] for listener in audit["workers"]],
            [8191, 8192, 8193, 8194, 8195],
        )
        self.assertTrue(audit["workers_loopback_only"])

    def test_rejects_a_worker_bound_to_every_interface(self):
        unsafe = SAFE_LISTENERS.replace("192.0.2.10:8193", "0.0.0.0:8193")

        with self.assertRaisesRegex(ValueError, "worker port 8193.*non-loopback"):
            audit_comfyui_listeners(
                unsafe,
                loopback_addresses={"127.0.0.1", "192.0.2.10"},
            )

    def test_rejects_a_missing_routed_endpoint(self):
        without_router = "\n".join(
            line for line in SAFE_LISTENERS.splitlines() if ":8188" not in line
        )

        with self.assertRaisesRegex(ValueError, "router port 8188 is not listening"):
            audit_comfyui_listeners(
                without_router,
                loopback_addresses={"127.0.0.1", "192.0.2.10"},
            )


if __name__ == "__main__":
    unittest.main()
